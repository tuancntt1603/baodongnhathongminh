# Hệ Thống Báo Động Đột Nhập Nhà Thông Minh (Smart Home Security System)

Hệ thống bảo vệ an ninh kết hợp cảm biến chuyển động PIR, cảm biến cửa từ, phần cứng xử lý Arduino/ESP8266 và Camera Laptop. Khi phát hiện đột nhập lúc hệ thống được kích hoạt chế độ an ninh (Armed), hệ thống lập tức hú còi, nháy đèn cảnh báo, đồng thời điều khiển Laptop chụp ảnh kẻ xâm nhập, lưu trữ, và gửi tin nhắn cảnh báo có đính kèm hình ảnh trực tiếp tới điện thoại của chủ nhà thông qua Telegram Bot.

---

## 🌟 Tính Năng Nổi Bật
- **Giám Sát Thời Gian Thực (Real-time):** Dashboard Web hiển thị liên tục trạng thái cảm biến PIR (chuyển động) và Cảm biến cửa (đóng/mở).
- **Phát Hiện & Chụp Ảnh Tức Thời:** Sử dụng luồng Webcam chạy nền giúp camera luôn ở trạng thái sẵn sàng để ghi hình ngay khi phát hiện đột nhập, không trễ thời gian khởi động camera.
- **Cảnh Báo Telegram Tiện Lợi:** Gửi tin nhắn khẩn cấp kèm hình ảnh chất lượng cao tới điện thoại hoàn toàn miễn phí.
- **Bảng Điều Khiển Cài Đặt Linh Hoạt:** Cho phép thay đổi cổng kết nối (COM Port), ID Camera, chế độ Giả lập, và cấu hình Token Telegram trực tiếp trên giao diện web mà không cần khởi động lại server.
- **Chế Độ Giả Lập Thông Minh (Simulator):** Tích hợp sẵn bộ mô phỏng cảm biến trên giao diện để kiểm tra toàn bộ hoạt động chụp ảnh và gửi tin nhắn của Laptop ngay cả khi không có phần cứng kết nối.

---

## 🔌 Sơ Đồ Đấu Nối Phần Cứng (Hardware Pins)

Hệ thống hoạt động tương thích với cả dòng **Arduino (Uno/Nano/Mega)** và **ESP8266 (NodeMCU)**:

| Thiết bị phần cứng | Chân trên Arduino | Chân trên ESP8266 (NodeMCU) | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Cảm biến PIR (OUT)** | Pin D2 | Pin D2 (GPIO4) | Mức cao (HIGH) = Có chuyển động |
| **Cảm biến cửa từ (Pin A)**| Pin D3 | Pin D1 (GPIO5) | Chân còn lại nối GND (INPUT\_PULLUP) |
| **Còi báo động (Buzzer +)**| Pin D4 | Pin D5 (GPIO14) | Chân (-) nối GND |
| **Đèn LED cảnh báo (+)**  | Pin D5 | Pin D6 (GPIO12) | Cần trở hạn dòng 220 Ohm, chân (-) nối GND |

> ⚠️ **Chú ý đối với cảm biến cửa từ:** Chân kết nối được khai báo là `INPUT_PULLUP` trong mã nguồn. Khi cửa đóng, hai cực nam châm hút nhau -> công tắc đóng -> pin nối GND (LOW). Khi cửa mở -> công tắc hở -> pin lên mức HIGH nhờ điện trở kéo lên bên trong.

---

## 🛠️ Hướng Dẫn Cài Đặt Phần Mềm

### 1. Nạp Code Cho Arduino/ESP8266
1. Mở phần mềm **Arduino IDE**.
2. Copy toàn bộ mã nguồn trong file [arduino_alarm.ino](./arduino_alarm.ino).
3. Kết nối Arduino/ESP8266 với máy tính, chọn đúng **Board** và **Port** trong menu *Tools*.
4. Nhấn **Upload** để nạp code.

### 2. Cài Đặt Môi Trường Trên Laptop
Yêu cầu Laptop đã cài đặt **Python 3.10+**.

Mở terminal tại thư mục dự án (`d:\btlnhan`) và thực hiện cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

### 3. Khởi Động Server Laptop
Chạy lệnh sau để khởi động máy chủ Flask:
```bash
python app.py
```
Sau khi khởi động thành công, màn hình sẽ hiển thị:
```
* Running on http://127.0.0.1:5000
```
Mở trình duyệt web và truy cập vào địa chỉ **`http://localhost:5000`** để sử dụng phần mềm.

---

## 🤖 Hướng Dẫn Cấu Hình Gửi Tin Nhắn Telegram Về Điện Thoại

Để nhận được tin nhắn và ảnh chụp đột nhập trên điện thoại, bạn cần tạo một Telegram Bot riêng:

### Bước 1: Tạo Telegram Bot
1. Trên điện thoại, mở ứng dụng Telegram và tìm kiếm bot **`@BotFather`** (có tích xanh chính chủ).
2. Chat lệnh `/newbot` và gửi.
3. Nhập tên hiển thị cho bot của bạn (ví dụ: `SafeHome Sec Bot`).
4. Nhập username cho bot (phải kết thúc bằng chữ `bot`, ví dụ: `my_safehome_alarm_bot`).
5. Sau khi hoàn thành, `@BotFather` sẽ gửi cho bạn một chuỗi **HTTP API Token** (Ví dụ: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`). Hãy lưu lại chuỗi này.

### Bước 2: Lấy Chat ID của Bạn
1. Tìm kiếm bot **`@userinfobot`** trên Telegram.
2. Nhấn nút **Start** hoặc gửi tin nhắn bất kỳ.
3. Bot sẽ phản hồi lại thông tin cá nhân của bạn, dòng **`Id:`** chính là **Chat ID** của bạn (Một chuỗi số, ví dụ: `987654321`).
4. Mở bot bạn vừa tạo ở Bước 1 và nhấn **Start** để kích hoạt cuộc trò chuyện với nó.

### Bước 3: Điền Cấu Hình Vào Phần Mềm
1. Trên giao diện Web Dashboard, nhấn vào biểu tượng **Bánh răng cài đặt** (Settings) ở góc trên bên phải.
2. Nhập **Telegram Bot Token** và **Telegram Chat ID** vào form.
3. Nhấn **Gửi Thử Tin Nhắn** (Test Telegram). Nếu điện thoại của bạn nhận được tin nhắn kiểm tra thì cấu hình đã hoàn toàn chính xác!
4. Nhấn **Lưu Cài Đặt** để lưu trữ cấu hình.

---

## 🖥️ Cách Kiểm Tra Hệ Thống Với Chế Độ Giả Lập (Simulator Mode)

Nếu chưa lắp đặt phần cứng Arduino/ESP8266, bạn vẫn có thể kiểm tra mọi chức năng cảnh báo của Laptop:
1. Mở cài đặt (icon Bánh răng), tích chọn **Chế độ giả lập (Không cần phần cứng)** và nhấn **Lưu Cài Đặt**.
2. Trên màn hình Dashboard, nhấn nút **KÍCH HOẠT HỆ THỐNG** (Armed) để khởi chạy chế độ bảo vệ.
3. Tại bảng **Bộ Giả Lập Thiết Bị**:
   - Nhấp vào nút **🚶 Chuyển động (PIR)** hoặc **🚪 Mở cửa (Cửa từ)**.
4. Hệ thống sẽ ngay lập tức chuyển sang trạng thái cảnh báo báo động (hú còi và đèn nhấp nháy trên màn hình), camera sẽ chụp một bức ảnh của bạn tại thời điểm đó, lưu vào mục Nhật ký và gửi ảnh về điện thoại của bạn qua Telegram.
5. Để tắt báo động, nhấn **TẮT BÁO ĐỘNG / VÔ HIỆU HÓA**.
