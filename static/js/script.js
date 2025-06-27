// script.js

// Global references to DOM elements
const sidebar = document.getElementById('sidebar');
const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
const newChatBtn = document.getElementById('newChatBtn');
const conversationsList = document.getElementById('conversationsList');
const conversationsListToggle = document.getElementById('conversationsListToggle'); // New: Toggle button for conversations list
const settingsBtn = document.getElementById('settingsBtn');
const editProfileBtn = document.getElementById('editProfileBtn');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const messagesContainer = document.getElementById('messages');
const typingIndicator = document.getElementById('typingIndicator');
const settingsModal = document.getElementById('settingsModal');
const closeSettingsModal = document.getElementById('closeSettingsModal');
const clearAllChatsBtn = document.getElementById('clearAllChatsBtn');
const autoReadAloudToggle = document.getElementById('autoReadAloudToggle'); // New: Auto read aloud toggle
const editProfileModal = document.getElementById('editProfileModal');
const closeEditProfileModal = document.getElementById('closeEditProfileModal');
const profileForm = document.getElementById('profileForm');
const addChildBtn = document.getElementById('addChildBtn');
const childrenContainer = document.getElementById('childrenContainer');
const displayUserName = document.getElementById('displayUserName');
const displayChildrenInfo = document.getElementById('displayChildrenInfo');
const currentChatTitle = document.getElementById('currentChatTitle');
const mainContainer = document.getElementById('mainContainer'); // Reference to the main container

// --- Global Variables ---
let isMarkedLoaded = false;
let currentSessionId = window.currentSessionId; // From Flask Jinja
let userProfileData = window.userProfileData; // From Flask Jinja
const synth = window.speechSynthesis; // Web Speech API
let autoReadAloudEnabled = false; // State for auto read aloud

// --- Utility Functions ---

// Function to safely parse Markdown and queue MathJax rendering
function parseAndRender(text) {
    let renderedHtml = isMarkedLoaded ? marked.parse(text) : text;
    return renderedHtml;
}

// Function to speak text using Web Speech API
function speakText(text) {
    if (!synth) {
        console.warn('Web Speech API tidak didukung di browser ini.');
        return;
    }
    if (synth.speaking) {
        synth.cancel(); // Hentikan jika ada yang sedang berbicara
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'id-ID'; // Menggunakan Bahasa Indonesia

    // Opsional: Coba cari suara yang cocok dengan aksen Indonesia jika tersedia
    // Ini mungkin tidak ada di semua browser, jadi biarkan opsional
    // Untuk mendapatkan daftar suara: synth.onvoiceschanged = () => { console.log(synth.getVoices()); };
    // let voices = synth.getVoices();
    // let foundVoice = voices.find(voice => voice.lang === 'id-ID' && voice.name.includes('Google')); // Contoh: Coba cari suara Google
    // if (foundVoice) {
    //     utterance.voice = foundVoice;
    // }

    synth.speak(utterance);
}

// Function to add a message to the chat display
function addMessage(text, sender, timestamp) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');

    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    contentDiv.innerHTML = parseAndRender(text);

    const timeDiv = document.createElement('div');
    timeDiv.classList.add('message-timestamp');
    let date;
    if (typeof timestamp === 'string') {
        date = new Date(timestamp);
    } else {
        date = timestamp;
    }
    timeDiv.textContent = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Tambahkan tombol speaker hanya untuk pesan bot
    if (sender === 'assistant') {
        const speakButton = document.createElement('button');
        speakButton.classList.add('speak-btn');
        speakButton.innerHTML = '<i class="fas fa-volume-up"></i>';
        speakButton.title = 'Dengarkan pesan ini';
        speakButton.onclick = (event) => {
            event.stopPropagation(); // Mencegah event lain yang mungkin ada di message-content
            speakText(text);
        };
        contentDiv.appendChild(speakButton); // Tambahkan di dalam konten pesan
    }


    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Setelah menambahkan, jika MathJax dimuat, render ulang konten pesan yang baru
    if (window.MathJax) {
        setTimeout(() => {
            MathJax.typesetPromise([contentDiv]).catch((err) => console.error("MathJax typesetting failed for new message: " + err.message));
        }, 10);
    }

    // Baca otomatis jika diaktifkan dan ini adalah pesan bot
    if (sender === 'assistant' && autoReadAloudEnabled) {
        speakText(text);
    }
}

// Function to show/hide typing indicator
function showTypingIndicator(show) {
    typingIndicator.style.display = show ? 'flex' : 'none';
    if (show) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Function to update profile display in sidebar
function updateProfileDisplay(profile) {
    displayUserName.textContent = profile.name || 'Anonim';
    displayChildrenInfo.innerHTML = '';
    if (profile.children && profile.children.length > 0) {
        profile.children.forEach(child => {
            const span = document.createElement('span');
            span.classList.add('child-info');
            // Tambahkan info BMI jika ada
            const bmiInfo = profile.children_bmi_info && profile.children_bmi_info[child.name.toLowerCase()] ? 
                            ` (BMI: ${profile.children_bmi_info[child.name.toLowerCase()].bmi}, ${profile.children_bmi_info[child.name.toLowerCase()].status})` : '';
            span.textContent = `${child.name} (${child.age} thn, ${child.gender})${bmiInfo}`;
            displayChildrenInfo.appendChild(span);
        });
    } else {
        const span = document.createElement('span');
        span.classList.add('child-info');
        span.textContent = 'Belum ada info anak';
        displayChildrenInfo.appendChild(span);
    }
}

// --- Chat Functionality ---

async function sendMessage() {
    const userMessage = chatInput.value.trim();
    if (userMessage === '') return;

    const initialSuggestionsDiv = messagesContainer.querySelector('.initial-suggestions');
    if (initialSuggestionsDiv) {
        initialSuggestionsDiv.remove();
    }

    addMessage(userMessage, 'user', new Date().toISOString());
    chatInput.value = '';
    sendBtn.disabled = true;
    showTypingIndicator(true);

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userMessage }),
        });

        const data = await response.json();

        if (response.ok) {
            addMessage(data.response, 'assistant', new Date().toISOString());
            updateConversationListTimestamp(currentSessionId);
            if (messagesContainer.querySelectorAll('.message').length <= 3) {
                 loadConversationsList();
            }
            // Update local userProfileData with potentially new BMI info from backend session
            if (data.user_profile) { // Backend might return updated profile data
                userProfileData = data.user_profile;
                updateProfileDisplay(userProfileData);
            } else if (data.extracted_user_info) { 
                // Jika backend hanya mengembalikan extracted_user_info, merge secara manual
                // Ini mungkin tidak terjadi dengan setup app_flask.py saat ini, tapi baik untuk berjaga-jaga
                userProfileData.children_bmi_info = data.extracted_user_info.children_bmi_info || userProfileData.children_bmi_info;
                updateProfileDisplay(userProfileData);
            }
           
        } else {
            // Check for specific error types from backend
            if (data.status === 'profile_required') {
                alert(data.response);
                openModal('editProfileModal');
            } else if (data.error_type === 'rate_limit') { // Handle rate limit error
                alert(data.response); // Show specific rate limit message
            }
            else {
                alert(`Error: ${data.response || 'Terjadi kesalahan tidak diketahui.'}`);
            }
            addMessage(`Error: ${data.response || 'Terjadi kesalahan tidak diketahui.'}`, 'assistant', new Date().toISOString());
        }
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Maaf, terjadi kesalahan koneksi atau pemrosesan respons. Silakan coba lagi.');
        addMessage('Maaf, terjadi kesalahan koneksi atau pemrosesan respons. Silakan coba lagi.', 'assistant', new Date().toISOString());
    } finally {
        sendBtn.disabled = false;
        showTypingIndicator(false);
        chatInput.style.height = 'auto';
    }
}

// Function to set message input (for example questions)
function setMessage(text) {
    chatInput.value = text;
    sendMessage();
    toggleSidebar(false); // Tutup sidebar setelah memilih saran
}

// --- Sidebar & Session Management ---

function toggleSidebar(forceOpen = null) {
    if (window.innerWidth <= 768) { // Mobile behavior: overlay
        if (forceOpen === true) {
            sidebar.classList.add('open');
            mainContainer.classList.add('sidebar-open-mobile'); // Add class to main container for overlay
        } else if (forceOpen === false) {
            sidebar.classList.remove('open');
            mainContainer.classList.remove('sidebar-open-mobile'); // Remove overlay
        } else {
            sidebar.classList.toggle('open');
            mainContainer.classList.toggle('sidebar-open-mobile'); // Toggle overlay
        }
    } else { // Desktop behavior: push content / minimal view
        if (forceOpen === true) {
            sidebar.classList.remove('closed-desktop'); // Open
            conversationsList.style.display = 'block'; // Tampilkan kembali daftar percakapan
        } else if (forceOpen === false) {
            sidebar.classList.add('closed-desktop'); // Close
            conversationsList.style.display = 'none'; // Sembunyikan daftar percakapan
        } else {
            sidebar.classList.toggle('closed-desktop'); // Toggle
            conversationsList.style.display = sidebar.classList.contains('closed-desktop') ? 'none' : 'block';
        }
    }
}


async function loadConversationsList() {
    try {
        const response = await fetch('/get_chat_sessions');
        const data = await response.json();
        conversationsList.innerHTML = '';

        if (data.sessions.length === 0) {
            conversationsList.innerHTML = '<p style="text-align:center; opacity:0.7; font-size:0.9em; padding:20px;">Belum ada percakapan. Mulai yang baru!</p>';
            // Hide the actual list if empty, but keep the toggle button visible
            conversationsList.style.display = 'none'; 
            return;
        } else {
            // Ensure the list is visible when there are conversations, unless sidebar is closed
            if (!sidebar.classList.contains('closed-desktop')) {
                conversationsList.style.display = 'block';
            }
        }

        data.sessions.forEach(session => {
            const sessionItem = document.createElement('div');
            sessionItem.classList.add('conversation-item');
            if (session.session_id === currentSessionId) {
                sessionItem.classList.add('active');
                currentChatTitle.textContent = session.title;
            }
            sessionItem.dataset.sessionId = session.session_id;

            sessionItem.innerHTML = `
                <span class="conversation-title">${session.title}</span>
                <span class="conversation-timestamp">${session.display_updated_at}</span>
                <button class="delete-conversation-btn" data-session-id="${session.session_id}" title="Hapus sesi ini">
                    <i class="fas fa-trash-alt"></i>
                </button>
            `;
            sessionItem.addEventListener('click', async (e) => {
                if (e.target.closest('.delete-conversation-btn')) {
                    e.stopPropagation();
                    await deleteChatSession(session.session_id);
                } else {
                    await loadChatSession(session.session_id);
                    toggleSidebar(false); // Tutup sidebar setelah memuat sesi baru
                }
            });
            conversationsList.appendChild(sessionItem);
        });
    }
    catch (error) {
        console.error('Error loading conversations list:', error);
    }
}

async function loadChatSession(sessionId) {
    try {
        const response = await fetch(`/get_chat_history/${sessionId}`);
        const data = await response.json();

        if (response.ok) {
            messagesContainer.innerHTML = '';
            data.messages.forEach(msg => {
                addMessage(msg.content, msg.role, msg.timestamp);
            });
            currentSessionId = data.current_session_id;
            updateActiveConversationItem(currentSessionId);

            const sessionTitleItem = document.querySelector(`.conversation-item[data-session-id="${currentSessionId}"] .conversation-title`);
            if (sessionTitleItem) {
                currentChatTitle.textContent = sessionTitleItem.textContent;
            } else {
                currentChatTitle.textContent = 'Sago Chat';
            }

            displayInitialSuggestions();
        } else {
            alert(`Gagal memuat riwayat chat: ${data.message}`);
        }
    } catch (error) {
        console.error('Error loading chat session:', error);
        alert('Terjadi kesalahan saat memuat sesi chat.');
    }
}

async function deleteChatSession(sessionId) {
    if (!confirm('Apakah Anda yakin ingin menghapus sesi chat ini?')) return;

    try {
        const response = await fetch(`/delete_chat_session/${sessionId}`, { method: 'POST' });
        const data = await response.json();
        if (response.ok) {
            alert(data.message);
            if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                loadConversationsList();
            }
        } else {
            alert(`Gagal menghapus sesi: ${data.message}`);
        }
    } catch (error) {
        console.error('Error deleting chat session:', error);
        alert('Terjadi kesalahan saat menghapus sesi chat.');
    }
}

async function startNewChat() {
    try {
        const response = await fetch('/new_chat_session', { method: 'POST' });
        const data = await response.json();
        if (response.ok && data.redirect) {
            window.location.href = data.redirect;
        } else {
            if (data.status === 'profile_required') {
                alert(data.response);
                openModal('editProfileModal');
            } else {
                alert(`Gagal memulai chat baru: ${data.message}`);
            }
        }
    } catch (error) {
        console.error('Error starting new chat:', error);
        alert('Terjadi kesalahan saat memulai chat baru.');
    }
}

function updateConversationListTimestamp(sessionId) {
    const activeItem = document.querySelector(`.conversation-item[data-session-id="${sessionId}"]`);
    if (activeItem) {
        activeItem.querySelector('.conversation-timestamp').textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
}

function updateActiveConversationItem(newSessionId) {
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
    const newItem = document.querySelector(`.conversation-item[data-session-id="${newSessionId}"]`);
    if (newItem) {
        newItem.classList.add('active');
    }
}

// --- Initial Suggestions Display ---
function displayInitialSuggestions() {
    const messagesCount = messagesContainer.querySelectorAll('.message').length;

    if (messagesContainer.querySelector('.initial-suggestions')) {
        return;
    }

    // Hanya tampilkan saran jika belum ada chat atau hanya ada pesan selamat datang
    if (messagesCount <= 1) {
        const userName = userProfileData.name && userProfileData.name !== 'Anonim' ? userProfileData.name : 'Anda';
        const suggestionsHTML = `
            <div class="initial-suggestions">
                <h2>Hai ${userName}, ada yang bisa Sago bantu?</h2>
                <p>Anda bisa bertanya tentang nutrisi atau meminta rekomendasi menu. Contohnya:</p>
                <div class="suggestion-buttons">
                    <button onclick="setMessage('Rekomendasi menu sehat untuk anak saya')">
                        Rekomendasi menu anak
                    </button>
                    <button onclick="setMessage('Apa manfaat protein untuk anak saya?')">
                        Manfaat protein
                    </button>
                    <button onclick="setMessage('Resep sup ayam yang sehat')">
                        Resep sup ayam
                    </button>
                    <button onclick="setMessage('Buatkan rencana makan mingguan untuk anak saya')">
                        Rencana makan mingguan
                    </button>
                    <button onclick="setMessage('Berapa kalori nasi putih?')">
                        Nilai gizi nasi
                    </button>
                    <button onclick="setMessage('Bagaimana cara memenuhi kebutuhan serat?')">
                        Kebutuhan serat
                    </button>
                    <button onclick="setMessage('Cek BMI anak saya')">
                        Cek BMI Anak
                    </button>
                </div>
            </div>
        `;
        messagesContainer.insertAdjacentHTML('beforeend', suggestionsHTML);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}


// --- Profile & Settings Modals ---

// Open/Close Modals
function openModal(modalId) { document.getElementById(modalId).classList.add('open'); }
function closeModal(modalId) { document.getElementById(modalId).classList.remove('open'); }

// Settings Modal
settingsBtn.addEventListener('click', () => openModal('settingsModal'));
closeSettingsModal.addEventListener('click', () => closeModal('settingsModal'));
clearAllChatsBtn.addEventListener('click', async () => {
    if (confirm('Ini akan menghapus SEMUA riwayat chat Anda. Apakah Anda yakin?')) {
        try {
            const response = await fetch('/clear', { method: 'POST' });
            const data = await response.json();
            if (response.ok && data.redirect) {
                alert(data.message);
                window.location.href = data.redirect;
            } else {
                alert(`Gagal menghapus semua chat: ${data.message}`);
            }
        } catch (error) {
            console.error('Error clearing all chats:', error);
            alert('Terjadi kesalahan saat menghapus semua chat.');
        }
    }
});
// Dark Mode Toggle
const darkModeToggle = document.getElementById('darkModeToggle');
darkModeToggle.checked = localStorage.getItem('darkMode') === 'enabled';
if (darkModeToggle.checked) { document.body.classList.add('dark-mode'); }
darkModeToggle.addEventListener('change', () => {
    if (darkModeToggle.checked) {
        document.body.classList.add('dark-mode');
        localStorage.setItem('darkMode', 'enabled');
    } else {
        document.body.classList.remove('dark-mode');
        localStorage.setItem('darkMode', 'disabled');
    }
});

// Auto Read Aloud Toggle
autoReadAloudToggle.checked = localStorage.getItem('autoReadAloud') === 'enabled';
autoReadAloudEnabled = autoReadAloudToggle.checked; // Inisialisasi state global
autoReadAloudToggle.addEventListener('change', () => {
    if (autoReadAloudToggle.checked) {
        autoReadAloudEnabled = true;
        localStorage.setItem('autoReadAloud', 'enabled');
    } else {
        autoReadAloudEnabled = false;
        localStorage.setItem('autoReadAloud', 'disabled');
        if (synth.speaking) {
            synth.cancel(); // Hentikan jika sedang berbicara
        }
    }
});


// Edit Profile Modal
editProfileBtn.addEventListener('click', () => {
    populateProfileForm(userProfileData);
    openModal('editProfileModal');
});
closeEditProfileModal.addEventListener('click', () => closeModal('editProfileModal'));

addChildBtn.addEventListener('click', () => addChildField());
profileForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(profileForm);
    const userName = formData.get('userName');
    const children = [];
    let hasInvalidChildAge = false; // Flag untuk melacak validasi usia

    document.querySelectorAll('.child-entry').forEach(childDiv => {
        const name = childDiv.querySelector('.child-name').value.trim();
        const age = parseInt(childDiv.querySelector('.child-age').value);
        const gender = childDiv.querySelector('.child-gender').value.trim();
        
        if (name && !isNaN(age) && gender) {
            // Validasi usia di frontend sesuai Kemenkes: 5-9 tahun (anak), 10-18 tahun (remaja)
            if (age < 5 || age > 18) {
                hasInvalidChildAge = true;
                // Memberikan feedback visual langsung (opsional, bisa dengan alert)
                childDiv.querySelector('.child-age').style.borderColor = 'red';
                alert(`Umur ${name} (${age} tahun) tidak valid. Sago hanya melayani anak usia 5-18 tahun.`);
            } else {
                childDiv.querySelector('.child-age').style.borderColor = ''; // Reset border
                children.push({ name, age, gender });
            }
        }
    });

    if (hasInvalidChildAge) {
        return; // Hentikan proses submit jika ada usia anak yang tidak valid
    }

    const newProfileData = { userName, children };

    try {
        const response = await fetch('/update_profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newProfileData),
        });
        const data = await response.json();
        if (response.ok) {
            alert(data.message);
            userProfileData = data.user_profile; // Update local data with new profile
            updateProfileDisplay(userProfileData);
            closeModal('editProfileModal');
            loadConversationsList();

            // Opsional: Reload halaman untuk memastikan userProfileData di Flask session terupdate,
            // namun untuk UX lebih baik, hindari reload penuh jika tidak esensial.
            // window.location.href = window.location.pathname + "?session_id=" + currentSessionId;
        } else {
            alert(`Gagal menyimpan profil: ${data.message}`);
        }
    } catch (error) {
        console.error('Error saving profile:', error);
        alert('Terjadi kesalahan saat menyimpan profil.');
    }
});

function populateProfileForm(profile) {
    document.getElementById('userName').value = profile.name === "Anonim" ? "" : profile.name;
    childrenContainer.innerHTML = '';
    // Sort children by name for consistent display
    const sortedChildren = [...profile.children].sort((a,b) => a.name.localeCompare(b.name));
    sortedChildren.forEach(child => addChildField(child));
}

function addChildField(child = {}) {
    const template = document.getElementById('child-template');
    const clone = template.content.cloneNode(true);
    clone.querySelector('.child-name').value = child.name || '';
    clone.querySelector('.child-age').value = child.age || '';
    clone.querySelector('.child-gender').value = child.gender || '';
    clone.querySelector('.remove-child-btn').addEventListener('click', (e) => {
        e.target.closest('.child-entry').remove();
    });
    childrenContainer.appendChild(clone);
}


// --- Event Listeners ---

document.addEventListener('DOMContentLoaded', () => {
    if (typeof marked !== 'undefined') {
        isMarkedLoaded = true;
    }

    chatInput.addEventListener('input', autoResizeTextarea);
    autoResizeTextarea();

    loadConversationsList();
    updateProfileDisplay(userProfileData);

    sidebarToggleBtn.addEventListener('click', () => {
        toggleSidebar();
    });

    // Close sidebar if clicking outside when in mobile overlay mode
    mainContainer.addEventListener('click', (event) => {
        if (window.innerWidth <= 768 && sidebar.classList.contains('open') && !sidebar.contains(event.target) && !sidebarToggleBtn.contains(event.target)) {
            toggleSidebar(false);
        }
    });

    newChatBtn.addEventListener('click', startNewChat);

    // New: Event listener for the conversations list toggle button
    conversationsListToggle.addEventListener('click', () => {
        // Toggle the visibility of the actual conversations list
        const isClosed = sidebar.classList.contains('closed-desktop');
        if (isClosed) { // If sidebar is closed, open it to show the list
            toggleSidebar(true);
        } else { // If sidebar is open, simply toggle the list visibility
            conversationsList.style.display = conversationsList.style.display === 'none' ? 'block' : 'none';
        }
    });


    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    setTimeout(() => {
        displayInitialSuggestions();
        showTypingIndicator(false);
    }, 100);
});

function autoResizeTextarea() {
    chatInput.style.height = 'auto';
    chatInput.style.height = chatInput.scrollHeight + 'px';
}