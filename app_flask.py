# app_flask.py
from flask import Flask, render_template, request, jsonify, session, url_for, redirect
import uuid
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import database

# Initialize the database when the app starts
database.init_db()

# Impor komponen yang diperlukan langsung dari agent.py
try:
    from agent import get_gizibot_response, WELCOME_MSG, NutritionState, GIZIBOT_SYSINT, final_nutrition_chatbot_graph
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
except ImportError as e:
    print(f"Error importing components from agent.py: {e}")
    exit(1)


app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB max file size

AGENT_HAS_CHECKPOINTER = final_nutrition_chatbot_graph.checkpointer is not None
print(f"Agent memiliki checkpointer: {AGENT_HAS_CHECKPOINTER}")

DEFAULT_USER_PROFILE = {
    "name": "Anonim",
    "children": [],
    "profile_set": False
}

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
            print(f"Session ID dari URL ({current_session_id}) tidak valid, membuat sesi baru.")
            new_session_id = database.create_new_session(user_id="default_user", title="Percakapan Baru")
            session['current_session_id'] = new_session_id
            database.save_message(new_session_id, 'assistant', WELCOME_MSG, datetime.now())
        else:
            session['current_session_id'] = current_session_id
            print(f"Menggunakan session ID dari URL: {current_session_id}")
    elif 'current_session_id' not in session:
        print("Tidak ada session ID di URL atau session, membuat sesi baru.")
        new_session_id = database.create_new_session(user_id="default_user", title="Percakapan Baru")
        session['current_session_id'] = new_session_id
        database.save_message(new_session_id, 'assistant', WELCOME_MSG, datetime.now())
    else:
        if not database.get_session_by_id(session['current_session_id']):
            print(f"Session ID di session ({session['current_session_id']}) tidak valid, membuat sesi baru.")
            new_session_id = database.create_new_session(user_id="default_user", title="Percakapan Baru")
            session['current_session_id'] = new_session_id
            database.save_message(new_session_id, 'assistant', WELCOME_MSG, datetime.now())
        else:
            print(f"Menggunakan session ID dari session: {session['current_session_id']}")


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
def chat():
    """Endpoint untuk interaksi chat dengan GiziBot."""
    current_session_id = session.get('current_session_id')
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

        children_info_formatted = [
            {"name": child['name'], "age": child['age'], "gender": child['gender']}
            for child in user_profile.get('children', [])
        ]
        extracted_user_info = {
            "user_name": user_profile['name'],
            "children_info": children_info_formatted,
        }

        agent_initial_state = NutritionState(
            messages=langchain_messages_history,
            user_age_group="",
            dietary_preferences=[],
            nutritional_needs=[],
            recommended_menu=[],
            finished_recommendation=False,
            extracted_user_info=extracted_user_info
        )

        result_state = get_gizibot_response(agent_initial_state)

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

        bot_response_content = bot_response_message.content if bot_response_message else "Maaf, GiziBot tidak dapat memberikan respons saat ini. Coba ulangi pertanyaan Anda."

        database.save_message(current_session_id, 'assistant', bot_response_content, datetime.now())

        return jsonify({
            'response': bot_response_content,
            'status': 'success'
        })

    except Exception as e:
        print(f"Error in /chat endpoint: {str(e)}")
        error_msg_content = f"Terjadi kesalahan internal: {str(e)}. Mohon coba lagi."
        if current_session_id:
            database.save_message(current_session_id, 'assistant', error_msg_content, datetime.now())
        return jsonify({
            'response': error_msg_content,
            'status': 'error'
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
    if user_profile['name'] == 'Anonim' and not user_profile['children']:
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

        profile_set_flag = bool(user_name and user_name != 'Anonim') or \
                           any(child.get('name') and child.get('age') and child.get('gender') for child in children_data)


        formatted_children = []
        for child in children_data:
            if child.get('name') and child.get('age') and child.get('gender'):
                try:
                    formatted_children.append({
                        "name": child['name'],
                        "age": int(child['age']),
                        "gender": child['gender']
                    })
                except ValueError:
                    pass

        session['user_profile'] = {
            "name": user_name if user_name else "Anonim",
            "children": formatted_children,
            "profile_set": profile_set_flag
        }

        session.modified = True
        return jsonify({'status': 'success', 'message': 'Profil berhasil diperbarui.', 'user_profile': session['user_profile']})
    except Exception as e:
        print(f"Error updating profile: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Gagal memperbarui profil: {str(e)}'}), 500


if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=5000)