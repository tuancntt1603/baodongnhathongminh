/*
 * SafeHome AI Security System - Main Frontend Controller
 */

// DOM Elements Cache
const elements = {
    // Badges & Status
    connectionBadge: document.getElementById('connectionBadge'),
    connectionText: document.getElementById('connectionText'),
    cameraStatus: document.getElementById('cameraStatus'),
    guardPulse: document.getElementById('guardPulse'),
    
    // Security Guard Card
    securityCard: document.getElementById('securityStateCard'),
    mainStatusIcon: document.getElementById('mainStatusIcon'),
    securityTitle: document.getElementById('securityStatusTitle'),
    securityDesc: document.getElementById('securityStatusDesc'),
    armBtn: document.getElementById('armBtn'),
    disarmBtn: document.getElementById('disarmBtn'),
    
    // Sensors
    sensorPir: document.getElementById('sensorPir'),
    badgePir: document.getElementById('badgePir'),
    sensorDoor: document.getElementById('sensorDoor'),
    badgeDoor: document.getElementById('badgeDoor'),
    
    // Webcam
    liveFeed: document.getElementById('liveFeed'),
    cameraFallback: document.getElementById('cameraFallback'),
    captureTestBtn: document.getElementById('captureTestBtn'),
    toggleCameraBtn: document.getElementById('toggleCameraBtn'),
    
    // Simulator
    simulatorPanel: document.getElementById('simulatorPanel'),
    simPirBtn: document.getElementById('simPirBtn'),
    simDoorBtn: document.getElementById('simDoorBtn'),
    
    // Logs & History
    logsList: document.getElementById('logsList'),
    clearHistoryBtn: document.getElementById('clearHistoryBtn'),
    
    // Settings Modal
    settingsModal: document.getElementById('settingsModal'),
    openSettingsBtn: document.getElementById('openSettingsBtn'),
    closeSettingsBtn: document.getElementById('closeSettingsBtn'),
    settingsForm: document.getElementById('settingsForm'),
    testTelegramBtn: document.getElementById('testTelegramBtn'),
    
    // Lightbox
    imageLightbox: document.getElementById('imageLightbox'),
    lightboxImg: document.getElementById('lightboxImg'),
    lightboxCaption: document.getElementById('lightboxCaption'),
    closeLightboxBtn: document.getElementById('closeLightboxBtn'),
    
    // Toast
    toast: document.getElementById('toast')
};

// Application State Variables
let currentSystemState = {
    is_armed: false,
    pir_detected: false,
    door_open: false,
    alarm_triggered: false,
    connection_status: 'Connecting',
    actual_port: 'None',
    webcam_status: 'Inactive'
};

let simState = {
    pir: false,
    door: false
};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    // Load config settings into form
    fetchSettings();
    
    // Load event logs
    fetchHistory();
    
    // Start polling loop
    startPolling();
    
    // Attach Event Listeners
    setupEventListeners();
});

// Setup DOM Event Listeners
function setupEventListeners() {
    // Security controls
    elements.armBtn.addEventListener('click', armSystem);
    elements.disarmBtn.addEventListener('click', disarmSystem);
    
    // Settings Modal
    elements.openSettingsBtn.addEventListener('click', openSettings);
    elements.closeSettingsBtn.addEventListener('click', closeSettings);
    elements.settingsForm.addEventListener('submit', saveSettings);
    elements.testTelegramBtn.addEventListener('click', testTelegram);
    
    // Close modal on click outside content
    elements.settingsModal.addEventListener('click', (e) => {
        if (e.target === elements.settingsModal) closeSettings();
    });
    
    // Clear history
    elements.clearHistoryBtn.addEventListener('click', clearHistory);
    
    // Lightbox Modal
    elements.closeLightboxBtn.addEventListener('click', closeLightbox);
    elements.imageLightbox.addEventListener('click', (e) => {
        if (e.target === elements.imageLightbox) closeLightbox();
    });
    
    // Webcam Capture Test & Toggle
    elements.captureTestBtn.addEventListener('click', captureTest);
    if (elements.toggleCameraBtn) {
        elements.toggleCameraBtn.addEventListener('click', toggleCamera);
    }
    
    // Sensor Simulators (Toggles)
    elements.simPirBtn.addEventListener('click', () => toggleSimSensor('PIR'));
    elements.simDoorBtn.addEventListener('click', () => toggleSimSensor('DOOR'));
}

// ----------------- TOAST UTILITY -----------------
function showToast(message, type = 'info') {
    elements.toast.textContent = message;
    elements.toast.className = 'toast'; // reset classes
    
    if (type === 'success') {
        elements.toast.classList.add('toast-success');
    } else if (type === 'error') {
        elements.toast.classList.add('toast-error');
    }
    
    elements.toast.classList.remove('hidden');
    
    // Auto hide
    if (window.toastTimeout) clearTimeout(window.toastTimeout);
    window.toastTimeout = setTimeout(() => {
        elements.toast.classList.add('hidden');
    }, 3000);
}

// ----------------- STATE POLLING LOOP -----------------
function startPolling() {
    // Poll system state every 1 second
    setInterval(pollSystemState, 1000);
    // Poll history every 3 seconds
    setInterval(fetchHistory, 3000);
}

async function pollSystemState() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) throw new Error("HTTP error " + response.status);
        const data = await response.json();
        
        updateUIState(data);
    } catch (error) {
        console.error("Failed to poll status:", error);
        elements.connectionBadge.className = 'status-badge disconnected';
        elements.connectionText.textContent = 'Mất kết nối server';
    }
}

// ----------------- UI SYNC UPDATE -----------------
function updateUIState(state) {
    const stateChanged = JSON.stringify(state) !== JSON.stringify(currentSystemState);
    currentSystemState = state;
    
    // 1. Connection Badge Status
    const connStatus = state.connection_status.toLowerCase();
    elements.connectionBadge.className = `status-badge ${connStatus}`;
    
    if (connStatus === 'connected') {
        elements.connectionText.textContent = `Thiết bị: ${state.actual_port}`;
    } else if (connStatus === 'connecting') {
        elements.connectionText.textContent = `Đang kết nối: ${state.actual_port}`;
    } else {
        elements.connectionText.textContent = 'Chế độ giả lập';
    }
    
    // 2. Show/Hide Simulator Panel
    if (state.settings.use_simulator) {
        elements.simulatorPanel.classList.remove('hidden');
    } else {
        elements.simulatorPanel.classList.add('hidden');
    }
    
    // 3. Sensor Badges & Items Styles
    // PIR sensor
    if (state.pir_detected) {
        elements.sensorPir.className = 'sensor-item state-triggered';
        elements.badgePir.textContent = 'Phát hiện chuyển động';
        elements.simPirBtn.classList.add('active');
    } else {
        elements.sensorPir.className = 'sensor-item state-normal';
        elements.badgePir.textContent = 'Bình thường';
        elements.simPirBtn.classList.remove('active');
    }
    
    // Door sensor
    if (state.door_open) {
        elements.sensorDoor.className = 'sensor-item state-triggered';
        elements.badgeDoor.textContent = 'Mở cửa!';
        elements.simDoorBtn.classList.add('active');
    } else {
        elements.sensorDoor.className = 'sensor-item state-normal';
        elements.badgeDoor.textContent = 'Đang Đóng';
        elements.simDoorBtn.classList.remove('active');
    }
    
    // 4. Main Guard/Armed status card
    elements.securityCard.className = 'glass-card security-card'; // reset
    
    if (state.alarm_triggered) {
        // Red alert state
        startSiren();
        elements.securityCard.classList.add('triggered');
        elements.securityTitle.textContent = '🚨 ĐỘT NHẬP CẢNH BÁO! 🚨';
        elements.securityDesc.textContent = 'Hệ thống đang hú còi và bật đèn cảnh báo. Đã gửi thông báo tới điện thoại!';
        
        elements.mainStatusIcon.innerHTML = `
            <svg class="icon-danger animate-pulse" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
        `;
        
        elements.armBtn.classList.add('hidden');
        elements.disarmBtn.classList.remove('hidden');
        elements.disarmBtn.textContent = 'TẮT BÁO ĐỘNG & VÔ HIỆU HÓA';
        
    } else {
        stopSiren();
        if (state.is_armed) {
            // Armed blue guarding state
            elements.securityCard.classList.add('armed');
            elements.securityTitle.textContent = '🛡️ CHẾ ĐỘ BẢO VỆ HOẠT ĐỘNG';
            elements.securityDesc.textContent = 'Hệ thống đang giám sát. Xâm nhập sẽ ngay lập tức kích hoạt còi và camera chụp hình.';
            
            elements.mainStatusIcon.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
            `;
            
            elements.armBtn.classList.add('hidden');
            elements.disarmBtn.classList.remove('hidden');
            elements.disarmBtn.textContent = 'VÔ HIỆU HÓA BẢO VỆ';
            
        } else {
            // Disarmed green state
            elements.securityTitle.textContent = 'HỆ THỐNG VÔ HIỆU HÓA';
            elements.securityDesc.textContent = 'Chế độ bảo vệ đang tắt. Các cảm biến không kích hoạt hú còi và chụp hình camera.';
            
            elements.mainStatusIcon.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0 1 9.9-1"/>
                </svg>
            `;
            
            elements.armBtn.classList.remove('hidden');
            elements.disarmBtn.classList.add('hidden');
        }
    }
    
    // 5. Webcam Status Display & Button state
    const isCamEnabled = state.settings.camera_enabled ?? true;
    
    // Update button text and icon
    if (elements.toggleCameraBtn) {
        const btnText = elements.toggleCameraBtn.querySelector('span');
        const btnIcon = elements.toggleCameraBtn.querySelector('svg');
        if (isCamEnabled) {
            btnText.textContent = "Tắt Camera";
            btnIcon.innerHTML = `
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
            `;
            elements.captureTestBtn.classList.remove('hidden');
        } else {
            btnText.textContent = "Bật Camera";
            btnIcon.innerHTML = `
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
            `;
            elements.captureTestBtn.classList.add('hidden');
        }
    }

    if (isCamEnabled && state.webcam_status === 'Active') {
        elements.liveFeed.classList.remove('hidden');
        elements.cameraFallback.classList.add('hidden');
        elements.cameraStatus.textContent = 'LIVE';
        elements.cameraStatus.className = 'status-indicator-live';
    } else {
        elements.liveFeed.classList.add('hidden');
        elements.cameraFallback.classList.remove('hidden');
        
        const fallbackText = elements.cameraFallback.querySelector('p');
        const fallbackSpan = elements.cameraFallback.querySelector('span');
        
        if (!isCamEnabled) {
            fallbackText.textContent = "Camera đang tắt";
            fallbackSpan.textContent = "Chế độ riêng tư được kích hoạt";
            elements.cameraStatus.textContent = 'RIÊNG TƯ';
            elements.cameraStatus.className = 'status-indicator-live warning';
        } else {
            fallbackText.textContent = "Không có tín hiệu Camera";
            fallbackSpan.textContent = "Kiểm tra webcam_id trong cài đặt";
            elements.cameraStatus.textContent = 'OFFLINE';
            elements.cameraStatus.className = 'status-indicator-live offline';
        }
    }
    
    // Refresh history if state changed to ensure logs sync immediately
    if (stateChanged) {
        fetchHistory();
    }
}

// ----------------- SECURITY ACTIONS -----------------
async function armSystem() {
    try {
        const r = await fetch('/api/arm', { method: 'POST' });
        const res = await r.json();
        if (res.success) {
            showToast('Đã kích hoạt chế độ an ninh!', 'success');
            pollSystemState();
        }
    } catch (e) {
        showToast('Lỗi kích hoạt bảo vệ', 'error');
    }
}

async function disarmSystem() {
    try {
        const r = await fetch('/api/disarm', { method: 'POST' });
        const res = await r.json();
        if (res.success) {
            showToast('Đã tắt chế độ an ninh / Tắt còi báo động', 'success');
            // reset simulator variables locally
            simState.pir = false;
            simState.door = false;
            pollSystemState();
        }
    } catch (e) {
        showToast('Lỗi tắt chế độ an ninh', 'error');
    }
}

// ----------------- SENSOR SIMULATOR -----------------
async function toggleSimSensor(sensor) {
    if (!currentSystemState.settings.use_simulator) {
        showToast('Chỉ hoạt động ở Chế độ giả lập', 'error');
        return;
    }
    
    if (sensor === 'PIR') {
        simState.pir = !simState.pir;
        await postSimState('PIR', simState.pir);
    } else if (sensor === 'DOOR') {
        simState.door = !simState.door;
        await postSimState('DOOR', simState.door);
    }
}

async function postSimState(sensor, state) {
    try {
        const r = await fetch('/api/simulate_trigger', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sensor, state })
        });
        const res = await r.json();
        if (res.success) {
            pollSystemState();
        }
    } catch (e) {
        console.error("Failed to post simulation state:", e);
    }
}

// ----------------- EVENT LOGS & IMAGES -----------------
async function fetchHistory() {
    try {
        const response = await fetch('/api/history');
        if (!response.ok) return;
        const logs = await response.json();
        
        renderHistory(logs);
    } catch (e) {
        console.error("Failed to fetch logs history:", e);
    }
}

function renderHistory(logs) {
    if (!logs || logs.length === 0) {
        elements.logsList.innerHTML = '<div class="log-empty">Chưa ghi nhận sự kiện nào.</div>';
        return;
    }
    
    let html = '';
    logs.forEach(log => {
        let typeClass = 'log-system';
        if (log.sensor === 'PIR') typeClass = 'log-pir';
        if (log.sensor === 'DOOR') typeClass = 'log-door';
        
        let actionHtml = '';
        if (log.image_path) {
            actionHtml = `
                <div class="log-action">
                    <div class="thumbnail-wrapper" onclick="openLightbox('${log.image_path}', '${log.event} - ${log.timestamp}')" title="Xem ảnh xâm nhập">
                        <img src="${log.image_path}" alt="Thumb">
                    </div>
                </div>
            `;
        }
        
        html += `
            <div class="log-row ${typeClass}">
                <div class="log-content">
                    <span class="log-indicator"></span>
                    <div>
                        <div class="log-message">${log.event}</div>
                        <div class="log-time">${log.timestamp}</div>
                    </div>
                </div>
                ${actionHtml}
            </div>
        `;
    });
    
    elements.logsList.innerHTML = html;
}

async function clearHistory() {
    if (!confirm("Bạn có chắc chắn muốn xóa toàn bộ nhật ký báo động?")) return;
    
    try {
        const r = await fetch('/api/history/clear', { method: 'POST' });
        const res = await r.json();
        if (res.success) {
            showToast('Đã xóa lịch sử nhật ký', 'success');
            fetchHistory();
        }
    } catch (e) {
        showToast('Lỗi xóa lịch sử', 'error');
    }
}

// ----------------- WEBCAM SNAPSHOT TEST -----------------
async function captureTest() {
    showToast('Đang chụp thử ảnh...');
    elements.liveFeed.src = "/api/video_feed?t=" + new Date().getTime(); // Refresh feed
    // Wait brief moment and show done
    setTimeout(() => {
        showToast('Hoàn tất. Có thể xem ở live stream hoặc chụp thử!', 'success');
    }, 1000);
}

async function toggleCamera() {
    try {
        const r = await fetch('/api/webcam/toggle', { method: 'POST' });
        const res = await r.json();
        if (res.success) {
            showToast(res.message, 'success');
            pollSystemState();
        }
    } catch (e) {
        showToast('Lỗi thay đổi trạng thái camera', 'error');
    }
}

function handleCameraError() {
    elements.liveFeed.classList.add('hidden');
    elements.cameraFallback.classList.remove('hidden');
    elements.cameraStatus.textContent = 'OFFLINE';
    elements.cameraStatus.className = 'status-indicator-live offline';
}

// ----------------- SETTINGS MANAGEMENT -----------------
async function fetchSettings() {
    try {
        const r = await fetch('/api/settings');
        const config = await r.json();
        
        document.getElementById('comPort').value = config.com_port || 'AUTO';
        document.getElementById('webcamId').value = config.webcam_id ?? 0;
        document.getElementById('useSimulator').checked = config.use_simulator ?? true;
        document.getElementById('telegramChatId').value = config.telegram_chat_id || '';
        
        // Handle token placeholder
        if (config.telegram_token) {
            document.getElementById('telegramToken').value = config.telegram_token;
        } else {
            document.getElementById('telegramToken').value = '';
        }
    } catch (e) {
        console.error("Failed to load settings:", e);
    }
}

function openSettings() {
    fetchSettings();
    elements.settingsModal.classList.remove('hidden');
}

function closeSettings() {
    elements.settingsModal.classList.add('hidden');
}

async function saveSettings(e) {
    e.preventDefault();
    
    const tokenInput = document.getElementById('telegramToken').value.trim();
    
    const data = {
        com_port: document.getElementById('comPort').value.trim(),
        webcam_id: parseInt(document.getElementById('webcamId').value),
        use_simulator: document.getElementById('useSimulator').checked,
        telegram_token: tokenInput,
        telegram_chat_id: document.getElementById('telegramChatId').value.trim()
    };
    
    try {
        const r = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const res = await r.json();
        if (res.success) {
            showToast('Đã lưu cấu hình cài đặt!', 'success');
            closeSettings();
            pollSystemState();
        }
    } catch (error) {
        showToast('Lỗi lưu cài đặt', 'error');
    }
}

async function testTelegram() {
    const tokenInput = document.getElementById('telegramToken').value.trim();
    const chatIdInput = document.getElementById('telegramChatId').value.trim();
    
    if (!tokenInput || !chatIdInput) {
        showToast('Vui lòng điền đủ Token và Chat ID trước khi test!', 'error');
        return;
    }
    
    showToast('Đang gửi thử tin nhắn Telegram...');
    
    // First save settings so the test route uses the correct values
    const data = {
        com_port: document.getElementById('comPort').value.trim(),
        webcam_id: parseInt(document.getElementById('webcamId').value),
        use_simulator: document.getElementById('useSimulator').checked,
        telegram_token: tokenInput,
        telegram_chat_id: chatIdInput
    };
    
    try {
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        // Execute test
        const r = await fetch('/api/test_telegram', { method: 'POST' });
        const res = await r.json();
        
        if (res.success) {
            showToast('Đã gửi tin nhắn test! Kiểm tra điện thoại của bạn.', 'success');
        } else {
            showToast('Lỗi gửi Telegram: ' + res.message, 'error');
        }
    } catch (e) {
        showToast('Gặp sự cố gửi thử Telegram', 'error');
    }
}

// ----------------- LIGHTBOX MODAL -----------------
function openLightbox(imagePath, captionText) {
    elements.lightboxImg.src = imagePath;
    elements.lightboxCaption.textContent = captionText;
    elements.imageLightbox.classList.remove('hidden');
}

function closeLightbox() {
    elements.imageLightbox.classList.add('hidden');
    elements.lightboxImg.src = '';
}

// ----------------- WEB AUDIO SIREN GENERATOR -----------------
let audioCtx = null;
let sirenInterval = null;

function startSiren() {
    if (sirenInterval) return;
    
    try {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        
        let osc = audioCtx.createOscillator();
        let gain = audioCtx.createGain();
        
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(800, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.2, audioCtx.currentTime); // 20% volume
        
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        
        let time = 0;
        sirenInterval = setInterval(() => {
            time += 0.15;
            let freq = 800 + Math.sin(time * Math.PI) * 200;
            osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
        }, 150);
        
        window.currentSiren = { osc, gain };
    } catch (e) {
        console.error("Audio API error:", e);
    }
}

function stopSiren() {
    if (sirenInterval) {
        clearInterval(sirenInterval);
        sirenInterval = null;
    }
    if (window.currentSiren) {
        try {
            window.currentSiren.osc.stop();
            window.currentSiren.osc.disconnect();
            window.currentSiren.gain.disconnect();
        } catch (e) {}
        window.currentSiren = null;
    }
}
