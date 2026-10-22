# PART QH — `/reports qh`

> Trạng thái: **ĐÃ CẤU HÌNH**. Workflow chung xem [../../SKILL.md](../../SKILL.md).
> Chạy script: `python "<skill_dir>/scripts/parse_ads.py" "<file FB>" --part qh`
> (Google / GPT Ads của QH thường là ảnh → đọc ảnh theo bảng mapping.)
> Chỉ xuất dòng Target **có xuất hiện** trong dữ liệu (không tự thêm dòng trống).

## Bảng mapping (source of truth: [mapping.json](mapping.json))

| Key trong tên campaign | Hình thức | TKQC | Target |
|---|---|---|---|
| `ASC_LAL.Reweb_Terms` | Conversion | Facebook | LAL MKT |
| `lead_title` | Conversion | Facebook | FB Title IR |
| `ReMKT_ASC` | Conversion | Facebook | Re MKT (ASC) |
| `Lead_ASC.CountryGroups_LAL.Reweb` | Conversion | Facebook | LKL MKT Countries |
| `_ReMKT_CountryGroups.ASC` | Conversion | Facebook | ReMKT ASC Countries |
| `Search_Brand_South` | Conversion | Google | Google SEM.SDA |
| `SEM - General` (vd `AK.QHD - SEM - General`) | Conversion | Google | Google SEM.SDA |
| `Search_Dynamic_South_V2` | Conversion | Google | Google SEM.SDA.02 |
| `SEM - SDA.02` (vd `AK.QHD - SEM - SDA.02`) | Conversion | Google | Google SEM.SDA.02 |
| *(GPT Ads — chưa có mapping)* | ? | ? | ? |

> Thứ tự bảng = thứ tự dòng trong Google Sheet mỗi ngày. Target phải ghi **đúng chính tả** như trên
> (vd `LKL MKT Countries`, `Re MKT (ASC)` có khoảng trắng, `ReMKT ASC Countries` không có).
> Thêm mapping mới → sửa **cả** `mapping.json` **và** bảng này.

## Cấu trúc sheet đích (từ ảnh mẫu)

- Cột **D = Week** (`Thứ Hai` … `Chủ Nhật`), **E = Hình thức**, **F = TKQC**, **G = Target**.
- Cột ngày nằm trước cột D; các cột Chi phí / Impression / Click nằm sau cột G → Gemini tự tìm theo tên header.
- Mỗi ngày 1 block dòng (tối đa 7 dòng theo bảng mapping).
- **Màu chip bắt buộc** (nguồn: `colors` trong `mapping.json`):

| Cột | Giá trị | Nền | Chữ |
|---|---|---|---|
| Hình thức | Conversion | `#B10202` đỏ đậm | `#FFCFC9` trắng hồng |
| TKQC | Facebook | `#BFE1F6` xanh dương nhạt | `#0A53A8` xanh dương |
| TKQC | Google | `#D4EDBC` xanh lá nhạt | `#11734B` xanh lá |

## Cột bảng kiểm tra ①

| Ngày | Week | Hình thức | TKQC | Target | Chi phí | Impression | Click |
|---|---|---|---|---|---|---|---|

## Prompt Gemini mẫu ②

````
Bạn đang làm việc trên sheet hiện tại. Hãy TỰ NHẬP đầy đủ từng dòng dữ liệu quảng cáo bên dưới vào sheet: gồm Ngày, Week, Hình thức, TKQC, Target và 3 chỉ số Chi phí, Impression, Click.

CẤU TRÚC SHEET:
- Cột ngày nằm bên trái cột D. Cột D = Week, cột E = Hình thức, cột F = TKQC, cột G = Target.
- Các cột "Chi phí" (Cost/Spend), "Impression" (Hiển thị) và "Click" nằm bên phải cột G — xác định đúng các cột này theo tên tiêu đề ở hàng header.
- Cột E, F, G là dropdown: chọn đúng giá trị có sẵn trong dropdown, viết y nguyên chính tả như dữ liệu.

CÁCH NHẬP (mỗi dòng dữ liệu = 1 dòng trong sheet):
1. Nếu sheet ĐÃ có dòng trùng Ngày + TKQC + Target → chỉ cập nhật 3 ô Chi phí, Impression, Click của dòng đó.
2. Nếu CHƯA có → thêm dòng mới ngay dưới dòng dữ liệu cuối cùng của bảng (giữ thứ tự ngày tăng dần, các dòng cùng ngày đứng liền nhau theo đúng thứ tự trong dữ liệu), rồi nhập ĐỦ 8 trường: Ngày (dd/mm/yyyy, đúng định dạng ngày của các dòng phía trên), Week, Hình thức, TKQC, Target, Chi phí, Impression, Click.
3. Chỉ số ghi dạng SỐ thuần (không dấu phân cách hàng nghìn, không ký hiệu tiền). Chi phí đơn vị [USD/VND]; dấu chấm trong dữ liệu là dấu THẬP PHÂN — nếu sheet dùng định dạng Việt Nam thì đổi sang dấu phẩy thập phân cho đúng giá trị.
4. Định dạng (dropdown, viền, font) của dòng mới phải giống các dòng phía trên. Các cột khác ngoài 8 trường trên: để trống hoặc kéo công thức xuống nếu cột đó là công thức.
5. MÀU CHIP — kiểm tra và chỉnh lại màu cho TẤT CẢ các dòng vừa nhập/cập nhật:
   - Cột Hình thức (E): "Conversion" = nền đỏ đậm #B10202, chữ trắng hồng #FFCFC9.
   - Cột TKQC (F): "Facebook" = nền xanh dương nhạt #BFE1F6, chữ xanh dương #0A53A8; "Google" = nền xanh lá nhạt #D4EDBC, chữ xanh lá #11734B.
   - Nếu chip chưa đúng màu, sửa màu của lựa chọn đó trong quy tắc dropdown (Xác thực dữ liệu) hoặc copy định dạng từ dòng phía trên có cùng giá trị.
6. KHÔNG sửa, xoá dữ liệu của các dòng/ngày khác.
7. Xong thì báo: số dòng đã cập nhật + số dòng đã thêm mới + dòng nào gặp lỗi (nếu có).

DỮ LIỆU (Ngày | Week | Hình thức | TKQC | Target | Chi phí | Impression | Click):
22/10/2026 | Thứ Năm | Conversion | Facebook | LAL MKT | 1250000 | 45210 | 380
22/10/2026 | Thứ Năm | Conversion | Google | Google SEM.SDA | 830000 | 2100 | 145
...
````

## Common Mistakes (riêng QH)

| Sai | Đúng |
|---|---|
| `ReMKT_ASC` khớp nhầm với `_ReMKT_CountryGroups.ASC` | Key dài khớp trước; 2 key này khác nhau hoàn toàn |
| Ghi Target sai chính tả (`LAL MKT Countries`) | Copy y nguyên từ bảng mapping (`LKL MKT Countries`) |
