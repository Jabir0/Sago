# app_flask.py
from flask import Flask, render_template, request, jsonify, session, url_for, redirect
import uuid
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import database
import logging # Import logging module
import time # Import time for sleep
import random # Import random for jitter
from functools import wraps

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Initialize the database when the app starts
database.init_db()

# Impor komponen yang diperlukan langsung dari agent.py
try:
    from agent import get_sago_response, WELCOME_MSG, NutritionState, SAGO_SYSINT, final_nutrition_chatbot_graph
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
    from google.api_core.exceptions import ResourceExhausted, InternalServerError, DeadlineExceeded, ServiceUnavailable # Import specific exceptions for rate limits and 5xx errors
except ImportError as e:
    logging.error(f"Error importing components from agent.py: {e}")
    exit(1)


app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB max file size

AGENT_HAS_CHECKPOINTER = final_nutrition_chatbot_graph.checkpointer is not None
logging.info(f"Agent memiliki checkpointer: {AGENT_HAS_CHECKPOINTER}")

DEFAULT_USER_PROFILE = {
    "name": "Anonim",
    "children": [],
    "profile_set": False
}

# Enhanced retry decorator dengan exponential backoff dan jitter
def retry_on_api_error(max_retries=5, initial_delay=2, max_delay=60, backoff_multiplier=2):
    """
    Enhanced retry decorator untuk mengatasi rate limiting dengan:
    - Exponential backoff dengan jitter
    - Max delay cap
    - Retry untuk berbagai error types
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (ResourceExhausted, DeadlineExceeded, ServiceUnavailable) as e:
                    last_exception = e
                    # Untuk rate limit, tunggu lebih lama
                    if isinstance(e, ResourceExhausted):
                        delay = min(delay * 2, max_delay)  # Cap at max_delay
                        # Add jitter untuk menghindari thundering herd
                        jitter = random.uniform(0.1, 0.5) * delay
                        actual_delay = delay + jitter
                        
                        logging.warning(f"Rate limit hit (attempt {attempt+1}/{max_retries}): {type(e).__name__} - {e}. Retrying in {actual_delay:.2f} seconds...")
                        time.sleep(actual_delay)
                    else:
                        # Untuk error lain, delay lebih pendek
                        actual_delay = min(delay, 10) + random.uniform(0, 2)
                        logging.warning(f"API Error caught (attempt {attempt+1}/{max_retries}): {type(e).__name__} - {e}. Retrying in {actual_delay:.2f} seconds...")
                        time.sleep(actual_delay)
                        delay = min(delay * backoff_multiplier, max_delay)
                        
                except InternalServerError as e:
                    last_exception = e
                    # Untuk 5xx errors, retry dengan delay yang lebih pendek
                    actual_delay = min(delay, 15) + random.uniform(0, 3)
                    logging.warning(f"Server Error (attempt {attempt+1}/{max_retries}): {type(e).__name__} - {e}. Retrying in {actual_delay:.2f} seconds...")
                    time.sleep(actual_delay)
                    delay = min(delay * 1.5, max_delay)  # Slower backoff for server errors
                    
                except Exception as e:
                    # For other exceptions, re-raise immediately (don't retry)
                    logging.error(f"Non-retryable error in {func.__name__}: {type(e).__name__} - {e}")
                    raise e
                    
            # If all retries fail, raise the last exception
            logging.error(f"Max retries ({max_retries}) exceeded for {func.__name__}. Last error: {type(last_exception).__name__} - {last_exception}")
            raise last_exception
            
        return wrapper
    return decorator

# Rate limiting dengan simple in-memory counter
class SimpleRateLimiter:
    def __init__(self):
        self.requests = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def is_allowed(self, key, max_requests=10, window_seconds=60):
        current_time = time.time()
        
        # Cleanup old entries periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup(current_time)
            self.last_cleanup = current_time
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [req_time for req_time in self.requests[key] 
                             if current_time - req_time < window_seconds]
        
        # Check if under limit
        if len(self.requests[key]) < max_requests:
            self.requests[key].append(current_time)
            return True
        return False
    
    def _cleanup(self, current_time):
        """Remove old entries to prevent memory leak"""
        keys_to_remove = []
        for key, timestamps in self.requests.items():
            # Remove entries older than 5 minutes
            recent_timestamps = [t for t in timestamps if current_time - t < 300]
            if not recent_timestamps:
                keys_to_remove.append(key)
            else:
                self.requests[key] = recent_timestamps
        
        for key in keys_to_remove:
            del self.requests[key]

rate_limiter = SimpleRateLimiter()

@app.route('/')
def home_index(): # Mengubah nama fungsi dan route utama
    """Halaman utama aplikasi, sekarang merender home.html."""
    return render_template('home.html')

@app.route('/chatbot.html') # Route baru untuk halaman chatbot (sebelumnya index.html)
def index():
    """Halaman aplikasi chatbot."""
    if 'user_profile' not in session:
        session['user_profile'] = DEFAULT_USER_PROFILE.copy()

    current_session_id = request.args.get('session_id')

    # Logika untuk menentukan session_id yang akan digunakan
    if current_session_id:
        if not database.get_session_by_id(current_session_id):
            logging.info(f"Session ID dari URL ({current_session_id}) tidak valid, membuat sesi baru.")
            new_session_id = database.create_new_session(user_id="default_user", title="Percakapan Baru")
            session['current_session_id'] = new_session_id
            database.save_message(new_session_id, 'assistant', WELCOME_MSG, datetime.now())
        else:
            session['current_session_id'] = current_session_id
            logging.info(f"Menggunakan session ID dari URL: {current_session_id}")
    elif 'current_session_id' not in session:
        logging.info("Tidak ada session ID di URL atau session, membuat sesi baru.")
        new_session_id = database.create_new_session(user_id="default_user", title="Percakapan Baru")
        session['current_session_id'] = new_session_id
        database.save_message(new_session_id, 'assistant', WELCOME_MSG, datetime.now())
    else:
        if not database.get_session_by_id(session['current_session_id']):
            logging.info(f"Session ID di session ({session['current_session_id']}) tidak valid, membuat sesi baru.")
            new_session_id = database.create_new_session(user_id="default_user", title="Percakapan Baru")
            session['current_session_id'] = new_session_id
            database.save_message(new_session_id, 'assistant', WELCOME_MSG, datetime.now())
        else:
            logging.info(f"Menggunakan session ID dari session: {session['current_session_id']}")


    initial_messages = database.get_messages_for_session(session['current_session_id'])

    if not initial_messages:
        database.save_message(session['current_session_id'], 'assistant', WELCOME_MSG, datetime.now())
        initial_messages = database.get_messages_for_session(session['current_session_id'])

    chat_sessions = database.get_all_sessions(user_id="default_user")

    return render_template('chatbot.html',
                           initial_messages=initial_messages,
                           user_profile=session['user_profile'],
                           chat_sessions=chat_sessions,
                           current_session_id=session['current_session_id'])


@app.route('/chat', methods=['POST'])
@retry_on_api_error(max_retries=5, initial_delay=2, max_delay=60) # Enhanced retry decorator
def chat():
    """Endpoint untuk interaksi chat dengan Sago."""
    current_session_id = session.get('current_session_id')
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    
    # Rate limiting check
    if not rate_limiter.is_allowed(f"chat_{client_ip}", max_requests=15, window_seconds=60):
        error_msg = "Terlalu banyak permintaan. Mohon tunggu sebentar sebelum mengirim pesan lagi."
        if current_session_id:
            database.save_message(current_session_id, 'assistant', error_msg, datetime.now())
        return jsonify({
            'response': error_msg,
            'status': 'error',
            'error_type': 'rate_limit_client'
        }), 429
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Pesan tidak boleh kosong'}), 400

        if not current_session_id:
            new_session_id = database.create_new_session(user_id="default_user", title="Percakapan Baru")
            session['current_session_id'] = new_session_id
            current_session_id = new_session_id
            database.save_message(current_session_id, 'assistant', WELCOME_MSG, datetime.now())

        user_profile = session.get('user_profile', DEFAULT_USER_PROFILE.copy())
        if not user_profile.get('profile_set', False): # Cek flag profile_set
            # Periksa jika nama atau anak-anak tidak ada/kosong
            if user_profile['name'] == 'Anonim' and not user_profile['children']:
                return jsonify({
                    'response': 'Untuk memberikan rekomendasi yang personal, mohon lengkapi profil Anda terlebih dahulu (nama Anda dan info anak).',
                    'status': 'profile_required'
                }), 400

        # Logika update judul sesi
        # Cek apakah ini pesan pertama dalam sesi (selain welcome message)
        existing_messages = database.get_messages_for_session(current_session_id)
        if len(existing_messages) == 1 and existing_messages[0]['role'] == 'assistant' and existing_messages[0]['content'] == WELCOME_MSG:
            # Ini adalah pesan pengguna pertama, gunakan untuk judul sesi
            new_title = user_message[:50] # Ambil 50 karakter pertama sebagai judul
            if len(user_message) > 50:
                new_title += "..."
            database.update_session_title(current_session_id, new_title) # Panggil fungsi baru

        # Save user message to database
        database.save_message(current_session_id, 'user', user_message, datetime.now())

        db_messages_raw = database.get_messages_for_session(current_session_id)
        langchain_messages_history = []
        for msg_dict in db_messages_raw:
            if msg_dict['role'] == 'user':
                langchain_messages_history.append(HumanMessage(content=msg_dict['content']))
            elif msg_dict['role'] == 'assistant':
                langchain_messages_history.append(AIMessage(content=msg_dict['content']))

        children_info_formatted = []
        for child in user_profile.get('children', []):
            # Hanya sertakan anak yang umurnya valid untuk agen
            if 5 <= int(child['age']) <= 18:
                children_info_formatted.append({
                    "name": child['name'],
                    "age": int(child['age']),
                    "gender": child['gender']
                })
        extracted_user_info = {
            "user_name": user_profile['name'],
            "children_info": children_info_formatted, # Hanya anak yang valid
            # Tambahkan placeholders untuk BMI info jika belum ada
            "children_bmi_info": user_profile.get("children_bmi_info", {}) 
        }

        agent_initial_state = NutritionState(
            messages=langchain_messages_history,
            user_age_group="", # Ini akan diisi oleh agent jika terdeteksi dari pesan atau profil
            dietary_preferences=[],
            nutritional_needs=[],
            recommended_menu=[],
            finished_recommendation=False,
            extracted_user_info=extracted_user_info
        )

        # Add small delay before API call to be respectful
        time.sleep(0.5)
        
        result_state = get_sago_response(agent_initial_state) # Menggunakan get_sago_response

        bot_response_message = None
        if result_state and result_state["messages"]:
            for msg in reversed(result_state["messages"]):
                if isinstance(msg, AIMessage):
                    bot_response_message = msg
                    break
            if not bot_response_message:
                for msg in reversed(result_state["messages"]):
                    if isinstance(msg, ToolMessage):
                        bot_response_message = msg
                        break

        bot_response_content = bot_response_message.content if bot_response_message else "Maaf, Sago tidak dapat memberikan respons saat ini. Coba ulangi pertanyaan Anda." # Menggunakan Sago

        database.save_message(current_session_id, 'assistant', bot_response_content, datetime.now())

        # Update session user_profile with any new extracted_user_info, especially BMI
        updated_extracted_info = result_state.get("extracted_user_info", {})
        if "children_bmi_info" in updated_extracted_info:
            session['user_profile']['children_bmi_info'] = updated_extracted_info['children_bmi_info']
            session.modified = True # Penting untuk menyimpan perubahan ke session

        return jsonify({
            'response': bot_response_content,
            'status': 'success',
            'user_profile': session['user_profile'] # Kirim user_profile kembali agar frontend bisa update BMI di sidebar
        })

    except (ResourceExhausted, DeadlineExceeded, ServiceUnavailable) as e:
        logging.error(f"API rate limit/timeout error in /chat endpoint: {str(e)}")
        
        if isinstance(e, ResourceExhausted):
            error_msg_content = "Maaf, Sago sedang sangat sibuk atau mencapai batas penggunaan. Mohon tunggu 1-2 menit dan coba lagi. Terima kasih atas kesabaran Anda! 🙏"
            error_type = 'rate_limit'
            status_code = 429
        else:
            error_msg_content = "Maaf, koneksi ke Sago sedang lambat. Mohon tunggu sebentar dan coba lagi."
            error_type = 'timeout'
            status_code = 503
            
        if current_session_id:
            database.save_message(current_session_id, 'assistant', error_msg_content, datetime.now())
        return jsonify({
            'response': error_msg_content, 
            'status': 'error', 
            'error_type': error_type
        }), status_code
        
    except InternalServerError as e:
        logging.error(f"Server error in /chat endpoint: {str(e)}")
        error_msg_content = "Maaf, ada masalah di server Sago. Kami sedang memperbaikinya. Mohon coba lagi dalam beberapa menit."
        if current_session_id:
            database.save_message(current_session_id, 'assistant', error_msg_content, datetime.now())
        return jsonify({
            'response': error_msg_content, 
            'status': 'error', 
            'error_type': 'server_error'
        }), 500
        
    except Exception as e:
        logging.error(f"Unexpected error in /chat endpoint: {str(e)}")
        
        # Handle specific error patterns
        error_msg_content = "Maaf, terjadi kesalahan saat memproses permintaan Anda. Mohon coba lagi."
        
        if "could not parse tool call" in str(e).lower() or "invalid tool call" in str(e).lower():
            error_msg_content = "Maaf, saya kesulitan memahami format permintaan Anda. Bisakah Anda coba jelaskan lebih sederhana?"
        elif "timeout" in str(e).lower():
            error_msg_content = "Maaf, respons Sago membutuhkan waktu terlalu lama. Mohon coba lagi dengan pertanyaan yang lebih sederhana."
        elif "connection" in str(e).lower():
            error_msg_content = "Maaf, ada masalah koneksi. Mohon periksa internet Anda dan coba lagi."
        
        if current_session_id:
            database.save_message(current_session_id, 'assistant', error_msg_content, datetime.now())
        return jsonify({
            'response': error_msg_content,
            'status': 'error',
            'error_details': str(e) if app.debug else None  # Only show details in debug mode
        }), 500


@app.route('/get_chat_sessions')
def get_chat_sessions():
    sessions_db = database.get_all_sessions(user_id="default_user")

    formatted_sessions = []
    for sess in sessions_db:
        created_at_dt = datetime.fromisoformat(sess['created_at']) if isinstance(sess['created_at'], str) else sess['created_at']
        updated_at_dt = datetime.fromisoformat(sess['updated_at']) if isinstance(sess['updated_at'], str) else sess['updated_at']

        formatted_sessions.append({
            'session_id': sess['id'],
            'title': sess['title'],
            'created_at': created_at_dt.isoformat(),
            'updated_at': updated_at_dt.isoformat(),
            'display_updated_at': updated_at_dt.strftime('%d/%m %H:%M')
        })
    return jsonify({'sessions': formatted_sessions})

@app.route('/get_chat_history/<session_id>')
def get_chat_history(session_id):
    messages = database.get_messages_for_session(session_id)
    session['current_session_id'] = session_id
    for msg in messages:
        msg['timestamp'] = msg['timestamp'].strftime('%Y-%m-%dT%H:%M:%S.%f%z')
    return jsonify({'messages': messages, 'current_session_id': session_id})

@app.route('/delete_chat_session/<session_id>', methods=['POST'])
def delete_chat_session_route(session_id):
    database.delete_session(session_id)
    if session.get('current_session_id') == session_id:
        new_session_id = database.create_new_session(user_id="default_user", title="Percakapan Baru")
        session['current_session_id'] = new_session_id
        database.save_message(new_session_id, 'assistant', WELCOME_MSG, datetime.now())
        return jsonify({'status': 'success', 'message': 'Sesi dihapus dan sesi baru dimulai.', 'new_session_id': new_session_id, 'redirect': url_for('index', session_id=new_session_id)})
    return jsonify({'status': 'success', 'message': 'Sesi dihapus.'})

# ROUTE untuk home.html (sekarang menjadi halaman utama)
@app.route('/home.html')
def gizibot_home_page():
    return render_template('home.html')

# ROUTE untuk articles.html
@app.route('/articles.html')
def gizibot_article_page():
    return render_template('articles.html')

@app.route('/recipes.html')
def gizibot_recipes_page():
    return render_template('recipes.html')

# ROUTE untuk article-detail.html (sebelumnya property-details.html)
@app.route('/article-detail.html')
def gizibot_article_detail_page():
    return render_template('article-detail.html')


@app.route('/new_chat_session', methods=['POST'])
def new_chat_session_route():
    user_profile = session.get('user_profile', DEFAULT_USER_PROFILE.copy())
    # Cek apakah profil sudah diset dengan nama atau anak yang valid
    if not user_profile.get('profile_set', False):
        return jsonify({
            'response': 'Untuk memulai percakapan baru, mohon lengkapi profil Anda terlebih dahulu (nama Anda dan info anak).',
            'status': 'profile_required'
        }), 400

    new_session_id = database.create_new_session(user_id="default_user", title="Percakapan Baru")
    session['current_session_id'] = new_session_id
    database.save_message(new_session_id, 'assistant', WELCOME_MSG, datetime.now())
    return jsonify({'status': 'success', 'message': 'Sesi baru dimulai.', 'new_session_id': new_session_id, 'redirect': url_for('index', session_id=new_session_id)})


@app.route('/clear', methods=['POST'])
def clear_all_chats_route():
    database.delete_all_sessions(user_id="default_user")
    new_session_id = database.create_new_session(user_id="default_user", title="Percakapan Baru")
    session['current_session_id'] = new_session_id
    database.save_message(new_session_id, 'assistant', WELCOME_MSG, datetime.now())

    return jsonify({'status': 'success', 'message': 'Semua riwayat chat telah dihapus. Sesi baru dimulai.', 'new_session_id': new_session_id, 'redirect': url_for('index', session_id=new_session_id)})

@app.route('/update_profile', methods=['POST'])
def update_profile():
    try:
        data = request.get_json()

        user_name = data.get('userName', '').strip()
        children_data = data.get('children', [])

        profile_set_flag = bool(user_name and user_name != 'Anonim') # Setidaknya nama pengguna
        
        valid_children = []
        for child in children_data:
            c_name = child.get('name', '').strip()
            c_age = child.get('age')
            c_gender = child.get('gender', '').strip()

            if not c_name or not c_age or not c_gender:
                # Lewati anak yang datanya tidak lengkap
                continue
            
            try:
                c_age = int(c_age)
                # Validasi usia sesuai Kemenkes: 5-9 tahun (anak), 10-18 tahun (remaja)
                if not (5 <= c_age <= 18):
                    return jsonify({'status': 'error', 'message': f'Umur {c_name} ({c_age} tahun) tidak valid. Sago hanya melayani anak usia 5-18 tahun.'}), 400
                
                valid_children.append({
                    "name": c_name,
                    "age": c_age,
                    "gender": c_gender
                })
                # Jika ada anak yang valid, set profile_set_flag menjadi True
                profile_set_flag = True
            except ValueError:
                return jsonify({'status': 'error', 'message': f'Umur {c_name} tidak valid. Mohon masukkan angka.'}), 400

        session['user_profile'] = {
            "name": user_name if user_name else "Anonim",
            "children": valid_children,
            "profile_set": profile_set_flag,
            "children_bmi_info": session.get('user_profile', {}).get("children_bmi_info", {}) # Pertahankan info BMI
        }

        session.modified = True
        return jsonify({'status': 'success', 'message': 'Profil berhasil diperbarui.', 'user_profile': session['user_profile']})
    except Exception as e:
        logging.error(f"Error updating profile: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Gagal memperbarui profil: {str(e)}'}), 500

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'rate_limiter_stats': {
            'active_keys': len(rate_limiter.requests),
            'total_tracked_requests': sum(len(reqs) for reqs in rate_limiter.requests.values())
        }
    })

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=5000)