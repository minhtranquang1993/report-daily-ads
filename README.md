# /reports — Báo cáo Ads hằng ngày → Prompt Gemini Google Sheets

Skill cho Claude Code / Antigravity: đọc số liệu **Facebook Ads, Google Ads, TikTok Ads, GPT Ads** (file CSV/Excel
hoặc ảnh), map tên campaign theo bảng chuẩn của từng **part** (QH, DND, …), rồi xuất:

1. **Bảng kiểm tra** để soát số.
2. **Prompt dán vào Gemini trong Google Sheets** để Gemini tự điền số vào sheet.
3. **TSV dự phòng** để copy-paste tay nếu Gemini lỗi.

## Cách dùng

| Lệnh | Ý nghĩa |
|---|---|
| `/reports qh` + file/ảnh | Báo cáo part QH (lệnh cũ `/report-qh` vẫn hiểu là QH) |
| `/reports dnd` + file/ảnh | Báo cáo part DND |
| `/reports` | Tự đoán part từ tên campaign, không đoán được thì hỏi |

Nguồn nào không gửi thì bỏ qua. Ảnh không thấy ngày thì skill hỏi 1 câu.

## Cấu trúc

```
reports/
├── SKILL.md              # Router + workflow chung cho mọi part
├── README.md             # File này
├── parts/
│   ├── qh/
│   │   ├── PART.md       # Mapping, cấu trúc sheet, màu chip, prompt Gemini mẫu của QH
│   │   └── mapping.json  # Source of truth mapping QH (script đọc file này)
│   └── dnd/
│       ├── PART.md
│       └── mapping.json
└── scripts/
    └── parse_ads.py      # Đọc file FB/Google/TikTok, map + gộp, in TSV
```

## Chạy script tay (khi cần kiểm tra)

```powershell
# QH — file Facebook
python scripts/parse_ads.py "fb.csv" --part qh

# DND — đủ 3 nguồn, nhiều file FB thì lặp --fb
python scripts/parse_ads.py --part dnd --fb "fb_tk1.csv" --fb "fb_tk2.csv" --google "gg.csv" --tiktok "tt.xlsx"

# Tuỳ chọn
--date 22/10/2026   # file không có cột ngày
--clicks all        # FB dùng Clicks (all) thay vì Link clicks
--json              # in JSON
```

Yêu cầu: Python 3.9+, `pandas`, `openpyxl` (`pip install pandas openpyxl`).

Output cuối có các dòng `# WARNING` (thiếu cột, file gộp nhiều ngày, thiếu nguồn) và `# UNMAPPED`
(campaign không khớp rule nào → không đưa vào báo cáo, cần bổ sung mapping).

## Lưu ý khi export file

| Nguồn | Cần có |
|---|---|
| Facebook | Breakdown theo **Day** (Ngày). Cột: tên chiến dịch, số tiền đã chi tiêu, **người tiếp cận (Reach)**, lượt hiển thị, **lượt bắt đầu cuộc trò chuyện qua tin nhắn** (DND), link clicks (QH). Mỗi TK quảng cáo 1 file cũng được. Có thêm cột Account ID thì script kiểm tra luôn TK. |
| Google Ads | Phân đoạn theo **Ngày**. Cột: chiến dịch, chi phí, số lần hiển thị, lượt nhấp. File có dòng tiêu đề / dòng "Tổng" ở đầu-cuối không sao, script tự bỏ. |
| TikTok | Theo ngày. Cột: campaign name, cost, reach (phạm vi tiếp cận), impressions (lần hiển thị), conversations (cuộc trò chuyện). Dòng "Total of …" tự bỏ. |

- File FB chỉ có "Bắt đầu/Kết thúc báo cáo" khác ngày nhau = **tổng nhiều ngày** → script cảnh báo, nên export lại theo Day.
- Tiền VND ghi số nguyên; USD giữ 2 số lẻ (script tự nhận đơn vị từ header `(VND)`/`(USD)` hoặc cột mã tiền tệ).
- **Reach** nhiều campaign cùng dòng được **cộng thẳng** (không khử trùng người dùng như Ads Manager).

## Thêm / sửa mapping

1. Sửa `parts/<part>/mapping.json` (script dùng file này).
2. Sửa **bảng mapping trong `parts/<part>/PART.md`** cho khớp (Claude đọc file này khi đọc ảnh).

Schema 1 rule:

```jsonc
{
  "source": "facebook",            // facebook | google | tiktok — bỏ trống = mọi nguồn
  "account": "1465106504558065",   // tuỳ chọn, chỉ check khi file có cột Account ID
  "all": ["PFM_PTKX_", "_DNDA_"],  // tên campaign phải chứa TẤT CẢ (không phân biệt hoa thường); [] = mọi campaign
  // hoặc "key": "lead_title"      // 1 chuỗi
  "hinh_thuc": "Message - Khúc Xạ",
  "tkqc": "DND Sài Gòn",
  "target": "",                    // QH dùng, DND bỏ
  "metrics": ["chi_phi", "reach", "impression", "tin_nhan"],  // chỉ số điền cho dòng này
  "copy": { "reach": "impression" },                          // lấy giá trị chỉ số khác
  "redirect": { "tin_nhan": { "hinh_thuc": "...", "tkqc": "..." } },  // cộng chỉ số sang dòng khác
  "optional": true                 // chỉ xuất dòng khi có số liệu
}
```

Cấp part: `columns` (thứ tự cột output), `labels` (đổi tên header), `default_metrics`, `fill_all_rows`
(`true` = mỗi ngày đủ mọi dòng, không có số thì để trống), `colors` (màu chip).
Thứ tự `rules` = thứ tự dòng trong sheet. Rule cụ thể hơn (tổng độ dài chuỗi lớn hơn) được khớp trước.

## Thêm part mới (vd `abc`)

1. Tạo `parts/abc/mapping.json` (copy từ part gần giống nhất) và `parts/abc/PART.md`.
2. Thêm dòng vào bảng "Chọn PART" trong `SKILL.md`.
3. Hoặc gõ `/reports abc` + gửi dữ liệu + ảnh sheet mẫu → nhờ Claude onboarding giúp.

## Tóm tắt quy tắc từng part

**QH** — chỉ xuất Target có số liệu. Cột: Ngày (dd/mm/yyyy) · Week (Thứ) · Hình thức · TKQC · Target · Chi phí ·
Impression · Click.

**DND** — mỗi ngày đủ 8 dòng cố định (Branding, Message Lão Thị / Khúc Xạ / Phaco / Kid, Google Search - Khúc Xạ,
Tiktok Branding / Message), không có số thì để trống; Event - CVS / Event - Live chỉ thêm khi có số liệu.
Cột nhập: Date (**mm/dd/yyyy**) · Hình thức · TKQC · Total Cost · Reach · Impression · Click · Tin nhắn.
Month / Week / Year / Thứ / CPM / CPC / Cost per Message là **công thức trong sheet** → không nhập.
Tin nhắn của Branding cộng sang Message - Khúc Xạ (chi phí/reach/impression Branding giữ riêng).
Google gộp 1 dòng, Reach = Impression.

## Đồng bộ nhiều nơi

Skill đang nằm ở 2 chỗ trên máy:

- `~/.claude/skills/reports` — **bản gốc**, là git repo này (nested repo trong repo `claude-skill`, đã được
  `.gitignore` ở repo cha).
- `~/.gemini/config/skills/reports` — bản copy cho Antigravity.

Sửa ở bản gốc rồi copy sang bản Gemini (hoặc dùng skill `sync-skills`). `/push` và `/pull` tự nhận nested repo
này nên không cần làm gì thêm.

Cài trên máy khác:

```bash
git clone https://github.com/minhtranquang1993/report-daily-ads.git ~/.claude/skills/reports
```
