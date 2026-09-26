# Kế hoạch Duck Race: light mode + linh vật vịt

Trạng thái: đề xuất triển khai, chưa sửa giao diện hoặc engine trong lượt lập kế hoạch này.

## 1. Phạm vi và định hướng

- Light mode mặc định, bỏ cyberpunk/neon và tên NEON DUCK; tên tạm dùng Đua Vịt.
- Surface chính: theo dõi cuộc đua; phụ: cấu hình người chơi. Không thêm hero marketing, điểm XP, streak hoặc nhiệm vụ không liên quan.
- Tham khảo ngôn ngữ tạo hình thân thiện của Duolingo: hình khối tròn, silhouette rõ, mắt biểu cảm, màu phẳng, nút có chiều sâu. Thiết kế vịt nguyên bản, không đổi màu linh vật cú Duo hay lấy tài sản thương hiệu.
- Giữ HTML/CSS/Canvas tự chứa, offline; không thêm backend/framework chỉ để đổi hình thức.
- Giữ đầy đủ bảng xếp hạng, đóng/mở lại, loại người thắng theo ID, khóa cấu hình lúc đua/tạm dừng và chống XSS.

## 2. Visual system đề xuất

| Thành phần | Hướng thiết kế |
|---|---|
| Nền | Trắng ngà #F7FAF5; panel trắng #FFFFFF |
| Chữ | Chính #24332B, phụ #53645A; kiểm tra contrast thực tế |
| Accent | Xanh lá tươi #58CC02; chữ tối trên xanh sáng hoặc xanh đậm với chữ trắng nếu contrast đạt |
| Đường đua | Nước xanh nhạt #DFF3FA, phân làn tinh tế, phao xuất phát và cổng đích rõ |
| Màu vịt | Vàng chủ đạo; xanh mint, san hô, xanh trời, tím lavender cho biến thể |
| Hình khối | Bo 16–24px, viền rõ, bóng cứng hướng xuống; bỏ glow/blur/clip góc cyberpunk |
| Typography | Sans tròn, hỗ trợ tiếng Việt; cân nhắc Nunito đóng gói local, font hệ thống dự phòng; chỉ dùng chữ đậm cho phân cấp |
| Nút | Chiều cao tối thiểu 44px; nhấn lún 2–3px bằng transform, không gây layout shift |

Các giá trị trên là token đề xuất, không phải kết quả đo hoặc chứng nhận accessibility. Không dùng chữ trắng trên xanh sáng mà chưa đo contrast.

## 3. Thiết kế linh vật vịt

### Tạo hình
- Thân quả lê/giọt nước mập, đầu lớn liền khối, đuôi ngắn và cánh dạng giọt nước.
- Mắt trắng lớn với đồng tử đậm, lông mày linh hoạt; mỏ dẹt rộng màu cam để đọc đúng là vịt, không giống cú.
- Góc nhìn 3/4 hướng sang phải; thấy nét mặt nhưng vẫn rõ chiều đua.
- Mảng màu phẳng và một mảng bóng; không 3D, không neon, không nét quá nhỏ.
- Phụ kiện ít chi tiết: băng đô, nơ, mũ lưỡi trai, kính. Phụ kiện không che toàn bộ mắt và không thay đổi hitbox/cán đích.
- Nhận diện bằng số người chơi + tên + phụ kiện, không chỉ dựa vào màu.

### Biểu cảm / chuyển động
| Trạng thái | Hành vi hình ảnh |
|---|---|
| Sẵn sàng | Mỉm cười, chớp mắt thưa, nhún nhẹ |
| Đang đua | Nghiêng thân vừa phải, quạt cánh, sóng nước phía sau |
| Tăng tốc | Mắt tập trung, đuôi nước dài hơn; không hiệu ứng lửa che người khác |
| Tạm dừng | Đóng băng pose và hiệu ứng |
| Về đích | Vui mừng ngắn; quán quân có huy hiệu riêng |
| Reduced motion | Bỏ nhún/phóng to/confetti mạnh, giữ chuyển động tiến độ cần thiết |

### Asset và renderer
- Làm character sheet trước: vịt gốc, biến thể và các trạng thái, kiểm tra ở kích thước chạy thực tế.
- Một bộ hình học vector dùng chung: avatar UI/podium và Canvas race không vẽ thành hai nhân vật khác nhau.
- Dùng Canvas paths, sprite cache/offscreen nếu cần sau đo; không thêm request ảnh bên ngoài.
- Pose và biểu cảm phụ thuộc thời gian/trạng thái hiển thị, không thay đổi tiến độ mô phỏng.

## 4. Bố cục và luồng

### Desktop
- Panel trái: danh sách, preset, thời lượng, tùy chọn, CTA.
- Sân đua ở giữa là trọng tâm. Timer/trạng thái/top dẫn đầu có vùng riêng ngoài làn.
- Footer điều khiển khi ẩn panel; tránh hai CTA giống nhau cùng tranh chú ý.

### Mobile / tablet
- Stage-first; Start/Pause/Reset luôn chạm được.
- Danh sách/cài đặt trong bottom sheet có nút đóng rõ ràng và quản lý focus; không dựa vào việc người dùng đoán thao tác vuốt.
- Chọn breakpoint theo chiều rộng sân đua còn lại, không mặc định tablet luôn đủ chỗ cho sidebar.
- Danh sách đông: làn có chiều cao tối thiểu, vùng sân đua cuộn riêng; camera không tự giật khi người dùng đang cuộn. Có hành động quay về nhóm dẫn đầu nếu triển khai follow mode.
- Không thu nhỏ 100 vịt thành các vạch không đọc được; khả năng xếp hạng 100 người không đồng nghĩa mọi vịt đều nhìn rõ cùng lúc.

### Kết quả
- Khối quán quân với avatar vui mừng; top 2/3 nhỏ hơn, không tạo người thứ ba khi chỉ có hai người.
- Bảng đầy đủ bên dưới: hạng, avatar/tên, thời gian mô phỏng, chênh lệch với người đầu.
- Giữ semantic table; style hàng nhẹ, không đổi thành hàng trăm thẻ lớn làm khó so sánh.
- Đóng không reset. Có Xếp hạng để mở lại; Đua vòng mới và Loại quán quân giữ đúng nghĩa.
- Tên đầy đủ đọc được trong kết quả; tên dài trên đường đua rút gọn có chủ đích.

## 5. Triển khai theo thứ tự

### Pha A: baseline và character sheet
- Lưu snapshot hiện tại cả source và tests vì vẫn có thay đổi chưa commit.
- Chạy lại regression hiện có, phân biệt test hành vi và assertion màu/tên cyberpunk.
- Tạo sheet vịt và mockup ready/racing/results ở desktop/mobile để duyệt một hướng.
- Nghiệm thu: vịt đọc rõ ở kích thước nhỏ, không giống bản sao Duo, sân đua có phân cấp rõ.

### Pha B: design system và responsive shell
- Thay khối CSS cũ bằng token/component gọn, không chồng thêm lớp override thứ ba.
- Đổi tên, copy, buttons, form states, HUD, sheet, results sang light mode.
- Đo contrast, kiểm tra disabled/focus/empty/invalid và kích thước vùng bấm.
- Nghiệm thu: không còn glow/nền đen/nhãn cyberpunk sót, không overflow hoặc controls bị che.

### Pha C: renderer linh vật và đường đua
- Thay Duck.draw/drawAccessory/drawNameTag, drawWater/drawTrack cùng hệ particle.
- Tạo neo vị trí nhất quán: animation nhún/nghiêng không dịch vị trí logic ở vạch đích.
- Tách RNG hiệu ứng khỏi RNG mô phỏng trước khi thêm animation mới. Source hiện còn dùng Math.random chung cho mô phỏng, hạt và âm thanh; thêm lời gọi random trang trí có thể thay đổi kết quả.
- Không nhân tiện thay thuật toán xếp hạng hay hứa công bằng/FPS-independent. Việc ổn định engine toàn diện là scope riêng.
- Nghiệm thu: cùng luồng RNG mô phỏng và bước thời gian, bật/tắt hiệu ứng không thay đổi thứ tự/thời điểm về đích.

### Pha D: nối đầy đủ trạng thái
- Ready/racing/paused/finished, danh sách rỗng hoặc 1 người, tên dài/trùng, bảng nhiều dòng.
- Quản lý focus sheet/modal, Esc/Tab, reduced motion, persistence cấu hình hiện có.
- Kết quả vẫn chỉ giữ trong phiên hiện tại, không tự thêm lịch sử hoặc lưu qua F5.

### Pha E: QA và bàn giao
- Giữ các assertion hành vi trong audit/test_cyberpunk.py; đổi tên suite và thay assertion thương hiệu/màu đã chủ ý đổi.
- Bổ sung tests RNG isolation, không bị animation tác động finish, scroll làn đông và accessibility controls.
- Chromium rendering thật tại 320x568, 390x844, 768x1024, 1440x900, 844x390; kiểm tra ready/racing/paused/results, zoom 200%, tên tiếng Việt.
- Kiểm thử roster 2/8/16/32/100, XSS, tên trùng, click lặp, reset sát finish, đóng/mở kết quả; real RAF race chứ không chỉ gọi update thủ công.
- Đo frame time/DOM update/particle budget, tránh hứa FPS trước đo; xác nhận không request asset ngoài khi chạy offline.
- Báo cáo riêng browser/device chưa kiểm tra. Không gọi probe exit=0 là toàn bộ audit pass.

## 6. Điều kiện hoàn thành

- Light mode nhất quán, vịt nguyên bản có biểu cảm, đọc được ở kích thước thực tế.
- Không HUD/nút che làn hoặc đích; roster đông có cách xem khả dụng.
- Bảng kết quả đủ người, số thứ hạng và thời gian thực ghi nhận; không tạo kết quả giả.
- Regression hành vi và test mới đạt, không console exception; contrast đo đạt AA cho chữ chức năng.
- Bàn giao HTML offline, character sheet/design tokens và báo cáo kiểm thử có giới hạn xác minh rõ ràng.

Ngoài phạm vi: tài khoản, backend, multiplayer, XP/streak, lịch sử nhiều phiên, chứng nhận fairness và cam kết thời lượng chính xác theo wall clock.
