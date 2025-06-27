# agent.py
from json import tool
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GOOGLE_API_KEY environment variable not set. Please set it in your .env file or environment.")

# --- Import Library yang Dibutuhkan ---
from typing import Annotated, TypedDict, Literal, Iterable
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages.ai import AIMessage
from langchain_core.messages.human import HumanMessage
from langchain_core.messages.tool import ToolMessage
from datetime import datetime # Import datetime for timestamp
from langchain_core.tools import tool


print("\nLibrary dan konfigurasi awal berhasil dimuat.")

# --- Definisi State untuk Sago ---
class NutritionState(TypedDict):
    """State yang merepresentasikan percakapan nutrisi pengguna."""
    messages: Annotated[list, add_messages]
    user_age_group: str # 'anak' (5-9 tahun) atau 'remaja' (10-18 tahun)
    dietary_preferences: list[str]
    nutritional_needs: list[str]
    recommended_menu: list[str]
    finished_recommendation: bool
    extracted_user_info: dict

print("Skema NutritionState berhasil didefinisikan.")

# --- Instruksi Sistem Sago (Diperkaya untuk Logat & Empati) ---
SAGO_SYSINT = (
    "system",
    "Anda adalah Sago, sebuah chatbot cerdas dan ramah yang dirancang khusus untuk membantu orang tua atau pengasuh "
    "dalam mendidik dan memberikan rekomendasi gizi kepada mereka untuk anak-anak dan remaja mereka. "
    "Fokus utama Anda adalah menyediakan informasi nutrisi dan rekomendasi menu yang dipersonalisasi "
    "berdasarkan kelompok usia anak (anak 5-9 tahun, remaja 10-18 tahun), jenis kelamin, kebutuhan gizi, dan preferensi makan mereka. "
    "Jika pertanyaan umum tentang gizi diajukan, selalu coba kaitkan respons dengan bagaimana informasi tersebut berlaku untuk gizi anak-anak atau remaja. "
    "Jika pengguna menyimpang dari topik gizi anak/remaja, arahkan percakapan kembali dengan sopan. "
    "Selalu berikan informasi yang akurat, relevan, dan mudah dipahami oleh orang tua, dengan nada yang mendukung dan positif. "
    "\n\n"
    "**Sangat penting:** Saat berkomunikasi, adopsi gaya bicara yang ramah dan akrab khas masyarakat Sulawesi Tenggara. Sisipkan frasa seperti 'iyo', 'nda apa-apa', 'santai mi dulu', 'mantapji kalau begitu', 'marijo', 'palu'. Gunakan intonasi dan struktur kalimat yang merefleksikan logat lokal untuk menciptakan kesan yang membumi dan akrab, bukan hanya sekadar menyisipkan kata."
    "**Contoh gaya bahasa yang diinginkan:**\n"
    "- Jika anak sehat: 'Iyo, kalau begini bae, anakta masih tergolong sehatji. Tapi lebih bagusmi tambahi sayur-sayur sedikit tiap hari, e.'\n"
    "- Jika ada kekhawatiran: 'Santai mi dulu, nda usah terlalu khawatir. Banyak juga anak di desa yang seperti itu, tapi pelan-pelanmi kita bantu atur makannya.' Berikan penguatan positif dan dorongan.\n"
    "- Jika memberi nasihat: 'Mantapji kalau begitu! Ingat, toh, gizi seimbang itu kunci utama untuk anak-anak kita, palu.'\n"
    "\n"
    "**Sangat Penting:** Untuk pencarian nilai gizi makanan, Anda memiliki akses ke dua dataset CSV: "
    "satu dalam Bahasa Inggris ('food') dan satu lagi yang juga memiliki kolom terjemahan Bahasa Indonesia ('makanan_indonesia'). "
    "**Pencarian Prioritas:** "
    "1.  **Coba cari langsung di kolom 'makanan_indonesia' pada dataset Bahasa Indonesia.** "
    "2.  **Jika tidak ditemukan, coba cari di kolom 'food' pada dataset Bahasa Inggris.** "
    "Ini memungkinkan pengguna bertanya dalam Bahasa Indonesia atau Inggris. "
    "Pastikan untuk memberikan respons nilai gizi dalam Bahasa Indonesia yang mudah dipahami dan ramah kepada pengguna. "
    "Jika nama makanan tidak dapat ditemukan di kedua dataset, berikan pesan bahwa informasi tidak tersedia dan sarankan makanan umum."
    "Untuk resep masakan, Anda hanya bisa membuat resep sederhana yang umum. Jangan mencoba mencari resep dari eksternal."
    "\n\n"
    "**Penting untuk Perhitungan BMI:** Anda dapat menghitung dan menganalisis BMI anak/remaja. Jika diminta untuk membahas berat/tinggi badan atau BMI, "
    "atau jika ingin memberikan rekomendasi yang lebih spesifik untuk kondisi berat badan (misalnya, menaikkan berat badan anak, menurunkan berat badan anak), "
    "pertama-tama **mintalah tinggi badan (cm) dan berat badan (kg) anak**. "
    "Gunakan alat `calculate_bmi_and_analyze` dengan informasi umur dan jenis kelamin yang sudah ada di profil (jika tersedia), atau tanyakan jika tidak ada. "
    "Setelah analisis BMI, berikan saran gizi dan **rekomendasi tindak lanjut yang jelas**: apakah perlu konsultasi ke posyandu, puskesmas, atau rujukan ke dokter spesialis."
    "Untuk interpretasi BMI, gunakan kategorisasi umum untuk anak/remaja (kurus, normal, gemuk, obesitas) sebagai panduan awal, "
    "dan selalu sebutkan bahwa konsultasi dengan profesional kesehatan lebih lanjut sangat disarankan."
    "**Jika hasil BMI menunjukkan status gizi 'kurus' atau 'obesitas' yang parah (sesuai interpretasi tool), berikan peringatan dini dan saran rujukan ke fasilitas kesehatan terdekat dengan tegas.**"
    "\n\n"
    "Untuk merekomendasikan menu sehat, gunakan alat 'get_nutrition_recommendation'. "
    "Untuk menjawab pertanyaan gizi umum atau tentang zat gizi, gunakan alat 'get_nutrition_info'. "
    "Untuk mencari nilai gizi spesifik dari suatu makanan, gunakan 'get_food_nutrition_facts'. "
    "Untuk membuat resep masakan, gunakan 'generate_recipe'. "
    "Untuk membuat rencana makan mingguan, gunakan 'generate_weekly_meal_plan'. "
    "Selalu klarifikasi kelompok usia (anak/remaja) dan kebutuhan spesifik sebelum memberikan rekomendasi. "
    "Berikan respons yang ramah, informatif, dan mudah dipahami. "
    "Jika pengguna mengucapkan terima kasih atau pamit, respons dengan sopan dan berikan motivasi untuk hidup sehat!"
    "\n\n"
    "**Informasi tentang Keluarga:**"
    "Anda sudah mengetahui informasi dasar tentang pengguna dan anak-anak mereka dari profil yang disediakan. "
    "Nama pengguna adalah {user_name}. Anak-anak yang Anda ketahui adalah: {children_info}. "
    "Gunakan informasi ini untuk memberikan rekomendasi yang lebih personal tanpa harus bertanya ulang."
    "Jika Anda memiliki informasi BMI terbaru untuk anak-anak, Anda bisa mengaksesnya dari 'extracted_user_info'."
)
print("Instruksi sistem SAGO_SYSINT berhasil didefinisikan.")

# --- Pesan Selamat Datang ---
WELCOME_MSG = "🌟 Halo ini Sago, Agen pintar panduan nutrisi pribadi untuk buah hati Anda! 🥗\n\nSaya di sini untuk membantu Anda menemukan rekomendasi menu sehat, info gizi, resep, dan jadwal makan untuk anak-anak Anda. Bagaimana saya bisa bantu Anda hari ini? Ceritakan usia anak Anda dan preferensi makan mereka, ya!"
print("Pesan selamat datang WELCOME_MSG berhasil didefinisikan.")

# --- Inisialisasi Model LLM ---
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.7)
print("Model Gemini 2.0 Flash berhasil diinisialisasi.")

# --- Data Gizi yang Diperluas (Disesuaikan dengan Kemenkes) ---
NUTRITION_DATA = {
    "anak": { # 5-9 tahun (Kemenkes)
        "umum": [
            "Sarapan: Bubur ayam dengan suwiran ayam, potongan telur rebus, dan kerupuk sehat (tidak digoreng terlalu banyak)",
            "Makan siang: Nasi, ikan gabus bakar, sayur asem, dan buah naga",
            "Camilan: Buah potong (pisang atau pepaya) dan segelas susu",
            "Makan malam: Sup sayur (wortel, buncis, kentang) dengan tahu dan nasi"
        ],
        "vegetarian": [
            "Sarapan: Roti gandum dengan selai kacang alami, pisang, dan segelas susu nabati",
            "Makan siang: Nasi, tempe orek, tumis kangkung, dan buah semangka",
            "Camilan: Edamame rebus dan yogurt plain",
            "Makan malam: Sayur lodeh dengan tahu, tempe, dan nasi merah"
        ],
        "tinggi_protein": [
            "Sarapan: Telur dadar dengan keju, roti gandum, dan jus alpukat tanpa gula",
            "Makan siang: Dada ayam panggang, nasi merah, tumis brokoli, dan buah apel",
            "Camilan: Greek yogurt dengan kacang mete dan buah beri",
            "Makan malam: Ikan tongkol kuah kuning (rendah santan) dengan nasi dan lalapan"
        ],
        "khas_sultra": [
             "Sarapan: Sinonggi dengan ikan kuah kuning bening (ikan cakalang/tuna, bukan santan kental)",
             "Makan siang: Nasi jagung, ikan bakar (kakap/bandeng), tumis bunga pepaya, dan pisang",
             "Camilan: Barongko (pisang kukus) atau putu cangkiri",
             "Makan malam: Sop konro (daging sapi) tanpa lemak berlebihan dengan sedikit nasi dan sambal mangga"
        ],
        "tinggi_energi": [ # Tambahan untuk anak dengan kebutuhan energi lebih
            "Sarapan: Roti gandum dengan telur orak-arik, alpukat, dan susu full cream",
            "Makan siang: Nasi, ayam goreng tanpa kulit (bukan deep-fried), tumis buncis wortel, dan mangga",
            "Camilan: Puding susu dengan buah-buahan, biskuit gandum",
            "Makan malam: Makaroni schotel dengan daging cincang dan sayuran"
        ],
        "rendah_karbohidrat": [ # Contoh tambahan, bisa disesuaikan
            "Sarapan: Omelet keju dengan bayam dan sosis ayam rendah lemak",
            "Makan siang: Daging sapi panggang dengan salad hijau dan brokoli rebus",
            "Camilan: Keju stik dan kacang almond",
            "Makan malam: Ikan salmon kukus dengan asparagus dan kembang kol"
        ]
    },
    "remaja": { # 10-18 tahun (Kemenkes)
        "umum": [
            "Sarapan: Nasi goreng kampung (sedikit minyak) dengan telur mata sapi dan irisan timun",
            "Makan siang: Nasi, sate lilit ayam/ikan (tanpa kulit), plecing kangkung, dan buah jeruk",
            "Camilan: Rujak buah segar (tanpa gula berlebihan) dan segelas es kelapa muda",
            "Makan malam: Gado-gado (bumbu kacang tidak terlalu banyak) dengan lontong dan kerupuk udang panggang"
        ],
        "vegetarian": [
            "Sarapan: Bubur kacang hijau tanpa santan kental, dengan roti gandum",
            "Makan siang: Nasi, kari sayuran (kentang, wortel, buncis) dengan tahu, dan buah nangka",
            "Camilan: Martabak manis mini (tidak terlalu manis) dan air kelapa",
            "Makan malam: Pecel sayuran dengan lontong dan tempe goreng"
        ],
        "rendah_karbohidrat": [
            "Sarapan: Omelet sayuran dengan jamur, bayam, dan irisan alpukat",
            "Makan siang: Dada ayam panggang, salad hijau dengan dressing minyak zaitun, dan telur rebus",
            "Camilan: Segenggam kacang almond atau edamame",
            "Makan malam: Ikan tenggiri bakar dengan tumis kembang kol dan brokoli"
        ],
        "tinggi_energi": [
            "Sarapan: Nasi uduk dengan ayam goreng (tanpa kulit), tempe, dan sambal kacang",
            "Makan siang: Nasi, rendang daging (tidak berlemak), sayur nangka, dan buah duku",
            "Camilan: Pisang goreng (tidak terlalu berminyak) atau ubi rebus",
            "Makan malam: Bubur manado dengan ikan asin dan sambal dabu-dabu"
        ],
        "khas_sultra": [
             "Sarapan: Kapurung dengan ikan kuah asam (ikan kakap/bandeng), ditaburi kacang tanah sangrai",
             "Makan siang: Nasi kuning khas Buton dengan ayam bumbu rica, sayur singkong, dan sambal terasi",
             "Camilan: Kue putu cangkiri atau baje (beras ketan)",
             "Makan malam: Tumis kerang atau udang dengan sayuran (misal: labu siam) dan nasi"
        ],
        "tinggi_protein": [
            "Sarapan: Telur rebus, roti gandum panggang, smoked beef, dan susu protein",
            "Makan siang: Ayam bakar/panggang, nasi merah, tumis buncis, dan alpukat",
            "Camilan: Greek yogurt dengan biji chia dan buah beri",
            "Makan malam: Ikan tuna panggang, quinoa, dan salad sayuran hijau"
        ]
    }
}
print("Data gizi yang diperluas berhasil didefinisikan.")

# --- Muat Dataset Nutrisi dari CSV ---

# Muat dataset Bahasa Indonesia (yang sudah diterjemahkan)
try:
    FOOD_DATA_ID_CSV_PATH = "nutrition_dataset/nutrition_food_dataset_id.csv" # Asumsi nama file ini
    nutrition_df_id = pd.read_csv(FOOD_DATA_ID_CSV_PATH, sep=';', encoding='utf-8')
    nutrition_df_id.columns = nutrition_df_id.columns.str.strip().str.replace(' ', '_').str.lower()
    if nutrition_df_id.columns[0].startswith(';'):
        nutrition_df_id.rename(columns={nutrition_df_id.columns[0]: nutrition_df_id.columns[0][1:]}, inplace=True)
    print(f"Dataset nutrisi Bahasa Indonesia berhasil dimuat dari {FOOD_DATA_ID_CSV_PATH}.")
    print(f"Kolom yang tersedia di ID: {nutrition_df_id.columns.tolist()}")
except FileNotFoundError:
    print(f"Error: File '{FOOD_DATA_ID_CSV_PATH}' tidak ditemukan. Pastikan file CSV yang diterjemahkan ada.")
    nutrition_df_id = pd.DataFrame()
except Exception as e:
    print(f"Error saat memuat atau memproses CSV Bahasa Indonesia: {e}")
    nutrition_df_id = pd.DataFrame()

# --- Fungsi Alat (Tools) ---
@tool
def get_nutrition_recommendation(age_group: str, dietary_preferences: Iterable[str], nutritional_needs: Iterable[str]) -> str:
    """Menyediakan rekomendasi menu sehat berdasarkan kelompok usia (anak 5-9 tahun, remaja 10-18 tahun), preferensi diet, dan kebutuhan gizi spesifik."""
    age_group_lower = age_group.lower()

    if isinstance(dietary_preferences, str):
        dietary_preferences = [dietary_preferences]
    if isinstance(nutritional_needs, str):
        nutritional_needs = [nutritional_needs]

    diet_key = "umum"
    prefs_lower = [d.lower() for d in dietary_preferences]
    needs_lower = [n.lower() for n in nutritional_needs]

    # Prioritas preferensi dan kebutuhan
    if "khas_sultra" in prefs_lower:
        diet_key = "khas_sultra"
    elif "vegetarian" in prefs_lower:
        diet_key = "vegetarian"
    elif "rendah_karbohidrat" in prefs_lower or "rendah karbohidrat" in prefs_lower:
        diet_key = "rendah_karbohidrat"
    elif "tinggi_protein" in needs_lower or "tinggi protein" in needs_lower:
        diet_key = "tinggi_protein"
    elif "tinggi_energi" in needs_lower or "tinggi energi" in needs_lower:
        diet_key = "tinggi_energi"

    # Periksa kembali rentang usia yang valid (5-9 untuk anak, 10-18 untuk remaja)
    if age_group_lower == "anak":
        valid_age_group = True
    elif age_group_lower == "remaja":
        valid_age_group = True
    else:
        valid_age_group = False
    
    if valid_age_group and age_group_lower in NUTRITION_DATA:
        if diet_key in NUTRITION_DATA[age_group_lower]:
            recommendations = NUTRITION_DATA[age_group_lower][diet_key]
            response = f"🍽️ **Rekomendasi Menu untuk {age_group.title()} Anda**\n\n"
            
            if "khas_sultra" in prefs_lower:
                response += f"Wah, mantapji ini! Berdasarkan preferensi makanan '{', '.join(dietary_preferences)}' dan kebutuhan '{', '.join(nutritional_needs)}', berikut menu sehat khas Sulawesi Tenggara yang saya rekomendasikan:\n\n"
            else:
                response += f"Berdasarkan preferensi '{', '.join(dietary_preferences)}' dan kebutuhan '{', '.join(nutritional_needs)}', berikut menu sehat yang saya rekomendasikan:\n\n"

            for i, rec in enumerate(recommendations, 1):
                response += f"{i}. {rec}\n"

            response += f"\n💡 **Tips Nutrisi Tambahan:**\n"
            if diet_key == "vegetarian":
                response += "- Pastikan mendapat cukup protein dari kacang-kacangan dan produk susu/olahan kedelai\n"
                response += "- Konsumsi makanan kaya zat besi seperti bayam, kacang-kacangan, dan biji-bijian\n"
            elif diet_key == "tinggi_protein":
                response += "- Protein sangat membantu pertumbuhan dan perbaikan otot, penting untuk anak aktif!\n"
                response += "- Jangan lupa konsumsi sayuran dan buah untuk serat, vitamin, dan mineral\n"
            elif diet_key == "rendah_karbohidrat":
                response += "- Fokus pada protein berkualitas dan lemak sehat. Konsultasikan dengan ahli gizi jika anak punya kondisi khusus.\n"
                response += "- Pastikan tetap mendapat energi dari sumber yang baik dan beragam\n"
            elif diet_key == "khas_sultra":
                response += "- Makanan khas Sultra banyak yang sehat lho, seperti ikan laut yang kaya Omega-3 dan sagu sebagai karbohidrat kompleks.\n"
                response += "- Perhatikan porsi dan cara memasak agar tetap sehat (kurangi santan kental, gorengan)\n"
            elif diet_key == "tinggi_energi":
                response += "- Untuk menambah energi, pilih karbohidrat kompleks, protein, dan lemak sehat dalam porsi cukup.\n"
                response += "- Camilan padat gizi sangat membantu, seperti buah kering atau campuran kacang.\n"
            else: # Umum
                response += "- Makan secara teratur 3 kali sehari dengan 2 camilan sehat di antara waktu makan utama\n"
                response += "- Minum air putih minimal 8 gelas per hari, penting untuk hidrasi tubuh anak\n"

            response += "\nSemoga bermanfaat, iyo!"
            return response
        else:
            return f"Maaf, saya belum memiliki rekomendasi spesifik untuk preferensi '{diet_key}' untuk {age_group_lower}. Tapi nda apa-apa, mari kita coba rekomendasi umum yang tetap sehat dan bergizi!"
    else:
        return "Untuk memberikan rekomendasi yang tepat, mohon sebutkan apakah anak Anda adalah 'anak' (5-9 tahun) atau 'remaja' (10-18 tahun), ya."

@tool
def get_nutrition_info(query: str) -> str:
    """Mengambil informasi nutrisi umum berdasarkan pertanyaan pengguna, dengan fokus pada gizi anak-anak dan remaja. Termasuk informasi tentang zat gizi makro dan mikro, serta tips pola makan sehat."""
    query_lower = query.lower()

    nutrition_info = {
        "protein": {
            "info": "Protein itu ibarat 'bahan bangunan' super penting buat tubuh anak Anda!",
            "benefits": "Membangun dan memperbaiki otot, jaringan, menjaga daya tahan tubuh, dan penting untuk pertumbuhan",
            "sources": "daging merah, ayam tanpa kulit, ikan (salmon, tuna), telur, susu, keju, yogurt, tahu, tempe, kacang-kacangan (lentil, buncis)"
        },
        "vitamin c": {
            "info": "Vitamin C itu seperti pahlawan super yang bantu tubuh anak melawan penyakit!",
            "benefits": "Meningkatkan daya tahan tubuh, membantu penyerapan zat besi, mempercepat penyembuhan luka, menjaga kesehatan kulit dan gusi",
            "sources": "jeruk, jambu biji, kiwi, stroberi, paprika merah, brokoli, mangga"
        },
        "kalsium": {
            "info": "Kalsium itu mineral ajaib untuk bikin tulang dan gigi anak Anda kuat seperti baja!",
            "benefits": "Membangun dan menjaga tulang dan gigi yang kuat, membantu fungsi otot dan saraf, pembekuan darah",
            "sources": "susu, keju, yogurt, ikan teri, bayam, brokoli, tahu (yang diperkaya kalsium)"
        },
        "serat": {
            "info": "Serat itu seperti 'pembersih' alami yang menjaga pencernaan anak tetap lancar dan sehat!",
            "benefits": "Membantu pencernaan agar tidak sembelit, menjaga perut kenyang lebih lama (bagus untuk kontrol berat badan), menurunkan kolesterol",
            "sources": "buah-buahan (apel, pir), sayuran (brokoli, wortel), oats, roti gandum utuh, kacang-kacangan"
        },
        "zat besi": {
            "info": "Zat besi itu penting banget supaya darah anak bisa bawa oksigen ke seluruh tubuh!",
            "benefits": "Mencegah anemia (kurang darah), memberikan energi, membantu konsentrasi dan fungsi kognitif",
            "sources": "daging merah (sapi, hati), ayam, ikan, bayam, kacang-kacangan, telur, sereal yang difortifikasi"
        },
        "vitamin d": {
            "info": "Vitamin D itu 'vitamin sinar matahari' yang esensial untuk tulang kuat dan daya tahan tubuh!",
            "benefits": "Membantu penyerapan kalsium, menjaga tulang kuat, meningkatkan mood, mendukung sistem kekebalan tubuh",
            "sources": "sinar matahari (berjemur 10-15 menit/hari), ikan salmon, tuna, telur, susu/yogurt yang diperkaya"
        },
        "karbohidrat": {
            "info": "Karbohidrat adalah sumber energi utama tubuh anak Anda, seperti bensin untuk kendaraan!",
            "benefits": "Memberikan energi untuk aktivitas fisik dan otak, menjaga kadar gula darah",
            "sources": "nasi, roti, kentang, ubi, pasta, jagung, sereal gandum utuh"
        },
        "lemak sehat": {
            "info": "Lemak sehat itu penting untuk otak dan penyerapan vitamin. Bukan lemak jahat ya!",
            "benefits": "Penting untuk perkembangan otak, penyerapan vitamin (A, D, E, K), sumber energi, melindungi organ",
            "sources": "alpukat, kacang-kacangan (almond, walnut), biji-bijian (chia, flaxseed), ikan berlemak (salmon, makarel), minyak zaitun"
        }
    }

    for key, info in nutrition_info.items():
        if key in query_lower:
            response = f"🌟 **Tentang {key.title()} untuk Anak Anda!**\n\n"
            response += f"📖 **Apa itu?** {info['info']}\n\n"
            response += f"✨ **Manfaatnya:** {info['benefits']}\n\n"
            response += f"🥗 **Sumber makanan yang bagus:** {info['sources']}\n\n"
            response += f"💡 **Tips:** Pastikan anak Anda mendapatkan {key} yang cukup dari makanan sehari-hari untuk tumbuh kembang yang optimal. Jangan lupa makan yang beragam, ya!"
            return response

    if any(word in query_lower for word in ["makan sehat", "gizi seimbang", "nutrisi", "pola makan"]):
        return ("🌈 **Pola Makan Sehat dan Gizi Seimbang untuk Anak & Remaja:**\n\n"
                "Pola makan sehat itu pentingji untuk pertumbuhan dan kecerdasan anak kita. Begini tipsnya:\n\n"
                "1. **Karbohidrat Kompleks** (nasi merah, roti gandum, ubi, jagung) - Ini sumber energi utama biar anak aktif dan fokus belajar.\n"
                "2. **Protein Berkualitas** (daging, ikan, telur, tahu, tempe) - Wajib ada untuk membangun otot dan perbaikan sel tubuh.\n"
                "3. **Lemak Sehat** (alpukat, kacang-kacangan, ikan berlemak) - Penting untuk perkembangan otak dan penyerapan vitamin.\n"
                "4. **Vitamin & Mineral** (buah dan sayuran warna-warni) - Biar daya tahan tubuh kuat dan tidak gampang sakit.\n"
                "5. **Air Putih Cukup** - Minimal 8 gelas per hari untuk menjaga tubuh tetap terhidrasi dengan baik.\n\n"
                "💡 **Ingat:** Variasi itu kunci! Ajak anak makan makanan yang beragam, seimbang, dan teratur. Biasakan sarapan ya! Semoga bermanfaat!"
        )

    elif "air" in query_lower or "minum" in query_lower or "hidrasi" in query_lower:
        return ("💧 **Air Putih - Kebutuhan Vital Tubuh Anak Anda!**\n\n"
                "**Mengapa penting sekali?** Air membantu semua fungsi tubuh anak berjalan lancar, dari menjaga suhu tubuh, membawa nutrisi, sampai membuang racun. Pentingji itu!\n\n"
                "**Kebutuhan harian (perkiraan):**\n"
                "• Anak (5-9 tahun): sekitar 6-8 gelas (1.5 - 2 liter) per hari\n"
                "• Remaja (10-18 tahun): sekitar 8-10 gelas (2 - 2.5 liter) per hari\n\n"
                "**Tips biar anak rajin minum air:**\n"
                "- Sediakan botol minum yang menarik dan mudah dijangkau.\n"
                "- Ingatkan untuk minum segelas air setiap bangun tidur dan sebelum makan.\n"
                "- Jadikan minum air kebiasaan keluarga. Mantapji kalau begitu!"
        )
    elif "makanan khas sulawesi tenggara" in query_lower or "makanan sultra" in query_lower:
        return ("🍜 **Beberapa Makanan Khas Sulawesi Tenggara yang Enak dan Bisa Sehat!**\n\n"
                "Sulawesi Tenggara punya banyak makanan enak lho, seperti:\n"
                "- **Sinonggi/Kapurung**: Makanan pokok dari sagu, biasanya dimakan dengan ikan kuah kuning dan sayuran. Sumber karbohidrat kompleks yang bagus!\n"
                "- **Ikan Bakar/Goreng** (Kakap, Baronang, Cakalang): Sumber protein tinggi, kaya Omega-3 kalau ikannya segar. Lebih sehat dibakar atau kukus!\n"
                "- **Garo Kangkung**: Tumisan kangkung dengan jagung muda, segar dan kaya serat.\n"
                "- **Karasi**: Sejenis keripik dari ikan teri, enak buat camilan, tapi makan secukupnya karena digoreng.\n"
                "- **Lapa-Lapa**: Ketupat khas yang gurih, cocok dengan lauk ikan.\n\n"
                "Pentingji untuk menjaga porsi dan cara memasaknya ya, biar tetap sehat untuk keluarga!"
        )
    else:
        return ("🤔 Pertanyaan menarik! Saya bisa bantu Anda dengan informasi tentang:\n\n"
                "• **Zat gizi:** protein, karbohidrat, lemak, vitamin, mineral (tanyakan nama spesifiknya)\n"
                "• **Vitamin:** A, B, C, D, E, K (tanyakan nama spesifiknya)\n"
                "• **Mineral:** kalsium, zat besi, zinc (tanyakan nama spesifiknya)\n"
                "• **Pola makan sehat**, **hidrasi**, dan **makanan khas Sulawesi Tenggara**.\n\n"
                "Coba tanya hal yang lebih spesifik, seperti 'Apa manfaat protein?' atau 'Sumber vitamin C apa saja?' atau 'Apa itu sinonggi?'"
        )

@tool
def get_food_nutrition_facts(food_name: str) -> str:
    """Mengambil informasi nilai gizi (kalori, protein, karbohidrat, lemak, dll) dari dataset CSV lokal.
    Input: nama makanan (dalam Bahasa Inggris atau Bahasa Indonesia, agen akan mencoba mencocokkan).
    Output berupa teks tabel Markdown dengan informasi gizi.
    """
    if nutrition_df_id.empty :
        return "Maaf, data nutrisi tidak tersedia. Terjadi masalah saat memuat kedua dataset."

    food_name_lower = food_name.lower().strip()
    result = pd.Series() # Inisialisasi Series kosong untuk menampung hasil
    found_lang = None # Untuk melacak dari mana hasil ditemukan

    # Prioritas 1: Exact Match di kolom 'makanan_indonesia'
    if not nutrition_df_id.empty and 'makanan_indonesia' in nutrition_df_id.columns:
        exact_match_id = nutrition_df_id[nutrition_df_id['makanan_indonesia'].str.lower() == food_name_lower]
        if not exact_match_id.empty:
            result = exact_match_id.iloc[0]
            found_lang = "id_exact"
    
    # Prioritas 2: Exact Match di kolom 'food' (jika belum ditemukan)
    if result.empty and not nutrition_df_id.empty and 'food' in nutrition_df_id.columns:
        exact_match_en = nutrition_df_id[nutrition_df_id['food'].str.lower() == food_name_lower]
        if not exact_match_en.empty:
            result = exact_match_en.iloc[0]
            found_lang = "en_exact"

    # Prioritas 3: Partial Match di kolom 'makanan_indonesia' (jika masih belum ditemukan)
    if result.empty and not nutrition_df_id.empty and 'makanan_indonesia' in nutrition_df_id.columns:
        # Menggunakan regex=False untuk pencarian substring sederhana, na=False untuk handle NaN
        partial_match_id = nutrition_df_id[nutrition_df_id['makanan_indonesia'].str.lower().str.contains(food_name_lower, na=False, regex=False)]
        if not partial_match_id.empty:
            # Pilih yang paling relevan (misal: yang paling pendek atau yang paling banyak cocok)
            # Untuk sederhana, ambil yang pertama
            result = partial_match_id.iloc[0]
            found_lang = "id_partial"

    # Prioritas 4: Partial Match di kolom 'food' (jika masih belum ditemukan)
    if result.empty and not nutrition_df_id.empty and 'food' in nutrition_df_id.columns:
        partial_match_en = nutrition_df_id[nutrition_df_id['food'].str.lower().str.contains(food_name_lower, na=False, regex=False)]
        if not partial_match_en.empty:
            # Pilih yang paling relevan (misal: yang paling pendek atau yang paling banyak cocok)
            result = partial_match_en.iloc[0]
            found_lang = "en_partial"


    if result.empty:
        return f"Maaf, saya tidak dapat menemukan informasi gizi untuk '{food_name}'. Coba nama makanan lain yang lebih umum atau periksa ejaannya."
    
    # Tentukan nama yang akan ditampilkan
    display_food_name = food_name.title() # Default ke input asli, akan ditimpa jika ditemukan kecocokan yang lebih baik
    if found_lang and ('id' in found_lang) and ('makanan_indonesia' in result.index) and pd.notna(result['makanan_indonesia']) and result['makanan_indonesia'].strip():
        display_food_name = result['makanan_indonesia'].title()
    elif found_lang and ('en' in found_lang) and ('food' in result.index) and pd.notna(result['food']) and result['food'].strip():
        display_food_name = result['food'].title()

    # Berikan intro yang sesuai
    if found_lang in ["id_partial", "en_partial"]:
        response_intro = f"Saya menemukan informasi gizi untuk **'{display_food_name}'** yang mirip dengan pencarian Anda:\n\n"
    else:
        response_intro = f"📊 **Nilai Gizi untuk {display_food_name} (per perkiraan porsi standar):**\n\n"

    # Buat tabel Markdown
    table_response = response_intro
    table_response += "| Zat Gizi           | Jumlah (perkiraan) |\n"
    table_response += "|--------------------|--------------------|\n"

    # Kolom yang ingin ditampilkan dan label yang ramah
    nutrients_to_display = {
        "caloric_value": "Kalori",
        "fat": "Lemak Total",
        "saturated_fats": "Lemak Jenuh",
        "monounsaturated_fats": "Lemak Tak Jenuh Tunggal",
        "polyunsaturated_fats": "Lemak Tak Jenuh Ganda",
        "carbohydrates": "Karbohidrat",
        "sugars": "Gula",
        "protein": "Protein",
        "dietary_fiber": "Serat Pangan",
        "cholesterol": "Kolesterol",
        "sodium": "Sodium",
        "water": "Air",
        "vitamin_a": "Vitamin A",
        "vitamin_b1": "Vitamin B1",
        "vitamin_b11": "Vitamin B11 (Folat)", 
        "vitamin_b12": "Vitamin B12",
        "vitamin_b2": "Vitamin B2 (Riboflavin)",
        "vitamin_b3": "Vitamin B3 (Niasin)",
        "vitamin_b5": "Vitamin B5 (Asam Pantotenat)",
        "vitamin_b6": "Vitamin B6",
        "vitamin_c": "Vitamin C",
        "vitamin_d": "Vitamin D",
        "vitamin_e": "Vitamin E",
        "vitamin_k": "Vitamin K",
        "calcium": "Kalsium",
        "copper": "Tembaga",
        "iron": "Zat Besi",
        "magnesium": "Magnesium",
        "manganese": "Mangan",
        "phosphorus": "Fosfor",
        "potassium": "Kalium",
        "selenium": "Selenium",
        "zinc": "Seng",
        "nutrition_density": "Kepadatan Nutrisi" 
    }

    for col, label in nutrients_to_display.items():
        if col in result.index and pd.notna(result[col]) and result[col] != 0.0:
            value = result[col]
            unit = ""
            if label == "Kalori":
                unit = " kkal"
            elif label in ["Protein", "Lemak Total", "Karbohidrat", "Gula", "Serat Pangan", "Air", "Lemak Jenuh", "Lemak Tak Jenuh Tunggal", "Lemak Tak Jenuh Ganda"]:
                unit = " g"
            elif label in ["Kolesterol", "Sodium", "Kalsium", "Zat Besi", "Tembaga", "Magnesium", "Mangan", "Fosfor", "Kalium", "Selenium", "Seng"]:
                unit = " mg"
            elif "Vitamin" in label:
                if col in ['vitamin_a', 'vitamin_d', 'vitamin_e', 'vitamin_k'] or value < 0.1:
                    unit = " mcg"
                else:
                    unit = " mg"
            elif label == "Kepadatan Nutrisi":
                unit = ""

            if isinstance(value, (int, float)):
                formatted_value = f"{value:.2f}"
                if formatted_value.endswith('.00'):
                    formatted_value = str(int(value))
                elif formatted_value.endswith('0'):
                    formatted_value = formatted_value.rstrip('0')
            else:
                formatted_value = str(value)

            table_response += f"| {label.ljust(18)} | {formatted_value}{unit.ljust(15)} |\n"
    
    table_response += "\n*Data ini berdasarkan perkiraan per porsi standar dari Data Nutrisi Makanan"
    table_response += "\n\nSemoga informasi ini bermanfaat, iyo!"
    return table_response


@tool
def generate_recipe(dish_name: str, ingredients: Iterable[str] = None, dietary_needs: Iterable[str] = None) -> str:
    """Membuat resep masakan sederhana berdasarkan nama hidangan, bahan yang tersedia, dan kebutuhan diet.
    Fungsi ini tidak memanggil API eksternal dan hanya menyediakan resep umum yang sudah terprogram."""
    if ingredients:
        ingredients_str = ", ".join(ingredients)
        response = f"Ok, mantapji! Mari kita coba buat resep {dish_name.title()} dengan bahan {ingredients_str}.\n\n"
    else:
        response = f"Siap! Saya akan bantu buatkan resep untuk {dish_name.title()}.\n\n"

    # Kembali ke resep hardcoded karena tidak ada API resep gratis yang mudah diintegrasikan dari CSV
    if "sup ayam" in dish_name.lower():
        response += (
            "🍲 **Resep Sup Ayam Sehat (untuk 4 porsi)**\n\n"
            "**Bahan:**\n"
            "- 1 potong dada ayam tanpa kulit, potong dadu\n"
            "- 1 wortel ukuran sedang, potong bulat\n"
            "- 2 kentang ukuran sedang, potong dadu\n"
            "- 1 batang seledri, iris halus\n"
            "- 1 liter kaldu ayam rendah garam atau air\n"
            "- 2 siung bawang putih, geprek lalu cincang\n"
            "- Garam, merica secukupnya\n"
            "- Minyak sayur secukupnya\n\n"
            "**Cara Membuat:**\n"
            "1. Panaskan sedikit minyak, tumis bawang putih hingga harum.\n"
            "2. Masukkan ayam, masak hingga berubah warna.\n"
            "3. Tuang kaldu ayam/air, masukkan wortel dan kentang. Masak hingga empuk.\n"
            "4. Bumbui dengan garam dan merica. Koreksi rasa.\n"
            "5. Masukkan seledri, aduk sebentar, angkat dan sajikan selagi hangat.\n\n"
            "Supaya makin sehat, bisa ditambah brokoli atau buncis juga, lho. Selamat mencoba di rumah, ya!"
        )
    elif "tumis kangkung" in dish_name.lower():
        response += (
            "🥬 **Resep Tumis Kangkung Jagung Sehat (untuk 2 porsi)**\n\n"
            "**Bahan:**\n"
            "- 1 ikat kangkung segar, siangi\n"
            "- 1/2 jagung manis, pipil atau serut\n"
            "- 3 siung bawang merah, iris tipis\n"
            "- 2 siung bawang putih, cincang\n"
            "- 1/2 buah tomat, potong-potong\n"
            "- 1 cabai merah (opsional, sesuaikan pedasnya), iris serong\n"
            "- Saus tiram rendah garam (opsional) atau kecap asin secukupnya\n"
            "- Minyak sayur untuk menumis\n"
            "- Sedikit air\n\n"
            "**Cara Membuat:**\n"
            "1. Panaskan minyak, tumis bawang merah, bawang putih, dan cabai hingga harum.\n"
            "2. Masukkan jagung manis, aduk rata, masak sebentar.\n"
            "3. Masukkan kangkung dan tomat, aduk cepat. Tambahkan sedikit air dan saus tiram/kecap asin.\n"
            "4. Masak hingga kangkung layu tapi tetap renyah. Jangan terlalu lama ya.\n"
            "5. Koreksi rasa, angkat, dan sajikan. Mantapji disantap dengan nasi hangat!"
        )
    elif "smoothie buah" in dish_name.lower():
        response += (
            "🍓🍌 **Resep Smoothie Buah Pelangi (untuk 1 porsi)**\n\n"
            "**Bahan:**\n"
            "- 1 buah pisang ukuran sedang, beku lebih enak\n"
            "- 1/2 cangkir stroberi beku\n"
            "- 1/2 cangkir mangga beku (atau buah lain sesuai selera)\n"
            "- 1/2 cangkir yogurt plain tanpa gula (atau susu rendah lemak)\n"
            "- Sedikit madu atau kurma (opsional, untuk pemanis alami)\n"
            "- Air secukupnya (untuk mengatur kekentalan)\n\n"
            "**Cara Membuat:**\n"
            "1. Masukkan semua bahan ke dalam blender.\n"
            "2. Blender hingga halus dan creamy. Tambahkan air sedikit demi sedikit sampai kekentalan yang diinginkan.\n"
            "3. Tuang ke dalam gelas dan sajikan segera. Kaya vitamin dan serat, anak pasti suka!"
        )
    else:
        response += (
            f"Hmm, untuk resep '{dish_name.title()}', saya butuh sedikit lebih banyak detail. "
            "Coba sebutkan bahan-bahan utama yang Anda punya atau jenis masakan yang Anda inginkan (misal: 'resep ayam panggang', 'resep sup sayur'). "
            "Saya akan bantu semampu saya ya, palu!"
        )
    return response

@tool
def generate_weekly_meal_plan(age_group: str, dietary_preferences: Iterable[str], nutritional_needs: Iterable[str], focus: Literal["diet", "weight_gain", "balanced", "available_food"] = "balanced", available_foods: Iterable[str] = None) -> str:
    """
    Membuat rencana makan mingguan (Senin-Minggu) dalam format teks.
    Dapat disesuaikan berdasarkan kelompok usia (anak 5-9 tahun, remaja 10-18 tahun), preferensi diet, kebutuhan gizi, fokus (diet/menambah berat badan/seimbang/makanan tersedia),
    dan daftar makanan yang tersedia di rumah. Output berupa teks.
    """
    age_group_lower = age_group.lower()
    # Periksa rentang usia yang valid sesuai Kemenkes
    if age_group_lower == "anak":
        pass # Akan diverifikasi lagi di NutritionState update
    elif age_group_lower == "remaja":
        pass # Akan diverifikasi lagi di NutritionState update
    else:
        return "Mohon sebutkan kelompok usia yang tepat: 'anak' (5-9 tahun) atau 'remaja' (10-18 tahun), ya."

    prefs_lower = [d.lower() for d in dietary_preferences] if dietary_preferences else []
    needs_lower = [n.lower() for n in nutritional_needs] if nutritional_needs else []
    
    plan = f"📅 **Rencana Makan Mingguan untuk {age_group.title()} Anda**\n"
    plan += f"Fokus: **{focus.replace('_', ' ').title()}**\n"
    if prefs_lower:
        plan += f"Preferensi Diet: {', '.join(prefs_lower).title()}\n"
    if needs_lower:
        plan += f"Kebutuhan Gizi: {', '.join(needs_lower).title()}\n"
    if available_foods:
        plan += f"Makanan Tersedia: {', '.join(available_foods).title()}\n"
    plan += "\n"

    diet_key = "umum"
    if "vegetarian" in prefs_lower:
        diet_key = "vegetarian"
    elif "rendah_karbohidrat" in prefs_lower or "rendah karbohidrat" in prefs_lower:
        diet_key = "rendah_karbohidrat"
    elif "tinggi_protein" in needs_lower or "tinggi protein" in needs_lower:
        diet_key = "tinggi_protein"
    elif "khas_sultra" in prefs_lower:
        diet_key = "khas_sultra"
    elif "tinggi_energi" in needs_lower or "tinggi energi" in needs_lower:
        diet_key = "tinggi_energi"

    base_recommendations = NUTRITION_DATA.get(age_group_lower, {}).get(diet_key, NUTRITION_DATA[age_group_lower]["umum"])

    hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    for i, h in enumerate(hari):
        plan += f"--- **{h}** ---\n"
        for meal in base_recommendations:
            plan += f"- {meal}\n"
        plan += "\n"
    
    plan += "💡 **Tips Tambahan untuk Rencana Makan Ini:**\n"
    if focus == "diet":
        plan += "- Fokus pada porsi yang terkontrol, perbanyak sayur dan protein tanpa lemak.\n"
        plan += "- Hindari minuman manis dan camilan tidak sehat.\n"
    elif focus == "weight_gain":
        plan += "- Tambahkan camilan bergizi tinggi (alpukat, kacang-kacangan, susu full cream).\n"
        plan += "- Pilih karbohidrat kompleks dan protein yang cukup.\n"
    elif focus == "available_food" and available_foods:
        plan += "- Maksimalkan penggunaan bahan yang ada, kreatif dengan resep sederhana.\n"
        plan += "- Jangan takut mencoba kombinasi baru untuk menghindari bosan.\n"
    else: # balanced
        plan += "- Pastikan ada variasi protein, karbohidrat, sayur, dan buah setiap hari.\n"
        plan += "- Selalu sediakan camilan sehat seperti buah atau yogurt.\n"
    plan += "- Jangan lupakan air putih yang cukup sepanjang hari.\n"
    plan += "\nSemoga rencana ini bisa bantu keluarga Anda hidup lebih sehat ya! Mantapji!"
    
    return plan

@tool
def calculate_bmi_and_analyze(child_name: str, age: int, gender: Literal["laki-laki", "perempuan"], height_cm: float, weight_kg: float) -> dict:
    """
    Menghitung Body Mass Index (BMI) untuk anak atau remaja dan menganalisis status gizinya.
    Parameter:
    - child_name (str): Nama anak.
    - age (int): Usia anak dalam tahun (harus antara 5-18 tahun).
    - gender (Literal["laki-laki", "perempuan"]): Jenis kelamin anak.
    - height_cm (float): Tinggi badan anak dalam sentimeter (cm).
    - weight_kg (float): Berat badan anak dalam kilogram (kg).
    Mengembalikan dictionary berisi status gizi (kurus, normal, gemuk, obesitas), nilai BMI, pesan lengkap, dan rekomendasi tindak lanjut.
    """
    if not (5 <= age <= 18):
        return {"status": "error", "message": f"Maaf, perhitungan BMI Sago saat ini hanya mendukung anak usia 5 hingga 18 tahun. Umur {child_name} ({age} tahun) di luar rentang ini."}
    if height_cm <= 0 or weight_kg <= 0:
        return {"status": "error", "message": "Tinggi dan berat badan harus lebih besar dari nol untuk menghitung BMI."}

    # Hitung BMI
    # Formula BMI: kg / (m^2)
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)

    status = "Tidak dapat diinterpretasikan"
    saran_gizi = ""
    saran_tindak_lanjut = ""
    peringatan_dini = False

    # Ambang batas BMI yang disederhanakan untuk anak dan remaja (bervariasi)
    # Ini adalah generalisasi dan tidak menggantikan grafik pertumbuhan WHO/CDC.
    # Disarankan selalu berkonsultasi dengan profesional.

    if age <= 9: # Anak (5-9 tahun)
        if bmi < 14.5:
            status = "kurus"
            peringatan_dini = True # Bisa jadi butuh perhatian lebih
        elif 14.5 <= bmi < 18.5:
            status = "normal"
        elif 18.5 <= bmi < 21:
            status = "gemuk"
            peringatan_dini = True
        else: # bmi >= 21
            status = "obesitas"
            peringatan_dini = True # Sangat butuh perhatian
    else: # Remaja (10-18 tahun)
        if bmi < 16:
            status = "kurus"
            peringatan_dini = True
        elif 16 <= bmi < 23:
            status = "normal"
        elif 23 <= bmi < 27:
            status = "gemuk"
            peringatan_dini = True
        else: # bmi >= 27
            status = "obesitas"
            peringatan_dini = True

    # Pesan saran gizi dan tindak lanjut berdasarkan status gizi
    if status == "kurus":
        saran_gizi = "Penting untuk meningkatkan asupan nutrisi padat gizi, seperti protein dan karbohidrat kompleks. Fokus pada makanan yang sehat, bukan hanya jumlahnya. Rekomendasi bisa mencakup porsi yang lebih besar, camilan bergizi, dan memastikan gizi mikro terpenuhi."
        saran_tindak_lanjut = "Sangat disarankan untuk segera membawa anak ke Puskesmas/Posyandu terdekat atau konsultasi dengan dokter anak/ahli gizi untuk pemeriksaan dan rencana diet yang lebih terperinci. Nda usah tunggu lama-lama, iyo."
    elif status == "normal":
        saran_gizi = "Lanjutkan dengan pola makan seimbang dan aktif bergerak. Pertahankan asupan buah, sayur, protein, dan karbohidrat kompleks yang cukup. Sago bisa bantu rekomendasikan menu-menu sehat untuk menjaga kesehatan optimalnya!"
        saran_tindak_lanjut = "Pertahankan konsultasi rutin ke Posyandu/Puskesmas untuk pemantauan tumbuh kembang dan gizi anakta, mantapji itu."
    elif status == "gemuk":
        saran_gizi = "Penting untuk mengelola asupan kalori dan meningkatkan aktivitas fisik. Fokus pada pengurangan makanan olahan, tinggi gula, dan tinggi lemak jenuh. Perbanyak konsumsi sayur, buah, protein tanpa lemak, dan serat."
        saran_tindak_lanjut = "Disarankan untuk berkonsultasi dengan dokter anak atau ahli gizi di Puskesmas/Posyandu terdekat untuk panduan gizi dan aktivitas fisik yang tepat. Jangan sungkan, ini untuk kebaikan anakta juga."
    elif status == "obesitas":
        saran_gizi = "Ini adalah kondisi yang membutuhkan perhatian serius. Perubahan pola makan dan peningkatan aktivitas fisik secara signifikan sangat penting. Hindari minuman manis, makanan cepat saji, dan camilan tinggi kalori."
        saran_tindak_lanjut = "MOHON PERHATIAN! Kami sangat menyarankan Anda untuk segera membawa anak ke Puskesmas atau rumah sakit terdekat dan konsultasi dengan dokter spesialis anak atau ahli gizi klinis untuk diagnosis dan penanganan yang komprehensif. Nda bisa tunda-tunda lagi, ini serius!"
    else:
        saran_gizi = "Maaf, Sago tidak dapat menginterpretasikan status BMI secara akurat saat ini. Mohon pastikan data tinggi, berat, umur, dan jenis kelamin sudah benar."
        saran_tindak_lanjut = "Untuk analisis yang lebih akurat, selalu konsultasi dengan profesional kesehatan."

    # Final response message
    if peringatan_dini:
        # Gaya bahasa lebih tegas untuk peringatan dini
        full_response_content = (
            f"⚠️ **PERINGATAN DINI!** ⚠️\n\n"
            f"Untuk **{child_name} ({age} tahun, {gender})**: Hasil BMI **{bmi:.2f}** menunjukkan status gizi **{status.title()}**.\n\n"
            f"{saran_gizi}\n\n"
            f"**Langkah Selanjutnya:** {saran_tindak_lanjut}\n\n"
            f"💡 **Penting:** Interpretasi BMI untuk anak-anak dan remaja sangat kompleks dan bergantung pada persentil usia serta jenis kelamin. Hasil ini adalah panduan awal. Untuk penilaian yang akurat dan penanganan lebih lanjut, mohon konsultasi langsung dengan dokter anak atau ahli gizi secepatnya, iyo!"
        )
    else:
        full_response_content = (
            f"📊 **Hasil BMI untuk {child_name} ({age} tahun, {gender})**: **{bmi:.2f}**\n"
            f"Status Gizi: **{status.title()}**\n\n"
            f"{saran_gizi}\n\n"
            f"**Langkah Selanjutnya:** {saran_tindak_lanjut}\n\n"
            f"💡 **Penting:** Interpretasi BMI untuk anak-anak dan remaja sangat kompleks dan bergantung pada persentil usia serta jenis kelamin. Hasil ini adalah panduan awal. Untuk penilaian yang akurat, mohon konsultasi langsung dengan dokter anak atau ahli gizi."
        )
    
    return {
        "status": "success",
        "bmi_value": round(bmi, 2), # Simpan nilai BMI yang sudah dibulatkan
        "bmi_status": status,
        "message": full_response_content
    }

print("Tool calculate_bmi_and_analyze berhasil didefinisikan.")

print("Fungsi alat (tools) berhasil didefinisikan.")

# --- Definisi Node ---

def chatbot_with_tools(state: NutritionState) -> NutritionState:
    """Chatbot dengan tools. Wrapper sederhana di sekitar antarmuka chat model."""
    defaults = {
        "user_age_group": "",
        "dietary_preferences": [],
        "nutritional_needs": [],
        "recommended_menu": [],
        "finished_recommendation": False,
        "extracted_user_info": state.get("extracted_user_info", {}) 
    }

    user_name = defaults["extracted_user_info"].get("user_name", "pengguna")
    
    children_info = defaults["extracted_user_info"].get("children_info", [])
    if children_info:
        # Filter anak-anak yang valid usianya (5-18) untuk dimasukkan ke system prompt
        valid_children_for_prompt = [
            f"{c['name']} ({c['age']} tahun, {c['gender']})" 
            for c in children_info 
            if 5 <= int(c['age']) <= 18
        ]
        children_info_str = ", ".join(valid_children_for_prompt) if valid_children_for_prompt else "tidak ada informasi anak yang relevan"
    else:
        children_info_str = "tidak ada informasi anak"
    
    dynamic_sys_int = (
        SAGO_SYSINT[0], 
        SAGO_SYSINT[1].format(user_name=user_name, children_info=children_info_str)
    )

    # Batasi riwayat pesan yang dikirim ke LLM untuk mengurangi token
    # Mengambil N pesan terakhir (misal 5 pasang pesan user-bot, atau 10 pesan total)
    # Anda bisa menyesuaikan angka ini berdasarkan kebutuhan dan quota API Anda
    MAX_HISTORY_MESSAGES = 10 # Jumlah total pesan (user + bot) yang akan dikirim
    
    # Filter dan ambil pesan yang relevan
    # System prompt hanya perlu dikirim sekali diawal, atau di gabung dengan prompt
    # Initial message for agent only contains system prompt and relevant messages
    messages_for_llm_history = state["messages"][-MAX_HISTORY_MESSAGES:] 
    
    messages_for_llm = [dynamic_sys_int] + messages_for_llm_history
    
    new_output = llm_with_tools.invoke(messages_for_llm)

    # --- Ekstraksi Informasi dari Respons LLM (usia, preferensi, kebutuhan) ---
    # Perbarui logika deteksi age_group sesuai Kemenkes (5-9 anak, 10-18 remaja)
    if not defaults["extracted_user_info"].get("age_group"):
        content_lower = new_output.content.lower()
        # Deteksi 'anak' (5-9)
        if any(keyword in content_lower for keyword in ["anak", "5 tahun", "6 tahun", "7 tahun", "8 tahun", "9 tahun"]):
            defaults["extracted_user_info"]["age_group"] = "anak"
        # Deteksi 'remaja' (10-18)
        elif any(keyword in content_lower for keyword in ["remaja", "10 tahun", "11 tahun", "12 tahun", "13 tahun", "14 tahun", "15 tahun", "16 tahun", "17 tahun", "18 tahun"]):
            defaults["extracted_user_info"]["age_group"] = "remaja"
    
    defaults["extracted_user_info"].setdefault("dietary_preferences", [])
    if "vegetarian" in new_output.content.lower() or "vegetaris" in new_output.content.lower():
        if "vegetarian" not in defaults["extracted_user_info"]["dietary_preferences"]:
            defaults["extracted_user_info"]["dietary_preferences"].append("vegetarian")
    if "khas sultra" in new_output.content.lower() or "sultra" in new_output.content.lower():
        if "khas_sultra" not in defaults["extracted_user_info"]["dietary_preferences"]:
            defaults["extracted_user_info"]["dietary_preferences"].append("khas_sultra")
    
    defaults["extracted_user_info"].setdefault("nutritional_needs", [])
    if "tinggi protein" in new_output.content.lower():
        if "tinggi_protein" not in defaults["extracted_user_info"]["nutritional_needs"]:
            defaults["extracted_user_info"]["nutritional_needs"].append("tinggi_protein")
    elif "rendah karbohidrat" in new_output.content.lower():
        if "rendah_karbohidrat" not in defaults["extracted_user_info"]["nutritional_needs"]:
            defaults["extracted_user_info"]["nutritional_needs"].append("rendah_karbohidrat")
    elif "tinggi energi" in new_output.content.lower():
        if "tinggi_energi" not in defaults["extracted_user_info"]["nutritional_needs"]:
            defaults["extracted_user_info"]["nutritional_needs"].append("tinggi_energi")

    return defaults | state | {"messages": [new_output]}


def nutrition_node(state: NutritionState) -> NutritionState:
    """Node nutrisi. Memproses panggilan tool dan update state."""
    tool_msg = state.get("messages", [])[-1]
    outbound_msgs = []

    extracted_user_info = state.get("extracted_user_info", {})
    age_group = extracted_user_info.get("age_group", state.get("user_age_group", "")) 
    dietary_preferences = extracted_user_info.get("dietary_preferences", state.get("dietary_preferences", []))
    nutritional_needs = extracted_user_info.get("nutritional_needs", state.get("nutritional_needs", []))
    
    recommended_menu = state.get("recommended_menu", [])
    finished_recommendation = state.get("finished_recommendation", False)

    for tool_call in tool_msg.tool_calls:
        response_content = "" # Gunakan nama berbeda agar tidak konflik dengan response dict dari tool BMI

        if tool_call["name"] == "get_nutrition_recommendation":
            age_group_arg = tool_call["args"].get("age_group") or age_group
            dietary_preferences_arg = tool_call["args"].get("dietary_preferences", []) or dietary_preferences
            nutritional_needs_arg = tool_call["args"].get("nutritional_needs", []) or nutritional_needs
            
            if isinstance(dietary_preferences_arg, str):
                dietary_preferences_arg = [dietary_preferences_arg]
            if isinstance(nutritional_needs_arg, str):
                nutritional_needs_arg = [nutritional_needs_arg]

            if age_group_arg:
                extracted_user_info["age_group"] = age_group_arg
            
            current_prefs = extracted_user_info.setdefault("dietary_preferences", [])
            for pref in dietary_preferences_arg:
                if pref not in current_prefs:
                    current_prefs.append(pref)
            
            current_needs = extracted_user_info.setdefault("nutritional_needs", [])
            for need in nutritional_needs_arg:
                if need not in current_needs:
                    current_needs.append(need)

            response_content = get_nutrition_recommendation.invoke({
                "age_group": extracted_user_info.get("age_group", "umum"), 
                "dietary_preferences": extracted_user_info.get("dietary_preferences", []),
                "nutritional_needs": extracted_user_info.get("nutritional_needs", [])
            })
            recommended_menu = [response_content]
            finished_recommendation = True

        elif tool_call["name"] == "get_nutrition_info":
            query_arg = tool_call["args"].get("query", "")
            response_content = get_nutrition_info.invoke({"query": query_arg})
        
        elif tool_call["name"] == "get_food_nutrition_facts":
            food_name_arg = tool_call["args"].get("food_name", "")
            response_content = get_food_nutrition_facts.invoke({
                "food_name": food_name_arg,
            })

        elif tool_call["name"] == "generate_recipe":
            dish_name_arg = tool_call["args"].get("dish_name", "")
            ingredients_arg = tool_call["args"].get("ingredients", [])
            dietary_needs_arg = tool_call["args"].get("dietary_needs", [])
            response_content = generate_recipe.invoke({
                "dish_name": dish_name_arg,
                "ingredients": ingredients_arg,
                "dietary_needs": dietary_needs_arg
            })
        
        elif tool_call["name"] == "generate_weekly_meal_plan":
            age_group_plan_arg = tool_call["args"].get("age_group") or age_group
            dietary_preferences_plan_arg = tool_call["args"].get("dietary_preferences", []) or dietary_preferences
            nutritional_needs_plan_arg = tool_call["args"].get("nutritional_needs", []) or nutritional_needs
            focus_arg = tool_call["args"].get("focus", "balanced")
            available_foods_arg = tool_call["args"].get("available_foods", [])

            if isinstance(dietary_preferences_plan_arg, str):
                dietary_preferences_plan_arg = [dietary_preferences_plan_arg]
            if isinstance(nutritional_needs_plan_arg, str):
                nutritional_needs_plan_arg = [nutritional_needs_plan_arg]
            if isinstance(available_foods_arg, str):
                available_foods_arg = [available_foods_arg]

            response_content = generate_weekly_meal_plan.invoke({
                "age_group": age_group_plan_arg,
                "dietary_preferences": dietary_preferences_plan_arg,
                "nutritional_needs": nutritional_needs_plan_arg,
                "focus": focus_arg,
                "available_foods": available_foods_arg
            })
        
        elif tool_call["name"] == "calculate_bmi_and_analyze":
            # Extract child info from args or state
            child_name_arg = tool_call["args"].get("child_name")
            age_arg = tool_call["args"].get("age")
            gender_arg = tool_call["args"].get("gender")
            height_cm_arg = tool_call["args"].get("height_cm")
            weight_kg_arg = tool_call["args"].get("weight_kg")

            # Try to get missing info from children_info in extracted_user_info
            target_child_from_profile = None
            if child_name_arg and extracted_user_info.get("children_info"):
                for child_profile in extracted_user_info["children_info"]:
                    if child_profile['name'].lower() == child_name_arg.lower():
                        target_child_from_profile = child_profile
                        break
            
            # Prioritaskan data dari tool_call args, lalu dari profil
            final_child_name = child_name_arg or (target_child_from_profile['name'] if target_child_from_profile else None)
            final_age = age_arg or (target_child_from_profile['age'] if target_child_from_profile else None)
            final_gender = gender_arg or (target_child_from_profile['gender'] if target_child_from_profile else None)
            
            # Validasi input untuk tool BMI sebelum memanggilnya
            # Jika nama anak tidak dapat ditentukan, atau info vital lainnya hilang, minta dari user
            if final_child_name is None or final_age is None or final_gender is None or height_cm_arg is None or weight_kg_arg is None:
                # Coba berikan pesan yang lebih spesifik berdasarkan apa yang hilang
                missing_info = []
                if final_child_name is None: missing_info.append("nama anak")
                if final_age is None: missing_info.append("umur")
                if final_gender is None: missing_info.append("jenis kelamin")
                if height_cm_arg is None: missing_info.append("tinggi badan (cm)")
                if weight_kg_arg is None: missing_info.append("berat badan (kg)")
                
                response_content = f"Untuk menghitung BMI, saya perlu informasi lengkap: {', '.join(missing_info)}. " \
                                   f"Mohon sebutkan data tersebut ya, misalnya: 'Anak saya [Nama], umur [X] tahun, jenis kelamin [Laki-laki/Perempuan], tinggi [Y] cm, berat [Z] kg'."
            elif not (5 <= final_age <= 18):
                 response_content = f"Maaf, Sago saat ini hanya mendukung perhitungan BMI untuk anak usia 5 hingga 18 tahun. Umur {final_child_name} ({final_age} tahun) di luar rentang ini."
            else:
                bmi_tool_result = calculate_bmi_and_analyze.invoke({
                    "child_name": final_child_name,
                    "age": final_age,
                    "gender": final_gender,
                    "height_cm": height_cm_arg,
                    "weight_kg": weight_kg_arg
                })
                
                # Check status from tool result
                if bmi_tool_result["status"] == "success":
                    # Simpan hasil BMI ke extracted_user_info untuk referensi di frontend melalui session Flask
                    extracted_user_info.setdefault("children_bmi_info", {})[final_child_name.lower()] = {
                        "bmi": bmi_tool_result["bmi_value"], # Ambil nilai BMI yang sudah dibulatkan
                        "status": bmi_tool_result["bmi_status"],
                        "timestamp": datetime.now().isoformat()
                    }
                    response_content = bmi_tool_result["message"]
                else:
                    response_content = bmi_tool_result["message"] # Pesan error dari tool

        else:
            raise NotImplementedError(f'Panggilan alat tidak dikenal: {tool_call["name"]}')

        outbound_msgs.append(
            ToolMessage(
                content=response_content,
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )

    return {
        "messages": outbound_msgs,
        "user_age_group": extracted_user_info.get("age_group", age_group),
        "dietary_preferences": extracted_user_info.get("dietary_preferences", dietary_preferences),
        "nutritional_needs": extracted_user_info.get("nutritional_needs", nutritional_needs),
        "recommended_menu": recommended_menu,
        "finished_recommendation": finished_recommendation,
        "extracted_user_info": extracted_user_info 
    }

print("Node-node LangGraph berhasil didefinisikan.")

# --- Definisi Edge Kondisional ---

all_tools = [get_nutrition_info, get_nutrition_recommendation, get_food_nutrition_facts, generate_recipe, generate_weekly_meal_plan, calculate_bmi_and_analyze]
all_tools_dict = {tool.name: tool for tool in all_tools}

llm_with_tools = llm.bind_tools(all_tools)

def maybe_route_to_tools(state: NutritionState) -> Literal["nutrition_node", "__end__"]: 
    """Routing logic untuk menentukan langkah selanjutnya."""
    if not (msgs := state.get("messages", [])):
        return END

    msg = msgs[-1]

    if hasattr(msg, "tool_calls") and len(msg.tool_calls) > 0:
        if any(tool_call["name"] in all_tools_dict for tool_call in msg.tool_calls): 
            return "nutrition_node"
        else:
            return END
    else:
        return END

print("Fungsi edge kondisional berhasil didefinisikan.")

# --- Kompilasi LangGraph Agent untuk Web App (TANPA CHECKPOINTER) ---
graph_builder = StateGraph(NutritionState)

graph_builder.add_node("chatbot", chatbot_with_tools)
graph_builder.add_node("nutrition_node", nutrition_node) 

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", maybe_route_to_tools)
graph_builder.add_edge("nutrition_node", "chatbot")

final_nutrition_chatbot_graph = graph_builder.compile()
print("✅ Sago agent berhasil dikompilasi tanpa persistence (menggunakan sesi Flask untuk memori).")

# --- Fungsi get_sago_response untuk Flask ---
def get_sago_response(initial_state: NutritionState) -> NutritionState: 
    """
    Fungsi untuk mendapatkan respons dari Sago untuk digunakan di Flask.
    Menerima state awal lengkap dan mengembalikan state akhir setelah eksekusi graph.
    """
    try:
        result_state = final_nutrition_chatbot_graph.invoke(initial_state)
        return result_state

    except Exception as e:
        print(f"Error in get_sago_response: {str(e)}") 
        # Coba ekstrak pesan error yang lebih relevan untuk pengguna
        error_content = str(e)
        if "Could not parse tool call" in error_content:
            error_content = "Maaf, saya kesulitan memahami format permintaan Anda untuk alat bantu saya. Bisakah Anda coba jelaskan lebih sederhana?"
        elif "Invalid Tool Call" in error_content:
            error_content = "Sepertinya ada masalah dengan cara saya mencoba menggunakan alat bantu. Mari kita coba lagi dengan pertanyaan yang berbeda."
        elif "429" in error_content or "RESOURCE_EXHAUSTED" in error_content:
            error_content = "Maaf, Sago sedang sangat sibuk atau mencapai batas penggunaan. Mohon tunggu sebentar dan coba lagi. Terima kasih atas kesabaran Anda!"
        elif "5" in error_content: # Catch-all for 5xx server errors
            error_content = "Maaf, ada masalah di server Sago. Kami sedang memperbaikinya. Mohon coba lagi nanti."
        else:
            error_content = "Maaf, terjadi kesalahan internal di agent. Coba ulangi pertanyaan Anda."

        return NutritionState(
            messages=initial_state["messages"] + [AIMessage(content=f"{error_content}")],
            user_age_group=initial_state.get("user_age_group", ""),
            dietary_preferences=initial_state.get("dietary_preferences", []),
            nutritional_needs=initial_state.get("nutritional_needs", []),
            recommended_menu=initial_state.get("recommended_menu", []),
            finished_recommendation=initial_state.get("finished_recommendation", False),
            extracted_user_info=initial_state.get("extracted_user_info", {})
        )
        
print("🎉 Sago siap digunakan untuk aplikasi web!")

# --- Fungsi untuk testing terminal (opsional) ---
def run_terminal_chat():
    """Fungsi untuk menjalankan chat di terminal (untuk testing)."""
    print("=== Sago Terminal Chat ===")
    print(WELCOME_MSG)
    
    terminal_messages_history = []
    terminal_user_profile = {
        "name": "Pengguna Terminal",
        "children": [
            {"name": "Anak Uji", "age": 8, "gender": "perempuan"}, # Umur valid 5-9
            {"name": "Remaja Uji", "age": 15, "gender": "laki-laki"} # Umur valid 10-18
        ]
    }

    while True:
        user_input = input("\nAnda: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q', 'selesai', 'keluar']:
            print("Sago: Terima kasih telah menggunakan Sago! Semoga hidup sehat selalu, ya! Sampai jumpa lagi!")
            break
            
        if not user_input:
            continue
        
        terminal_messages_history.append({'role': 'user', 'content': user_input})
        
        langchain_messages_history = []
        for msg_dict in terminal_messages_history:
            if msg_dict['role'] == 'user':
                langchain_messages_history.append(HumanMessage(content=msg_dict['content']))
            elif msg_dict['role'] == 'assistant':
                langchain_messages_history.append(AIMessage(content=msg_dict['content']))

        # Format children_info_formatted untuk agent
        children_info_formatted = []
        for child in terminal_user_profile.get('children', []):
            if 5 <= int(child['age']) <= 18: # Filter anak yang valid
                children_info_formatted.append({
                    "name": child['name'],
                    "age": int(child['age']),
                    "gender": child['gender']
                })

        initial_agent_state = NutritionState(
            messages=langchain_messages_history,
            user_age_group="",
            dietary_preferences=[],
            nutritional_needs=[],
            recommended_menu=[],
            finished_recommendation=False,
            extracted_user_info={
                "user_name": terminal_user_profile['name'],
                "children_info": children_info_formatted,
                "children_bmi_info": {} # Tambahkan ini untuk testing terminal
            }
        )

        result_state = get_sago_response(initial_agent_state)
        
        bot_response = "Maaf, Sago tidak dapat memberikan respons saat ini."
        if result_state and result_state["messages"]:
            # Dapatkan pesan terakhir dari agent
            last_message = result_state["messages"][-1]
            if isinstance(last_message, AIMessage):
                bot_response = last_message.content
            elif isinstance(last_message, ToolMessage):
                bot_response = last_message.content
            else:
                bot_response = "Maaf, Sago tidak dapat memberikan respons saat ini (format pesan tidak dikenal)."

        print(f"Sago: {bot_response}")

        terminal_messages_history.append({'role': 'assistant', 'content': bot_response})

if __name__ == "__main__":
    run_terminal_chat()