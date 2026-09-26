# 🦆 Duck Race Next-Gen | Đua Vịt Siêu Kịch Tính

Ứng dụng quay số ngẫu nhiên / đua vịt trực tuyến thế hệ mới, chạy hoàn toàn độc lập trên trình duyệt với phong cách đồ họa **Duolingo Light Mode**, hiệu ứng vật lý Canvas 2D procedural mượt mà và thuật toán xếp hạng công bằng tuyệt đối.

![License](https://img.shields.io/badge/license-MIT-green.svg)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)
![Platform](https://img.shields.io/badge/platform-Web%20%7C%20Mobile%20%7C%20Desktop-blue.svg)
![Build](https://img.shields.io/badge/build-pure%20static%20HTML5-success.svg)

---

## ✨ Điểm nổi bật & Tính năng cốt lõi

- **🎨 Thiết kế Duolingo Light Mode**: Giao diện tươi sáng, góc bo tròn mềm mại, nút bấm xúc giác 3D dập nổi và hiệu ứng phản hồi sinh động.
- **🦆 Linh vật Vịt Procedural (Canvas 2D)**: Từng chú vịt được vẽ trực tiếp bằng thuật toán vector Canvas: chuyển động vỗ cánh bơi lội, chớp mắt biểu cảm, lắc lư theo dòng nước và phụ kiện ngẫu nhiên (mũ lưỡi trai, vương miện, kính râm...).
- **📱 Vừa vặn đúng 1 View Height (100vh)**: Toàn bộ đường đua và giao diện luôn nằm gọn trong 1 màn hình duy nhất, không phát sinh thanh cuộn dọc ngoài ý muốn.
- **🌊 Cơ chế Chồng lớp tự nhiên (Flock Overlap)**: Hỗ trợ từ 2 đến hơn 100 vịt. Vịt giữ nguyên kích thước chuẩn 100% (`scale = 0.95`), tự động xếp lớp theo chiều sâu trục Y như trò đua vịt truyền thống.
- **🎥 Cam Cận Cảnh (Tracking Follow Camera)**: Chế độ camera lia ngang bám sát đàn vịt dẫn đầu trên đường đua ảo dài 2.3x. Vạch đích hoàn toàn nằm ngoài màn hình trong suốt chặng đua, chỉ xuất hiện ở những giây nước rút nghẹt thở cuối cùng.
- **💾 Quản lý Mẫu danh sách trên máy (IndexedDB)**: Người dùng tự do lưu, đặt tên và xóa không giới hạn các mẫu danh sách thí sinh (VD: *Lớp 12A1*, *Giveaway Tết*, *Nhóm thuyết trình*...). Dữ liệu lưu 100% offline cục bộ trên trình duyệt máy bạn.
- **🎲 Thuật toán Công bằng & Tách biệt RNG**: Tách bạch tuyệt đối giữa nguồn ngẫu nhiên mô phỏng cuộc đua (`simRandom`) và hiệu ứng đồ họa/âm thanh (`fxRandom`). Thuật toán nội suy thời gian về đích liên tục, phân định thứ hạng chính xác đến từng phần nghìn giây.
- **🏆 Bảng Top dẫn đầu linh hoạt**: Hỗ trợ nút ẩn/hiện bảng Top dẫn đầu linh hoạt trên cả máy tính lẫn điện thoại, trả lại mặt nước thông thoáng không bị che khuất.
- **⚡ Không phụ thuộc (Zero Dependencies)**: Đóng gói trọn vẹn trong 1 file `index.html` duy nhất (Vanilla HTML/CSS/JS). Không cần cài đặt Node.js, không npm build, không gọi CDN bên ngoài, chạy mượt mà ngay cả khi không có mạng.

---

## 🎮 Hướng dẫn sử dụng & Thao tác

### 1. Nhập danh sách & Quản lý mẫu
- Nhập tên thí sinh vào ô văn bản (mỗi dòng một tên).
- Bấm **"Xáo tên"** để đảo ngẫu nhiên vị trí các làn đua.
- Bấm **"+ Lưu danh sách này"** để đặt tên và lưu mẫu danh sách vào máy (lưu trong IndexedDB).
- Nhấp vào thẻ mẫu đã lưu để nạp nhanh danh sách bất cứ lúc nào; bấm dấu **✕** trên thẻ để xóa mẫu.

### 2. Tùy chọn cuộc đua (Accordion mở rộng)
- **Thời lượng mục tiêu**: Kéo thanh trượt điều chỉnh độ dài cuộc đua (từ 5 đến 30 giây).
- **Lội ngược dòng**: Bật cơ chế lật kèo ngẫu nhiên cho các chú vịt phía sau bứt tốc bất ngờ.
- **Vạch đích Slow-Mo**: Tự động quay chậm kịch tính khi vịt đầu tiên chuẩn bị cán đích.
- **Âm thanh vui nhộn & Đọc tên quán quân**: Phát nhạc nền, hiệu ứng bơi lội và giọng đọc TTS xướng tên người chiến thắng.
- **Cam cận cảnh**: Góc nhìn bám đuổi giấu vạch đích đến phút chót.

### 3. Phím tắt tiện lợi (Desktop)
- **`Space` (Phím cách)**: Bắt đầu cuộc đua / Tạm dừng hoặc Tiếp tục.
- **`R`**: Đua lại vòng mới với danh sách hiện tại.
- **`Esc`**: Đóng nhanh bảng xếp hạng hoặc bảng điều khiển.

---

## 🚀 Hướng dẫn Chạy cục bộ

### Cách 1: Mở trực tiếp
Nhấp đúp chuột vào file `index.html` hoặc kéo thả file vào bất kỳ trình duyệt web nào (Chrome, Edge, Firefox, Safari).

### Cách 2: Chạy qua Local Web Server
```bash
# Sử dụng Python 3 có sẵn
python3 -m http.server 8080

# Hoặc sử dụng Node.js (nếu có)
npx serve .
```
Sau đó truy cập: `http://localhost:8080`

---

## 🌐 Hướng dẫn Deploy lên mạng (Miễn phí)

Dự án là **Static Web 100% (Zero Build)**, bạn có thể triển khai lên các nền tảng hosting miễn phí trong vòng 30 giây:

### 1. GitHub Pages
1. Push mã nguồn lên GitHub repository của bạn.
2. Vào tab **Settings** > **Pages**.
3. Tại mục **Build and deployment** > **Source**, chọn **Deploy from a branch**.
4. Chọn branch `master` (hoặc `main`) và thư mục `/ (root)`, sau đó bấm **Save**.

### 2. Cloudflare Pages
1. Đăng nhập [Cloudflare Dashboard](https://dash.cloudflare.com/) > **Workers & Pages** > **Create application** > **Pages**.
2. Kết nối với GitHub Repo của bạn.
3. Phần **Build command**: *để trống*.
4. Phần **Build output directory**: `.` (thư mục gốc).
5. Bấm **Save and Deploy**.

### 3. Vercel hoặc Netlify
- Kéo thả trực tiếp thư mục dự án vào trang quản trị của Netlify hoặc Vercel để nhận ngay URL trực tuyến.

---

## 📁 Cấu trúc thư mục Repository

```text
duck-race-nextgen/
├── index.html                # Ứng dụng web hoàn chỉnh (HTML5 + CSS3 + Canvas 2D + JS)
├── README.md                 # Tài liệu hướng dẫn sử dụng & triển khai
├── LICENSE                   # Giấy phép mã nguồn mở MIT
├── .gitignore                # Cấu hình loại trừ cho Git
└── design/                   # Tài liệu thiết kế & character sheet tham khảo
    ├── character-sheet.html  # Bảng vẽ chi tiết giải phẫu tạo hình vịt Canvas
    └── mockup.html           # Khung wireframe giao diện tham khảo
```

---

## 📄 Bản quyền & Tác giả

Phát triển bởi **Phan Chí Kiên** (23520804).  
Mã nguồn phát hành theo giấy phép [MIT License](LICENSE).
