# PART DND — `/reports dnd`

> Trạng thái: **ĐÃ CẤU HÌNH**. Workflow chung xem [../../SKILL.md](../../SKILL.md).
> Chạy script (đưa file nào có thì truyền file đó, nhiều file FB thì lặp `--fb`):
> ```powershell
> python "<skill_dir>/scripts/parse_ads.py" --part dnd --fb "<fb1.csv>" --fb "<fb2.csv>" --google "<gg.csv>" --tiktok "<tt.xlsx>"
> ```
> macOS: `uv run -q --with pandas --with openpyxl --with "psycopg[binary]" python3 "<skill_dir>/scripts/parse_ads.py" ...`
> Script **tự lấy Lead Tổng / Đặt lịch / Đã khám từ Supabase** cho đúng các ngày có trong file ads (xem mục
> "Lead từ Supabase" bên dưới). Ads đọc từ **ảnh** (không chạy parse_ads) → chạy riêng:
> `uv run -q --with "psycopg[binary]" python3 "<skill_dir>/scripts/fetch_leads.py" --part dnd --date DD/MM/YYYY [--date ...]`
> rồi ghép 3 cột vào đúng dòng (Date + Hình thức + TKQC).

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
| 6 | Facebook | 553260191728855 | `PFM_PTKX_` + `_CVA_MS_` | Message - Khúc Xạ | Agency | Total Cost · Reach · Impression · Tin nhắn |
| 7 | Facebook | 553260191728855 | `Event_` + `_EV.CVS_` | Event - CVS | Agency | Total Cost · Reach · Impression · Tin nhắn — *chỉ xuất khi có số liệu* |
| 8 | Facebook | 553260191728855 | `Event_` + `_EV.Live.` | Event - Live | Agency | Total Cost · Reach · Impression · Tin nhắn — *chỉ xuất khi có số liệu* |
| 9 | Google | — | *(mọi campaign, cộng hết thành 1 dòng)* | Google Search - Khúc Xạ | DND Sài Gòn | Total Cost · Reach (= Impression) · Impression · Click |
| 10 | TikTok | — | `Branding_` + (`_Tiktok_` hoặc `_TTA_`) | Tiktok - Branding | DND Sài Gòn | Total Cost · Reach · Impression · Tin nhắn |
| 11 | TikTok | — | `PFM_Mess_` + `_Tiktok_` hoặc `PPFM_Tiktok_Mess` / `PFM_Tiktok_Mess` | Tiktok - Message | DND Sài Gòn | Total Cost · Reach · Impression · Tin nhắn |
| 12 | TikTok | — | `PFM_Conversion_Tiktok` | Tiktok - Conversion | DND Sài Gòn | Total Cost · Reach · Impression · Tin nhắn |

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

- Mỗi ngày **luôn xuất đủ 10 dòng cố định** (#1–6, #9–12), kể cả khi không có số liệu / không gửi file nguồn đó
  → vẫn ghi Date, Hình thức, TKQC; các ô chỉ số **để trống** (không ghi 0, không ghi `-`).
- Event - CVS / Event - Live (#7, #8) **không cố định** — chỉ thêm khi file có campaign Event ngày đó,
  chèn sau Message - Khúc Xạ (Agency). Không có thì bỏ, không tạo dòng trống.
- Campaign có xuất hiện nhưng số = 0 → ghi `0`. Chỉ số không áp dụng cho dòng (vd Click của Facebook) → để trống.

## Lead từ Supabase (Lead Tổng · Đặt Lịch / XN tham gia · Đã Khám)

Nguồn: bảng `status_data` (tab **Khách hàng** của app data-ads), source of truth `leads` trong
[mapping.json](mapping.json). Script `scripts/fetch_leads.py` **chỉ đọc** (session read-only), parse_ads tự gọi.
Ngày lấy = đúng các ngày có trong file/ảnh ads lần chạy đó; không có file/ảnh ads → hỏi ngày.

| Chỉ số (cột sheet) | Lọc ngày theo | Trạng thái được đếm |
|---|---|---|
| Lead Tổng (cột R) | **Ngày đăng ký** (`created_at`) | **Tất cả** (kể cả Lead rác, Không nhu cầu) |
| Đặt Lịch / XN tham gia (cột X) | **Ngày cập nhật** (`updated_at`) | Trạng thái HIỆN TẠI ∈ Đặt lịch, Đặt lịch tái khám, Xác nhận tham gia, Đã khám, Đã tham gia, Chốt đơn (**không** tính Hủy lịch) |
| Đã Khám (cột AB) | **Ngày cập nhật** (`updated_at`) | Trạng thái HIỆN TẠI ∈ Đã khám, Đã tham gia, Chốt đơn |

- Đặt lịch tính **cộng dồn**: hôm đó 8 khách đặt lịch, 3 khách đã khám ngay trong ngày → Đặt lịch vẫn = 8 (3 khách
  đó đang ở trạng thái Đã khám nhưng vẫn được đếm), Đã khám = 3.
- Ngày cắt theo giờ **Việt Nam** (Asia/Ho_Chi_Minh). Đếm theo **số dòng** khách (giống bộ lọc tab Khách hàng).
- Số **0 → để trống** (`zero_as_blank`). Không kết nối được Supabase → script báo WARNING, 3 cột để trống, vẫn ra
  phần ads bình thường — báo user.
- ⚠️ "Ngày cập nhật" còn nhảy khi sửa **doanh thu / phí / giờ hẹn / phân loại chốt** (không chỉ khi đổi trạng thái)
  → ngày nào sửa doanh thu hàng loạt thì Đặt lịch / Đã khám ngày đó sẽ cao bất thường; số của ngày cũ cũng có thể
  giảm dần nếu khách sau đó được cập nhật tiếp. Thấy số lạ → ghi chú cho user trong phần ①.

Gán dòng sheet (khớp từ trên xuống, dòng đầu tiên khớp thì dùng; TKQC luôn **DND Sài Gòn**):

| Nguồn (`nguon`) | Loại dịch vụ | Hình thức |
|---|---|---|
| Facebook | Phaco | Message - Phaco |
| Facebook | KX - Lão thị | Message - Lão Thị |
| Facebook | Kiểm Soát Cận Thị (Ortho-K) | Message - Kid |
| Facebook | mọi loại còn lại (Cận loạn thị, Bệnh lý, Cắt kính, Thẩm mỹ, Mộng, trống…) | Message - Khúc Xạ |
| Google | tất cả | Google Search - Khúc Xạ |
| TikTok | tất cả | Tiktok - Conversion |

- Chỉ nguồn đúng `Facebook` — **không** tính `FB-Hội thảo`, `FB-livestream`. Hotline / Zalo / Website / Liên Các Viện
  / Trạm Sáng / Khác → không đưa vào sheet.
- Các dòng còn lại (Branding, Message - Khúc Xạ **Agency**, Event, Tiktok - Branding / Message) → 3 cột lead để trống.

## Cấu trúc sheet đích (từ ảnh sheet mẫu)

Thứ tự cột từ trái sang phải:

| Month | Week | Year | Date | Date | Hình thức | TKQC | Total Cost | Reach | Impression | CPM | Click | CPC | Tin nhắn (Message) | Cost per Message |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `10` | `43` | `2026` | `10/20/2026` | `Thứ Ba` | dropdown | dropdown | nhập | nhập | nhập | **công thức** | nhập | **công thức** | nhập | **công thức** |

| Loại cột | Cột |
|---|---|
| **Nhập** | Date (cột Date thứ nhất), Hình thức, TKQC, Total Cost, Reach, Impression, Click, Tin nhắn (Message), **Lead Tổng** (cột R), **Đặt Lịch / XN tham gia** (cột X), **Đã Khám** (cột AB) |
| **Công thức — không nhập** | Month, Week, Year, Date thứ hai (thứ), CPM, CPC, Cost per Message |
| **Không đụng** | Mọi cột khác sau Cost per Message (P → AB) ngoài 3 cột lead ở trên |

- 3 cột lead tìm theo **tên header** (`Lead Tổng`, `Đặt Lịch / XN tham gia`, `Đã Khám`); chữ cột R / X / AB chỉ là
  vị trí hiện tại để đối chiếu — header bị dời thì theo tên header.

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
| Hình thức | Tiktok - Branding, Tiktok - Message, Tiktok - Conversion | `#3D3D3D` xám đen | `#E6E6E6` xám nhạt |
| TKQC | DND Sài Gòn 02 | `#BFE1F6` xanh dương nhạt | `#0A53A8` xanh dương |
| TKQC | DND Sài Gòn | `#D4EDBC` xanh lá nhạt | `#11734B` xanh lá |
| Hình thức / TKQC | Event - CVS, Event - Live / Agency | *chưa có* — giữ màu sẵn có trong dropdown | |

## Cột bảng kiểm tra ①

| Date | Hình thức | TKQC | Total Cost | Reach | Impression | Click | Tin nhắn (Message) | Lead Tổng | Đặt Lịch / XN tham gia | Đã Khám |
|---|---|---|---|---|---|---|---|---|---|---|

(Output script đã đúng thứ tự cột này; Date dạng mm/dd/yyyy giống sheet.)
Ghi chú dưới bảng thêm 1 dòng nguồn lead, vd: "Lead/Đặt lịch/Đã khám: Supabase, giờ VN, ngày 11/02–11/03; 0 để trống".

## Prompt Gemini mẫu ②

Ô trống trong dữ liệu ghi là rỗng giữa 2 dấu `|`.

````
Bạn đang làm việc trên sheet hiện tại. Hãy TỰ NHẬP đầy đủ từng dòng dữ liệu quảng cáo + lead bên dưới vào sheet.

CẤU TRÚC SHEET (thứ tự cột từ trái sang phải theo header):
Month | Week | Year | Date | Date | Hình thức | TKQC | Total Cost | Reach | Impression | CPM | Click | CPC | Tin nhắn (Message) | Cost per Message | ... | Lead Tổng (cột R) | ... | Đặt Lịch / XN tham gia (cột X) | ... | Đã Khám (cột AB)
- Có 2 cột tên "Date": CHỈ nhập vào cột Date THỨ NHẤT (ngày dạng mm/dd/yyyy, vd 10/20/2026 = ngày 20 tháng 10).
- CỘT CÔNG THỨC — KHÔNG nhập tay: Month, Week, Year, cột Date THỨ HAI (thứ trong tuần), CPM, CPC, Cost per Message. Các cột này tự nhảy theo Date / chỉ số; dòng mới thì kéo/copy công thức từ dòng phía trên xuống.
- 3 CỘT LEAD: tìm cột theo ĐÚNG tên header "Lead Tổng", "Đặt Lịch / XN tham gia", "Đã Khám" (hiện đang là cột R, X, AB — nếu header đã bị dời thì theo tên header). Các cột khác sau Cost per Message (ngoài 3 cột này) KHÔNG đụng vào; nếu là cột công thức thì dòng mới kéo/copy công thức từ dòng phía trên xuống.
- Hình thức và TKQC là dropdown: chọn đúng giá trị có sẵn, viết y nguyên chính tả như dữ liệu.

CÁCH NHẬP (mỗi dòng dữ liệu = 1 dòng trong sheet):
1. Nếu sheet ĐÃ có dòng trùng Date + Hình thức + TKQC → chỉ cập nhật các ô Total Cost, Reach, Impression, Click, Tin nhắn (Message), Lead Tổng, Đặt Lịch / XN tham gia, Đã Khám của dòng đó.
2. Nếu CHƯA có → thêm dòng mới ngay dưới dòng dữ liệu cuối cùng của bảng (giữ thứ tự ngày tăng dần, các dòng cùng ngày đứng liền nhau theo ĐÚNG thứ tự trong dữ liệu), nhập Date (mm/dd/yyyy, đúng định dạng các dòng phía trên), Hình thức, TKQC và các chỉ số.
3. Ô TRỐNG trong dữ liệu (không có gì giữa 2 dấu |): vẫn tạo/giữ dòng đó, nhưng để TRỐNG ô tương ứng — không ghi 0, không ghi "-". Nếu dòng đã có sẵn và ô đó đang có giá trị thì GIỮ NGUYÊN, không xoá.
4. Chỉ số ghi dạng SỐ thuần (không dấu phân cách hàng nghìn, không ký hiệu ₫). Total Cost đơn vị [VND/USD]; dấu chấm trong dữ liệu là dấu THẬP PHÂN. Lead Tổng / Đặt Lịch / Đã Khám là số nguyên.
5. MÀU CHIP — kiểm tra và chỉnh lại màu cho TẤT CẢ các dòng vừa nhập/cập nhật:
   - Hình thức: "Branding", "Message - Lão Thị", "Message - Khúc Xạ", "Message - Phaco", "Message - Kid" = nền xanh dương đậm #0A53A8, chữ xanh nhạt #BFE1F6; "Google Search - Khúc Xạ" = nền xanh lá đậm #11734B, chữ #D4EDBC; "Tiktok - Branding", "Tiktok - Message", "Tiktok - Conversion" = nền xám đen #3D3D3D, chữ #E6E6E6.
   - TKQC: "DND Sài Gòn 02" = nền xanh dương nhạt #BFE1F6, chữ xanh dương #0A53A8; "DND Sài Gòn" = nền xanh lá nhạt #D4EDBC, chữ xanh lá #11734B.
   - Giá trị khác (vd Event - CVS, Agency): copy định dạng từ dòng có cùng giá trị.
   - Định dạng còn lại (viền, font, định dạng số ₫ của Total Cost) giống các dòng phía trên.
6. KHÔNG sửa, xoá dữ liệu của các dòng/ngày khác.
7. Xong thì báo: số dòng đã cập nhật + số dòng đã thêm mới + dòng nào gặp lỗi (nếu có).

DỮ LIỆU (Date | Hình thức | TKQC | Total Cost | Reach | Impression | Click | Tin nhắn (Message) | Lead Tổng | Đặt Lịch / XN tham gia | Đã Khám):
10/21/2026 | Branding | DND Sài Gòn 02 | 400000 | 30000 | 60000 |  |  |  |  | 
10/21/2026 | Message - Lão Thị | DND Sài Gòn |  |  |  |  |  | 1 |  | 
10/21/2026 | Message - Khúc Xạ | DND Sài Gòn | 1000000 | 13000 | 29000 |  | 28 | 7 | 7 | 1
10/21/2026 | Google Search - Khúc Xạ | DND Sài Gòn | 1500000 | 2500 | 2500 | 175 |  | 3 | 3 | 2
...
````

## Common Mistakes (riêng DND)

| Sai | Đúng |
|---|---|
| Bỏ dòng không có số liệu | DND luôn đủ 10 dòng cố định/ngày, ô chỉ số để trống |
| Ghi tin nhắn Branding vào dòng Branding | Để trống, CHỈ tin nhắn cộng sang Message - Khúc Xạ |
| Cộng cả Total Cost/Reach/Impression Branding vào Khúc Xạ | Chỉ cộng tin nhắn; các chỉ số khác giữ ở dòng Branding |
| Google tách nhiều dòng theo campaign | Cộng hết thành 1 dòng "Google Search - Khúc Xạ" |
| Google Reach để trống | Reach = Impression (cùng số hiển thị) |
| `PFM_KXLT_` / `PFM_PTKX_` không có `_DNDA_` vẫn đưa vào | Phải chứa đủ cả 2 chuỗi; thiếu → ⚠️ Chưa map |
| Gộp `PFM_PTKX_` + `_CVA_MS_` vào Khúc Xạ TKQC "DND Sài Gòn" | Đây là dòng riêng: Message - Khúc Xạ / **Agency** (tin nhắn Branding KHÔNG cộng vào dòng này) |
| Ghi Date dạng dd/mm/yyyy | Sheet dùng mm/dd/yyyy (`10/20/2026`) |
| Tự tính / nhập tay Month, Week, Year, Thứ | Cột công thức theo Date — chỉ nhập Date |
| Nhập tay CPM / CPC / Cost per Message | Cột công thức — kéo công thức xuống |
| Cộng dòng "Tổng"/"Total" của Google/TikTok | Bỏ dòng tổng |
| Đặt lịch chỉ đếm khách đang ở trạng thái "Đặt lịch" | Cộng dồn: Đặt lịch + Đặt lịch tái khám + XN tham gia + Đã khám + Đã tham gia + Chốt đơn (không Hủy lịch) |
| Lead Tổng lọc theo ngày cập nhật | Lead Tổng theo **Ngày đăng ký**; Đặt lịch / Đã khám theo **Ngày cập nhật** |
| Gộp FB-Hội thảo / FB-livestream vào Facebook | Chỉ nguồn đúng `Facebook` |
| Lead Facebook ghi vào dòng TKQC Agency | Mọi lead ghi vào TKQC **DND Sài Gòn** |
| Ghi `0` cho lead | 0 → để trống |
| Tự đếm lead bằng tay / đoán | Luôn chạy script (parse_ads tự gọi, hoặc fetch_leads.py); lỗi kết nối → để trống + báo user |
