# agent.py
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
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode


print("\nLibrary dan konfigurasi awal berhasil dimuat.")

# --- Definisi State untuk GiziBot ---
class NutritionState(TypedDict):
    """State yang merepresentasikan percakapan nutrisi pengguna."""
    messages: Annotated[list, add_messages]
    user_age_group: str
    dietary_preferences: list[str]
    nutritional_needs: list[str]
    recommended_menu: list[str]
    finished_recommendation: bool
    extracted_user_info: dict

print("Skema NutritionState berhasil didefinisikan.")

# --- Instruksi Sistem GiziBot ---
GIZIBOT_SYSINT = (
    "system",
    "Anda adalah Sago, sebuah chatbot cerdas dan ramah yang dirancang khusus untuk membantu orang tua "
    "dalam mendidik anak-anak dan remaja mereka tentang nutrisi. "
    "Tujuan utama Anda adalah merekomendasikan menu sehat yang dipersonalisasi berdasarkan kebutuhan gizi, "
    "kelompok usia (anak 6-12 tahun, remaja 13-18 tahun), dan kebiasaan makan anak/remaja. "
    "Anda juga harus mampu menjawab pertanyaan interaktif tentang nilai gizi makanan, memberikan resep sederhana, "
    "dan menyusun jadwal makan mingguan. "
    "Selalu berikan informasi yang akurat, relevan, dan mudah dipahami, dengan nada yang mendukung dan positif. "
    "Jika Anda perlu mengekstrak usia pengguna, preferensi diet, atau kebutuhan gizi spesifik untuk memberikan "
    "rekomendasi yang dipersonalisasi, ajukan pertanyaan klarifikasi dengan sopan. "
    "Fokus hanya pada topik terkait nutrisi dan hindari diskusi di luar topik. "
    "Cobalah untuk sesekali menggunakan sentuhan bahasa informal atau nuansa logat daerah Sulawesi Tenggara "
    "(misalnya 'iyo', 'nda apa-apa', 'mantapji') untuk menciptakan pengalaman yang lebih akrab. "
    "Contoh logat: 'Selamat datang di GiziBot, palu! Marijo kita bahas gizi sehat.' "
    "\n\n"
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
)
print("Instruksi sistem SAGO_SYSINT berhasil didefinisikan.")

# --- Pesan Selamat Datang ---
WELCOME_MSG = "🌟 Halo ini Sago, Agen pintar panduan nutrisi pribadi untuk buah hati Anda! 🥗\n\nSaya di sini untuk membantu Anda menemukan rekomendasi menu sehat, info gizi, resep, dan jadwal makan. Bagaimana saya bisa bantu Anda hari ini? Ceritakan usia anak Anda dan preferensi makan mereka, ya!"
print("Pesan selamat datang WELCOME_MSG berhasil didefinisikan.")

# --- Inisialisasi Model LLM ---
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.7)
print("Model Gemini 2.0 Flash berhasil diinisialisasi.")

# --- Data Gizi yang Diperluas ---
NUTRITION_DATA = {
    "anak": { # 6-12 tahun
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
        ]
    },
    "remaja": { # 13-18 tahun
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
    """Menyediakan rekomendasi menu sehat berdasarkan kelompok usia, preferensi diet, dan kebutuhan gizi spesifik."""
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

    if age_group_lower in NUTRITION_DATA:
        if diet_key in NUTRITION_DATA[age_group_lower]:
            recommendations = NUTRITION_DATA[age_group_lower][diet_key]
            response = f"🍽️ **Rekomendasi Menu untuk {age_group.title()} Anda**\n\n"
            
            # Tambahkan sentuhan logat Kendari
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
            else:
                response += "- Makan secara teratur 3 kali sehari dengan 2 camilan sehat di antara waktu makan utama\n"
                response += "- Minum air putih minimal 8 gelas per hari, penting untuk hidrasi tubuh anak\n"

            response += "\nSemoga bermanfaat, iyo!"
            return response
        else:
            return f"Maaf, saya belum memiliki rekomendasi spesifik untuk preferensi '{diet_key}' untuk {age_group_lower}. Tapi nda apa-apa, mari kita coba rekomendasi umum yang tetap sehat dan bergizi!"
    else:
        return "Untuk memberikan rekomendasi yang tepat, mohon sebutkan apakah anak Anda adalah 'anak' (6-12 tahun) atau 'remaja' (13-18 tahun), ya."

@tool
def get_nutrition_info(query: str) -> str:
    """Mengambil informasi nutrisi umum berdasarkan pertanyaan pengguna. Termasuk informasi tentang zat gizi makro dan mikro, serta tips pola makan sehat."""
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
                "• Anak (6-12 tahun): sekitar 6-8 gelas (1.5 - 2 liter) per hari\n"
                "• Remaja (13-18 tahun): sekitar 8-10 gelas (2 - 2.5 liter) per hari\n\n"
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

    # Prioritas 1: Cari di kolom 'makanan_indonesia' pada dataset ID
    if not nutrition_df_id.empty and 'makanan_indonesia' in nutrition_df_id.columns:
        exact_match_id = nutrition_df_id[nutrition_df_id['makanan_indonesia'].str.lower() == food_name_lower]
        if not exact_match_id.empty:
            result = exact_match_id.iloc[0]
            found_lang = "id"
    
    # Prioritas 2: Jika tidak ditemukan, cari di kolom 'food' pada dataset EN
    if result.empty and not nutrition_df_id.empty and 'food' in nutrition_df_id.columns:
        exact_match_en = nutrition_df_id[nutrition_df_id['food'].str.lower() == food_name_lower]
        if not exact_match_en.empty:
            result = exact_match_en.iloc[0]
            found_lang = "en"

    # Prioritas 3: Jika masih tidak ditemukan, coba partial match di kolom 'makanan_indonesia'
    if result.empty and not nutrition_df_id.empty and 'makanan_indonesia' in nutrition_df_id.columns:
        partial_match_id = nutrition_df_id[nutrition_df_id['makanan_indonesia'].str.lower().str.contains(food_name_lower, na=False)]
        if not partial_match_id.empty:
            result = partial_match_id.iloc[0]
            found_lang = "id_partial"

    # Prioritas 4: Jika masih tidak ditemukan, coba partial match di kolom 'food'
    if result.empty and not nutrition_df_id.empty and 'food' in nutrition_df_id.columns:
        partial_match_en = nutrition_df_id[nutrition_df_id['food'].str.lower().str.contains(food_name_lower, na=False)]
        if not partial_match_en.empty:
            result = partial_match_en.iloc[0]
            found_lang = "en_partial"


    if result.empty:
        return f"Maaf, saya tidak dapat menemukan informasi gizi untuk '{food_name}'. Coba nama makanan lain yang lebih umum atau periksa ejaannya."
    
    # Tentukan nama yang akan ditampilkan
    if 'makanan_indonesia' in result.index and pd.notna(result['makanan_indonesia']) and result['makanan_indonesia'].strip():
        display_food_name = result['makanan_indonesia'].title()
    else:
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
    Dapat disesuaikan berdasarkan kelompok usia, preferensi diet, kebutuhan gizi, fokus (diet/menambah berat badan/seimbang/makanan tersedia),
    dan daftar makanan yang tersedia di rumah. Output berupa teks.
    """
    age_group_lower = age_group.lower()
    if age_group_lower not in ["anak", "remaja"]:
        return "Mohon sebutkan kelompok usia yang tepat: 'anak' (6-12 tahun) atau 'remaja' (13-18 tahun), ya."

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
        children_info_str = ", ".join([f"{c['name']} ({c['age']} tahun, {c['gender']})" for c in children_info])
    else:
        children_info_str = "tidak ada informasi anak"
    
    dynamic_sys_int = (
        GIZIBOT_SYSINT[0], 
        GIZIBOT_SYSINT[1].format(user_name=user_name, children_info=children_info_str)
    )

    messages_for_llm = [dynamic_sys_int] + state["messages"]
    
    new_output = llm_with_tools.invoke(messages_for_llm)

    if not defaults["extracted_user_info"].get("age_group"):
        content_lower = new_output.content.lower()
        if any(keyword in content_lower for keyword in ["anak", "6-12", "6", "7", "8", "9", "10", "11", "12"]):
            defaults["extracted_user_info"]["age_group"] = "anak"
        elif any(keyword in content_lower for keyword in ["remaja", "13-18", "13", "14", "15", "16", "17", "18"]):
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
        response = "" 

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

            response = get_nutrition_recommendation.invoke({
                "age_group": extracted_user_info.get("age_group", "umum"), 
                "dietary_preferences": extracted_user_info.get("dietary_preferences", []),
                "nutritional_needs": extracted_user_info.get("nutritional_needs", [])
            })
            recommended_menu = [response]
            finished_recommendation = True

        elif tool_call["name"] == "get_nutrition_info":
            query_arg = tool_call["args"].get("query", "")
            response = get_nutrition_info.invoke({"query": query_arg})
        
        elif tool_call["name"] == "get_food_nutrition_facts":
            food_name_arg = tool_call["args"].get("food_name", "")
            # Hapus quantity dan unit karena CSV tidak memilikinya seperti API Edamam
            # quantity_arg = tool_call["args"].get("quantity", 1)
            # unit_arg = tool_call["args"].get("unit", "serving")
            response = get_food_nutrition_facts.invoke({
                "food_name": food_name_arg,
                # "quantity": quantity_arg,
                # "unit": unit_arg
            })

        elif tool_call["name"] == "generate_recipe":
            dish_name_arg = tool_call["args"].get("dish_name", "")
            ingredients_arg = tool_call["args"].get("ingredients", [])
            dietary_needs_arg = tool_call["args"].get("dietary_needs", [])
            response = generate_recipe.invoke({
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

            response = generate_weekly_meal_plan.invoke({
                "age_group": age_group_plan_arg,
                "dietary_preferences": dietary_preferences_plan_arg,
                "nutritional_needs": nutritional_needs_plan_arg,
                "focus": focus_arg,
                "available_foods": available_foods_arg
            })

        else:
            raise NotImplementedError(f'Panggilan alat tidak dikenal: {tool_call["name"]}')

        outbound_msgs.append(
            ToolMessage(
                content=response,
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

all_tools = [get_nutrition_info, get_nutrition_recommendation, get_food_nutrition_facts, generate_recipe, generate_weekly_meal_plan]
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
print("✅ GiziBot agent berhasil dikompilasi tanpa persistence (menggunakan sesi Flask untuk memori).")

# --- Fungsi get_gizibot_response untuk Flask ---
def get_gizibot_response(initial_state: NutritionState) -> NutritionState: 
    """
    Fungsi untuk mendapatkan respons dari GiziBot untuk digunakan di Flask.
    Menerima state awal lengkap dan mengembalikan state akhir setelah eksekusi graph.
    """
    try:
        result_state = final_nutrition_chatbot_graph.invoke(initial_state)
        return result_state

    except Exception as e:
        print(f"Error in get_gizibot_response: {str(e)}") 
        return NutritionState(
            messages=initial_state["messages"] + [AIMessage(content=f"Maaf, terjadi kesalahan internal di agent: {str(e)}. Coba ulangi pertanyaan Anda.")],
            user_age_group=initial_state.get("user_age_group", ""),
            dietary_preferences=initial_state.get("dietary_preferences", []),
            nutritional_needs=initial_state.get("nutritional_needs", []),
            recommended_menu=initial_state.get("recommended_menu", []),
            finished_recommendation=initial_state.get("finished_recommendation", False),
            extracted_user_info=initial_state.get("extracted_user_info", {})
        )
        
print("🎉 GiziBot siap digunakan untuk aplikasi web!")

# --- Fungsi untuk testing terminal (opsional) ---
def run_terminal_chat():
    """Fungsi untuk menjalankan chat di terminal (untuk testing)."""
    print("=== GiziBot Terminal Chat ===")
    print(WELCOME_MSG)
    
    terminal_messages_history = []
    terminal_user_profile = {
        "name": "Pengguna Terminal",
        "children": [
            {"name": "Anak Uji", "age": 10, "gender": "perempuan"}
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

        initial_agent_state = NutritionState(
            messages=langchain_messages_history,
            user_age_group="",
            dietary_preferences=[],
            nutritional_needs=[],
            recommended_menu=[],
            finished_recommendation=False,
            extracted_user_info={
                "user_name": terminal_user_profile['name'],
                "children_info": terminal_user_profile['children']
            }
        )

        result_state = get_gizibot_response(initial_agent_state)
        
        bot_response = "Maaf, Sago tidak dapat memberikan respons saat ini."
        if result_state and result_state["messages"]:
            for msg in reversed(result_state["messages"]):
                if isinstance(msg, AIMessage):
                    bot_response = msg.content
                    break
                elif isinstance(msg, ToolMessage): 
                    bot_response = msg.content
                    break

        print(f"Sago: {bot_response}")

        terminal_messages_history.append({'role': 'assistant', 'content': bot_response})

if __name__ == "__main__":
    run_terminal_chat()