# 🦆 Duck Race Next-Gen | Đua Vịt Siêu Kịch Tính

Ứng dụng quay số ngẫu nhiên / đua vịt trực tuyến thế hệ mới, chạy hoàn toàn độc lập trên trình duyệt với phong cách đồ họa **Duolingo Light Mode**, hiệu ứng vật lý Canvas 2D procedural mượt mà và thuật toán xếp hạng chuẩn xác tuyệt đối.

![License](https://img.shields.io/badge/license-MIT-green.svg)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)
![Platform](https://img.shields.io/badge/platform-Web%20%7C%20Mobile%20%7C%20Desktop-blue.svg)
![Tests](https://img.shields.io/badge/tests-82%2F82%20passed-success.svg)

---

## ✨ Điểm nổi bật & Tính năng cốt lõi

- **🎨 Thiết kế Duolingo Light Mode**: Giao diện tươi sáng, góc bo tròn mềm mại, nút bấm xúc giác 3D dập nổi và hiệu ứng phản hồi sinh động.
- **🦆 Linh vật Vịt Procedural (Canvas 2D)**: Vịt vẽ trực tiếp bằng thuật toán vector Canvas, chuyển động cánh vỗ, chớp mắt biểu cảm, trang phục & phụ kiện ngẫu nhiên (mũ lưỡi trai, vương miện, kính râm...).
- **📱 Vừa vặn đúng 1 View Height (100vh)**: Toàn bộ giao diện và đường đua luôn nằm trọn trong 1 màn hình duy nhất, không phát sinh thanh cuộn dọc ngoài ý muốn.
- **🌊 Cơ chế Chồng lớp tự nhiên (Flock Overlap)**: Hỗ trợ từ 2 đến hơn 100 vịt. Vịt giữ nguyên kích thước chuẩn 100% (`scale = 0.95`), tự động xếp lớp theo chiều sâu trục Y như phiên bản đua vịt truyền thống.
- **🎥 Cam Cận Cảnh (Tracking Follow Camera)**: Chế độ camera lia ngang bám sát vịt dẫn đầu trên đường đua ảo dài 2.3x. Vạch đích hoàn toàn nằm ngoài màn hình trong suốt chặng đua, chỉ xuất hiện ở những giây nước rút nghẹt thở cuối cùng!
- **💾 Quản lý Mẫu lưu trên máy (IndexedDB)**: Người dùng tự do thêm, lưu, đặt tên và xóa không giới hạn các mẫu danh sách thí sinh (VD: *Lớp 12A1*, *Giveaway Tết*...). Dữ liệu lưu 100% offline cục bộ trên máy người dùng.
- **🎲 Cách ly RNG & Xếp hạng chuẩn xác**: Tách bạch tuyệt đối giữa nguồn ngẫu nhiên mô phỏng cuộc đua (`simRandom`) và hiệu ứng đồ họa/âm thanh (`fxRandom`). Thuật toán nội suy thời gian về đích liên tục, phân định thứ hạng công bằng đến từng phần nghìn giây.
- **🏆 Tùy biến bảng Top dẫn đầu**: Hỗ trợ nút ẩn/hiện bảng Top dẫn đầu linh hoạt trên cả máy tính lẫn điện thoại, không che khuất các làn bơi phía trên.
- **⚡ Không phụ thuộc (Zero Dependencies)**: Đóng gói trọn vẹn trong 1 file `index.html` duy nhất (Vanilla HTML/CSS/JS). Không cần `npm install`, không gọi CDN bên ngoài, chạy mượt mà ngay cả khi không có mạng.

---

## 🚀 Hướng dẫn chạy nhanh

### Cách 1: Mở trực tiếp
Nhấp đúp chuột vào file `index.html` hoặc kéo thả vào bất kỳ trình duyệt web nào (Chrome, Edge, Firefox, Safari).

### Cách 2: Chạy qua Local Web Server
```bash
# Python 3
python3 -m http.server 8080

# Hoặc Node.js
npx serve .
```
Sau đó truy cập: `http://localhost:8080`

---

## 🌐 Hướng dẫn Deploy lên mạng

Do dự án là **Static Web 100% (Zero Build)**, bạn có thể triển khai lên bất kỳ nền tảng miễn phí nào trong vòng 30 giây:

### 1. GitHub Pages
1. Push mã nguồn lên GitHub repo của bạn.
2. Vào **Settings** > **Pages**.
3. Tại mục **Build and deployment** > **Source**, chọn **Deploy from a branch**.
4. Chọn branch `master` (hoặc `main`) và thư mục `/ (root)`, bấm **Save**.

### 2. Cloudflare Pages
1. Đăng nhập [Cloudflare Dashboard](https://dash.cloudflare.com/) > **Workers & Pages** > **Create application** > **Pages**.
2. Kết nối với GitHub Repo của bạn.
3. Phần **Build command**: *để trống*.
4. Phần **Build output directory**: `.` (thư mục gốc).
5. Bấm **Save and Deploy**.

### 3. Vercel / Netlify
- Kéo thả cả thư mục dự án vào trang điều khiển của Netlify/Vercel, trang web sẽ có URL trực tiếp ngay lập tức.

---

## 📁 Cấu trúc thư mục

```text
duck-race-nextgen/
├── index.html                # Ứng dụng chính (HTML5 + CSS3 + Canvas 2D + JS)
├── README.md                 # Tài liệu hướng dẫn & đặc tả dự án
├── .gitignore                # Danh sách loại trừ cho Git
├── audit/                    # Bộ kiểm thử tự động hóa (Chromium CDP)
│   ├── test_light.py         # Test hồi quy 41 ca kiểm thử chức năng & UX
│   ├── test_light_parent.py  # Test kiểm tra tính bất biến 100vh, overlap & RNG
│   ├── test_light_independent.py # Bộ kiểm thử độc lập 34 assertions đa viewport
│   └── screenshots/          # Ảnh chụp màn hình kiểm chứng tự động
└── design/                   # Tài liệu bản vẽ & character sheet
    └── character-sheet.html  # Bảng thiết kế chi tiết tạo hình vịt
```

---

## 🧪 Kiểm thử tự động (Automated Test Suite)

Dự án đi kèm bộ test tự động hóa toàn diện thông qua **Chrome DevTools Protocol (CDP)**, kiểm thử trực tiếp trên Chromium Headless:

```bash
# Chạy toàn bộ 82 assertions
python3 audit/test_light.py && python3 audit/test_light_parent.py && python3 audit/test_light_independent.py
```
*Kết quả: **82/82 assertions PASS (100%)** trên 5 kích thước màn hình khác nhau (320px, 390px, 768px, 844x390px, 1440px).*

---

## 📄 Bản quyền & Tác giả

Phát triển bởi **Phan Chí Kiên** (23520804).  
Mã nguồn phát hành theo giấy phép [MIT License](LICENSE).
