# **Bahasa Indonesia**

# **Sago: Smart Agent Gizi Online (untuk Anak & Remaja di Sulawesi Tenggara)** 🥗✨

<div align="center">
      <img src="static/images/logo.png" controls width="80"></img>
</div> <!-- Pastikan path logo sesuai -->

Sago adalah aplikasi chatbot cerdas yang dirancang khusus untuk membantu orang tua dan pengasuh dalam mendidik dan memenuhi kebutuhan gizi anak-anak dan remaja (usia 5-18 tahun) dengan pendekatan yang relevan dan **membumi pada kearifan lokal Sulawesi Tenggara**.

Dibangun dengan teknologi Generative AI terbaru dari Google Gemini, Sago memberikan rekomendasi gizi personal, informasi nutrisi yang akurat, analisis status gizi (BMI), serta resep masakan yang praktis, semuanya disajikan dengan gaya bahasa yang akrab dan empatik khas masyarakat Sulawesi Tenggara.

## **Tujuan Proyek**

- **Meningkatkan Kesadaran Gizi:** Menyediakan sumber informasi gizi yang mudah diakses dan dipahami oleh orang tua/pengasuh.
- **Personalisasi Rekomendasi:** Memberikan saran gizi yang disesuaikan dengan usia, jenis kelamin, preferensi, dan kondisi gizi spesifik anak.
- **Mendukung Kearifan Lokal:** Mengintegrasikan makanan tradisional dan gaya komunikasi lokal Sulawesi Tenggara dalam setiap interaksi.
- **Deteksi Dini Masalah Gizi:** Membantu orang tua memantau status gizi anak melalui perhitungan BMI dan memberikan rekomendasi tindak lanjut ke fasilitas kesehatan jika diperlukan.
- **Aksesibilitas:** Memastikan informasi mudah diakses melalui chatbot interaktif, bahkan dengan fitur baca otomatis untuk kenyamanan pengguna.

## **Fitur Unggulan**

- **Konsultasi Gizi Interaktif:** Chatbot cerdas berbasis **Google Gemini 2.0 Flash** yang merespons pertanyaan gizi secara _real-time_.
- **Personalisasi Profil Anak:** Menyimpan informasi nama, umur, dan jenis kelamin anak (rentang usia 5-18 tahun sesuai Kemenkes) untuk rekomendasi yang sangat relevan.
- **Gaya Bahasa Lokal:** Menggunakan **logat dan frasa akrab khas masyarakat Sulawesi Tenggara** (`iyo`, `mantapji`, `santai mi dulu`) untuk menciptakan pengalaman komunikasi yang hangat dan membumi.
- **Rekomendasi Menu Sehat:** Memberikan daftar menu harian yang disesuaikan dengan kebutuhan usia, preferensi diet (misal: vegetarian), dan kebutuhan gizi spesifik (misal: tinggi protein, tinggi energi).
- **Analisis BMI Komprehensif:**
  - Menghitung dan menginterpretasikan **Body Mass Index (BMI)** anak/remaja berdasarkan umur dan jenis kelamin.
  - Memberikan status gizi (`kurus`, `normal`, `gemuk`, `obesitas`).
  - Menyertakan **saran gizi dan rekomendasi tindak lanjut yang jelas**, termasuk saran untuk konsultasi ke Posyandu, Puskesmas, atau rujukan ke dokter spesialis gizi/anak jika diperlukan.
  - Dilengkapi **sistem peringatan dini** dengan pesan tegas untuk kasus gizi buruk/obesitas parah.
- **Pencarian Nilai Gizi Makanan:** Menyediakan informasi detail nilai gizi (kalori, protein, dll.) dari makanan yang ada di dataset lokal (`nutrition_food_dataset_id.csv`), mendukung pencarian dalam Bahasa Indonesia dan Inggris.
- **Resep & Rencana Makan:** Mampu membuat resep sederhana dan menyusun rencana makan mingguan.
- **Manajemen Sesi Chat:** Riwayat percakapan tersimpan dan dapat diakses kembali kapan saja.
- **Fitur Pembacaan Respons (Text-to-Speech):** Respon dari Sago dapat dibacakan secara otomatis atau manual, sangat membantu orang tua yang lebih nyaman mendengarkan.
- **Antarmuka Pengguna (UI) Responsif & Ramah Orang Tua:** Desain yang bersih, navigasi intuitif, dan elemen yang mudah dijangkau, dengan dukungan mode gelap (Dark Mode).

## **Arsitektur Sistem**

Sago dibangun dengan pendekatan **Generative AI Agent** menggunakan:

- **Frontend:** HTML, CSS, JavaScript (termasuk Web Speech API untuk fitur Text-to-Speech).
- **Backend:** **Flask** (Python) sebagai framework web.
- **Agent Core:** **LangGraph** (untuk orkestrasi alur percakapan) dan **LangChain** (untuk integrasi LLM dan tools).
- **Model AI:** **Google Gemini 2.0 Flash** (melalui Google Generative AI API).
- **Database:** SQLite (untuk menyimpan riwayat chat dan profil pengguna).
- **Data Nutrisi:** Dataset CSV lokal untuk informasi gizi makanan.

LLM berfungsi sebagai 'otak' yang memahami niat pengguna dan memutuskan kapan harus memanggil 'tools' (fungsi Python spesifik) yang bertindak sebagai 'tangan' untuk melakukan tugas seperti menghitung BMI atau mencari data. Konteks percakapan dikelola dengan membatasi riwayat pesan yang dikirim ke LLM untuk optimasi penggunaan token API.

## **Demo Video**

<div align="center">
      <a href="https://youtu.be/AMiF4tCYqPE" target="_blank">
            <img src="https://img.youtube.com/vi/AMiF4tCYqPE/0.jpg" alt="Demo Video Thumbnail" width="700"/>
            <br>
      </a>
</div>

## **Instalasi dan Jalankan Proyek**

### **Prasyarat**

- Python 3.8+
- pip (Pengelola Paket Python)
- Akun Google Cloud dengan Google Generative AI API diaktifkan
- `GOOGLE_API_KEY` (diatur sebagai environment variable)

### **Langkah-langkah Instalasi**

1.  **Clone repositori ini:**

    ```bash
    git clone [URL_REPO_ANDA]
    cd sago
    ```

2.  **Buat Virtual Environment (Sangat Disarankan):**

    ```bash
    python -m venv venv
    source venv/bin/activate # Di macOS/Linux
    # venv\Scripts\activate # Di Windows
    ```

3.  **Instal Dependensi:**

    ```bash
    pip install -r requirements.txt
    ```

    (Pastikan `requirements.txt` Anda berisi `Flask`, `langchain-google-genai`, `langgraph`, `pandas`, `python-dotenv`, `werkzeug`, dll.)

4.  **Siapkan Google API Key:**

    - Dapatkan `GOOGLE_API_KEY` dari Google Cloud Console.
    - Buat file `.env` di root folder proyek Anda:
      ```
      GOOGLE_API_KEY="YOUR_API_KEY_HERE"
      FLASK_SECRET_KEY="some_random_secret_key" # Ganti dengan string acak yang kuat
      ```

5.  **Struktur Dataset Nutrisi:**
    - Pastikan file `nutrition_food_dataset_id.csv` berada di dalam folder `nutrition_dataset/`.
    - Struktur proyek Anda seharusnya terlihat seperti ini:
      ```
      sago/
      ├── agent.py
      ├── app_flask.py
      ├── database.py
      ├── .env
      ├── requirements.txt
      ├── templates/
      │   ├── chatbot.html
      │   ├── home.html
      │   ├── articles.html
      │   ├── recipes.html
      │   └── article-detail.html
      └── static/
          ├── css/
          │   └── style.css
          ├── js/
          │   └── script.js
          └── images/
              └── logo.png
      └── nutrition_dataset/
          └── nutrition_food_dataset_id.csv
      ```

### **Jalankan Aplikasi**

```bash
python app_flask.py
```

Aplikasi akan berjalan di `http://127.0.0.1:5000/`.

## **Kontribusi**

Masukan dan kontribusi dari para ahli gizi, dokter, pengembang, dan masyarakat sangat kami harapkan untuk terus menyempurnakan Sago. Jika Anda memiliki saran, temuan _bug_, atau ingin berkontribusi dalam pengembangan, silakan hubungi kami atau buka _issue_ di repositori ini.

---

**Sago: Sahabat Gizi Keluarga Sehat di Sulawesi Tenggara\!** 🌟

# **English**

# **Sago: Smart Online Nutrition Agent (for Children & Adolescents in Southeast Sulawesi)** 🥗✨

Sago is an intelligent chatbot application specifically designed to assist parents and guardians in educating themselves and meeting the nutritional needs of children and adolescents (aged 5-18 years) with an approach that is relevant and **rooted in the local wisdom of Southeast Sulawesi**.

Built with the latest Generative AI technology from Google Gemini, Sago provides personalized nutrition recommendations, accurate nutritional information, nutritional status analysis (BMI), and practical recipes, all delivered in a familiar and empathetic tone characteristic of Southeast Sulawesi's local community.

## **Project Goal**

- **Increase Nutritional Awareness:** To provide an easily accessible and understandable source of nutritional information for parents/guardians.
- **Personalized Recommendations:** To offer nutritional advice tailored to the child's age, gender, preferences, and specific nutritional conditions.
- **Support Local Wisdom:** To integrate traditional foods and local communication styles of Southeast Sulawesi into every interaction.
- **Early Detection of Nutritional Problems:** To help parents monitor their child's nutritional status through BMI calculations and provide follow-up recommendations to healthcare facilities if necessary.
- **Accessibility:** To ensure information is easily accessible via an interactive chatbot, complete with an audio-reading feature for user convenience.

## **Key Features**

- **Interactive Nutrition Consultation:** An intelligent chatbot powered by **Google Gemini 2.0 Flash** that responds to nutritional inquiries in _real-time_.
- **Child Profile Personalization:** Stores child's name, age, and gender (age range 5-18 years according to Ministry of Health guidelines) for highly relevant recommendations.
- **Local Language Style:** Utilizes **local dialects and familiar phrases characteristic of Southeast Sulawesi** (`iyo`, `mantapji`, `santai mi dulu`) to create a warm and down-to-earth communication experience.
- **Healthy Meal Recommendations:** Provides daily meal plans tailored to age-specific needs, dietary preferences (e.g., vegetarian), and specific nutritional requirements (e.g., high protein, high energy).
- **Comprehensive BMI Analysis:**
  - Calculates and interprets **Body Mass Index (BMI)** for children/adolescents based on age and gender.
  - Provides nutritional status (`underweight`, `normal`, `overweight`, `obese`).
  - Includes **clear nutritional advice and follow-up recommendations**, such as suggestions for consultation at the nearest Posyandu, Puskesmas, or referral to a specialist nutritionist/pediatrician if required.
  - Equipped with an **early warning system** with firm messages for severe malnutrition/obesity cases.
- **Food Nutritional Facts Search:** Provides detailed nutritional information (calories, protein, etc.) from a local dataset (`nutrition_food_dataset_id.csv`), supporting searches in both Indonesian and English.
- **Recipes & Meal Plans:** Capable of generating simple recipes and compiling weekly meal plans.
- **Chat Session Management:** Conversation history is saved and can be accessed at any time.
- **Response Reading Feature (Text-to-Speech):** Sago's responses can be automatically or manually read aloud, greatly assisting parents who prefer listening to information.
- **Responsive & Parent-Friendly User Interface (UI):** Clean design, intuitive navigation, and easily accessible elements, with Dark Mode support.

## **System Architecture**

Sago is built with a **Generative AI Agent** approach using:

- **Frontend:** HTML, CSS, JavaScript (including Web Speech API for Text-to-Speech feature).
- **Backend:** **Flask** (Python) as the web framework.
- **Agent Core:** **LangGraph** (for conversation flow orchestration) and **LangChain** (for LLM and tool integration).
- **AI Model:** **Google Gemini 2.0 Flash** (via Google Generative AI API).
- **Database:** SQLite (to store chat history and user profiles).
- **Nutrition Data:** Local CSV dataset for food nutritional information.

The LLM functions as the 'brain' that understands user intent and decides when to call specific 'tools' (Python functions) that act as 'hands' to perform tasks like calculating BMI or retrieving data. Conversation context is managed by limiting the message history sent to the LLM to optimize API token usage.

## **Demo Video**

<div align="center">
      <a href="https://youtu.be/AMiF4tCYqPE" target="_blank">
            <img src="https://img.youtube.com/vi/AMiF4tCYqPE/0.jpg" alt="Demo Video Thumbnail" width="700"/>
            <br>
      </a>
</div>

## **Installation and Running the Project**

### **Prerequisites**

- Python 3.8+
- pip (Python package installer)
- Google Cloud Account with Google Generative AI API enabled
- `GOOGLE_API_KEY` (set as an environment variable)

### **Installation Steps**

1.  **Clone this repository:**

    ```bash
    git clone [YOUR_REPO_URL]
    cd sago
    ```

2.  **Create a Virtual Environment (Highly Recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate # On macOS/Linux
    # venv\Scripts\activate # On Windows
    ```

3.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    (Ensure your `requirements.txt` includes `Flask`, `langchain-google-genai`, `langgraph`, `pandas`, `python-dotenv`, `werkzeug`, etc.)

4.  **Set up Google API Key:**

    - Obtain your `GOOGLE_API_KEY` from the Google Cloud Console.
    - Create a `.env` file in the root of your project folder:
      ```
      GOOGLE_API_KEY="YOUR_API_KEY_HERE"
      FLASK_SECRET_KEY="some_random_strong_secret_key" # Replace with a strong, random string
      ```

5.  **Nutrition Dataset Structure:**

    - Ensure your `nutrition_food_dataset_id.csv` file is located inside a `nutrition_dataset/` folder.
    - Your project structure should look like this:
      ```
      sago/
      ├── agent.py
      ├── app_flask.py
      ├── database.py
      ├── .env
      ├── requirements.txt
      ├── templates/
      │   ├── chatbot.html
      │   ├── home.html
      │   ├── articles.html
      │   ├── recipes.html
      │   └── article-detail.html
      └── static/
          ├── css/
          │   └── style.css
          ├── js/
          │   └── script.js
          └── images/
              └── logo.png
      └── nutrition_dataset/
          └── nutrition_food_dataset_id.csv
      ```

### **Run the Application**

```bash
python app_flask.py
```

The application will be accessible at `http://127.0.0.1:5000/`.

## **Contribution**

We highly value input and contributions from nutritionists, doctors, developers, and the community to continuously improve Sago. If you have suggestions, bug reports, or wish to contribute to the development, please feel free to reach out or open an issue in this repository.

---

**Sago: Your Partner for Healthy Family Nutrition in Southeast Sulawesi\!** 🌟
