# PART HLW (HelianWell) — `/reports hlw`

> Trạng thái: **ĐÃ CẤU HÌNH (Cơ bản)**. Workflow chung xem [../../SKILL.md](../../SKILL.md).
> Chạy script: `python "<skill_dir>/scripts/parse_ads.py" "<file FB>" --part hlw`
> Nếu gửi ảnh chụp Ads Manager → đọc trực tiếp từ ảnh theo bảng mapping bên dưới.
> Chỉ xuất dòng chiến dịch **có phát sinh số liệu** trong ngày (bỏ qua chiến dịch đang tắt có chi tiêu `0,00 $` và chỉ số `—`).

## Bảng mapping (source of truth: [mapping.json](mapping.json))

| Key trong tên campaign | Hình thức | TKQC | Target |
|---|---|---|---|
| `HelianWell` + `Leadform` + `ASC.Parents.S1` | Leadform | Facebook | ASC.Parents.S1 |
| `HelianWell` + `Conversion` + `ASC.Parents.S1` | Conversion | Facebook | ASC.Parents.S1 |
| `HelianWell_Leadform` *(fallback)* | Leadform | Facebook | HelianWell |
| `HelianWell_Conversion` *(fallback)* | Conversion | Facebook | HelianWell |

> Thêm mapping mới → sửa **cả** `mapping.json` **và** bảng này.

## Quy tắc riêng HLW

- **Đơn vị tiền tệ**: **USD** (`$`) — giữ 2 chữ số thập phân, dùng dấu chấm thập phân (vd `63,43 $` → `63.43`).
- **Click FB**: dùng cột **Lượt click vào liên kết** (Link clicks).
- **Kết quả (Lead)**: lấy cột **Kết quả** (Results / Mẫu tìm kiếm khách hàng tiềm năng).
- **Các cột tính toán** (CPL / Chi phí trên mỗi kết quả, CPC, CTR, CPM, Tần suất): để sheet tự nhảy công thức (hoặc kéo công thức từ dòng trên xuống).
- Chiến dịch tắt không thuộc HelianWell hoặc không chi tiêu (`0,00 $`, chỉ số `—`, vd `EAM//Acquisition/US/CBO`) → ghi chú nhẹ ở phần kiểm tra, không đưa vào prompt điền sheet.

## Cột bảng kiểm tra ①

| Ngày | Week | Hình thức | TKQC | Target | Chi phí (USD) | Reach | Impression | Click | Kết quả (Lead) |
|---|---|---|---|---|---|---|---|---|---|

## Prompt Gemini mẫu ② (Cơ bản)

````
Bạn đang làm việc trên sheet hiện tại. Hãy TỰ NHẬP dữ liệu báo cáo quảng cáo HelianWell bên dưới vào sheet.

CÁCH NHẬP:
1. Xác định các cột tương ứng trên hàng tiêu đề (header) của sheet hiện tại: Ngày (Date), Thứ (Week), Hình thức / Chiến dịch, TKQC (Kênh), Target, Chi phí (Spend/Cost), Reach (Người tiếp cận), Impression (Lượt hiển thị), Click (Lượt click liên kết), Kết quả / Lead. (Sheet không có cột nào trong số này thì bỏ qua cột đó).
2. Nếu sheet ĐÃ có dòng trùng Ngày + Hình thức + Target → chỉ cập nhật các ô chỉ số của dòng đó.
3. Nếu CHƯA có → thêm dòng mới ngay dưới dòng dữ liệu cuối cùng (giữ đúng định dạng ngày, viền, font, dropdown của dòng phía trên) và điền số liệu.
4. Chỉ số ghi dạng SỐ thuần (không ký hiệu $, không dấu phân cách hàng nghìn). Chi phí tính bằng USD, dấu chấm (.) là dấu thập phân (nếu sheet đang để locale Việt Nam dùng dấu phẩy thập phân thì tự chuyển sang dấu phẩy để đúng giá trị số).
5. Các cột công thức (như CPL / Chi phí trên mỗi kết quả, CPC, CTR, CPM, Tần suất): KHÔNG nhập tay mà kéo/copy công thức từ dòng phía trên xuống.
6. KHÔNG sửa hoặc xoá dữ liệu của các ngày khác. Xong thì báo lại dòng đã thêm/cập nhật.

DỮ LIỆU (Ngày | Week | Hình thức | TKQC | Target | Chi phí (USD) | Reach | Impression | Click | Kết quả):
22/10/2026 | Thứ Năm | Leadform | Facebook | ASC.Parents.S1 | 63.43 | 1626 | 2024 | 63 | 8
````
