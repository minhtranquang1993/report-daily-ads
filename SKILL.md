---
inclusion: manual
name: reports
description: >
  Lọc báo cáo Chi phí | Reach | Impression | Click | Tin nhắn từ file/ảnh Facebook Ads, Google Ads,
  TikTok Ads, GPT Ads, map tên campaign theo bảng chuẩn của từng PART (QH, DND, ...), rồi tạo PROMPT
  để dán vào Gemini trong Google Sheets tự điền số liệu vào sheet. Thiếu nguồn nào thì bỏ qua.
  Trigger: "/reports qh", "/reports dnd", "/reports", "/report-qh" (= part qh), "report qh",
  "report dnd", "lọc chi phí impression click", "tạo prompt gemini sheet".
---

# /reports — Chi phí · Reach · Impression · Click · Tin nhắn → Prompt Gemini Google Sheets

## Chọn PART (bắt buộc làm đầu tiên)

| Lệnh | Part | File quy tắc riêng |
|---|---|---|
| `/reports qh` (hoặc `/report-qh` cũ) | QH | [parts/qh/PART.md](parts/qh/PART.md) + [parts/qh/mapping.json](parts/qh/mapping.json) |
| `/reports dnd` | DND | [parts/dnd/PART.md](parts/dnd/PART.md) + [parts/dnd/mapping.json](parts/dnd/mapping.json) |

- Part lấy từ chữ ngay sau `/reports` (không phân biệt hoa thường).
- Không ghi part → suy ra từ tên campaign trong dữ liệu (vd chứa `QHD` → QH); không suy ra được → hỏi
  **1 câu**: "Báo cáo này của part nào (QH / DND)?"
- **Luôn đọc `parts/<part>/PART.md` trước khi xử lý** — file đó chứa: bảng mapping, cấu trúc sheet đích,
  màu chip, prompt Gemini mẫu. Mọi thứ trong PART.md **ưu tiên hơn** phần chung bên dưới.
- Part có PART.md ở trạng thái `CHƯA CẤU HÌNH` → làm theo mục "Onboarding part mới" trong file đó.

## Input (nguồn nào không có thì BỎ QUA, không hỏi)

| Nguồn | Dạng thường gặp | Cách đọc |
|---|---|---|
| Facebook Ads | File CSV / Excel (có thể nhiều file, mỗi TK 1 file) | `scripts/parse_ads.py --fb <file>` (xem bước 2) |
| Google Ads | File CSV / Excel **hoặc** ảnh chụp bảng campaign | File → `--google <file>`; ảnh → đọc cột Campaign, Cost, Impr., Clicks |
| TikTok Ads | File CSV / Excel hoặc ảnh | File → `--tiktok <file>`; ảnh → đọc tay |
| GPT Ads | Ảnh chụp | Đọc ảnh: tên campaign, chi phí, impression, click |

## Quy tắc khớp mapping (chung mọi part)

Khớp theo **tên campaign** (không khớp thì thử ad set → ad), **không phân biệt hoa thường**.
Rule dạng `key` = tên chứa chuỗi đó; dạng `all` = tên phải chứa **TẤT CẢ** chuỗi trong list (`all: []` = mọi
campaign của nguồn đó). Rule có `source` chỉ áp cho nguồn đó (facebook / google / tiktok). Rule cụ thể hơn
(tổng độ dài chuỗi lớn hơn) khớp trước. Source of truth: `parts/<part>/mapping.json`.
Thêm mapping mới → sửa **cả** `mapping.json` **và** bảng mapping trong `PART.md` của part đó.

Cấu hình cấp part trong `mapping.json`: `columns` (thứ tự cột output), `default_metrics` (chỉ số điền mặc định),
`fill_all_rows` (`true` = mỗi ngày xuất đủ mọi dòng, không có số liệu thì để trống). Cấp rule: `metrics`,
`copy` (vd Reach = Impression), `redirect` (cộng chỉ số sang dòng khác), `account` (ID TK quảng cáo).

---

## Workflow chung

### Bước 1 — Xác định ngày báo cáo
- Lấy từ cột Day/Ngày trong file FB, hoặc date range hiển thị trên ảnh Google/GPT Ads.
- Ảnh không thấy ngày và user không nói → hỏi **1 câu** duy nhất: "Số liệu này của ngày nào?"
- Nhiều ngày → tách theo từng ngày, sắp xếp tăng dần.

### Bước 2 — File (Facebook / Google / TikTok)
```powershell
python "<skill_dir>/scripts/parse_ads.py" "<fb.csv>" --part qh                      # file không kèm cờ = Facebook
python "<skill_dir>/scripts/parse_ads.py" --part dnd --fb "<fb1>" --fb "<fb2>" --google "<gg.csv>" --tiktok "<tt.xlsx>"
python "<skill_dir>/scripts/parse_ads.py" --part dnd --fb "<file>" --date 22/10/2026  # file không có cột ngày
python "<skill_dir>/scripts/parse_ads.py" "<fb.csv>" --part qh --clicks all          # FB dùng Clicks (all)
```
- Script đọc `parts/<part>/mapping.json`, tự nhận cột (EN/VI), tự bỏ dòng tiêu đề của Google CSV và dòng
  Tổng/Total, gộp theo (Ngày, dòng sheet), in bảng TSV theo `columns` của part + `file/columns_used` +
  `WARNING` + `UNMAPPED`.
- Có `WARNING` file là tổng khoảng nhiều ngày → báo user, đề nghị export lại breakdown theo **Day**.
- `WARNING` thiếu cột → chỉ số đó để trống; báo user cột nào thiếu.
- Không chạy được script → tự đọc file, áp dụng đúng quy tắc mapping của part.

### Bước 3 — Google / GPT Ads (ảnh)
- Đọc từng dòng campaign: Cost, Impr., Clicks. Bỏ dòng Total/Tổng.
- Map theo bảng của part; nhiều campaign cùng Target thì **cộng dồn**.
- Số tiền: **VND** → số nguyên không dấu phân cách (vd `1250000`); **USD** → giữ 2 số lẻ, dấu chấm thập phân
  (vd `36.49`) và ghi rõ đơn vị USD trong prompt Gemini. Ảnh ghi `₫1,25 Tr`/`1.25M` → quy đổi.
  Ảnh Google VN dùng dấu phẩy thập phân (`36,49 US$`) → đổi thành `36.49`.
- Chữ trong ảnh mờ, không chắc → ghi `?` và nêu rõ, **không đoán**.

### Bước 4 — Campaign không khớp mapping
- **Không** đưa vào bảng điền sheet. Liệt kê riêng ở mục "⚠️ Chưa map" kèm số liệu.
- Hỏi user: campaign này thuộc Target nào? → sau khi user trả lời, cập nhật `mapping.json` + bảng
  mapping trong `PART.md` **của đúng part đó**.

### Bước 5 — Output (đúng 3 phần, theo thứ tự)

**① Bảng kiểm tra** (markdown, để user soát số) — cột theo PART.md (mặc định:
`Ngày | Week | Hình thức | TKQC | Target | Chi phí | Impression | Click`).
Kèm dòng ghi chú ngắn: part, nguồn nào đã có / bị bỏ qua, loại click đã dùng cho FB, mục ⚠️ Chưa map (nếu có).

**② Prompt cho Gemini trong Google Sheets** — dùng **prompt mẫu trong PART.md** của part, đặt trong
1 code block, điền dữ liệu thật vào.

**③ TSV dự phòng** — code block thuần tab-separated (cùng cột như bảng ①, không header), để user
copy-paste tay vào sheet nếu Gemini không điền được.

---

## Quy tắc chung

| Quy tắc | Chi tiết |
|---|---|
| Thiếu nguồn | Không có file/ảnh nguồn nào → bỏ qua nguồn đó, không hỏi (part có `fill_all_rows` vẫn xuất dòng, để trống chỉ số) |
| Dòng không có số liệu | Theo part: QH bỏ dòng; DND (`fill_all_rows`) vẫn xuất dòng, ô chỉ số để trống. Campaign có xuất hiện mà số = 0 → ghi `0` |
| Week / ngày | Theo `columns` của part: QH `Ngày` = `DD/MM/YYYY`, `Week` = Thứ Hai … Chủ Nhật; DND chỉ xuất Date `MM/DD/YYYY` (Month/Week/Year/Thứ sheet tự nhảy công thức) |
| Click FB | Mặc định **Link clicks** (Lượt click vào liên kết); thiếu cột này mới dùng Clicks (all) |
| Không bịa số | Số không đọc được → `?` + cảnh báo, không đưa số đó vào prompt Gemini |
| Không trộn part | Mapping/màu/prompt của part này **không** dùng cho part khác |
| Không commentary thừa | Chỉ 3 phần output + ghi chú ngắn |

## Common Mistakes (chung)

| Sai | Đúng |
|---|---|
| Quên đọc PART.md, dùng mapping QH cho DND | Luôn đọc `parts/<part>/PART.md` trước |
| Đưa campaign chưa map vào prompt | Để riêng mục ⚠️ Chưa map, hỏi user |
| Ghi tiền `1.250.000` hoặc `1tr25` | VND ghi `1250000`; USD ghi `36.49` (số thuần cho Sheets) |
| Làm tròn USD thành số nguyên | Giữ 2 số lẻ (script tự nhận đơn vị từ header `(USD)`/`(VND)`) |
| Google click | Cột "Lượt tương tác" (search = lượt nhấp) hoặc "Lượt nhấp" |
| Cộng nhiều ngày vào 1 dòng | Tách từng ngày |
