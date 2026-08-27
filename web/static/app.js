// ============================================
// J.A.R.V.I.S. - Hologram Interface
// Three.js 3D Sphere + Web Speech API + Socket.IO
// ============================================

const socket = io();
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const chatOverlay = document.getElementById('chat-overlay');
const micBtn = document.getElementById('mic-btn');
const micStatus = document.getElementById('mic-status');
const clockEl = document.getElementById('clock');
const dateEl = document.getElementById('date');

let ttsEnabled = true;
let recognition = null;
let isListening = false;
let micPermissionGranted = false;
let scene, camera, renderer, sphere, rings = [], particles;
let mouseX = 0, mouseY = 0;
let hologramState = 0;
let selectedVoice = null;
let voicesLoaded = false;

// ============================================
// INIT
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('init-time').textContent = getTimeStamp();
    initThreeJS();
    initTTS();
    initSpeechRecognition();
    updateClock();
    setInterval(updateClock, 1000);
    setupEventListeners();
    animate();
});

// ============================================
// THREE.JS - Hologram Sphere
// ============================================
function initThreeJS() {
    const canvas = document.getElementById('hologram-canvas');
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 5;

    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x030810, 1);

    const innerGeo = new THREE.SphereGeometry(1.2, 32, 32);
    const innerMat = new THREE.MeshBasicMaterial({ color: 0x00d4ff, transparent: true, opacity: 0.05 });
    sphere = new THREE.Mesh(innerGeo, innerMat);
    scene.add(sphere);

    const wireGeo = new THREE.SphereGeometry(1.5, 24, 18);
    const wireMat = new THREE.MeshBasicMaterial({ color: 0x00d4ff, wireframe: true, transparent: true, opacity: 0.15 });
    const wireSphere = new THREE.Mesh(wireGeo, wireMat);
    scene.add(wireSphere);
    rings.push(wireSphere);

    for (let i = 0; i < 3; i++) {
        const ringGeo = new THREE.RingGeometry(1.6 + i * 0.15, 1.62 + i * 0.15, 64);
        const ringMat = new THREE.MeshBasicMaterial({ color: 0x00d4ff, side: THREE.DoubleSide, transparent: true, opacity: 0.2 - i * 0.05 });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.rotation.x = Math.PI / 2 + (i - 1) * 0.3;
        ring.rotation.z = i * 0.5;
        scene.add(ring);
        rings.push(ring);
    }

    const coreGeo = new THREE.SphereGeometry(0.3, 16, 16);
    const coreMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.6 });
    scene.add(new THREE.Mesh(coreGeo, coreMat));

    const particleCount = 500;
    const particleGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
        const radius = 1.8 + Math.random() * 2;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
        positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        positions[i * 3 + 2] = radius * Math.cos(phi);
        colors[i * 3] = 0;
        colors[i * 3 + 1] = 0.83 + Math.random() * 0.17;
        colors[i * 3 + 2] = 1;
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    particles = new THREE.Points(particleGeo, new THREE.PointsMaterial({ size: 0.015, vertexColors: true, transparent: true, opacity: 0.6 }));
    scene.add(particles);

    for (let i = 0; i < 2; i++) {
        const dataRingGeo = new THREE.TorusGeometry(2 + i * 0.5, 0.005, 8, 100);
        const dataRingMat = new THREE.MeshBasicMaterial({ color: i === 0 ? 0x00d4ff : 0x0088ff, transparent: true, opacity: 0.12 });
        const dataRing = new THREE.Mesh(dataRingGeo, dataRingMat);
        dataRing.rotation.x = Math.PI / 3 + i * 0.8;
        dataRing.rotation.y = i * 1.2;
        scene.add(dataRing);
        rings.push(dataRing);
    }

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
    document.addEventListener('mousemove', (e) => {
        mouseX = (e.clientX / window.innerWidth) * 2 - 1;
        mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
    });
}

function animate() {
    requestAnimationFrame(animate);
    const t = Date.now() * 0.001;

    sphere.rotation.y = t * 0.2;
    sphere.rotation.x = Math.sin(t * 0.3) * 0.1;

    if (rings[0]) {
        rings[0].rotation.y = t * 0.15 + mouseX * 0.3;
        rings[0].rotation.x = t * 0.1 + mouseY * 0.3;
    }
    for (let i = 1; i < 4; i++) {
        if (rings[i]) rings[i].rotation.z += 0.002 * (i % 2 === 0 ? 1 : -1);
    }
    for (let i = 4; i < rings.length; i++) {
        if (rings[i]) rings[i].rotation.z += 0.003;
    }
    particles.rotation.y = t * 0.05;
    particles.rotation.x = t * 0.03;

    updateHologramState(t);
    renderer.render(scene, camera);
}

function updateHologramState(t) {
    const m = sphere.material;
    switch (hologramState) {
        case 0: m.color.setHex(0x00d4ff); m.opacity = 0.05 + Math.sin(t * 2) * 0.02; break;
        case 1: m.color.setHex(0x0088ff); m.opacity = 0.1 + Math.sin(t * 8) * 0.05; sphere.rotation.y += 0.05; break;
        case 2: m.color.setHex(0x00ff88); m.opacity = 0.15; setTimeout(() => { hologramState = 0; }, 2000); break;
        case 3: m.color.setHex(0xff3333); m.opacity = 0.1 + Math.sin(t * 10) * 0.05; setTimeout(() => { hologramState = 0; }, 2000); break;
    }
}

function setHologramState(state) { hologramState = state; }

// ============================================
// CLOCK
// ============================================
function updateClock() {
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString('de-DE', { hour12: false });
    dateEl.textContent = now.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
}
function getTimeStamp() { return new Date().toLocaleTimeString('de-DE', { hour12: false }); }

// ============================================
// Text-to-Speech - FIXED: Cache male voice
// ============================================
function initTTS() {
    if (!window.speechSynthesis) { console.warn('TTS nicht verfuegbar.'); return; }

    function pickVoice() {
        if (voicesLoaded) return;
        const voices = window.speechSynthesis.getVoices();
        if (voices.length === 0) return;

        // Male German voice preference list (Windows, Mac, Linux)
        const maleNames = [
            'Microsoft Hans', 'Microsoft Conrad', 'Microsoft David',
            'Google Deutsch', 'Google Deutsch (German (Germany))',
            'Stefan', 'Hans', 'Klaus', 'Peter', 'Thomas',
            'Markus', 'Steffen', 'Yannick',
            'de-DE-Hans', 'de-DE-Conrad',
        ];

        // 1. Try exact male name match
        for (const name of maleNames) {
            const found = voices.find(v => v.name === name);
            if (found) { selectedVoice = found; voicesLoaded = true; console.log('TTS maennliche Stimme:', found.name); return; }
        }

        // 2. Try partial male name match
        for (const name of maleNames) {
            const found = voices.find(v => v.name.includes(name));
            if (found) { selectedVoice = found; voicesLoaded = true; console.log('TTS Stimme (partiell):', found.name); return; }
        }

        // 3. Any German voice - check if male by name heuristics
        const germanVoices = voices.filter(v => v.lang.startsWith('de'));
        const femaleHints = ['female', 'fem', 'woman', 'katja', 'anna', 'petra', 'sandra', 'sabine', 'monika', 'helena'];
        for (const v of germanVoices) {
            const lowerName = v.name.toLowerCase();
            const isFemale = femaleHints.some(h => lowerName.includes(h));
            if (!isFemale) { selectedVoice = v; voicesLoaded = true; console.log('TTS Stimme (fallback):', v.name); return; }
        }

        // 4. Just use first German voice
        if (germanVoices.length > 0) {
            selectedVoice = germanVoices[0];
            voicesLoaded = true;
            console.log('TTS Stimme (erste deutsche):', selectedVoice.name);
        }
    }

    // Voices load async - try now and also on event
    pickVoice();
    window.speechSynthesis.onvoiceschanged = () => pickVoice();

    // Retry after short delay in case voices weren't ready
    setTimeout(pickVoice, 500);
    setTimeout(pickVoice, 1500);
}

function speak(text) {
    if (!ttsEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'de-DE';
    utterance.rate = 1.0;
    utterance.pitch = 0.8;

    if (selectedVoice) {
        utterance.voice = selectedVoice;
    } else {
        // Emergency fallback - find ANY German voice right now
        const voices = window.speechSynthesis.getVoices();
        const german = voices.find(v => v.lang.startsWith('de'));
        if (german) {
            utterance.voice = german;
            selectedVoice = german;
        }
    }

    window.speechSynthesis.speak(utterance);
}

// ============================================
// Web Speech API - STT - FIXED: Permission handling
// ============================================
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        micStatus.textContent = 'NICHT VERFUEGBAR';
        micStatus.style.color = '#ff3333';
        micBtn.style.opacity = '0.4';
        micBtn.style.cursor = 'not-allowed';
        console.warn('Web Speech API nicht verfuegbar. Chrome oder Edge noetig.');
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = 'de-DE';
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
        isListening = true;
        micPermissionGranted = true;
        micBtn.classList.add('listening');
        micStatus.textContent = 'HOERE ZU...';
        micStatus.style.color = '#ff3333';
        setHologramState(1);
    };

    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }

        if (interimTranscript) {
            micStatus.textContent = interimTranscript.substring(0, 30);
            micStatus.style.color = '#ffd700';
        }

        if (finalTranscript) {
            chatInput.value = finalTranscript;
            micStatus.textContent = 'VERSTANDEN!';
            micStatus.style.color = '#00ff88';
            setTimeout(() => {
                sendMessage();
                micStatus.textContent = 'Bereit';
                micStatus.style.color = '';
            }, 300);
        }
    };

    recognition.onerror = (event) => {
        console.error('STT Fehler:', event.error);
        isListening = false;
        micBtn.classList.remove('listening');
        setHologramState(3);

        const errorMessages = {
            'no-speech': 'Keine Stimme erkannt - nochmal versuchen',
            'audio-capture': 'Kein Mikrofon gefunden',
            'not-allowed': 'Mikrofon-Zugriff verweigert - Bitte im Browser erlauben',
            'network': 'Netzwerkfehler - Online noetig',
            'aborted': 'Abgebrochen',
            'service-not-allowed': 'Sprachdienst nicht erlaubt',
        };
        micStatus.textContent = errorMessages[event.error] || `Fehler: ${event.error}`;
        micStatus.style.color = '#ff3333';
        setTimeout(() => {
            micStatus.textContent = 'Bereit';
            micStatus.style.color = '';
        }, 4000);
    };

    recognition.onend = () => {
        isListening = false;
        micBtn.classList.remove('listening');
        if (micStatus.textContent.includes('HOERE')) {
            micStatus.textContent = 'Bereit';
            micStatus.style.color = '';
        }
    };

    micBtn.addEventListener('click', toggleSTT);
}

async function toggleSTT() {
    if (!recognition) {
        addSystemMessage('Spracherkennung nicht verfuegbar. Bitte Chrome oder Edge verwenden.');
        return;
    }

    if (isListening) {
        recognition.stop();
        return;
    }

    // Request microphone permission explicitly first
    if (!micPermissionGranted) {
        try {
            micStatus.textContent = 'Mikrofon anfordern...';
            micStatus.style.color = '#ffd700';
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(t => t.stop());
            micPermissionGranted = true;
            console.log('Mikrofon-Berechtigung erteilt.');
        } catch (e) {
            console.error('Mikrofon-Berechtigung verweigert:', e);
            micStatus.textContent = 'Mikrofon verweigert!';
            micStatus.style.color = '#ff3333';
            addSystemMessage('Mikrofon-Zugriff verweigert. Bitte in den Browser-Einstellungen erlauben.');
            setHologramState(3);
            return;
        }
    }

    try {
        recognition.start();
    } catch (e) {
        console.error('STT Start Fehler:', e);
        if (e.message && e.message.includes('already started')) {
            recognition.stop();
            setTimeout(() => { try { recognition.start(); } catch(e2) {} }, 200);
        } else {
            micStatus.textContent = 'Fehler beim Starten';
            micStatus.style.color = '#ff3333';
        }
    }
}

// ============================================
// SOCKET EVENTS
// ============================================
socket.on('connect', () => {
    console.log('HUD connected to JARVIS');
    addSystemMessage('Verbindung zum J.A.R.V.I.S. Kern hergestellt.');
});

socket.on('disconnect', () => addSystemMessage('Verbindung unterbrochen...'));
socket.on('connected', (data) => addSystemMessage(data.message));
socket.on('user_message', (data) => addUserMessage(data.text, data.timestamp));

socket.on('jarvis_response', (data) => {
    addJarvisMessage(data.text, data.timestamp);
    speak(data.text);
    setHologramState(2);
    if (data.is_farewell) {
        setTimeout(() => addSystemMessage('J.A.R.V.I.S. wurde beendet.'), 1000);
    }
});

socket.on('system_stats', () => {});

socket.on('reminder', (data) => {
    addSystemMessage(`Erinnerung: ${data.text}`);
    speak(`Erinnerung: ${data.text}`);
});

// CAMERA EVENTS
socket.on('camera_feed', (data) => {
    console.log('Kamera erhalten:', data);
    showCameraFeed(data);
});

socket.on('camera_error', (data) => {
    addSystemMessage(`Kamera-Fehler: ${data.message}`);
});

socket.on('camera_results', (data) => {
    if (data.cameras && data.cameras.length > 0) {
        const names = data.cameras.map(c => `${c.name} (${c.city})`).join(', ');
        addJarvisMessage(`Gefundene Kameras: ${names}. Sende "zeig kamera [name]" um eine zu oeffnen.`);
    } else {
        addJarvisMessage('Keine passenden Kameras gefunden.');
    }
});

// ============================================
// MESSAGES
// ============================================
function addUserMessage(text, time) { addMessage('user-msg', 'DU', text, time); }
function addJarvisMessage(text, time) { addMessage('jarvis-msg', 'J.A.R.V.I.S.', text, time); }
function addSystemMessage(text) { addMessage('system-msg', 'SYSTEM', text, getTimeStamp()); }

function addMessage(type, sender, text, time) {
    const div = document.createElement('div');
    div.className = `chat-message ${type}`;
    div.innerHTML = `<span class="msg-sender">${sender}</span><span class="msg-text">${escapeHtml(text)}</span><span class="msg-time">${time || getTimeStamp()}</span>`;
    chatOverlay.appendChild(div);
    chatOverlay.scrollTop = chatOverlay.scrollHeight;
    while (chatOverlay.children.length > 20) chatOverlay.removeChild(chatOverlay.firstChild);
}

function escapeHtml(text) { const d = document.createElement('div'); d.textContent = text; return d.innerHTML; }

// ============================================
// CAMERA FEED
// ============================================
function showCameraFeed(data) {
    const overlay = document.getElementById('camera-overlay');
    const frame = document.querySelector('.camera-frame');
    const title = document.getElementById('camera-title');
    const info = document.getElementById('camera-info');

    // Clear previous content
    frame.innerHTML = '';

    if (data.type === 'image') {
        // Direct image feed (foto-webcam.eu, USGS, etc.)
        const img = document.createElement('img');
        img.src = data.url;
        img.style.width = '100%';
        img.style.height = '100%';
        img.style.objectFit = 'contain';
        img.style.background = '#000';
        img.alt = data.name;
        img.onerror = () => {
            img.src = data.thumbnail || data.url;
            img.alt = 'Bild konnte nicht geladen werden';
        };
        frame.appendChild(img);

        // Auto-refresh every 60 seconds
        img._refreshInterval = setInterval(() => {
            img.src = data.url + '?t=' + Date.now();
        }, 60000);
    } else {
        // YouTube iframe embed
        const iframe = document.createElement('iframe');
        iframe.src = data.url;
        iframe.allow = 'autoplay; encrypted-media';
        iframe.allowFullscreen = true;
        frame.appendChild(iframe);
    }

    title.textContent = data.type === 'image' ? `LIVE: ${data.name}` : `LIVE: ${data.name}`;
    info.textContent = `${data.city}${data.country ? ', ' + data.country : ''} | ${data.type === 'image' ? 'Bild-Feed' : 'Video-Stream'}`;
    overlay.style.display = 'block';
}

document.getElementById('camera-close').addEventListener('click', () => {
    const frame = document.querySelector('.camera-frame');
    // Clear any refresh intervals
    const img = frame.querySelector('img');
    if (img && img._refreshInterval) clearInterval(img._refreshInterval);
    frame.innerHTML = '';
    document.getElementById('camera-overlay').style.display = 'none';
});

// ============================================
// SEND MESSAGE
// ============================================
function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    setHologramState(1);
    socket.emit('user_message', { message: text });
    chatInput.value = '';
}

sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });

// ============================================
// EVENT LISTENERS
// ============================================
function setupEventListeners() {
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            chatInput.value = btn.dataset.action;
            sendMessage();
        });
    });

    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'm') { e.preventDefault(); toggleSTT(); }
        if (e.ctrlKey && e.key === '/') { e.preventDefault(); chatInput.focus(); }
        if (e.key === 'Escape') {
            chatInput.value = '';
            chatInput.blur();
            if (isListening && recognition) recognition.stop();
            document.getElementById('camera-iframe').src = '';
            document.getElementById('camera-overlay').style.display = 'none';
        }
    });
}

console.log('%c J.A.R.V.I.S. Hologram Interface ', 'background: #00d4ff; color: #030810; font-size: 14px; font-weight: bold; padding: 4px 8px; border-radius: 3px;');
