import os
import time
import json
import threading
import cv2
import requests
from flask import Flask, render_template, jsonify, request, Response, send_from_directory

app = Flask(__name__)

# Constants
SETTINGS_FILE = "settings.json"
HISTORY_FILE = "history.json"
CAPTURES_DIR = os.path.join("static", "captures")

# Ensure directories exist
os.makedirs(CAPTURES_DIR, exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Global variables for system state
system_state = {
    "is_armed": False,
    "pir_detected": False,
    "door_open": False,
    "alarm_triggered": False,
    "connection_status": "Simulating",  # "Connected", "Connecting", "Simulating"
    "actual_port": "None"
}

# Settings with default values
default_settings = {
    "com_port": "AUTO",
    "telegram_token": "",
    "telegram_chat_id": "",
    "webcam_id": 0,
    "use_simulator": True,
    "camera_enabled": True
}

settings = {}

def load_settings():
    global settings
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception as e:
            print(f"Error loading settings.json: {e}")
            settings = default_settings.copy()
    else:
        settings = default_settings.copy()
        save_settings(settings)

def save_settings(new_settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(new_settings, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving settings.json: {e}")

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading history.json: {e}")
            return []
    return []

def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history.json: {e}")

def add_log(event, sensor, image_path=None):
    history = load_history()
    log_entry = {
        "id": int(time.time() * 1000),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": event,
        "sensor": sensor,
        "image_path": image_path
    }
    history.insert(0, log_entry)  # Add to top of list
    # Limit history to 100 entries
    save_history(history[:100])
    return log_entry

# Haar Cascade for Face Detection
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
except Exception as e:
    print(f"Error loading Haar Cascade: {e}")
    face_cascade = None

def detect_and_draw_faces(frame):
    if frame is None or face_cascade is None or face_cascade.empty():
        return False, frame
    
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(35, 35))
        
        faces_detected = len(faces) > 0
        if faces_detected:
            for (x, y, w, h) in faces:
                # Draw red box (BGR: 0, 0, 255)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 3)
                # Label box
                cv2.putText(frame, "INTRUDER", (x, y-12), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            print(f"AI Face Detection: Detected {len(faces)} face(s)!")
        return faces_detected, frame
    except Exception as e:
        print(f"Error in detect_and_draw_faces: {e}")
        return False, frame

# Webcam Manager Class
class WebcamManager:
    def __init__(self):
        self.cap = None
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        self.thread = None
        self.webcam_id = 0

    def start(self, webcam_id=0):
        self.webcam_id = webcam_id
        if self.running:
            self.stop()
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        print(f"Webcam Manager started for device {self.webcam_id}")
        self.cap = cv2.VideoCapture(self.webcam_id)
        while self.running:
            if not self.cap or not self.cap.isOpened():
                # Retry connection
                self.cap = cv2.VideoCapture(self.webcam_id)
                time.sleep(2)
                continue
            
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame.copy()
            else:
                time.sleep(0.03)
            time.sleep(0.01)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.frame = None
        print("Webcam Manager stopped.")

    def get_frame_jpeg(self):
        with self.lock:
            if self.frame is not None:
                # Add timestamp overlay to live feed
                feed_frame = self.frame.copy()
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(feed_frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                ret, jpeg = cv2.imencode('.jpg', feed_frame)
                if ret:
                    return jpeg.tobytes()
        return None

    def save_current_frame(self, filepath, run_face_detection=True):
        with self.lock:
            if self.frame is not None:
                frame_to_save = self.frame.copy()
                faces_detected = False
                if run_face_detection:
                    faces_detected, frame_to_save = detect_and_draw_faces(frame_to_save)
                # Write frame to file
                cv2.imwrite(filepath, frame_to_save)
                return True, faces_detected
        return False, False

# Serial Port Auto-Detection
import serial.tools.list_ports
def auto_detect_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        desc = p.description.lower()
        if "arduino" in desc or "ch340" in desc or "usb-serial" in desc or "silicon labs" in desc or "cp210" in desc:
            return p.device
    if ports:
        return ports[0].device
    return None

# Serial Manager Class
import serial
class SerialManager:
    def __init__(self, on_trigger_callback, on_status_callback):
        self.ser = None
        self.running = False
        self.thread = None
        self.port = "AUTO"
        self.on_trigger = on_trigger_callback
        self.on_status = on_status_callback

    def start(self, port="AUTO"):
        self.port = port
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except:
                pass
        if self.thread:
            self.thread.join(timeout=1.0)
        self.ser = None
        print("Serial Manager stopped.")

    def _run(self):
        global system_state
        while self.running:
            if settings.get("use_simulator", True):
                system_state["connection_status"] = "Simulating"
                system_state["actual_port"] = "None"
                time.sleep(1)
                continue

            target_port = self.port
            if target_port == "AUTO":
                target_port = auto_detect_port()

            if not target_port:
                system_state["connection_status"] = "Disconnected"
                system_state["actual_port"] = "None"
                time.sleep(2)
                continue

            try:
                system_state["connection_status"] = "Connecting"
                system_state["actual_port"] = target_port
                print(f"Connecting to Arduino on {target_port}...")
                self.ser = serial.Serial(target_port, 9600, timeout=1)
                time.sleep(2.0)  # Wait for Arduino reboot
                
                system_state["connection_status"] = "Connected"
                print(f"Connected to Arduino on {target_port}!")
                
                # Request initial status and sync arm state
                self.sync_arm_state()
                
                while self.running and self.ser.is_open:
                    if self.ser.in_waiting > 0:
                        line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            self._handle_message(line)
                    time.sleep(0.05)
            except Exception as e:
                print(f"Serial communication error on {target_port}: {e}")
                system_state["connection_status"] = "Disconnected"
                if self.ser:
                    try:
                        self.ser.close()
                    except:
                        pass
                    self.ser = None
                time.sleep(2)

    def write_command(self, cmd):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(f"{cmd}\n".encode('utf-8'))
                print(f"Laptop -> Arduino: {cmd}")
                return True
            except Exception as e:
                print(f"Error writing to serial: {e}")
        return False

    def sync_arm_state(self):
        cmd = "ARM" if system_state["is_armed"] else "DISARM"
        self.write_command(cmd)

    def _handle_message(self, line):
        if line.startswith("STATUS:"):
            # FORMAT: STATUS:ARMED=0,PIR=0,DOOR=0,ALARM=0
            try:
                parts = line[7:].split(',')
                status = {}
                for p in parts:
                    k, v = p.split('=')
                    status[k] = (v == '1')
                self.on_status(status)
            except Exception as e:
                print(f"Error parsing serial status: {e} | Line: {line}")
        elif line.startswith("TRIGGER:"):
            # FORMAT: TRIGGER:PIR or TRIGGER:DOOR
            sensor = line[8:]
            self.on_trigger(sensor)
        elif line.startswith("SYSTEM:READY"):
            print("Arduino reported: READY")
            self.sync_arm_state()

# Alert System Integration
def send_telegram_notification(sensor, photo_path=None, faces_detected=False):
    token = settings.get("telegram_token", "").strip()
    chat_id = settings.get("telegram_chat_id", "").strip()
    
    if not token or not chat_id:
        print("Telegram Alert: Token or Chat ID not configured. Skipping notification.")
        return False
        
    sensor_name = "Cảm biến chuyển động PIR" if sensor == "PIR" else "Cảm biến cửa từ"
    timestamp = time.strftime("%H:%M:%S %d/%m/%Y")
    
    ai_status = "⚠️ <b>Nhận diện AI:</b> PHÁT HIỆN KHUÔN MẶT KẺ XÂM NHẬP! 👤" if faces_detected else "ℹ️ <b>Nhận diện AI:</b> Không phát hiện khuôn mặt rõ ràng."
    
    msg_text = (
        f"🚨 <b>CẢNH BÁO BÁO ĐỘNG ĐỘT NHẬP</b> 🚨\n\n"
        f"⚠️ <b>Phát hiện:</b> Xâm nhập bất thường!\n"
        f"🔌 <b>Nguồn kích hoạt:</b> {sensor_name}\n"
        f"📅 <b>Thời gian:</b> {timestamp}\n"
        f"{ai_status}\n"
        f"🔒 <b>Hệ thống:</b> Đang Báo Động (Còi & Đèn sáng)\n\n"
        f"<i>Vui lòng kiểm tra camera và tình hình ngôi nhà của bạn ngay lập tức!</i>"
    )
    
    # 1. Send Text alert first
    send_url = f"https://api.telegram.org/bot{token}/sendMessage"
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🔕 Tắt Báo Động (Disarm)", "callback_data": "disarm"},
                {"text": "📸 Chụp Ảnh Mới", "callback_data": "capture"}
            ]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": msg_text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    }
    
    try:
        r = requests.post(send_url, json=payload, timeout=5)
        if r.status_code != 200:
            print(f"Telegram Text Error: {r.text}")
            return False
            
        # 2. Send image if available
        if photo_path and os.path.exists(photo_path):
            photo_url = f"https://api.telegram.org/bot{token}/sendPhoto"
            caption_text = f"📸 Ảnh chụp từ camera giám sát lúc {time.strftime('%H:%M:%S')}"
            if faces_detected:
                caption_text += " [👤 Phát hiện khuôn mặt!]"
            with open(photo_path, 'rb') as img_file:
                files = {'photo': img_file}
                photo_payload = {
                    "chat_id": chat_id,
                    "caption": caption_text
                }
                r_photo = requests.post(photo_url, data=photo_payload, files=files, timeout=10)
                if r_photo.status_code != 200:
                    print(f"Telegram Photo Error: {r_photo.text}")
        return True
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")
        return False

# Initialize managers
webcam_manager = WebcamManager()

def on_arduino_trigger(sensor):
    global system_state
    if not system_state["is_armed"]:
        return
        
    system_state["alarm_triggered"] = True
    print(f"INTRUSION TRIGGERED BY SENSOR: {sensor}")
    
    # Take photo
    photo_filename = f"intrusion_{int(time.time())}.jpg"
    photo_path = os.path.join(CAPTURES_DIR, photo_filename)
    relative_path = f"/static/captures/{photo_filename}"
    
    success = False
    faces_detected = False
    if settings.get("camera_enabled", True):
        success, faces_detected = webcam_manager.save_current_frame(photo_path, run_face_detection=True)
        
    if not success:
        photo_path = None
        relative_path = None
        print("Failed to capture frame from webcam or camera is disabled.")
    
    # Add to log history
    if faces_detected:
        event_desc = "👤 PHÁT HIỆN KHUÔN MẶT KẺ XÂM NHẬP!"
    else:
        event_desc = f"Phát hiện chuyển động qua cảm biến PIR" if sensor == "PIR" else f"Phát hiện cửa mở bất thường"
        
    add_log(event_desc, sensor, relative_path)
    
    # Send Telegram message in a background thread to prevent blocking
    threading.Thread(
        target=send_telegram_notification,
        args=(sensor, photo_path, faces_detected),
        daemon=True
    ).start()

def on_arduino_status(status):
    global system_state
    # Update local states
    system_state["is_armed"] = status.get("ARMED", system_state["is_armed"])
    system_state["pir_detected"] = status.get("PIR", False)
    system_state["door_open"] = status.get("DOOR", False)
    
    # Only update triggered status if it came from Arduino
    system_state["alarm_triggered"] = status.get("ALARM", False)

serial_manager = SerialManager(on_arduino_trigger, on_arduino_status)

# Load configurations on boot
load_settings()
if settings.get("camera_enabled", True):
    webcam_manager.start(settings.get("webcam_id", 0))
else:
    print("Webcam disabled on startup by user preference.")
serial_manager.start(settings.get("com_port", "AUTO"))

# Flask HTTP Router Endpoints
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/api/status', methods=['GET'])
def get_status():
    global system_state
    
    # If in simulator mode, check sensor and trigger alarms locally in Python
    if settings.get("use_simulator", True):
        # Trigger alarm if armed and any sensor is activated
        if system_state["is_armed"]:
            if system_state["pir_detected"]:
                on_arduino_trigger("PIR")
            elif system_state["door_open"]:
                on_arduino_trigger("DOOR")
                
    # Check webcam activity
    webcam_active = webcam_manager.cap is not None and webcam_manager.cap.isOpened()
    
    return jsonify({
        "is_armed": system_state["is_armed"],
        "pir_detected": system_state["pir_detected"],
        "door_open": system_state["door_open"],
        "alarm_triggered": system_state["alarm_triggered"],
        "connection_status": system_state["connection_status"],
        "actual_port": system_state["actual_port"],
        "webcam_status": "Active" if (webcam_active and settings.get("camera_enabled", True)) else "Inactive",
        "settings": {
            "com_port": settings.get("com_port"),
            "webcam_id": settings.get("webcam_id"),
            "use_simulator": settings.get("use_simulator"),
            "camera_enabled": settings.get("camera_enabled", True),
            "telegram_token": settings.get("telegram_token") != "", # Hide token for security
            "telegram_chat_id": settings.get("telegram_chat_id")
        }
    })

@app.route('/api/arm', methods=['POST'])
def arm_system():
    global system_state
    system_state["is_armed"] = True
    add_log("Kích hoạt chế độ bảo vệ (Armed)", "SYSTEM", None)
    
    # Notify Arduino
    if not settings.get("use_simulator", True):
        serial_manager.write_command("ARM")
        
    return jsonify({"success": True, "message": "System ARMED"})

@app.route('/api/disarm', methods=['POST'])
def disarm_system():
    global system_state
    system_state["is_armed"] = False
    system_state["alarm_triggered"] = False
    
    # If in simulation mode, clear detected states on disarm
    if settings.get("use_simulator", True):
        system_state["pir_detected"] = False
        system_state["door_open"] = False
        
    add_log("Tắt chế độ bảo vệ (Disarmed)", "SYSTEM", None)
    
    # Notify Arduino
    if not settings.get("use_simulator", True):
        serial_manager.write_command("DISARM")
        
    return jsonify({"success": True, "message": "System DISARMED"})

@app.route('/api/simulate_trigger', methods=['POST'])
def simulate_trigger():
    global system_state
    if not settings.get("use_simulator", True):
        return jsonify({"success": False, "message": "Not in simulator mode."}), 400
        
    data = request.json or {}
    sensor = data.get("sensor")
    state = data.get("state", False)
    
    if sensor == "PIR":
        system_state["pir_detected"] = state
    elif sensor == "DOOR":
        system_state["door_open"] = state
    else:
        return jsonify({"success": False, "message": "Invalid sensor"}), 400
        
    # Check trigger condition
    if system_state["is_armed"] and state:
        # Trigger alarm
        on_arduino_trigger(sensor)
        
    return jsonify({"success": True, "message": f"Simulated {sensor} state set to {state}"})

@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify(load_history())

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    save_history([])
    return jsonify({"success": True, "message": "History cleared"})

@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    global settings
    if request.method == 'GET':
        # Return settings, mask the token
        safe_settings = settings.copy()
        if safe_settings.get("telegram_token"):
            safe_settings["telegram_token"] = "•" * 15 + safe_settings["telegram_token"][-4:]
        return jsonify(safe_settings)
        
    else:  # POST
        data = request.json or {}
        new_settings = settings.copy()
        
        # Only update token if it's not the masked representation
        new_token = data.get("telegram_token", "").strip()
        if new_token and not new_token.startswith("••••••••••••"):
            new_settings["telegram_token"] = new_token
        
        new_settings["telegram_chat_id"] = data.get("telegram_chat_id", "").strip()
        new_settings["com_port"] = data.get("com_port", "AUTO")
        new_settings["use_simulator"] = data.get("use_simulator", True)
        
        # Check if webcam_id changed
        old_webcam_id = settings.get("webcam_id", 0)
        new_webcam_id = int(data.get("webcam_id", 0))
        new_settings["webcam_id"] = new_webcam_id
        
        # Save settings
        save_settings(new_settings)
        settings = new_settings
        
        # Apply changes dynamically
        if old_webcam_id != new_webcam_id and settings.get("camera_enabled", True):
            webcam_manager.start(new_webcam_id)
            
        serial_manager.stop()
        serial_manager.start(settings.get("com_port", "AUTO"))
        
        return jsonify({"success": True, "message": "Settings updated successfully"})

@app.route('/api/test_telegram', methods=['POST'])
def test_telegram():
    token = settings.get("telegram_token", "").strip()
    chat_id = settings.get("telegram_chat_id", "").strip()
    
    if not token or not chat_id:
        return jsonify({"success": False, "message": "Telegram Token hoặc Chat ID chưa được cấu hình!"}), 400
        
    test_msg = (
        "🔔 <b>THỬ NGHIỆM HỆ THỐNG AN NINH</b> 🔔\n\n"
        "✅ Kết nối Telegram Bot thành công!\n"
        "📈 Hệ thống sẵn sàng gửi tin nhắn khi có xâm nhập."
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": test_msg,
        "parse_mode": "HTML"
    }
    
    try:
        r = requests.post(url, json=payload, timeout=5)
        if r.status_code == 200:
            return jsonify({"success": True, "message": "Đã gửi tin nhắn test thành công tới Telegram!"})
        else:
            return jsonify({"success": False, "message": f"Telegram API Error: {r.text}"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Exception: {str(e)}"}), 500

@app.route('/api/webcam/toggle', methods=['POST'])
def toggle_webcam():
    global settings
    current_state = settings.get("camera_enabled", True)
    new_state = not current_state
    settings["camera_enabled"] = new_state
    save_settings(settings)
    
    if new_state:
        webcam_manager.start(settings.get("webcam_id", 0))
        add_log("Bật Camera giám sát", "SYSTEM", None)
        message = "Đã bật camera giám sát"
    else:
        webcam_manager.stop()
        add_log("Tắt Camera giám sát (Chế độ riêng tư)", "SYSTEM", None)
        message = "Đã tắt camera (Chế độ riêng tư)"
        
    return jsonify({
        "success": True, 
        "camera_enabled": new_state, 
        "message": message
    })

# Video Streaming Feed Route
def generate_video_stream():
    while True:
        frame_bytes = webcam_manager.get_frame_jpeg()
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            # If camera is not ready, return a dummy transparent frame or sleep
            time.sleep(0.1)
        time.sleep(0.04) # Target ~25 FPS

@app.route('/api/video_feed')
def video_feed():
    return Response(generate_video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Telegram Interactive Bot Handlers
def edit_message_text(chat_id, message_id, text, token):
    url = f"https://api.telegram.org/bot{token}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error editing message: {e}")

def handle_telegram_callback(callback_query, token):
    global system_state
    query_id = callback_query["id"]
    chat_id = callback_query["message"]["chat"]["id"]
    data = callback_query.get("data", "")
    
    response_text = ""
    
    if data == "disarm":
        system_state["is_armed"] = False
        system_state["alarm_triggered"] = False
        if settings.get("use_simulator", True):
            system_state["pir_detected"] = False
            system_state["door_open"] = False
        else:
            serial_manager.write_command("DISARM")
            
        add_log("Tắt chế độ bảo vệ từ Telegram", "TELEGRAM", None)
        response_text = "🔕 Đã tắt báo động thành công!"
        
        edit_msg_text = (
            f"🚨 <b>BÁO ĐỘNG ĐÃ ĐƯỢC XỬ LÝ</b> 🚨\n\n"
            f"🔕 Hệ thống đã được <b>VÔ HIỆU HÓA</b> từ xa qua Telegram."
        )
        edit_message_text(chat_id, callback_query["message"]["message_id"], edit_msg_text, token)
        
    elif data == "arm":
        system_state["is_armed"] = True
        if not settings.get("use_simulator", True):
            serial_manager.write_command("ARM")
        add_log("Kích hoạt chế độ bảo vệ từ Telegram", "TELEGRAM", None)
        response_text = "🛡️ Đã kích hoạt bảo vệ thành công!"
        
        edit_msg_text = (
            f"🛡️ <b>HỆ THỐNG ĐÃ ĐƯỢC KÍCH HOẠT</b> 🛡️\n\n"
            f"Hệ thống đã chuyển sang chế độ <b>Armed</b> qua Telegram."
        )
        edit_message_text(chat_id, callback_query["message"]["message_id"], edit_msg_text, token)
        
    elif data == "capture":
        photo_filename = f"tele_capture_{int(time.time())}.jpg"
        photo_path = os.path.join(CAPTURES_DIR, photo_filename)
        relative_path = f"/static/captures/{photo_filename}"
        
        success = False
        faces_detected = False
        if settings.get("camera_enabled", True):
            success, faces_detected = webcam_manager.save_current_frame(photo_path, run_face_detection=True)
            
        if success:
            add_log("Yêu cầu chụp hình từ Telegram", "TELEGRAM", relative_path)
            send_photo_url = f"https://api.telegram.org/bot{token}/sendPhoto"
            caption_text = f"📸 Ảnh chụp trực tiếp theo yêu cầu lúc {time.strftime('%H:%M:%S')}"
            if faces_detected:
                caption_text += " [👤 Phát hiện khuôn mặt!]"
            with open(photo_path, 'rb') as img_file:
                files = {'photo': img_file}
                photo_payload = {
                    "chat_id": chat_id,
                    "caption": caption_text
                }
                requests.post(send_photo_url, data=photo_payload, files=files, timeout=10)
            response_text = "📸 Đã gửi ảnh mới!"
        else:
            response_text = "❌ Không thể chụp ảnh!"
            
    answer_url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
    try:
        requests.post(answer_url, json={"callback_query_id": query_id, "text": response_text}, timeout=5)
    except:
        pass

def handle_telegram_message(message, token):
    global system_state
    text = message.get("text", "").strip()
    chat_id = message["chat"]["id"]
    
    if text == "/status":
        state_text = (
            f"ℹ️ <b>TRẠNG THÁI HỆ THỐNG AN NINH</b>\n\n"
            f"🛡️ <b>Chế độ bảo vệ:</b> {'KÍCH HOẠT (Armed)' if system_state['is_armed'] else 'VÔ HIỆU HÓA (Disarmed)'}\n"
            f"🚨 <b>Báo động:</b> {'ĐANG HÚ CÒI 🚨' if system_state['alarm_triggered'] else 'Bình thường'}\n"
            f"🚶 <b>Cảm biến PIR:</b> {'Phát hiện chuyển động 🚶' if system_state['pir_detected'] else 'Bình thường'}\n"
            f"🚪 <b>Cảm biến Cửa:</b> {'Mở cửa! 🚪' if system_state['door_open'] else 'Đóng'}\n"
            f"🔌 <b>Kết nối phần cứng:</b> {system_state['connection_status']}\n"
            f"📸 <b>Camera:</b> {'Đang bật (LIVE)' if settings.get('camera_enabled', True) else 'Đang tắt'}"
        )
        
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "🔕 Vô Hiệu Hóa (Disarm)", "callback_data": "disarm"} if system_state["is_armed"] else {"text": "🛡️ Kích Hoạt (Arm)", "callback_data": "arm"}
                ],
                [
                    {"text": "📸 Chụp Ảnh Ngay", "callback_data": "capture"}
                ]
            ]
        }
        
        send_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": state_text,
            "parse_mode": "HTML",
            "reply_markup": reply_markup
        }
        try:
            requests.post(send_url, json=payload, timeout=5)
        except Exception as e:
            print(f"Error sending status to telegram: {e}")

def telegram_polling_thread():
    last_update_id = 0
    print("Telegram Polling Thread started.")
    time.sleep(2)
    
    while True:
        token = settings.get("telegram_token", "").strip()
        if not token:
            time.sleep(3)
            continue
            
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            params = {"timeout": 10}
            if last_update_id > 0:
                params["offset"] = last_update_id + 1
                
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        last_update_id = update["update_id"]
                        
                        if "callback_query" in update:
                            handle_telegram_callback(update["callback_query"], token)
                        elif "message" in update and "text" in update["message"]:
                            handle_telegram_message(update["message"], token)
            time.sleep(0.5)
        except Exception as e:
            time.sleep(3)

if __name__ == '__main__':
    print("Starting Smart Home Alarm System backend server...")
    # Add an initial log
    add_log("Khởi động hệ thống máy chủ an ninh", "SYSTEM", None)
    
    # Start Telegram background polling thread
    threading.Thread(target=telegram_polling_thread, daemon=True).start()
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
