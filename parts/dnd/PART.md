# PART DND — `/reports dnd`

> Trạng thái: **ĐÃ CẤU HÌNH**. Workflow chung xem [../../SKILL.md](../../SKILL.md).
> Chạy script (đưa file nào có thì truyền file đó, nhiều file FB thì lặp `--fb`):
> ```powershell
> python "<skill_dir>/scripts/parse_ads.py" --part dnd --fb "<fb1.csv>" --fb "<fb2.csv>" --google "<gg.csv>" --tiktok "<tt.xlsx>"
> ```

## Bảng mapping (source of truth: [mapping.json](mapping.json))

Khớp khi tên campaign chứa **TẤT CẢ** chuỗi ở cột Filter (không phân biệt hoa thường). Thứ tự bảng = thứ
tự dòng trong sheet mỗi ngày (đúng như sheet thật). Hình thức / TKQC ghi **đúng chính tả** như bảng.

| # | Nguồn | TK quảng cáo | Filter tên campaign (AND) | Hình thức | TKQC | Chỉ số điền |
|---|---|---|---|---|---|---|
| 1 | Facebook | 1917832182458596 | `Branding_` + `_DND2A_` | Branding | DND Sài Gòn 02 | Total Cost · Reach · Impression (Tin nhắn **để trống**) |
| 2 | Facebook | 1465106504558065 | `PFM_KXLT_` + `_DNDA_` | Message - Lão Thị | DND Sài Gòn | Total Cost · Reach · Impression · Tin nhắn |
| 3 | Facebook | 1465106504558065 | `PFM_PTKX_` + `_DNDA_` | Message - Khúc Xạ | DND Sài Gòn | Total Cost · Reach · Impression · Tin nhắn (+ tin nhắn Branding) |
| 4 | Facebook | 1465106504558065 | `PFM_Phaco_` + `_DNDA_` | Message - Phaco | DND Sài Gòn | Total Cost · Reach · Impression · Tin nhắn |
| 5 | Facebook | 1465106504558065 | `PFM_KXTE_` + `_DNDA_` | Message - Kid | DND Sài Gòn | Total Cost · Reach · Impression · Tin nhắn |
| 6 | Facebook | 553260191728855 | `Event_` + `_EV.CVS_` | Event - CVS | Agency | Total Cost · Reach · Impression · Tin nhắn — *chỉ xuất khi có số liệu* |
| 7 | Facebook | 553260191728855 | `Event_` + `_EV.Live.` | Event - Live | Agency | Total Cost · Reach · Impression · Tin nhắn — *chỉ xuất khi có số liệu* |
| 8 | Google | — | *(mọi campaign, cộng hết thành 1 dòng)* | Google Search - Khúc Xạ | DND Sài Gòn | Total Cost · Reach (= Impression) · Impression · Click |
| 9 | TikTok | — | `Branding_` + (`_Tiktok_` hoặc `_TTA_`) | Tiktok - Branding | DND Sài Gòn | Total Cost · Reach · Impression · Tin nhắn |
| 10 | TikTok | — | `PFM_Mess_` + `_Tiktok_` | Tiktok - Message | DND Sài Gòn | Total Cost · Reach · Impression · Tin nhắn |

Quy tắc riêng từng nguồn:
- **Facebook**: Tin nhắn = cột "Lượt bắt đầu cuộc trò chuyện qua tin nhắn" (Messaging conversations started).
  Không điền Click.
- **Branding (#1)**: Total Cost · Reach · Impression **giữ riêng ở dòng Branding**. **CHỈ số tin nhắn** của Branding
  được cộng sang Message - Khúc Xạ (#3) nếu > 0 (Total Cost/Reach/Impression của Khúc Xạ KHÔNG cộng gì từ Branding).
  Ô Tin nhắn dòng Branding để trống. Ghi chú rõ trong output (vd "Tin nhắn Khúc Xạ 28 = 25 + 3 từ Branding").
- Cột TK quảng cáo chỉ dùng để kiểm tra khi file có cột Account ID; không có cột đó thì lọc theo tên campaign.
- **Google**: không chia campaign — cộng toàn bộ thành 1 dòng. Reach và Impression **cùng lấy số "Số lần hiển thị"**
  (Impr.). Click = "Lượt nhấp" (Clicks). Không điền Tin nhắn. Bỏ các dòng "Tổng: ..." / "Total: ...".
- **TikTok**: Reach = "Phạm vi tiếp cận" (Reach), Impression = "Lần hiển thị" (Impressions),
  Tin nhắn = "Cuộc trò chuyện" (Conversations). Không điền Click. Bỏ dòng "Total of ...".
- Đọc từ **ảnh** thay vì file → áp dụng đúng các quy tắc trên bằng tay.
- Reach của nhiều campaign cùng dòng được **cộng thẳng** (không khử trùng lặp người dùng).

## Luôn đủ dòng (khác QH)

- Mỗi ngày **luôn xuất đủ 8 dòng cố định** (#1–5, #8–10), kể cả khi không có số liệu / không gửi file nguồn đó
  → vẫn ghi Date, Hình thức, TKQC; các ô chỉ số **để trống** (không ghi 0, không ghi `-`).
- Event - CVS / Event - Live (#6, #7) **không cố định** — chỉ thêm khi file có campaign Event ngày đó,
  chèn sau Message - Kid. Không có thì bỏ, không tạo dòng trống.
- Campaign có xuất hiện nhưng số = 0 → ghi `0`. Chỉ số không áp dụng cho dòng (vd Click của Facebook) → để trống.

## Cấu trúc sheet đích (từ ảnh sheet mẫu)

Thứ tự cột từ trái sang phải:

| Month | Week | Year | Date | Date | Hình thức | TKQC | Total Cost | Reach | Impression | CPM | Click | CPC | Tin nhắn (Message) | Cost per Message |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `10` | `43` | `2026` | `10/20/2026` | `Thứ Ba` | dropdown | dropdown | nhập | nhập | nhập | **công thức** | nhập | **công thức** | nhập | **công thức** |

| Loại cột | Cột |
|---|---|
| **Nhập** | Date (cột Date thứ nhất), Hình thức, TKQC, Total Cost, Reach, Impression, Click, Tin nhắn (Message) |
| **Công thức — không nhập** | Month, Week, Year, Date thứ hai (thứ), CPM, CPC, Cost per Message |

- Chỉ nhập Date dạng **mm/dd/yyyy** (`10/20/2026` = 20 tháng 10) ở cột Date **thứ nhất**; Month / Week / Year /
  cột Date thứ hai (thứ) sheet tự nhảy công thức → không tính, không đưa vào dữ liệu.
- Dòng mới: kéo/copy công thức của các cột công thức từ dòng phía trên xuống.
- Total Cost hiển thị dạng `338,726 ₫` (định dạng số của sheet) → nhập số thuần `338726`.
- Khóa nhận diện dòng: **Date + Hình thức + TKQC**.
- **Màu chip** (nguồn: `colors` trong `mapping.json`):

| Cột | Giá trị | Nền | Chữ |
|---|---|---|---|
| Hình thức | Branding, Message - Lão Thị / Khúc Xạ / Phaco / Kid | `#0A53A8` xanh dương đậm | `#BFE1F6` xanh nhạt |
| Hình thức | Google Search - Khúc Xạ | `#11734B` xanh lá đậm | `#D4EDBC` xanh lá nhạt |
| Hình thức | Tiktok - Branding, Tiktok - Message | `#3D3D3D` xám đen | `#E6E6E6` xám nhạt |
| TKQC | DND Sài Gòn 02 | `#BFE1F6` xanh dương nhạt | `#0A53A8` xanh dương |
| TKQC | DND Sài Gòn | `#D4EDBC` xanh lá nhạt | `#11734B` xanh lá |
| Hình thức / TKQC | Event - CVS, Event - Live / Agency | *chưa có* — giữ màu sẵn có trong dropdown | |

## Cột bảng kiểm tra ①

| Date | Hình thức | TKQC | Total Cost | Reach | Impression | Click | Tin nhắn (Message) |
|---|---|---|---|---|---|---|---|

(Output script đã đúng thứ tự cột này; Date dạng mm/dd/yyyy giống sheet.)

## Prompt Gemini mẫu ②

Ô trống trong dữ liệu ghi là rỗng giữa 2 dấu `|`.

````
Bạn đang làm việc trên sheet hiện tại. Hãy TỰ NHẬP đầy đủ từng dòng dữ liệu quảng cáo bên dưới vào sheet.

CẤU TRÚC SHEET (thứ tự cột từ trái sang phải theo header):
Month | Week | Year | Date | Date | Hình thức | TKQC | Total Cost | Reach | Impression | CPM | Click | CPC | Tin nhắn (Message) | Cost per Message
- Có 2 cột tên "Date": CHỈ nhập vào cột Date THỨ NHẤT (ngày dạng mm/dd/yyyy, vd 10/20/2026 = ngày 20 tháng 10).
- CỘT CÔNG THỨC — KHÔNG nhập tay: Month, Week, Year, cột Date THỨ HAI (thứ trong tuần), CPM, CPC, Cost per Message. Các cột này tự nhảy theo Date / chỉ số; dòng mới thì kéo/copy công thức từ dòng phía trên xuống.
- Hình thức và TKQC là dropdown: chọn đúng giá trị có sẵn, viết y nguyên chính tả như dữ liệu.

CÁCH NHẬP (mỗi dòng dữ liệu = 1 dòng trong sheet):
1. Nếu sheet ĐÃ có dòng trùng Date + Hình thức + TKQC → chỉ cập nhật các ô Total Cost, Reach, Impression, Click, Tin nhắn (Message) của dòng đó.
2. Nếu CHƯA có → thêm dòng mới ngay dưới dòng dữ liệu cuối cùng của bảng (giữ thứ tự ngày tăng dần, các dòng cùng ngày đứng liền nhau theo ĐÚNG thứ tự trong dữ liệu), nhập Date (mm/dd/yyyy, đúng định dạng các dòng phía trên), Hình thức, TKQC và các chỉ số.
3. Ô TRỐNG trong dữ liệu (không có gì giữa 2 dấu |): vẫn tạo/giữ dòng đó, nhưng để TRỐNG ô tương ứng — không ghi 0, không ghi "-". Nếu dòng đã có sẵn và ô đó đang có giá trị thì GIỮ NGUYÊN, không xoá.
4. Chỉ số ghi dạng SỐ thuần (không dấu phân cách hàng nghìn, không ký hiệu ₫). Total Cost đơn vị [VND/USD]; dấu chấm trong dữ liệu là dấu THẬP PHÂN.
5. MÀU CHIP — kiểm tra và chỉnh lại màu cho TẤT CẢ các dòng vừa nhập/cập nhật:
   - Hình thức: "Branding", "Message - Lão Thị", "Message - Khúc Xạ", "Message - Phaco", "Message - Kid" = nền xanh dương đậm #0A53A8, chữ xanh nhạt #BFE1F6; "Google Search - Khúc Xạ" = nền xanh lá đậm #11734B, chữ #D4EDBC; "Tiktok - Branding", "Tiktok - Message" = nền xám đen #3D3D3D, chữ #E6E6E6.
   - TKQC: "DND Sài Gòn 02" = nền xanh dương nhạt #BFE1F6, chữ xanh dương #0A53A8; "DND Sài Gòn" = nền xanh lá nhạt #D4EDBC, chữ xanh lá #11734B.
   - Giá trị khác (vd Event - CVS, Agency): copy định dạng từ dòng có cùng giá trị.
   - Định dạng còn lại (viền, font, định dạng số ₫ của Total Cost) giống các dòng phía trên.
6. KHÔNG sửa, xoá dữ liệu của các dòng/ngày khác.
7. Xong thì báo: số dòng đã cập nhật + số dòng đã thêm mới + dòng nào gặp lỗi (nếu có).

DỮ LIỆU (Date | Hình thức | TKQC | Total Cost | Reach | Impression | Click | Tin nhắn (Message)):
10/21/2026 | Branding | DND Sài Gòn 02 | 400000 | 30000 | 60000 |  | 
10/21/2026 | Message - Lão Thị | DND Sài Gòn |  |  |  |  | 
10/21/2026 | Message - Khúc Xạ | DND Sài Gòn | 1000000 | 13000 | 29000 |  | 28
10/21/2026 | Google Search - Khúc Xạ | DND Sài Gòn | 1500000 | 2500 | 2500 | 175 | 
...
````

## Common Mistakes (riêng DND)

| Sai | Đúng |
|---|---|
| Bỏ dòng không có số liệu | DND luôn đủ 8 dòng cố định/ngày, ô chỉ số để trống |
| Ghi tin nhắn Branding vào dòng Branding | Để trống, CHỈ tin nhắn cộng sang Message - Khúc Xạ |
| Cộng cả Total Cost/Reach/Impression Branding vào Khúc Xạ | Chỉ cộng tin nhắn; các chỉ số khác giữ ở dòng Branding |
| Google tách nhiều dòng theo campaign | Cộng hết thành 1 dòng "Google Search - Khúc Xạ" |
| Google Reach để trống | Reach = Impression (cùng số hiển thị) |
| `PFM_KXLT_` / `PFM_PTKX_` không có `_DNDA_` vẫn đưa vào | Phải chứa đủ cả 2 chuỗi; thiếu → ⚠️ Chưa map |
| Ghi Date dạng dd/mm/yyyy | Sheet dùng mm/dd/yyyy (`10/20/2026`) |
| Tự tính / nhập tay Month, Week, Year, Thứ | Cột công thức theo Date — chỉ nhập Date |
| Nhập tay CPM / CPC / Cost per Message | Cột công thức — kéo công thức xuống |
| Cộng dòng "Tổng"/"Total" của Google/TikTok | Bỏ dòng tổng |
