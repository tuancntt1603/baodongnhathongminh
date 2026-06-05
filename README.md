<h2 align="center">
<a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
🎓 Faculty of Information Technology (DaiNam University)
</a>
</h2>

<h1 align="center">
🏠 HỆ THỐNG BÁO ĐỘNG NHÀ THÔNG MINH
</h1>

<div align="center">

<img width="180" src="https://github.com/user-attachments/assets/77fe0fd1-2e55-4032-be3c-b1a705a1b574"/>

<br><br>

![Arduino](https://img.shields.io/badge/Arduino-UNO-blue?style=for-the-badge&logo=arduino)
![ESP8266](https://img.shields.io/badge/ESP8266-IoT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-Flask-yellow?style=for-the-badge&logo=python)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?style=for-the-badge&logo=telegram)
![GitHub](https://img.shields.io/badge/GitHub-Repository-black?style=for-the-badge&logo=github)

</div>

---

# 📖 1. Giới thiệu đề tài

**Hệ Thống Báo Động Nhà Thông Minh** là dự án ứng dụng công nghệ IoT nhằm giám sát và bảo vệ ngôi nhà trước các nguy cơ đột nhập trái phép.

Hệ thống sử dụng cảm biến chuyển động PIR, cảm biến từ cửa, Arduino UNO và ESP8266 để phát hiện các sự kiện bất thường. Khi phát hiện đột nhập, hệ thống sẽ kích hoạt còi báo động, đèn cảnh báo và gửi thông báo đến người dùng thông qua Telegram Bot hoặc giao diện Web.

### 🎯 Mục tiêu đề tài

* Xây dựng hệ thống báo động nhà thông minh chi phí thấp
* Ứng dụng công nghệ IoT vào giám sát an ninh
* Cảnh báo thời gian thực cho người dùng
* Điều khiển và giám sát từ xa
* Nâng cao kỹ năng lập trình nhúng và Web

---

# 🔍 2. Chức năng hệ thống

* ✅ Phát hiện chuyển động bằng cảm biến PIR
* ✅ Phát hiện mở cửa trái phép
* ✅ Kích hoạt còi báo động tự động
* ✅ Bật đèn LED cảnh báo
* ✅ Gửi cảnh báo qua Telegram
* ✅ Hiển thị trạng thái trên Web Dashboard
* ✅ Điều khiển bật/tắt hệ thống từ xa
* ✅ Lưu lịch sử cảnh báo

---

# ✨ 3. Tính năng nổi bật

## 🟢 Giám sát an ninh

* Theo dõi ngôi nhà 24/7
* Phát hiện người lạ xâm nhập
* Giám sát trạng thái cửa ra vào
* Cảnh báo tức thời

## 🔴 Hệ thống báo động

* Buzzer phát âm thanh cảnh báo
* LED nhấp nháy khi có sự cố
* Cảnh báo theo thời gian thực
* Dễ dàng mở rộng thêm thiết bị

## 🟡 Điều khiển từ xa

* Điều khiển qua Web
* Điều khiển qua Telegram Bot
* Theo dõi trạng thái mọi lúc mọi nơi
* Nhận thông báo tức thời

## 🔵 Quản lý dữ liệu

* Lưu lịch sử cảnh báo
* Quản lý dữ liệu tập trung
* Hỗ trợ phân tích sự kiện
* Dễ dàng nâng cấp hệ thống

---

# ⚙️ 4. Công nghệ sử dụng

| Thành phần | Công nghệ sử dụng |
|------------|------------------|
| Vi điều khiển | Arduino UNO |
| Kết nối IoT | ESP8266 |
| Cảm biến | PIR Sensor, Magnetic Door Sensor |
| Backend | Python Flask |
| Frontend | HTML, CSS, JavaScript |
| Thông báo | Telegram Bot API |
| Database | SQLite |
| Giao thức | HTTP, REST API |
| Quản lý mã nguồn | GitHub |

---

# 📂 5. Cấu trúc dự án

```bash
baodongnhathongminh/
│
├── arduino/
│   ├── smart_alarm.ino
│
├── server/
│   ├── app.py
│   ├── database.db
│
├── static/
│   ├── css/
│   ├── js/
│
├── templates/
│   ├── index.html
│
├── telegram/
│   ├── bot.py
│
├── requirements.txt
├── README.md
```

---

# ▶️ 6. Cách cài đặt và chạy dự án

## 1️⃣ Clone dự án

```bash
git clone https://github.com/tuancntt1603/baodongnhathongminh.git
```

```bash
cd baodongnhathongminh
```

---

## 2️⃣ Cài đặt thư viện

```bash
pip install -r requirements.txt
```

---

## 3️⃣ Nạp chương trình Arduino

```text
Mở Arduino IDE
Chọn Board Arduino UNO
Chọn cổng COM tương ứng
Upload file smart_alarm.ino
```

---

## 4️⃣ Chạy hệ thống

```bash
python app.py
```

---

## 5️⃣ Truy cập giao diện

```text
http://127.0.0.1:5000
```

---

# 🔌 7. Sơ đồ hoạt động hệ thống

```text
Cảm biến PIR/Cửa
        ↓
   Arduino UNO
        ↓
      ESP8266
        ↓
      Server
        ↓
 Web Dashboard
        ↓
 Telegram Bot
        ↓
     Người dùng
```

---

# 🧠 8. Thiết bị sử dụng

### Arduino UNO

* Điều khiển trung tâm của hệ thống
* Thu thập dữ liệu cảm biến
* Điều khiển còi và LED

### ESP8266

* Kết nối WiFi
* Truyền dữ liệu lên Server
* Nhận lệnh điều khiển

### PIR Sensor

* Phát hiện chuyển động
* Giám sát khu vực cần bảo vệ

### Magnetic Door Sensor

* Phát hiện trạng thái đóng/mở cửa
* Cảnh báo khi có xâm nhập

### Buzzer

* Phát âm thanh cảnh báo

### LED

* Hiển thị trạng thái hệ thống

---

# 📲 9. Chức năng Telegram Bot

Telegram Bot hỗ trợ:

* Nhận cảnh báo tức thời
* Kiểm tra trạng thái hệ thống
* Điều khiển từ xa
* Theo dõi lịch sử cảnh báo

Ví dụ:

```text
🚨 CẢNH BÁO ĐỘT NHẬP

⏰ Thời gian: 20:30:15
🚪 Cửa chính bị mở
📍 Vị trí: Phòng khách
```
---

# 📸 11. Hình ảnh Demo

## 🖥️ Giao diện Web Dashboard

<p align="center">
<img src="https://github.com/user-attachments/assets/0feb4f03-7f34-4797-ba01-10f43b0fabb8" width="800">
</p>

<p align="center">
<i>Hình 1. Giao diện giám sát hệ thống báo động nhà thông minh</i>
</p>

---

## Cài đặt hệ thống

<p align="center">
<img src="https://github.com/user-attachments/assets/0deb9562-69ec-4e31-a964-fc1091ee2d21" width="800">
</p>

<p align="center">
<i>Hình 2. Hình ảnh cài đặt hệ thôngs</i>
</p>

---

## 📲 Thông báo Telegram

<p align="center">
<img src="https://github.com/user-attachments/assets/7ebbf6a0-cbab-4154-9475-a5df27e01370" width="400">
</p>

<p align="center">
<i>Hình 3. Tin nhắn cảnh báo gửi đến Telegram</i>
</p>

---

## 🔌 Mô hình phần cứng

<p align="center">
<img src="https://github.com/user-attachments/assets/561930b4-787f-4197-b051-37b6092bf363" width="700">
</p>

<p align="center">
<i>Hình 4. Arduino UNO, ESP8266, cảm biến PIR, cảm biến cửa, LED và Buzzer</i>
</p>

---

---

# 🚀 10. Hướng phát triển

* Tích hợp ESP32-CAM
* Chụp ảnh người đột nhập
* Nhận diện khuôn mặt bằng AI
* Gửi hình ảnh qua Telegram
* Điều khiển bằng ứng dụng Mobile
* Lưu dữ liệu trên Cloud
* Tích hợp Firebase
* Kết nối nhiều cảm biến hơn

---

# 👨‍💻 11. Thông tin sinh viên

* **Họ và tên:** Bùi Anh Tuấn
* **Lớp:** CNTT 16-03
* **Khoa:** Công nghệ Thông tin
* **Trường:** Đại học Đại Nam

---

# 📌 12. Kết luận

Đề tài **Hệ Thống Báo Động Nhà Thông Minh** giúp sinh viên tiếp cận các công nghệ IoT, Arduino, ESP8266, Web Server và Telegram Bot trong việc xây dựng hệ thống giám sát an ninh thông minh.

Dự án có tính ứng dụng thực tế cao, dễ triển khai và có khả năng mở rộng để phát triển thành hệ thống Smart Home hoàn chỉnh trong tương lai.

---

<div align="center">
