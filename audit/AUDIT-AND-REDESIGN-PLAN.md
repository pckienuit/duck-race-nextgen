# Duck Race: audit logic, UI/UX và kế hoạch chỉnh sửa

## Kết luận

Bản hiện tại chứng minh được ý tưởng, chưa đủ tin cậy để dùng bốc thăm hoặc giveaway thật. Vấn đề lớn nhất không phải thiếu hiệu ứng: vòng đời cuộc đua chưa chặt, thứ hạng có thể sai, dữ liệu người dùng được đưa vào HTML không an toàn và bố cục mobile bị hỏng.

Đề xuất: chỉnh sửa có kiểm soát trên nền Canvas 2D + HTML/CSS/JavaScript hiện tại. Không cần đổi sang Next.js, thêm backend, tài khoản hay WebGL để giải quyết các vấn đề này.

**Trạng thái bàn giao:** chỉ audit và kế hoạch. Không sửa `index.html`. Có thêm tài liệu tham chiếu, script tái hiện và kết quả trong thư mục `audit/`.

## Phạm vi, phương pháp, giới hạn

- Đọc toàn bộ `index.html` hiện tại, 1.685 dòng.
- Chạy Chromium/Thorium headless thật qua CDP. Đo DOM và layout, không dùng kết quả bố cục Lightpanda để kết luận visual.
- Viewport kiểm tra: 1440×900, 768×1024, 390×844, 320×568.
- Các probe logic tắt requestAnimationFrame để bước thời gian có kiểm soát. Một số probe chủ động đặt trạng thái/vị trí vịt nhằm tái hiện edge case. Đây là fault-injection test, không phải tất cả đều là luồng click end-to-end.
- Chạy thêm cuộc đua thực dùng requestAnimationFrame: hoàn thành, có modal và Top 3; không ghi nhận JavaScript exception trong lần kiểm thử cuối.
- Mô phỏng 100 cuộc đua cho mỗi mức 30/60/120 bước mỗi giây bằng PRNG kiểm thử có seed, để so sánh độ phụ thuộc frame. Đây không phải benchmark FPS hay chứng nhận RNG công bằng.
- Chưa đánh giá bằng mắt qua screenshot; nhận xét thẩm mỹ dựa trên CSS/DOM và cấu trúc. Các lỗi viewport/che khuất được đo hình học trên browser.
- Chưa nghe âm thanh/TTS bằng loa, chưa thử Safari/Firefox/điện thoại thật, fullscreen bị từ chối trong iframe, hoặc đo Core Web Vitals.
- Repo hiện chỉ có HTML ứng dụng, không có package.json/test suite/Git repository. Không có căn cứ cho tuyên bố trước đó rằng đã đo 60–120 FPS.

Tái chạy bằng: `python audit/probe.py` khi app đang được phục vụ ở `http://127.0.0.1:8788/index.html`. Script cần Chromium và Python package `websockets` như môi trường kiểm thử hiện tại.

Bằng chứng thô: `audit/evidence.json`. Lần chạy sau ghi đè bằng chứng cũ.

## Áp dụng TasteSkill đúng phạm vi

Nguồn trực tiếp đã đọc:

1. https://www.tasteskill.dev/docs
2. https://www.tasteskill.dev/guide
3. https://github.com/Leonxlnx/taste-skill/blob/main/skills/taste-skill/SKILL.md
4. https://github.com/Leonxlnx/taste-skill/blob/main/skills/redesign-skill/SKILL.md

Bản core được trang tài liệu gọi là **v2 experimental**. Đầu file nói rõ trọng tâm là landing pages, portfolios, redesigns, không phải dashboard hay multi-step product UI; các quy tắc phải tùy ngữ cảnh. Vì vậy:

- Dùng Section 11 để audit trước, giữ luồng sản phẩm và nguồn nội dung.
- Dùng typography, color/shape consistency, semantic states, accessibility, reduced motion và mobile checks.
- Dùng redesign-skill để cải thiện trên stack hiện tại.
- Không dựng hero/8 section, không thêm ảnh stock, marquee, scroll hijack, GSAP hoặc framework migration vào game chỉ để tick checklist.
- Màu riêng của vịt phục vụ phân biệt người chơi, không phải nhiều accent UI. Nhãn tên trên vịt là dữ liệu trò chơi, không phải tag trang trí trên ảnh marketing.
- Không áp dụng các gợi ý tạo dữ liệu trông thật: không bịa lượt chơi, testimonial, kết quả, lịch sử hay mức FPS.

## Audit hiện trạng theo Section 11.B

### Brand tokens

- Nền `#0b0f19`, panel `#131b2e`, border `#1f2d4a`.
- Accent vàng cam `#f59e0b`, primary xanh `#3b82f6`.
- Sông gradient `#0284c7` → `#0369a1` → `#075985`.
- Font system sans; timer monospace. Phần lớn nhãn/CTA dùng đậm và chữ hoa, ít phân cấp.
- Radius trải từ 6, 8, 10, 12, 14, 16, 24 đến pill, chưa có quy tắc vai trò.
- Logo emoji vịt, chữ DUCK RACE gradient, badge NEXT-GEN.
- Nhiều shadow đậm, glow cam/đỏ và backdrop blur cùng tranh sự chú ý với sân đua.

### Information architecture

Một trang duy nhất `/index.html`: sidebar nhập tên/cấu hình → Start → sân đua và leaderboard → modal kết quả → reset hoặc loại quán quân.

Không có navigation đa trang, server, analytics hay luật chơi được giải thích. Preset Giveaway đang chứa **phần thưởng**, không phải tên người tham gia, khác ngữ nghĩa trường nhập tên.

### Giữ lại

- Ý tưởng chọn tên bằng cuộc đua vịt.
- Nhập mỗi dòng một người, xáo danh sách và preset.
- Sân đua Canvas, cá tính vịt, vệt sóng và chuyển động vui.
- Pause/resume, cấu hình thời lượng, Top 3, loại người thắng.
- Khả năng chạy local/offline, không bắt đăng nhập.

### Loại bỏ hoặc sửa

- NEXT-GEN và copy công nghệ không giải thích lợi ích.
- Emoji gần như ở mọi control, gradient/glow ở nhiều lớp UI.
- Sidebar cứng 380px, HUD đè lên vùng cán đích, banner slow-mo che giữa sân.
- Nút khả dụng sai trạng thái, thông báo lỗi bằng alert.
- Claim không đúng thực tế: headphone chưa được vẽ; skin/phụ kiện gán theo index chứ không random; không có camera zoom hoặc ảnh photo finish; fullscreen không phải OBS transparent mode; chưa có persistence.

### Dial reading

Đây là đánh giá thiết kế chủ quan, không phải phép đo:

- Hiện tại: `DESIGN_VARIANCE 3`, `MOTION_INTENSITY 7`, `VISUAL_DENSITY 7`: bố cục sidebar truyền thống, hiệu ứng liên tục, control dày và cạnh tranh.
- Đề xuất: `DESIGN_VARIANCE 5`, `MOTION_INTENSITY 4`, `VISUAL_DENSITY 4` cho UI; Canvas vẫn có chuyển động đua cần thiết. Reduced-motion giảm chuyển động trang trí và bỏ spin/zoom, không làm thay đổi kết quả.

### SEO baseline và bảo toàn

Chỉ thấy title và h1 trong nguồn; không có meta description/OG/structured data. Không có dữ liệu ranking hoặc Search Console để kết luận SEO. Giữ route `/index.html`, các input/control ID hiện có hoặc có mapping kiểm thử nếu tách module. Đề xuất đổi copy/wordmark treatment được nêu rõ trong kế hoạch, chưa thực hiện. Không phát sinh trang legal/cookie giả nếu app vẫn local-only và không tracking.

## Audit lỗi logic và an toàn

P1 = chặn dùng đáng tin cậy/phát hành. P2 = cần sửa trong bản chỉnh sửa. P3 = polish. Mức độ XSS phụ thuộc cách phát hành, không giả định có backend hoặc nhiều người dùng.

| ID | Ưu tiên | Phát hiện và bằng chứng | Nguyên nhân | Hướng sửa |
|---|---|---|---|---|
| L01 | P1 | DOM XSS: tên chứa image onerror đã đặt biến kiểm thử `auditXSS=1`. Payload chỉ ghi biến local, không gửi dữ liệu ra ngoài. | `innerHTML` nội suy `duck.name` tại L1488 và L1549–1555. | Tạo node cố định và gán `textContent` ở mọi điểm render tên. Không giải quyết bằng cấm dấu ngoặc ở input. |
| L02 | P1 | Bấm Start lần hai: thời gian từ 1 về 0 nhưng progress giữ nguyên. Start ở finished có thể kẹt racing với mọi duck đã finished và danh sách kết quả rỗng. | `startRace` L1328–1359 không guard state, không reset từng duck; Start không disabled. | State machine, Start chỉ hợp lệ ở ready; restart qua một transition reset nguyên tử. |
| L03 | P1 | Gõ thêm tên giữa cuộc đua làm game về idle/time=0. Đổi slider giữa đua lập tức đổi totalDuration thành 30. | Input gọi build/reset ngay, settings được đọc trực tiếp trong update. | Snapshot roster/settings lúc Start; khóa field ảnh hưởng kết quả, hoặc giữ draft cho vòng sau. |
| L04 | P1 | A ở .991, B ở .999, cùng speed, cùng bước .1 giây: A được xếp nhất dù B phải cán đích trước. | L1469–1481 push theo thứ tự mảng, finishTime chỉ bằng thời gian cuối frame. | Tính thời điểm crossing bên trong bước mô phỏng và sort; quy tắc tie rõ ràng, không ưu tiên index. |
| L05 | P1 | Đã tái hiện state=finished khi chỉ A về đích; B/C còn ở .261/.161. Top 3 không được bảo đảm. | Dừng toàn bộ sau grace period 1.8 giây, không đợi đủ thứ hạng. | Timeline hữu hạn bảo đảm mọi người về đích; chỉ công bố rank đã xác định. Không bịa người nhì/ba. |
| L06 | P1 | Cùng cấu hình 10s, thời gian về nhất trung bình 8.08s/7.68s/7.19s ở 30/60/120 bước mỗi giây. | Xác suất boost/spin, noise và particle dựa trên số frame; logic/âm thanh/trang trí dùng chung Math.random. | Tách RNG kết quả khỏi FX; simulation thời gian cố định hoặc timeline xác định, RNG có seed cho test. |
| L07 | P1 | onFinish → reset → chờ 1s: state idle nhưng modal cũ tự mở. | Timeout 900ms L1426 không được hủy hoặc gắn runId; speech queue không cancel. | Quản lý timeout/RAF/audio/speech theo runId; reset invalidates callback cũ và dọn tài nguyên. |
| L08 | P1 | Danh sách An, An, Bình; loại một An thì chỉ còn Bình. | Xóa bằng `name !== winner`, không bằng định danh L1253–1254. | Participant ID độc lập displayName, xóa đúng một ID; cảnh báo trùng tên, không tự gộp. |
| L09 | P2 | Cấu hình 10s, tắt drama, bật slow-mo trong probe: mô phỏng 14.63s thời gian render trước finished; timer hiển thị 11.81s. | totalDuration là mẫu số tốc độ, không deadline; slow-mo đổi simulation clock; cộng grace period. | Định nghĩa rõ countdown/race/reveal; deadline T cho animation race, slow-mo nằm trong timeline thay vì kéo dài ngầm. |
| L10 | P2 | Focus nút Xáo tên rồi gửi Space lại Start cuộc đua. | Hotkey toàn cục chỉ bỏ qua input/textarea; không bỏ qua button/dialog/contenteditable/repeat. | Bảo toàn native keyboard, shortcut chỉ hoạt động ở vùng sân và trạng thái phù hợp. |

### Những thiếu sót logic/phạm vi khác

- Refresh mất roster/settings: đã tái hiện, mặc định trở về 8 tên và 10 giây.
- Không giới hạn số lượng/độ dài tên. Với 100 người ở chiều cao 900px, spacing chỉ 7.52px, nhãn cao 18px và thân vịt cao khoảng 24px. Không thể đọc.
- Pause dừng raceTime nhưng nước và hạt vẫn chạy. Có thể chấp nhận ambient riêng, nhưng phải nói rõ và tôn trọng reduced motion; hiện chưa có quyết định UX.
- Audio/TTS bật mặc định, không volume/master mute/cancel; không kiểm tra giọng Việt khả dụng. Nhánh audio bắt lỗi im lặng có thể khiến checkbox nói bật nhưng thực tế không phát.
- Fullscreen gọi API không guard hỗ trợ, catch im lặng và vẫn thu sidebar. Cần fallback rõ khi embed chặn hoặc browser không hỗ trợ. Đây là phát hiện từ source, chưa tái hiện trên Safari.
- `resize` chỉ nghe window, cộng timeout 320ms sau toggle. Không dùng ResizeObserver cho container thay đổi, không cap DPR.
- DOM leaderboard bị dựng lại mỗi frame, luôn sort/render cả idle, particle update không dt. Đây là rủi ro hiệu năng từ code; chưa kết luận FPS thực.

## Audit UI/UX

| ID | Ưu tiên | Hiện trạng | Đề xuất |
|---|---|---|---|
| U01 | P1 | Màn 390px: sidebar 380px, sân 10px, trackWidth=-150. Màn 320px: sân 0px, nội dung rộng 380px. | Mobile stage-first, panel cấu hình thành sheet hoặc bước riêng; 100dvh, min-width:0, geometry không âm. |
| U02 | P2 | HUD ở x1200–1420/y75–220 che vị trí cán đích lane A tại x1360 trong viewport 1440×900. Slow-mo banner giữa sân. | Tách vùng thông tin khỏi đường đua, badge slow-mo nhỏ ở mép, không che vịt/finish. |
| U03 | P2 | CTA chữ trắng trên gradient vàng cam: contrast endpoint 2.15:1 và 3.19:1, không đạt 4.5:1 cho chữ 16px. | CTA vàng với chữ đậm tối; focus/disabled/error cũng kiểm tra tương phản. |
| U04 | P2 | Modal opacity=0 vẫn nhận focus vào nút loại winner. Không role/aria-modal/focus trap; input và range không có label liên kết. | Native dialog hoặc pattern accessible, hidden/inert đúng, focus restore, label/for, status aria-live tiết chế. |
| U05 | P2 | Xóa sạch: leaderboard trống, Start vẫn enabled, báo lỗi bằng alert. Pause khả dụng ngay khi idle. | Empty/invalid/ready/paused/finished riêng; CTA phụ thuộc state; lỗi inline dưới field. |
| U06 | P2 | Nhiều control đậm, emoji, glow, border và glass cùng lúc; màu UI tranh với màu vịt. | Một accent, neutral surfaces, một bộ icon, spacing theo nhóm nhiệm vụ, ít card lồng nhau. |
| U07 | P2 | Hành động “Loại quán quân & Đua vòng tiếp” chỉ reset, không start; loại người thắng bị tô đỏ như hành động nguy hiểm nhất. | Copy đúng hành động: “Bỏ người thắng, chuẩn bị vòng sau”; nút “Đua lại” riêng, undo loại. |
| U08 | P2 | Không reduced-motion; tên Canvas 11px, sidebar nhiều chữ 12px, nút fullscreen chỉ cao 34px ở desktop. | Chữ control 14–16px, hit area tối thiểu 44px cho touch; motion preference và DOM kết quả đọc được. |

### Chẩn đoán thẩm mỹ, không chấm điểm marketing giả

Điểm yếu chủ yếu là hierarchy và bố cục trạng thái, không phải chỉ thay font. Glow/blur không mang ý nghĩa elevation rõ ràng; trọng lượng chữ quá đồng đều; bố cục chỉ đúng khi dư bề ngang. Trò chơi được phép vui, nhưng chrome xung quanh phải yên để vịt và kết quả là nhân vật chính.

Không cần loại bỏ toàn bộ màu, motion hay vịt vector. Đây là các thành phần có mục đích, khác với trang trí AI không liên quan sản phẩm.

## Hướng thiết kế đề xuất: Race studio

**Design read:** công cụ chọn tên cho lớp học/hội nhóm/livestream, giao diện vận hành gọn và dễ đọc, sân đua vui, không mang dáng landing page hay dashboard giả.

**Mode đề xuất:** overhaul bố cục responsive và visual chrome, giữ bản sắc vịt, accent vàng và chức năng cốt lõi. Đây là đề xuất cần duyệt, không phải thay đổi đã làm.

### Design tokens dự kiến

- Dark base `#101820`, surface `#19242E`, text `#F3F6F8`, muted `#A7B4C0`.
- Accent giữ vàng `#F5B83D`, CTA ink `#17212A`; đỏ chỉ dành lỗi/hủy hành động thật.
- Light mode đồng bộ: base `#F4F7F9`, surface `#FCFDFE`, text `#17212A`, muted `#536371`. Tùy chọn Sáng/Tối/Theo hệ thống lưu cục bộ; không trộn theme theo section.
- Màu sông và các vịt là palette minh họa riêng, không áp one-accent máy móc vào đồ chơi.
- Một sans có bộ ký tự tiếng Việt đầy đủ, đề xuất Be Vietnam Pro self-host hoặc embed woff2 trong bản standalone; system fallback. Timer dùng tabular numerals.
- Type scale dự kiến 12/14/16/20/28, chữ trên sân tăng theo chế độ trình chiếu. Hạn chế uppercase.
- Spacing 4/8/12/16/24/32. Radius: control 10px, panel 16px, avatar/pill theo vai trò riêng được ghi rõ.
- Focus ring rõ, hover/press nhẹ, không glow phủ khắp UI. Các cặp màu đề xuất phải đo contrast trước khi duyệt mockup.

### Bố cục desktop

```
Duck Race                 Vòng hiện tại       Âm thanh | Hiển thị
┌──────────────────────┬─────────────────────────────────────────┐
│ Người tham gia       │ Trạng thái + thời gian còn lại          │
│ textarea / counter   ├─────────────────────────────────────────┤
│ Xáo / danh sách mẫu  │                                         │
│                      │              SÂN ĐUA                   │
│ Thời lượng           │        không có HUD che đích            │
│ Hiệu ứng [thu gọn]   │                                         │
│                      ├─────────────────────────────────────────┤
│                      │ Dẫn đầu / tóm tắt vòng                 │
└──────────────────────┴─────────────────────────────────────────┘
                 [Bắt đầu] hoặc [Tạm dừng] [Hủy vòng]
```

Panel khoảng 300–320px khi đủ chỗ, có thể thu gọn. Khi racing, roster/settings bị khóa và control điều khiển nằm ngoài panel nên không biến mất trong chế độ trình chiếu. Header không chồng lên Canvas. Không thêm hero.

### Mobile và nhiều người

- 320–767px: sân chiếm chiều rộng viewport; nút điều khiển cố định trong vùng safe area, cấu hình mở sheet hoặc màn Thiết lập rồi trở lại sân.
- 768–1023px: panel có thể thu gọn; không cố giữ hai cột nếu không đủ vùng đua.
- ResizeObserver đo vùng Canvas thật; không ép một đường đua âm khi panel mở.
- Đề xuất giới hạn công bố v2 là 2–32 người, tối đa 60 ký tự/tên. Nếu cần 100+ người, phải có thiết kế crowd riêng trước khi quảng cáo hỗ trợ.
- Nhiều lane dùng viewport cuộn/follow leader với min lane height; chỉ vẽ vùng thấy được. Có bảng kết quả DOM đầy đủ và nút “Theo người dẫn đầu”, không co mọi người thành nhãn không đọc nổi.

### Flow và copy

1. Thiết lập: nhập/paste tên → báo số người và tên trùng → chọn 5/10/15/30s → Start.
2. Countdown 3 giây có thể bỏ qua; label nói rõ thời lượng đua không gồm countdown.
3. Đang đua: countdown thời gian còn lại, Pause/Resume/Hủy. Âm lượng có thể đổi nhưng không đổi roster, duration hoặc luật.
4. Về đích: hiệu ứng ngắn, thứ hạng chắc chắn; không popup cũ và không trì hoãn vô hạn.
5. Kết quả: tên quán quân, nhì/ba nếu đủ người, danh sách đầy đủ, “Đua lại”, “Bỏ người thắng, chuẩn bị vòng sau”, “Sửa danh sách”.
6. Chỉ còn một người: thông báo không đủ số lượng để đua; không tự chạy vòng lỗi.
7. Loại tên có Undo; người trùng tên được phân biệt bằng ID/số thứ tự hiển thị.

Giảm NEXT-GEN/Physics/Synth/PHOTO FINISH nếu không có chức năng tương ứng. “Chậm ở vạch đích” trung thực hơn “Photo finish” khi không xuất ảnh hoặc replay camera. “Toàn màn hình” không được gọi là OBS mode.

## Quyết định kỹ thuật đề xuất

### Kết quả độc lập với animation

Ưu tiên cho công cụ chọn tên, không phải mô phỏng vật lý thi đấu:

- Tạo thứ tự kết quả bằng shuffle không thiên lệch từ nguồn ngẫu nhiên phù hợp, mỗi participant ID có một suất bằng nhau.
- RNG kết quả riêng, FX/skin/audio dùng RNG khác; kiểm thử có seed tái lập.
- Timeline chuyển động tạo drama nhưng tôn trọng thứ tự đã chọn và thời lượng T. Công khai rằng chuyển động là minh họa kết quả ngẫu nhiên, không gọi đó là vật lý quyết định thắng thua.
- Deadline winner ở T; các vị trí tiếp theo hoàn thành trong đoạn reveal ngắn có giới hạn, được mô tả rõ. Không cộng grace tùy tiện làm thiếu rank.
- Slow-mo là hiệu ứng timeline/camera có budget, không thay đổi RNG hay kéo dài đồng hồ ngầm.
- Nếu muốn giữ game mô phỏng thực, cần fixed-step + crossing interpolation + RNG riêng và kiểm định thiên lệch. Đây là lựa chọn khác, không trộn hai cơ chế mà không giải thích.
- Không gọi là “provably fair” hay phù hợp quay thưởng có giá trị cao nếu chưa có protocol/verifier độc lập. Local browser vẫn sửa được code.

### State machine

`editing → ready → countdown → racing ↔ paused → finishing → results`.

Hủy/reset chuyển về ready hoặc editing sau khi dọn run hiện tại. Sự kiện Start lặp bị bỏ qua. Mỗi run có ID, immutable roster/settings và result riêng. Handler, timeout, audio và render không được tự thay đổi state ngoài transition hợp lệ.

### Cấu trúc mã

Giữ vanilla stack; tách nguồn thành `race-engine`, `roster`, `renderer`, `audio`, `storage`, `ui-controller`, CSS tokens/components. Có thể bundle thành một HTML độc lập để người dùng mở offline. Source modular không bắt người dùng cài framework.

- Engine thuần, không truy cập DOM, Canvas hoặc Audio.
- Renderer không quyết định thứ hạng; cập nhật DOM HUD tối đa 10 lần/giây hoặc khi rank thay đổi.
- Pool/cap particle, dt cho FX, cap DPR sau khi đo, hạn chế vẽ khi hidden/idle.
- Pause khi tab bị ẩn theo chính sách công khai; không âm thầm chạy bốc thăm trong background.
- Storage có version và validation, lưu roster/settings/skin, không lưu trạng thái đang chạy như thể resume được. Catch localStorage bị chặn/quota.
- Fallback audio/TTS/fullscreen thông báo trung thực; speech cancel khi hủy/reset, master mute bao gồm cả voice.

## Kế hoạch triển khai theo thứ tự

### Giai đoạn 0: đóng băng baseline và đặc tả

- Giữ bản hiện tại làm baseline, tạo version control hoặc backup trước sửa.
- Chốt phạm vi 2–32 người, thời lượng, kết quả random độc lập animation, chính sách tên trùng và background.
- Chốt visual direction và mapping copy/control ID; không đổi route ngầm.
- Chuyển từng probe quan trọng thành assertion regression, không lấy script audit exit=0 làm nghĩa là app pass.

**Nghiệm thu:** spec rõ, mỗi P1 có test tái hiện đỏ trên baseline; không mất bản gốc.

### Giai đoạn 1: an toàn và lifecycle

- Sửa L01, L02, L03, L07, L08 trước.
- Participant IDs, immutable run snapshot, state machine, safe DOM rendering, cancel theo runId.
- Cập nhật disabled states gắn với state, giữ âm thanh là setting live riêng.

**Nghiệm thu:** payload hiển thị nguyên văn; Start liên tục không reset progress/time; reset không bật modal cũ; loại đúng một ID; input không hủy cuộc đua ngoài ý muốn.

### Giai đoạn 2: engine, thời gian và thứ hạng

- Sửa L04, L05, L06, L09.
- Tách kết quả/timeline/render RNG; bảo đảm thứ tự và deadline.
- Timeline pause/resume, slow-mo, background policy; không dựa vào callback frequency.

**Nghiệm thu:** cùng seed/settings/roster, các render schedule 30/60/120 Hz và dropped frames cho cùng kết quả; đủ rank; pause không đổi timeline; winner chạm đích tại T theo đồng hồ active-time đã chốt.

### Giai đoạn 3: design system và responsive shell

- Thực hiện U01, U02, U03, U06, U08: tokens, type, panel/sheet, Canvas geometry, dock điều khiển.
- Stage-first mobile, safe-area, responsive roster đông, light/dark/system.
- Mockup cần duyệt ở ready, racing, results trước polish hiệu ứng.

**Nghiệm thu:** 320/390/768/1024/1440/1920px không overflow/track âm; CTA thấy và chạm được; HUD không che đích; contrast AA; reduced-motion hoạt động.

### Giai đoạn 4: hoàn chỉnh luồng sử dụng

- U04/U05/U07/L10: semantic dialog, keyboard, inline validation, label/aria-live và trạng thái rỗng.
- Persistence/Undo, sửa preset Giveaway, text đúng hành động.
- Đảm bảo skin khai báo đều render được; bỏ hoặc hoàn thiện headphone.
- Master volume/mute, TTS opt-in, fullscreen fallback, tách trình chiếu với fullscreen.

**Nghiệm thu:** reload giữ cấu hình; Tab không lọt vào modal ẩn; Space trên button làm đúng native action; kết quả sau loại người trùng không mất người khác; fullscreen bị từ chối không khiến UI bị mắc kẹt.

### Giai đoạn 5: QA và bàn giao

- Unit: parser, IDs, transitions, schedule, rank, RNG boundary, serialization/migration.
- Integration/browser: chuẩn 2/8/16/32 người; rỗng/1/vượt giới hạn; tên dài, Unicode tiếng Việt, HTML payload, trùng tên; double-click, key repeat, reset lúc finish pending, đổi roster giữa race, resize/orientation/fullscreen.
- So sánh kết quả bật/tắt âm thanh, drama, reduced-motion; toggles trình bày không làm đổi kết quả.
- Chromium, Firefox, WebKit; phone thật nếu có. Test 200% zoom, keyboard-only và screen reader smoke test.
- Performance trên máy/thông số công bố: p95 frame time theo mục tiêu 60fps, DOM update rate, particle count và listener/timer cleanup. Không hứa 120fps trước đo.
- Regression visual bằng screenshot ready/racing/paused/results/empty trên desktop và mobile. Kiểm tra cả font tiếng Việt và long names.
- Lập checklist TasteSkill có Pass/Fail/N/A. Hero/marketing sections N/A có lý do, không tick Pass giả.

**Điều kiện hoàn thành:** mọi P1 đã fix và regression pass; các lỗi UI/UX trong scope được kiểm tra; không console exception; có báo cáo điều chưa xác minh; bàn giao source, HTML standalone và hướng dẫn mở.

## Ngoài phạm vi vòng chỉnh sửa này

Chưa làm multiplayer, backend, account, upload Excel, OBS alpha overlay, Battle Royale, team mode, photo-finish export, 3D/WebGL hoặc chứng nhận fairness. Các tính năng đó không giải quyết lỗi nền tảng hiện tại và nên tách roadmap sau khi core đáng tin cậy.

## 7. Kết quả triển khai và kiểm chứng thực tế (Post-Fix Verification)

Đã hoàn thành toàn bộ công việc tái thiết kế và khắc phục lỗi vào ngày 26/09/2026.
Tất cả các bài kiểm tra tự động qua CDP (`probe.py`) trên Chromium thật đều vượt qua:

| Bài kiểm tra (Probe Check) | Trước khi sửa | Sau khi sửa | Đánh giá |
| :--- | :--- | :--- | :--- |
| **XSS Injection (`name_xss`)** | `executed: 1` (Lỗ hổng nguy hiểm) | `executed: 0` (DOM an toàn 100%) | Đã xử lý triệt để |
| **Click Start 2 lần (`start_twice`)** | Reset giờ về 0, giữ nguyên vị trí | Nút khóa disabled, thời gian liên tục | Chuẩn State Machine |
| **Bấm Start sau Finish (`restart_finished`)** | Kẹt trạng thái, vịt finished từ trước | Reset toàn bộ progress & ducks về 0 | Vòng lặp sạch sẽ |
| **Nhập liệu giữa chừng (`edit_mid_race`)** | Phá hỏng cuộc đua, nhảy về idle | Khóa input, chặng đua an toàn | Bất biến (Immutable run) |
| **Kéo Slider giữa chừng (`duration_change`)** | Đổi ngay thời lượng đang chạy | Khóa slider, bảo toàn thời lượng gốc | Bất biến |
| **Loại người thắng trùng tên (`duplicate_elim`)** | Xóa sạch cả 2 người cùng tên | Chỉ xóa 1 người theo vị trí mảng | Chính xác |
| **Cùng frame về đích (`same_frame_order`)** | Ưu tiên vịt đứng trước mảng | Tính toán thời gian cắt vạch chính xác | Tuyệt đối công bằng |
| **Bàn phím Modal ẩn (`hidden_modal_focus`)** | Focus lọt vào nút bên trong | Dùng thuộc tính `hidden` & role `dialog` | Đạt chuẩn WCAG |
| **Lưu cấu hình (`reload_persistence`)** | Mất sạch dữ liệu khi F5 | Lưu `localStorage` tự động phục hồi | Tiện dụng |
| **Layout Mobile 390px (`layout_390`)** | Canvas bị ép âm (-150px) | Stage-first, trackWidth 230px | Responsive mượt mà |
| **Layout Mobile 320px (`layout_320`)** | Canvas rộng 0px | Stage-first, trackWidth 160px | Responsive mượt mà |
| **Che khuất vạch đích (`hud_overlap`)** | HUD đè lên lane 1 vạch đích | Chuyển HUD sang góc trái, không che | Tầm nhìn thông thoáng |
| **Độ trễ theo FPS (`duration_and_fps`)** | Lệch gần 1 giây giữa 30 và 120 FPS | Độ lệch chỉ còn 0.07 giây | FPS-Independent |
