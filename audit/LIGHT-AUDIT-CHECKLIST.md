# Bảng kiểm tra và Báo cáo Kiểm thử Độc lập: Duck Race Light Mascot Redesign

Tài liệu này xác định bộ quy tắc, phương pháp đo lường thực nghiệm và ma trận kiểm thử độc lập cho phiên bản thiết kế lại giao diện sáng (Light Mode) và linh vật vịt thân thiện (Duolingo-inspired Friendly Mascot) của dự án **Duck Race Next-Gen**.

---

## 1. Mục tiêu và Nguyên tắc Kiểm thử Độc lập

Bộ kiểm thử này được thiết kế và vận hành hoàn toàn độc lập với luồng triển khai giao diện (`index.html`) và bài kiểm tra đi kèm của nhóm lập trình:
- **Tập tin sở hữu độc lập**: Duy nhất `audit/test_light_independent.py` và `audit/LIGHT-AUDIT-CHECKLIST.md`. Tuyệt đối không can thiệp, không sửa đổi mã nguồn sản phẩm `index.html` hoặc các bài kiểm tra song song (`test_cyberpunk.py`, `test_light.py`).
- **Thực nghiệm qua Chrome DevTools Protocol (CDP)**: Điều khiển tiến trình Chromium headless độc lập (`--headless=new`, `--remote-debugging-port=0`, thư mục tạm an toàn trong `TMPDIR`), giao tiếp trực tiếp qua WebSocket CDP.
- **Thao tác con trỏ thật (Real Pointer Events)**: Không chỉ dựa vào `element.click()` tổng hợp trong JavaScript. Sử dụng `Input.dispatchMouseEvent` (`mouseMoved`, `mousePressed`, `mouseReleased`) tại tọa độ thực `getBoundingClientRect()` để phát hiện các phần tử bị cuộn ra ngoài màn hình (offscreen), bị che khuất hoặc có vùng bấm không hợp lệ.
- **Thao tác bàn phím thật (Real Keyboard Dispatch)**: Sử dụng `Input.dispatchKeyEvent` (`rawKeyDown`, `keyUp`) để kiểm tra tương tác phím Tab, Escape, Spacebar.
- **Đo lường hình học thực tế (DOM & Canvas Geometry)**: Đo đạc kích thước thực tế, độ phủ viewport, thanh cuộn, vùng an toàn touch target (tối thiểu 44×44px), độ sáng tương đối (Relative Luminance theo WCAG 2.1) và tỷ lệ tương phản thực tế giữa màu chữ và màu nền composite.
- **Không đặt giả định thẩm mỹ tùy tiện**: Không áp đặt mã màu hex cố định ngoại trừ yêu cầu độ sáng của Light Theme (Luminance nền > 0.5, tương phản chữ chức năng ≥ 4.5:1). Không bịa đặt tên hàm nội bộ để ép kiểm tra.

---

## 2. Phát hiện Kiểm thử trên Phiên bản Baseline (Cyberpunk Baseline Audit Findings)

Trước khi tiến hành xây dựng giao diện mới, bộ kiểm thử độc lập đã chạy rà soát toàn diện trên phiên bản hiện tại (`index.html` Cyberpunk baseline tại `http://127.0.0.1:8788/index.html`). Dưới đây là các lỗ hổng và điểm nghẽn kỹ thuật được đo lường chính xác:

### Finding B1: Đảo ngược thứ tự thời gian về đích (Non-monotonic Finish Times) ở quy mô 100 người chơi
- **Triệu chứng**: Khi kiểm thử cuộc đua 100 vịt, thỉnh thoảng xuất hiện các cặp vịt có thời gian về đích nghịch đảo (ví dụ: Vịt hạng 32 ghi nhận `finishTime = 4.950745s` nhưng đứng sau Vịt hạng 31 có `finishTime = 4.950753s`).
- **Nguyên nhân gốc rễ**: Trong hàm `update(dt)` của `index.html`:
  ```javascript
  if (justFinished.length > 0) {
    justFinished.sort((a, b) => {
      if (Math.abs(a.finishTime - b.finishTime) > 0.00001) {
        return a.finishTime - b.finishTime;
      }
      return (b.rawProgress || b.prevProgress) - (a.rawProgress || a.prevProgress);
    });
  ```
  Khi độ chênh lệch thời gian giữa hai vịt trong cùng frame nhỏ hơn $10^{-5}$ giây ($0.00001$s), thuật toán bỏ qua so sánh `finishTime` và rơi vào nhánh so sánh `rawProgress`. Sự không nhất quán này dẫn đến việc vịt chạm vạch trước bị xếp sau, vi phạm tính đơn điệu của bảng xếp hạng.
- **Kỳ vọng ở bản mới**: Thời gian về đích và thứ hạng phải luôn đơn điệu tăng dần: $T_1 \le T_2 \le \dots \le T_N$ và $Rank_i = i$.

### Finding B2: Lỗi rò rỉ tiêu điểm phím Tab vào thanh điều khiển ngầm trên Mobile (Offscreen Hidden Controls Tab Focus)
- **Triệu chứng**: Ở kích thước màn hình điện thoại (ví dụ: 390×844, 320×568), khi Bottom Sheet (`#sidebar`) đang đóng, người dùng nhấn phím Tab vẫn có thể nhảy tiêu điểm (focus) vào các phần tử ẩn bên dưới màn hình như `#btn-shuffle`, `#names-input`, `#preset-class`.
- **Nguyên nhân gốc rễ**: Giao diện chỉ ẩn sidebar bằng thuộc tính CSS `transform: translateY(100%)` mà không thiết lập `inert`, `visibility: hidden` hoặc `display: none`. Vì phần tử vẫn nằm trong Accessibility Tree và DOM tab order, tiêu điểm bàn phím bị "mất tích" vào vùng vô hình.
- **Kỳ vọng ở bản mới**: Khi Bottom Sheet đóng, phần tử chứa phải có `inert` hoặc `visibility: hidden`/`display: none` để ngăn hoàn toàn Tab focus.

### Finding B3: Thiếu phím Escape và nút đóng cho Mobile Bottom Sheet
- **Triệu chứng**: Khi mở Bottom Sheet trên mobile bằng nút "Cài đặt", phím `Escape` không đóng được sheet; không có nút đóng (X hoặc "Đóng") chuyên biệt bên trong sheet. Người dùng bị mắc kẹt nếu không biết bấm nút toggle bên ngoài.
- **Kỳ vọng ở bản mới**: Phải có nút đóng rõ ràng trong bottom sheet và hỗ trợ phím `Escape` để đóng theo chuẩn WAI-ARIA Dialog/Drawer.

### Finding B4: Vỡ bố cục trên màn hình ngang điện thoại (Short Landscape 844×390)
- **Triệu chứng**: Tại viewport 844×390 (iPhone nằm ngang), chiều rộng 844px $\ge$ 768px khiến media query `@media (max-width: 767px)` không kích hoạt. Ứng dụng chuyển sang chế độ Desktop và dựng `#sidebar` cố định bên trái. Tuy nhiên, chiều cao nội dung sidebar vượt quá 600px trong khi viewport chỉ có 390px, khiến nút "BẮT ĐẦU CUỘC ĐUA" (`#btn-start`) bị trôi xuống tọa độ $Y \approx 522px$ (nằm ngoài đáy màn hình). Một con trỏ chuột thật không thể bấm nút nếu không cuộn riêng sidebar. Trong khi đó, thanh điều khiển `#mobile-controls` vẫn xuất hiện ở đáy sân khấu, gây tranh chấp hai nút bấm chính.
- **Kỳ vọng ở bản mới**: Breakpoint thích ứng linh hoạt theo tỷ lệ khung hình và chiều cao khả dụng. Trên màn hình thấp (height $\le$ 500px), các điều khiển đua chính phải luôn nằm trong tầm nhìn mà không cần cuộn trang.

### Finding B5: Chen chúc cực hạn và thiếu khả năng phát hiện làn (Discoverability) ở 100 vịt
- **Triệu chứng**: Khi chạy danh sách 100 người, khoảng cách giữa các làn trên Canvas co cụm lại chỉ còn $\approx 6$ pixel, trong khi chiều cao thân vịt là 24px và thẻ tên là 18px. Toàn bộ 100 vịt đè chồng lên nhau thành một khối pixel không đọc được. Sân khấu Canvas không có thanh cuộn riêng hay cơ chế xem từng làn đua.
- **Kỳ vọng ở bản mới**: Giữ khả năng đua và xếp hạng đầy đủ 100 người trong bảng kết quả; trên đường đua, có làn với chiều cao tối thiểu hoặc cơ chế cuộn/theo dõi nhóm dẫn đầu (follow mode) mà không giật camera.

### Finding B6: Độ sáng nền tối (Dark Theme Luminance) của Baseline
- **Triệu chứng**: Màu nền baseline là `#03070d` (Relative Luminance $L \approx 0.002$), nền canvas `#080c14` ($L \approx 0.003$), phong cách neon/cyberpunk.
- **Kỳ vọng ở bản mới**: Chuyển đổi toàn diện sang Light Mode: màu nền tổng thể có $L > 0.5$ (ví dụ: nền ngà `#F7FAF5` có $L \approx 0.94$, panel trắng `#FFFFFF` có $L = 1.0$, đường nước `#DFF3FA` có $L \approx 0.88$), màu chữ chính có độ tương phản $\ge 4.5:1$ theo tiêu chuẩn WCAG AA.

---

## 3. Ma trận Kiểm thử Độc lập (Independent Audit Matrix)

Dưới đây là 32 tiêu chí kiểm định nghiêm ngặt được thực thi tự động trong `audit/test_light_independent.py`:

| STT | Mã kiểm thử | Nhóm danh mục | Mô tả kiểm tra | Phương pháp đo đạc & Tiêu chí Pass |
|---|---|---|---|---|
| 1 | `NET_OFFLINE_01` | Offline Safety | Không phát sinh bất kỳ HTTP request ra ngoài origin | Lắng nghe sự kiện CDP `Network.requestWillBeSent`. Tất cả request phải thuộc `http://127.0.0.1:8788` hoặc `data:`. Không có CDN, Google Fonts, hay telemetry. |
| 2 | `NET_LOCAL_02` | Offline Safety | Không chứa external CSS hay external web fonts | Quét toàn bộ thẻ `<link rel="stylesheet">` và thuộc tính CSS `@import` / `url()`. Đảm bảo font hệ thống hoặc local, tự chứa 100%. |
| 3 | `LIGHT_LUM_01` | Light Theme | Độ sáng nền trang (Body Background Luminance) | Đo màu nền tính toán `getComputedStyle(document.body).backgroundColor`. Tính Relative Luminance $L$. Yêu cầu: $L > 0.5$ (Light Mode chuẩn). |
| 4 | `LIGHT_LUM_02` | Light Theme | Độ sáng panel giao diện (Sidebar & Podium Card) | Đo màu nền tính toán của `#sidebar` và `.podium-card`. Yêu cầu: $L > 0.6$. |
| 5 | `LIGHT_CONTRAST_03` | Light Theme | Độ tương phản màu chữ chức năng (WCAG 2.1 AA) | Tính tỷ lệ tương phản $(L_1+0.05)/(L_2+0.05)$ giữa màu chữ chính và màu nền panel. Yêu cầu: Contrast Ratio $\ge 4.5:1$. |
| 6 | `LIGHT_CANVAS_04` | Light Theme | Màu nước đường đua Canvas thuộc phổ sáng | Đọc pixel trung tâm canvas bằng `ctx.getImageData()`. Tính $L$ của màu nước nền. Yêu cầu: $L > 0.5$ (không dùng nền đen/xanh đen cyberpunk). |
| 7 | `BRAND_CLEAN_05` | Light Mascot | Xóa bỏ hoàn toàn thương hiệu và nhãn Cyberpunk/Neon | Kiểm tra `document.title`, `.brand-title`, và text nội dung. Không còn chứa "NEON DUCK", "CYBER" hay "Cyberpunk". Tên ứng dụng phản ánh "Đua Vịt". |
| 8 | `PTR_DESKTOP_PRESET_01` | Real Pointer | Nhấp chuột thật vào Preset trên Desktop (1440×900) | Gửi chuỗi sự kiện CDP `mouseMoved`, `mousePressed`, `mouseReleased` tại tâm của `#preset-grand`. Xác nhận danh sách nạp đủ 16 người. |
| 9 | `PTR_DESKTOP_RACE_02` | Real Pointer | Nhấp chuột thật vào Start, Pause, Resume, Reset | Gửi CDP pointer click lần lượt vào `#btn-start`, `#btn-pause` (pause), `#btn-pause` (resume), `#btn-reset`. Kiểm tra chuyển đổi trạng thái `idle` $\to$ `racing` $\to$ `paused` $\to$ `racing` $\to$ `idle`. |
| 10 | `PTR_MODAL_CLOSE_03` | Real Pointer | Nhấp chuột thật vào nút Đóng bảng kết quả | Sau khi cuộc đua kết thúc, gửi CDP pointer click vào `#btn-close-modal`. Xác nhận modal bị ẩn (`hidden === true`) và kết quả được giữ nguyên trong bộ nhớ. |
| 11 | `PTR_MODAL_REOPEN_04` | Real Pointer | Nhấp chuột thật vào nút "Xếp hạng" để mở lại | Gửi CDP pointer click vào `#btn-results`. Xác nhận modal mở lại, hiển thị nguyên vẹn đầy đủ danh sách kết quả. |
| 12 | `PTR_MOBILE_CTRL_05` | Real Pointer | Nhấp chuột thật vào nút điều khiển Mobile (390×844) | Gửi CDP pointer click vào `#btn-mobile-start`, `#btn-mobile-pause`, `#btn-mobile-reset`. Xác minh chuyển trạng thái chính xác. |
| 13 | `A11Y_SHEET_INERT_01` | Mobile A11y | Bottom Sheet khi đóng không nhận Tab Focus | Khi `#sidebar` đóng trên mobile (không có class `open`), kiểm tra phần tử có `inert`, `visibility: hidden` hoặc `display: none`. Gọi `.focus()` vào phần tử con bên trong phải thất bại hoặc không cho phép Tab nhảy vào. |
| 14 | `A11Y_SHEET_ESC_02` | Mobile A11y | Phím Escape đóng Mobile Bottom Sheet | Mở sheet bằng `#btn-toggle-sidebar`. Phát sự kiện phím Escape qua CDP `rawKeyDown` + `keyUp`. Xác nhận sheet đóng lại (`open === false`). |
| 15 | `A11Y_SHEET_CLOSE_03` | Mobile A11y | Có nút đóng rõ ràng bên trong Mobile Bottom Sheet | Kiểm tra sự tồn tại của nút đóng trực quan trong sheet (`aria-label` đóng hoặc nút X) và xác nhận nhấp chuột vào nút sẽ đóng sheet. |
| 16 | `A11Y_MODAL_INERT_04` | Modal A11y | Modal kết quả làm vô hiệu hóa nền (Inert Background) | Khi Winner Modal mở, xác nhận `#sidebar.inert === true` và `#stage-container.inert === true`. |
| 17 | `A11Y_MODAL_ESC_05` | Modal A11y | Phím Escape đóng Modal kết quả | Phát phím Escape khi modal đang mở. Xác nhận modal đóng và tiêu điểm được trả về nút mở trước đó hoặc giao diện chính. |
| 18 | `A11Y_HIDDEN_TRAP_06` | Modal A11y | Modal khi ẩn không nhận tiêu điểm bàn phím | Khi `#winner-modal[hidden]`, đảm bảo các nút bên trong không thể nhận tiêu điểm bàn phím từ trang chính. |
| 19 | `GEO_VIEWPORT_320` | Responsive | Bố cục hình học tại màn hình 320×568 (iPhone SE) | Không có thanh cuộn ngang trang (`scrollWidth <= innerWidth`). Touch target của các nút bấm $\ge 44 \times 44$px. Các nút topbar không tràn màn hình. |
| 20 | `GEO_VIEWPORT_390` | Responsive | Bố cục hình học tại màn hình 390×844 (Mobile chuẩn) | Canvas phủ kín container, các nút điều khiển đáy nằm trọn vẹn trong viewport (`bottom <= innerHeight`). Không chồng chéo thanh HUD. |
| 21 | `GEO_VIEWPORT_768` | Responsive | Bố cục hình học tại màn hình 768×1024 (Tablet dọc) | Không vỡ layout giữa sidebar và stage. Nút bấm và canvas hiển thị cân đối. |
| 22 | `GEO_VIEWPORT_1440` | Responsive | Bố cục hình học tại màn hình 1440×900 (Desktop chuẩn) | Sidebar và Stage song song. Nút Bắt đầu nằm trong tầm nhìn trực tiếp không bị đẩy khỏi màn hình. |
| 23 | `GEO_VIEWPORT_844_LAND` | Responsive | Bố cục tại màn hình ngang thấp 844×390 (Landscape Mobile) | Các điều khiển cuộc đua cốt lõi (Start/Pause/Reset) phải tương tác được ngay, không bị tràn màn hình hay bị sidebar che khuất. |
| 24 | `PODIUM_TWO_RACERS_01` | Podium Logic | Cuộc đua chỉ có 2 người không tạo người thứ 3 | Thiết lập danh sách 2 người. Đua kết thúc: Modal hiển thị Quán quân và Hạng Nhì; phần tử Hạng Ba bị ẩn hoàn toàn (`hidden === true` hoặc không xuất hiện trong DOM). |
| 25 | `VALID_EMPTY_ONE_02` | Input Guard | Không cho phép bắt đầu khi danh sách có 0 hoặc 1 người | Khi danh sách rỗng hoặc chỉ có 1 tên: nút Start bị `disabled`. Gọi hàm `startRace()` không kích hoạt trạng thái `racing`. |
| 26 | `GUARD_ACTIVE_PAUSED_03` | State Machine | Khóa nhập liệu và presets khi đang đua hoặc tạm dừng | Khi đang đua (`racing`) hoặc tạm dừng (`paused`), danh sách tên và các nút preset bị vô hiệu hóa; không thể xóa hoặc chèn thí sinh giữa chừng. |
| 27 | `GUARD_RESET_CLEANUP_04` | Lifecycle | Reset hủy toàn bộ timeout và callback kết quả cũ | Gọi `startRace()`, mô phỏng hoàn tất, ngay lập tức gọi `resetRace()` trong khoảng chờ 800ms. Đợi 1000ms: Modal kết quả KHÔNG được phép tự động bật lên. |
| 28 | `DATA_UNICODE_LONG_01` | Data Safety | Tên tiếng Việt dài (>50 ký tự) không vỡ bảng kết quả | Nạp các tên tiếng Việt rất dài có dấu. Bảng kết quả tự co dãn, word-break hoặc hiển thị thanh cuộn nội bộ; modal không tràn ra ngoài viewport. |
| 29 | `DATA_XSS_LITERAL_02` | Data Safety | Kháng mã độc XSS trong tên thí sinh | Nạp tên chứa `<img src=x onerror=...><script>...`. Xác minh không có script/event nào bị thực thi; nội dung render dưới dạng văn bản thuần. |
| 30 | `SCALE_ROSTER_UNIQUE_01` | Scale Roster | Roster 2, 8, 16, 32, 100 vịt: tất cả về đích với ID duy nhất | Chạy đua cho từng quy mô. Đảm bảo mọi thí sinh đều về đích, bảng kết quả có đủ số dòng tương ứng và mỗi dòng gắn `dataset.participantId` duy nhất. |
| 31 | `SCALE_TIME_MONOTONIC_02` | Engine Fairness | Tính đơn điệu nghiêm ngặt của thời gian và thứ hạng | Duyệt qua danh sách kết quả ở quy mô 100 người: thứ hạng phải liên tục $1, 2, \dots, 100$ và thời gian $T_i \ge T_{i-1}$ cho mọi $i \ge 2$. |
| 32 | `SCALE_SCROLL_ROW100_03` | Scale Roster | Khả năng cuộn và tiếp cận dòng thứ 100 trong bảng kết quả | Với cuộc đua 100 người, container cuộn kết quả `.results-scroll` phải cho phép cuộn; khi cuộn xuống đáy, dòng thứ 100 phải hiển thị trọn vẹn trong tầm nhìn. |

---

## 4. Hướng dẫn Thực thi Kiểm thử (Operational Instructions)

Bài kiểm thử độc lập được đóng gói duy nhất trong file Python `audit/test_light_independent.py`.

### 4.1. Môi trường yêu cầu
- Python 3.10+
- Gói `websockets` (đã có sẵn trong hệ thống)
- Trình duyệt `chromium` cài đặt trên máy
- Máy chủ web cục bộ đang phục vụ thư mục dự án tại cổng `8788`:
  ```bash
  # Kiểm tra trạng thái máy chủ
  curl -I http://127.0.0.1:8788/index.html
  ```

### 4.2. Chế độ 1: Rà soát Baseline (Baseline Gap Analysis)
Chạy bộ kiểm thử với cờ `--baseline` để ghi nhận các điểm đạt và các lỗ hổng đã được xác định trước của phiên bản Cyberpunk hiện tại:
```bash
python3 audit/test_light_independent.py --baseline
```
- **Ý nghĩa**: Kiểm tra tất cả 32 tiêu chí. Các tiêu chí thuộc về Light Mode mới (Luminance sáng, tên Đua Vịt, nút đóng Bottom Sheet) sẽ được gắn cờ `BASELINE_EXPECTED_FAIL`, còn các tiêu chí bất biến (an toàn offline, guard tạm dừng, ID duy nhất, không XSS) phải vượt qua. Mã thoát: `0` nếu kết quả khớp chính xác với dự báo baseline.
- **Tập tin bằng chứng xuất ra**: `audit/light-audit-evidence.json`.

### 4.3. Chế độ 2: Nghiệm thu Toàn diện sau khi Cải tiến (Post-Builder Full Audit)
Sau khi nhóm lập trình hoàn tất việc triển khai giao diện sáng và linh vật trong `index.html`, chạy lệnh nghiệm thu chuẩn:
```bash
python3 audit/test_light_independent.py
```
- **Ý nghĩa**: Chạy chế độ kiểm định nghiêm ngặt. Toàn bộ 32 tiêu chí (bao gồm cả các yêu cầu về độ sáng, tỷ lệ tương phản, quản lý focus bottom sheet, phím Escape, tính đơn điệu của 100 vịt và khả năng tiếp cận) BẮT BUỘC phải đạt `PASS`.
- **Mã thoát (Exit Code)**:
  - `0`: Tất cả tiêu chí kiểm định đều đạt (Tự động sẵn sàng bàn giao).
  - `1`: Còn ít nhất 1 tiêu chí thất bại (Có danh sách lỗi chi tiết trong console và JSON).

### 4.4. Các tùy chọn bổ sung
- Chạy với URL tùy chỉnh:
  ```bash
  python3 audit/test_light_independent.py --url http://127.0.0.1:8788/index.html
  ```
- Xuất file bằng chứng đến vị trí khác:
  ```bash
  python3 audit/test_light_independent.py --output audit/custom-evidence.json
  ```
- Chạy chế độ hiển thị chi tiết (verbose):
  ```bash
  python3 audit/test_light_independent.py --verbose
  ```
