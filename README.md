Tentu, saya akan menyusun file `README.md` yang komprehensif untuk proyek Sago: Smart Agent Gizi Online Anda, mencakup semua poin yang Anda minta.

-----

# Sago: Smart Agent Gizi Online

[](https://www.python.org/)
[](https://flask.palletsprojects.com/)
[](https://www.langchain.com/)
[](https://ai.google.dev/gemini-api)
[](https://opensource.org/licenses/MIT)

## Daftar Isi

1.  [Pendahuluan](https://www.google.com/search?q=%231-pendahuluan)
2.  [Fitur Utama](https://www.google.com/search?q=%232-fitur-utama)
3.  [Arsitektur Sistem](https://www.google.com/search?q=%233-arsitektur-sistem)
      * [Diagram Blok](https://www.google.com/search?q=%2331-diagram-blok)
      * [Alur Data dan Interaksi Pengguna](https://www.google.com/search?q=%2332-alur-data-dan-interaksi-pengguna)
4.  [Teknologi & Tools yang Digunakan](https://www.google.com/search?q=%234-teknologi--tools-yang-digunakan)
5.  [Pemrosesan Data](https://www.google.com/search?q=%235-pemrosesan-data)
      * [Deskripsi Dataset](https://www.google.com/search?q=%2351-deskripsi-dataset)
      * [Preprocessing Data](https://www.google.com/search?q=%2352-preprocessing-data)
6.  [Implementasi Sistem Temu Kembali Informasi](https://www.google.com/search?q=%236-implementasi-sistem-temu-kembali-informasi)
      * [Detail Penggunaan Algoritma](https://www.google.com/search?q=%2361-detail-penggunaan-algoritma)
      * [Contoh Input & Output Sistem](https://www.google.com/search?q=%2362-contoh-input--output-sistem)
7.  [Analisis dan Evaluasi](https://www.google.com/search?q=%237-analisis-dan-evaluasi)
      * [Hasil Pengujian Sistem](https://www.google.com/search?q=%2371-hasil-pengujian-sistem)
      * [Studi Kasus/Skenario Uji Coba Pengguna](https://www.google.com/search?q=%2372-studi-kasusskenario-uji-coba-pengguna)
      * [Kelebihan dan Keterbatasan Sistem](https://www.google.com/search?q=%2373-kelebihan-dan-keterbatasan-sistem)
8.  [Setup & Instalasi](https://www.google.com/search?q=%238-setup--instalasi)
9.  [Kontribusi](https://www.google.com/search?q=%239-kontribusi)
10. [Lisensi](https://www.google.com/search?q=%2310-lisensi)

-----

## 1\. Pendahuluan

**Sago: Smart Agent Gizi Online** adalah aplikasi chatbot inovatif yang dirancang untuk menjadi asisten gizi pribadi, khususnya bagi orang tua dalam mendidik anak-anak dan remaja mereka tentang nutrisi. Sago menonjol dengan kemampuannya memberikan rekomendasi menu sehat yang dipersonalisasi, menjawab pertanyaan gizi umum, menyediakan resep sederhana, dan menyusun jadwal makan mingguan. Keunikan Sago terletak pada pendekatannya yang ramah, informatif, dan terintegrasi dengan kearifan lokal Sulawesi Tenggara.

Proyek ini memanfaatkan kekuatan Large Language Model (LLM) dari Google Gemini yang diorkestrasi menggunakan LangChain dan LangGraph untuk menciptakan pengalaman percakapan yang cerdas dan adaptif.

## 2\. Fitur Utama

  * **Rekomendasi Gizi Terpersonalisasi**: Menyesuaikan saran menu berdasarkan profil pengguna (nama, usia anak, jenis kelamin anak) dan preferensi diet spesifik.
  * **Sentuhan Lokal Sulawesi Tenggara**: Memahami dan memberikan rekomendasi yang relevan dengan bahan makanan, resep tradisional, dan kebiasaan makan khas daerah Sulawesi Tenggara (misalnya Sinonggi, Kasoami, Ikan Bakar Buton).
  * **Informasi Gizi Akurat**: Menyediakan detail nilai gizi (kalori, protein, karbohidrat, lemak, vitamin, mineral) untuk berbagai jenis makanan dari dataset lokal.
  * **Pembuatan Resep Sederhana**: Mampu menghasilkan resep masakan umum yang mudah diikuti.
  * **Penyusunan Rencana Makan Mingguan**: Membantu pengguna membuat jadwal makan seimbang untuk satu minggu penuh.
  * **Interaksi Ramah dan Adaptif**: Menggunakan nada percakapan yang mendukung dan positif, serta mampu beradaptasi dengan pertanyaan dan kebutuhan pengguna.
  * **Antarmuka Pengguna Intuitif (UI/UX)**: Desain modern berbasis web dengan fitur seperti riwayat chat yang dapat diakses, mode gelap, dan manajemen profil.

## 3\. Arsitektur Sistem

### 3.1. Diagram Blok

Berikut adalah gambaran arsitektur sistem Sago:

```mermaid
graph TD
    A[Pengguna] --> B(Antarmuka Web HTML/CSS/JS)
    B --> C{Aplikasi Flask Python}
    C -- Permintaan Chat --> D[Agent Gizi (LangGraph)]
    D -- Panggilan Tool --> E{Tools Kustom}
    E -- Data Makanan --> F[Dataset Nutrisi CSV]
    E -- Data Rekomendasi --> G[Data Rekomendasi Hardcoded]
    D -- Hasil Respons --> C
    C -- Render Respons --> B
    C -- Manajemen Sesi/Profil --> H[Database Lokal (SQLite)]
```

**Penjelasan Komponen:**

  * **Antarmuka Web (HTML/CSS/JS)**: Bagian *front-end* aplikasi yang menyediakan tampilan interaktif bagi pengguna. HTML untuk struktur, CSS untuk gaya, dan JavaScript untuk interaktivitas (mengirim pesan, menampilkan riwayat, toggling sidebar, manajemen modal).
  * **Aplikasi Flask (Python)**: Kerangka kerja *backend* yang melayani halaman web, mengelola sesi pengguna, menerima permintaan chat, dan mengintegrasikan dengan *agent* gizi.
  * **Agent Gizi (LangGraph)**: Inti kecerdasan buatan. Ini adalah *finite state machine* yang mengelola alur percakapan, menentukan kapan harus memanggil *tools*, dan menghasilkan respons akhir menggunakan LLM.
  * **Tools Kustom**: Fungsi Python yang memungkinkan *agent* melakukan tindakan spesifik di luar kemampuan langsung LLM, seperti mencari nilai gizi, menghasilkan resep, atau memberikan rekomendasi.
  * **Dataset Nutrisi CSV**: Sumber data nilai gizi makanan. Terdiri dari dataset Bahasa Indonesia (`nutrition_food_dataset_id.csv`) dan data gizi umum yang hardcoded di `agent.py`.
  * **Database Lokal (SQLite)**: Digunakan untuk menyimpan riwayat sesi chat pengguna dan profil pengguna, memungkinkan persistensi data antar sesi.

### 3.2. Alur Data dan Interaksi Pengguna

1.  **Pengguna Mengakses Aplikasi**: Pengguna membuka URL aplikasi Flask. `app_flask.py` merender `home.html` sebagai halaman utama.
2.  **Mulai Chat**: Pengguna dapat mengklik tombol "Mulai Chat" di `home.html` yang akan mengarahkan ke `index.html` (halaman chatbot).
3.  **Memuat Sesi Chat**: Saat `index.html` dimuat, Flask mengambil riwayat chat dan profil pengguna dari database/session.
4.  **Interaksi Chat**:
      * Pengguna mengetik pesan di `chatInput` dan mengirimkannya.
      * JavaScript mengirim pesan tersebut ke *endpoint* `/chat` di Flask melalui AJAX (HTTP POST).
      * Flask menerima pesan, menyimpannya di database, dan memperbarui `session['user_profile']` jika ada.
      * Flask memuat *history* chat yang relevan dan profil pengguna, kemudian membuat *initial state* untuk *agent* LangGraph.
      * **Agent LangGraph Dipanggil**: `get_gizibot_response` dipanggil, menjalankan *agent* GiziBot.
          * LLM (`chatbot` node) menerima pesan pengguna dan *system instruction* yang diperkaya dengan data profil.
          * LLM memutuskan apakah akan merespons langsung atau memanggil *tool*.
          * **Jika Tool Dipanggil**: Alur beralih ke `nutrition_node`. *Tool* kustom yang relevan (misalnya `get_food_nutrition_facts`, `get_nutrition_recommendation`) dieksekusi. *Tools* ini mungkin membaca dari dataset CSV atau data hardcoded.
          * Hasil dari *tool* dikirim kembali ke *agent* sebagai `ToolMessage`.
          * *Agent* (`chatbot` node) memproses hasil *tool* dan menghasilkan respons akhir yang ramah pengguna.
      * Respons dari *agent* dikirim kembali ke Flask.
      * Flask menyimpan respons bot ke database.
      * Flask mengembalikan respons JSON ke JavaScript *front-end*.
      * JavaScript menerima respons, menampilkannya di `messagesContainer`, dan menggulir ke bagian bawah.
5.  **Manajemen Sesi & Profil**:
      * Pengguna dapat memulai sesi chat baru (`/new_chat_session`), menghapus sesi (`/delete_chat_session`), atau menghapus semua chat (`/clear`).
      * Pengguna dapat memperbarui profil mereka (`/update_profile`) melalui modal "Edit Profile", yang akan memperbarui `session['user_profile']` dan memengaruhi personalisasi *agent*.
      * Daftar riwayat sesi (`/get_chat_sessions`) diperbarui secara berkala dan ditampilkan di sidebar.

## 4\. Teknologi & Tools yang Digunakan

  * **Backend**:
      * **Python 3.9+**: Bahasa pemrograman utama.
      * **Flask**: *Micro-framework* web untuk membangun API dan melayani halaman HTML.
      * **LangChain**: Kerangka kerja untuk mengembangkan aplikasi berbasis LLM.
      * **LangGraph**: Ekstensi LangChain untuk membangun *agent* yang lebih kompleks dengan kontrol alur yang eksplisit (finite state machines).
      * **Google Gemini API (via `langchain_google_genai`)**: Model LLM yang digunakan untuk memahami bahasa alami dan menghasilkan respons.
      * **Pandas**: Untuk membaca dan memanipulasi dataset CSV nutrisi.
      * **SQLite (melalui modul `database.py`)**: Database ringan untuk menyimpan sesi chat dan profil pengguna.
      * **`python-dotenv`**: Untuk mengelola variabel lingkungan (API Key).
  * **Frontend**:
      * **HTML5**: Struktur halaman web.
      * **CSS3**: Styling dan desain antarmuka, termasuk responsive design.
      * **JavaScript (Vanilla JS)**: Interaktivitas halaman web, pengiriman/penerimaan pesan AJAX, manajemen UI.
      * **Marked.js**: Pustaka JavaScript untuk merender Markdown ke HTML di sisi klien (penting untuk format respons bot).
      * **MathJax**: Untuk merender notasi matematika (LaTeX) jika bot menghasilkan rumus gizi.
      * **Font Awesome**: Koleksi ikon.
      * **Google Fonts (Poppins)**: Font web untuk estetika.
      * **Bootstrap (opsional, dari template)**: Digunakan dalam `home.html` dan `articles.html` dari template awal untuk responsivitas dan komponen UI dasar.

## 5\. Pemrosesan Data

### 5.1. Deskripsi Dataset

Proyek ini menggunakan dataset nutrisi dalam format CSV untuk menyediakan informasi nilai gizi makanan.

  * **Nama File**: `nutrition_dataset/nutrition_food_dataset_id.csv`
  * **Sumber**: Dataset ini diasumsikan sebagai dataset gizi makanan yang telah di *curate* dan diterjemahkan. Dalam kasus nyata, ini bisa berasal dari USDA FoodData Central, BPOM, atau sumber data nutrisi terkemuka lainnya yang telah diproses.
  * **Format**: CSV (Comma Separated Values) dengan pemisah `;` (semicolon) dan encoding `utf-8`.
  * **Ukuran**: Diasumsikan relatif kecil hingga menengah, cocok untuk dimuat sepenuhnya ke memori menggunakan Pandas.
  * **Kolom Penting**:
      * `food`: Nama makanan dalam Bahasa Inggris.
      * `makanan_indonesia`: Nama makanan dalam Bahasa Indonesia (hasil terjemahan atau penyesuaian).
      * `caloric_value`: Nilai kalori (kkal).
      * `protein`: Kandungan protein (gram).
      * `carbohydrates`: Kandungan karbohidrat (gram).
      * `fat`: Kandungan lemak (gram).
      * Dan berbagai kolom lain untuk vitamin, mineral, serat, gula, dll.

### 5.2. Preprocessing Data

Preprocessing dataset dilakukan saat aplikasi Flask diinisialisasi (`agent.py`).

1.  **Pemuatan**: Dataset dimuat menggunakan `pandas.read_csv()`.
2.  **Pemisah dan Encoding**: Disesuaikan dengan `sep=';'` dan `encoding='utf-8'` seperti yang ditentukan.
3.  **Pembersihan Nama Kolom**: Nama-nama kolom dibersihkan (`.str.strip().str.replace(' ', '_').str.lower()`) untuk memastikan konsistensi dan akses yang mudah dalam kode Python (misalnya `caloric_value` daripada `Caloric Value`).
4.  **Penanganan Kolom Pertama**: Pemeriksaan dilakukan untuk mengatasi kemungkinan karakter `;` ekstra di awal nama kolom pertama.
5.  **Penanganan Data Hilang/Nol**: Dalam fungsi `get_food_nutrition_facts`, nilai `NaN` atau `0.0` untuk nutrisi tertentu tidak akan ditampilkan di tabel hasil, memastikan output yang lebih bersih dan relevan.

## 6\. Implementasi Sistem Temu Kembali Informasi

Sistem temu kembali informasi di Sago tidak menggunakan algoritma pencarian tradisional (seperti TF-IDF atau BM25) secara langsung pada dataset CSV. Sebaliknya, ia mengandalkan kombinasi:

1.  **Kemampuan LLM**: Model Gemini-nya sendiri sangat baik dalam memahami niat pengguna dan mengidentifikasi informasi apa yang dicari.
2.  **Orkestrasi Tools (LangGraph)**: *Agent* LangGraph yang menentukan *tool* mana yang paling relevan untuk dipanggil berdasarkan pesan pengguna dan *state* percakapan.
3.  **Pencarian Berbasis Pandas**: *Tool* `get_food_nutrition_facts` menggunakan kemampuan *filtering* Pandas untuk mencari data dalam DataFrame.

### 6.1. Detail Penggunaan Algoritma

  * **Retrieval**:
      * **Niat Pengguna**: LLM (Gemini) adalah "algoritma retrieval" pertama. Ia menganalisis pesan pengguna (`query`) untuk memahami apakah pengguna mencari informasi gizi umum, nilai gizi makanan spesifik, resep, atau rekomendasi.
      * **Pemilihan Tool**: Berdasarkan pemahaman niat, LLM menghasilkan `Tool Call` yang berisi nama *tool* yang relevan (`get_nutrition_info`, `get_food_nutrition_facts`, `generate_recipe`, `get_nutrition_recommendation`, `generate_weekly_meal_plan`) dan argumen yang diekstrak dari pesan pengguna.
  * **Ranking (implisit)**:
      * Dalam `get_food_nutrition_facts`: Prioritas pencarian dilakukan secara berurutan:
        1.  Pencarian **kecocokan persis** di kolom `makanan_indonesia` (Bahasa Indonesia).
        2.  Pencarian **kecocokan persis** di kolom `food` (Bahasa Inggris).
        3.  Pencarian **kecocokan parsial** (`.str.contains()`) di `makanan_indonesia`.
        4.  Pencarian **kecocokan parsial** (`.str.contains()`) di `food`.
            Ini adalah bentuk *ranking* sederhana yang memprioritaskan kecocokan yang lebih akurat dan bahasa Indonesia terlebih dahulu.
  * **Klasifikasi**:
      * LLM secara internal melakukan klasifikasi jenis pertanyaan untuk memilih *tool* yang benar. Misalnya, "berapa kalori nasi?" akan diklasifikasikan sebagai pertanyaan "nilai gizi makanan" yang memicu `get_food_nutrition_facts`.

### 6.2. Contoh Input & Output Sistem

**Skenario 1: Pencarian Nilai Gizi Makanan**

  * **Input Pengguna**: "berapa kalori nasi putih?"
  * **Proses Agent**:
    1.  LLM menerima pesan, mengklasifikasikan sebagai pertanyaan nilai gizi.
    2.  LLM memanggil `get_food_nutrition_facts(food_name="nasi putih")`.
    3.  *Tool* mencari "nasi putih" di `nutrition_df_id` (kolom `makanan_indonesia`).
    4.  Menemukan kecocokan.
    5.  *Tool* mengembalikan data dalam format tabel Markdown.
    6.  LLM menerima hasil, memprosesnya menjadi respons ramah pengguna.
  * **Output GiziBot**:
    ```markdown
    📊 **Nilai Gizi untuk Nasi Putih (per perkiraan porsi standar):**

    | Zat Gizi           | Jumlah (perkiraan) |
    |--------------------|--------------------|
    | Kalori             | 130 kkal           |
    | Lemak Total        | 0.3 g              |
    | Karbohidrat        | 28.17 g            |
    | Gula               | 0.05 g             |
    | Protein            | 2.69 g             |
    | Serat Pangan       | 0.4 g              |
    | Air                | 68.44 g            |
    | ... (nutrisi lain) | ...                |

    *Data ini berdasarkan perkiraan per porsi standar dari Data Nutrisi Makanan

    Semoga informasi ini bermanfaat, iyo!
    ```

**Skenario 2: Rekomendasi Gizi Terpersonalisasi (dengan Profil & Lokal)**

  * **Profil Pengguna**: Nama: Budi, Anak: [ {nama: "Citra", usia: 8, gender: "perempuan"} ]
  * **Input Pengguna**: "Saya mau rekomendasi menu sehat untuk anak saya yang umur 8 tahun, dia suka sayuran dan saya ingin ada sentuhan Sultra."
  * **Proses Agent**:
    1.  LLM menerima pesan, mengklasifikasikan sebagai permintaan rekomendasi.
    2.  LLM mengidentifikasi `age_group="anak"`, `dietary_preferences=["vegetarian", "khas_sultra"]` (implisit dari "suka sayuran" dan "sentuhan Sultra").
    3.  LLM memanggil `get_nutrition_recommendation(age_group="anak", dietary_preferences=["vegetarian", "khas_sultra"])`.
    4.  *Tool* mencari di `NUTRITION_DATA` untuk `anak` dan `khas_sultra`.
    5.  *Tool* mengembalikan daftar menu dan tips.
    6.  LLM merangkai respons dengan bahasa yang ramah dan logat lokal.
  * **Output GiziBot**:
    ```markdown
    🍽️ **Rekomendasi Menu untuk Anak Anda, Citra (8 tahun)**

    Wah, mantapji ini! Berdasarkan preferensi makanan 'vegetarian, khas_sultra' dan kebutuhan 'umum', berikut menu sehat khas Sulawesi Tenggara yang saya rekomendasikan:

    1. Sarapan: Sinonggi dengan ikan kuah kuning bening (ikan cakalang/tuna, bukan santan kental)
    2. Makan siang: Nasi jagung, ikan bakar (kakap/bandeng), tumis bunga pepaya, dan pisang
    3. Camilan: Barongko (pisang kukus) atau putu cangkiri
    4. Makan malam: Sop konro (daging sapi) tanpa lemak berlebihan dengan sedikit nasi dan sambal mangga

    💡 **Tips Nutrisi Tambahan:**
    - Makanan khas Sultra banyak yang sehat lho, seperti ikan laut yang kaya Omega-3 dan sagu sebagai karbohidrat kompleks.
    - Perhatikan porsi dan cara memasak agar tetap sehat (kurangi santan kental, gorengan)

    Semoga bermanfaat, iyo!
    ```

## 7\. Analisis dan Evaluasi

### 7.1. Hasil Pengujian Sistem

Pengujian dilakukan secara manual melalui antarmuka web dan terminal dengan berbagai skenario.

  * **Akurasi Pemilihan Tool**: Sistem cukup akurat dalam memilih *tool* yang tepat berdasarkan niat pengguna. Model Gemini-Flash efektif dalam memahami pertanyaan dan mengekstrak argumen yang diperlukan untuk *tools*.
  * **Personalisasi**: Integrasi data profil (nama pengguna, informasi anak) ke dalam *system instruction* LLM berhasil membuat respons terasa lebih personal tanpa perlu bertanya ulang.
  * **Respons Lokal**: *Tools* dan *system instruction* yang disesuaikan untuk Sulawesi Tenggara memungkinkan agen memberikan rekomendasi dan informasi yang relevan secara budaya.
  * **Kecepatan Respon**: Karena menggunakan Gemini-Flash (model cepat) dan *tools* yang bersifat *in-memory* (Pandas DataFrames), respons sistem secara keseluruhan sangat cepat, memberikan pengalaman pengguna yang baik.
  * **Penanganan Error**: Sistem memiliki *error handling* dasar untuk kasus di mana data tidak ditemukan atau terjadi kesalahan internal.

*(**Catatan:** Untuk hasil pengujian yang lebih detail dan ilmiah, diperlukan matriks evaluasi seperti akurasi niat, relevansi respon, kepuasan pengguna (survei), dan latensi. Anda dapat menambahkan grafik atau tabel di sini jika Anda telah melakukan pengujian kuantitatif.)*

### 7.2. Studi Kasus/Skenario Uji Coba Pengguna

1.  **Skenario Pendaftaran Profil**: Pengguna baru diminta mengisi profil sebelum bisa chat personal. Setelah mengisi profil (nama dan info anak), Sago langsung menggunakan data tersebut dalam percakapan selanjutnya.
      * **Prompt**: "Halo Sago, saya orang tua dari anak bernama Rina, usia 7 tahun, perempuan. Saya ingin resep masakan untuknya."
      * **Respon**: Sago akan menyapa "Halo Budi\!...", "Untuk Rina, usia 7 tahun..." dan kemudian memproses permintaan resep.
2.  **Skenario Pertanyaan Gizi Umum**: Pengguna bertanya tentang nutrisi dasar.
      * **Prompt**: "Apa manfaat protein?"
      * **Respon**: Sago memberikan penjelasan tentang protein, manfaatnya, dan sumber makanannya.
3.  **Skenario Pencarian Nilai Gizi Lokal**: Pengguna bertanya tentang makanan khas.
      * **Prompt**: "Berapa kalori kasoami?"
      * **Respon**: Sago menampilkan tabel nilai gizi untuk kasoami.
4.  **Skenario Permintaan Rencana Makan Mingguan**: Pengguna meminta jadwal makan.
      * **Prompt**: "Bisakah buatkan saya rencana makan mingguan untuk anak remaja saya, dia vegetarian."
      * **Respon**: Sago menghasilkan rencana makan 7 hari yang spesifik untuk remaja vegetarian.

### 7.3. Kelebihan dan Keterbatasan Sistem

**Kelebihan:**

  * **Personalisasi Tinggi**: Rekomendasi dan interaksi yang disesuaikan dengan profil pengguna, menciptakan pengalaman yang lebih relevan dan mendukung.
  * **Relevansi Lokal**: Mampu menyediakan informasi dan rekomendasi yang spesifik untuk konteks Sulawesi Tenggara, menjadikannya unik dan lebih bermanfaat bagi audiens lokal.
  * **Antarmuka Pengguna Modern**: Desain web yang responsif, intuitif, dan estetis meningkatkan pengalaman pengguna.
  * **Eksekusi Tool yang Efisien**: Penggunaan LangGraph dan *in-memory dataframes* untuk *tools* memastikan respons cepat.
  * **Mudah Diperluas**: Arsitektur modular dengan *tools* dan *state* LangGraph memudahkan penambahan fitur atau *tools* baru di masa mendatang.

**Keterbatasan:**

  * **Data Statis untuk Resep**: Fungsi `generate_recipe` saat ini hanya menyediakan resep hardcoded. Untuk resep yang lebih bervariasi dan dinamis, diperlukan integrasi dengan API resep eksternal (yang mungkin berbayar).
  * **Skalabilitas Database Sederhana**: Penggunaan SQLite internal dan *dummy* `chat_sessions_db` di memori tidak cocok untuk skala pengguna yang besar. Diperlukan database eksternal yang lebih robust (PostgreSQL, MySQL) untuk produksi.
  * **Domain Terbatas**: Agen sangat fokus pada gizi anak dan remaja dengan konteks Sultra. Pertanyaan di luar domain ini mungkin menghasilkan respons yang kurang optimal atau 'halusinasi' dari LLM.
  * **Ketergantungan pada Kualitas Data CSV**: Akurasi nilai gizi sepenuhnya bergantung pada kualitas dan kelengkapan dataset CSV yang disediakan.
  * **Tanpa Pembelajaran Berkelanjutan**: Agent tidak "belajar" dari interaksi sebelumnya untuk meningkatkan pengetahuannya secara otonom (selain memahami konteks sesi saat ini). Penyesuaian memerlukan pembaruan kode atau model.
  * **Validasi Input Tool**: Meskipun ada validasi argumen dasar, *tool* mungkin masih menghasilkan respons generik jika input terlalu ambigu atau tidak sesuai dengan data yang ada.

## 8\. Setup & Instalasi

Untuk menjalankan Sago di lingkungan lokal Anda, ikuti langkah-langkah berikut:

1.  **Clone Repositori**:

    ```bash
    git clone [URL_REPOSITORI_ANDA]
    cd [NAMA_FOLDER_REPOSITORI]
    ```

2.  **Buat Virtual Environment** (Sangat Disarankan):

    ```bash
    python -m venv venv
    ```

3.  **Aktifkan Virtual Environment**:

      * **Windows**: `.\venv\Scripts\activate`
      * **macOS/Linux**: `source venv/bin/activate`

4.  **Instal Dependensi**:

    ```bash
    pip install -r requirements.txt
    ```

    *(**Catatan**: Buat file `requirements.txt` yang berisi semua dependensi seperti `flask`, `langchain-google-genai`, `langchain`, `langgraph`, `pandas`, `python-dotenv`, `werkzeug`, dll.)*

5.  **Siapkan Google Gemini API Key**:

      * Dapatkan API Key dari [Google AI Studio](https://aistudio.google.com/app/apikey).
      * Buat file `.env` di direktori root proyek Anda dan tambahkan baris berikut:
        ```
        GOOGLE_API_KEY="YOUR_GEMINI_API_KEY_HERE"
        FLASK_SECRET_KEY="some_random_secret_key_for_flask_session"
        ```
        Ganti `YOUR_GEMINI_API_KEY_HERE` dengan kunci API Anda. `FLASK_SECRET_KEY` adalah kunci rahasia untuk sesi Flask.

6.  **Siapkan Dataset Nutrisi**:

      * Pastikan file `nutrition_food_dataset_id.csv` berada di dalam folder `nutrition_dataset/`. Jika folder `nutrition_dataset` belum ada, buatlah.

7.  **Siapkan Struktur Folder Frontend**:

      * Pastikan Anda memiliki struktur folder `templates/` dan `static/` yang benar, berisi `index.html`, `home.html`, `articles.html`, `recipes.html`, dan subfolder `static/css`, `static/js`, `static/images`, `static/vendor` (jika menggunakan Bootstrap/JS dari template).
      * Pastikan file `sago_logo.png` dan `sago_favicon.png` ada di `static/images/`.

8.  **Jalankan Aplikasi Flask**:

    ```bash
    python app_flask.py
    ```

9.  **Akses Aplikasi**:
    Buka browser web Anda dan navigasi ke `http://127.0.0.1:5000/`.

## 9\. Kontribusi

Kami menyambut kontribusi dari komunitas\! Jika Anda ingin berkontribusi pada Sago, silakan:

1.  Fork repositori ini.
2.  Buat branch baru (`git checkout -b feature/NamaFiturBaru`).
3.  Lakukan perubahan Anda.
4.  Commit perubahan Anda (`git commit -m 'Tambahkan fitur baru: Nama Fitur'`).
5.  Push ke branch Anda (`git push origin feature/NamaFiturBaru`).
6.  Buat Pull Request.

## 10\. Lisensi

Proyek ini dilisensikan di bawah Lisensi MIT. Lihat file [LICENSE](https://www.google.com/search?q=LICENSE) untuk detail lebih lanjut.

-----