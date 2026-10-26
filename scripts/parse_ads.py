#!/usr/bin/env python3
"""
parse_ads.py — Doc file export Facebook / Google / TikTok Ads (CSV/XLSX), map ten campaign
theo parts/<part>/mapping.json, gop chi so theo (Ngay, dong sheet = Hinh thuc | TKQC | Target).

Usage:
  python parse_ads.py --part dnd --fb a.csv [--fb b.csv] [--google g.csv] [--tiktok t.xlsx]
  python parse_ads.py <file_fb.csv> --part qh          # file khong kem co = Facebook

Options:
  --part    : part bao cao (ten thu muc trong parts/), mac dinh qh.
  --date    : DD/MM/YYYY — ep ngay cho toan bo file (file khong co cot Ngay / Day).
  --clicks  : (Facebook) link = Link clicks (mac dinh), all = Clicks (all).
  --json    : in JSON thay vi bang TSV.

Schema rule trong mapping.json:
  key | all     : 1 chuoi (key) hoac list chuoi (all) — ten campaign phai chua TAT CA. all=[] = bat moi campaign.
  source        : facebook | google | tiktok (bo trong = moi nguon).
  account       : (tuy chon) ID tai khoan — chi kiem tra neu file co cot Account ID.
  hinh_thuc, tkqc, target : gia tri dien vao sheet (target co the bo trong).
  metrics       : list chi so dien cho dong nay (mac dinh = default_metrics cua part).
  copy          : {"reach": "impression"} — lay gia tri chi so khac.
  redirect      : {"tin_nhan": {"hinh_thuc": ..., "tkqc": ...}} — cong chi so sang dong khac.
  optional      : true = (khi fill_all_rows) chi xuat dong nay khi co so lieu.
Part-level: columns (thu tu cot output), labels (doi ten header), default_metrics, fill_all_rows
(true = moi ngay du tat ca dong, khong co so lieu thi de trong).
Cot ngay co the dung: ngay (dd/mm/yyyy), week (Thu), month, iso_week, year, date_mdy (mm/dd/yyyy), thu.
"""
import argparse
import csv
import io
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent.parent
PARTS_DIR = HERE / "parts"

WEEKDAYS_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
METRICS = ["chi_phi", "reach", "impression", "click", "tin_nhan", "ket_qua"]
LABELS = {
    "ngay": "Ngày", "week": "Week", "hinh_thuc": "Hình thức", "tkqc": "TKQC", "target": "Target",
    "chi_phi": "Chi phí", "reach": "Reach", "impression": "Impression", "click": "Click",
    "tin_nhan": "Tin nhắn (Message)", "ket_qua": "Kết quả",
    "month": "Month", "iso_week": "Week No", "year": "Year", "date_mdy": "Date (mm/dd/yyyy)", "thu": "Thứ",
}


def norm(s) -> str:
    """lowercase, bo dau tieng Viet, gop khoang trang."""
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D")
    return re.sub(r"\s+", " ", s).strip().lower()


# Ten cot (da norm) — uu tien theo thu tu trong list. Dung chung cho FB / Google / TikTok (EN + VI).
COLS = {
    "campaign": ["campaign name", "ten chien dich", "chien dich", "campaign", "id chien dich", "campaign id"],
    "adset": ["ad set name", "ten nhom quang cao", "nhom quang cao", "ad set", "ad group name", "ad group"],
    "ad": ["ad name", "ten quang cao", "quang cao"],
    "account": ["account id", "id tai khoan", "advertiser id", "id nha quang cao", "customer id", "id khach hang"],
    "day": ["day", "ngay", "date", "by day", "theo ngay"],
    "start": ["reporting starts", "bat dau bao cao", "luot bat dau bao cao"],
    "end": ["reporting ends", "ket thuc bao cao", "luot ket thuc bao cao"],
    "currency": ["currency code", "currency", "ma don vi tien te", "ma tien te", "don vi tien te", "tien te"],
    "spend": ["amount spent (vnd)", "so tien da chi tieu (vnd)", "amount spent", "so tien da chi tieu",
              "chi tieu", "chi phi", "cost", "spend", "total cost", "tong chi phi"],
    "reach": ["reach", "nguoi tiep can", "luot tiep can", "pham vi tiep can", "tiep can"],
    "impr": ["impressions", "luot hien thi", "so lan hien thi", "lan hien thi", "so luot hien thi",
             "impr.", "impression", "hien thi"],
    "click_link": ["link clicks", "luot click vao lien ket", "so lan nhap vao lien ket", "luot nhap vao lien ket"],
    "click_all": ["clicks (all)", "luot click (tat ca)", "so lan nhap (tat ca)", "luot nhap (tat ca)",
                  "clicks", "luot click", "luot nhap", "so luot nhap", "so lan nhap"],
    "click_inter": ["interactions", "luot tuong tac", "so luot tuong tac"],
    "msg": ["messaging conversations started", "luot bat dau cuoc tro chuyen qua tin nhan",
            "cuoc tro chuyen qua tin nhan da bat dau", "so cuoc tro chuyen qua tin nhan da bat dau",
            "cuoc tro chuyen (tin nhan truc tiep tren tiktok)",
            "conversations", "cuoc tro chuyen", "so cuoc tro chuyen", "tin nhan"],
    "results": ["results", "ket qua", "leads", "khach hang tiem nang", "on-facebook leads"],
}
NAME_ALIASES = set(COLS["campaign"])
TOTAL_RE = re.compile(r"^(tong|total)(\b|:)")
COST_PER_RE = re.compile(r"\b(per|moi|tren moi|cho moi|cpa|cpc|cpm|cpl)\b")


def find_col(columns, key):
    normed = {norm(c): c for c in columns}
    for cand in COLS[key]:
        if cand in normed:
            return normed[cand]
    # fallback: startswith (vd "Amount spent (USD)"), tranh nham "Chi phi cho moi..."
    for cand in COLS[key]:
        for n, orig in normed.items():
            if n.startswith(cand) and not (key == "spend" and COST_PER_RE.search(n)):
                return orig
    return None


def _find_header_line(lines):
    """Google Ads CSV co 1-2 dong tieu de/khoang ngay truoc header -> tim dong chua cot ten campaign."""
    for i, line in enumerate(lines[:30]):
        for delim in ("\t", ",", ";"):
            cells = next(csv.reader([line], delimiter=delim), [])
            if len(cells) > 1 and any(norm(c) in NAME_ALIASES for c in cells):
                return i, delim
    return None, None


def read_any(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        raw = pd.read_excel(path, header=None, dtype=object)
        for i in range(min(30, len(raw))):
            if any(norm(c) in NAME_ALIASES for c in raw.iloc[i].tolist() if isinstance(c, str)):
                df = raw.iloc[i + 1:].copy()
                df.columns = [str(c) for c in raw.iloc[i].tolist()]
                df = df.reset_index(drop=True)
                df.attrs["preamble"] = [
                    " ".join(str(x) for x in raw.iloc[r].tolist() if pd.notna(x)) for r in range(i)
                ]
                return df
        return pd.read_excel(path)
    last_err = None
    for enc in ("utf-8-sig", "utf-16", "cp1258", "latin-1"):
        try:
            text = path.read_text(encoding=enc)
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue
        lines = text.splitlines()
        idx, delim = _find_header_line(lines)
        if idx is None:
            last_err = f"khong thay dong header (encoding {enc})"
            continue
        df = pd.read_csv(io.StringIO("\n".join(lines[idx:])), sep=delim, dtype=str, engine="python")
        df.attrs["preamble"] = lines[:idx]
        return df
    raise RuntimeError(f"Khong doc duoc file {path}: {last_err}")


def to_num(v) -> float:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d.,\-]", "", str(v))
    if not s or s in "-.,":
        return 0.0
    if "," in s and "." in s:
        # dau xuat hien sau cung la dau thap phan
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif s.count(".") > 1 or (s.count(".") == 1 and len(s.split(".")[1]) == 3):
        s = s.replace(".", "")  # 1.234.567 -> nghin
    elif s.count(",") > 1 or (s.count(",") == 1 and len(s.split(",")[1]) == 3):
        s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def fmt_money(x: float):
    """Giu 2 so thap phan (USD); so nguyen thi bo .0 (VND)."""
    x = round(x, 2)
    return int(x) if x == int(x) else x


def parse_date(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (datetime, pd.Timestamp)):
        return pd.Timestamp(v).date()
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    m = re.search(r"(\d{1,2})\s*thang\s*(\d{1,2}),?\s*(\d{4})", norm(s))  # "T5, 22 tháng 10, 2026"
    if m:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).date()
    try:
        return pd.to_datetime(s, dayfirst=True).date()
    except Exception:  # noqa: BLE001
        return None


def norm_acct(v) -> str:
    """ID tai khoan -> chuoi so (Excel co the doc thanh float 1.465e15)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, (int, float)):
        return str(int(v))
    s = re.sub(r"\.0+$", "", str(v).strip())
    return re.sub(r"\D", "", s)


def rid(r) -> tuple:
    return (r["hinh_thuc"], r["tkqc"], r.get("target", "") or "")


def rule_keys(r):
    return [r["key"]] if "key" in r else list(r.get("all", []))


def load_part(part: str) -> dict:
    mapping_file = PARTS_DIR / part / "mapping.json"
    if not mapping_file.exists():
        avail = sorted(p.name for p in PARTS_DIR.iterdir() if (p / "mapping.json").exists())
        sys.exit(f"Khong co part '{part}'. Cac part hien co: {avail}")
    cfg = json.loads(mapping_file.read_text(encoding="utf-8"))
    cfg.setdefault("columns", ["ngay", "week", "hinh_thuc", "tkqc", "target", "chi_phi", "impression", "click"])
    cfg.setdefault("default_metrics", ["chi_phi", "impression", "click"])
    cfg.setdefault("fill_all_rows", False)
    order = {}
    for r in cfg["rules"]:
        order.setdefault(rid(r), len(order))
    for r in cfg["rules"]:
        for m, t in r.get("redirect", {}).items():
            if rid(t) not in order:
                sys.exit(f"mapping.json: redirect {m} -> {rid(t)} khong ton tai trong rules")
    cfg["_order"] = order
    return cfg


def match(names, acct, rules):
    for nm in names:
        n = nm.lower()
        for r in rules:
            if r.get("account") and acct and r["account"] != acct:
                continue
            if all(k.lower() in n for k in rule_keys(r)):
                return r
    return None


def apply_rule(rule, d, vals, cfg, agg):
    metrics = rule.get("metrics") or cfg["default_metrics"]
    copy = rule.get("copy", {})
    redirect = rule.get("redirect", {})
    g = agg.setdefault((d, rid(rule)), {})
    for m in metrics:
        if m in redirect:
            continue
        src_m = copy.get(m, m)
        if src_m in vals:
            g[m] = g.get(m, 0.0) + vals[src_m]
    for m, target in redirect.items():
        if vals.get(m):  # chi chuyen khi > 0, tranh bien o trong thanh 0
            t = agg.setdefault((d, rid(target)), {})
            t[m] = t.get(m, 0.0) + vals[m]


def process_file(src, path, cfg, a, forced, st):
    tag = f"[{src}:{path.name}]"
    df = read_any(path)
    cols = {k: find_col(df.columns, k) for k in COLS}
    name_cols = [cols[k] for k in ("campaign", "adset", "ad") if cols[k]]
    if not name_cols:
        st["warnings"].append(f"{tag} Khong tim thay cot ten campaign -> BO QUA file. Cac cot: {list(df.columns)}")
        return
    if src == "facebook":
        click_col = cols["click_link"] if a.clicks == "link" else cols["click_all"]
        click_col = click_col or cols["click_all"] or cols["click_link"]
    else:
        click_col = cols["click_all"] or cols["click_inter"] or cols["click_link"]
    metric_col = {"chi_phi": cols["spend"], "reach": cols["reach"], "impression": cols["impr"],
                  "click": click_col, "tin_nhan": cols["msg"], "ket_qua": cols["results"]}

    rules = [r for r in cfg["rules"] if r.get("source") in (None, src)]
    rules.sort(key=lambda r: (len(rule_keys(r)) > 0, sum(len(k) for k in rule_keys(r))), reverse=True)
    if not rules:
        st["warnings"].append(f"{tag} Part '{a.part}' khong co rule cho nguon {src} — tat ca vao UNMAPPED.")

    needed = set()
    for r in rules:
        ms = r.get("metrics") or cfg["default_metrics"]
        needed |= {r.get("copy", {}).get(m, m) for m in ms} | set(r.get("redirect", {}))
    for m in sorted(needed):
        if not metric_col.get(m):
            st["warnings"].append(f"{tag} Thieu cot '{LABELS[m]}' -> chi so nay se de TRONG.")

    preamble_date = None
    if not forced and not cols["day"]:
        if cols["start"] and cols["end"]:
            s = df[cols["start"]].dropna().map(parse_date).unique()
            e = df[cols["end"]].dropna().map(parse_date).unique()
            if len(s) == 1 and len(e) == 1 and s[0] != e[0]:
                st["warnings"].append(f"{tag} File la tong khoang {s[0]} -> {e[0]}, KHONG tach theo ngay. Hoi user ngay hoac export lai theo Day.")
        elif not cols["start"]:
            for pline in df.attrs.get("preamble", []):
                clean_line = pline.strip().strip('"').strip("'")
                parts = re.split(r"\s*[-–—]\s*", clean_line)
                if len(parts) == 2:
                    d1, d2 = parse_date(parts[0]), parse_date(parts[1])
                    if d1 and d2:
                        if d1 == d2:
                            preamble_date = d1
                        else:
                            st["warnings"].append(f"{tag} File la tong khoang {d1} -> {d2}, KHONG tach theo ngay. Hoi user ngay hoac export lai theo Day.")
                        break
            if not preamble_date:
                st["warnings"].append(f"{tag} File khong co cot ngay — can hoi user ngay bao cao (dung --date).")

    currency = "?"
    cur = re.search(r"\(([A-Za-z]{3})\)", str(cols["spend"]))
    if cur:
        currency = cur.group(1).upper()
    elif cols["currency"]:
        vals_cur = df[cols["currency"]].dropna().astype(str).str.strip().unique()
        if len(vals_cur):
            currency = vals_cur[0].upper()
    st["files"].append({"file": path.name, "source": src, "currency": currency,
                        "columns_used": {k: v for k, v in cols.items() if v} | {"click_used": click_col}})

    for _, row in df.iterrows():
        names = [str(row[c]).strip() for c in name_cols
                 if isinstance(row[c], str) and row[c].strip() and row[c].strip() != "--"]
        if not names:
            continue  # dong trong
        if any(isinstance(v, str) and TOTAL_RE.match(norm(v)) for v in row.tolist()):
            continue  # dong Tong / Total
        acct = norm_acct(row[cols["account"]]) if cols["account"] else ""
        rule = match(names, acct, rules)
        if forced:
            d = forced
        elif cols["day"]:
            d = parse_date(row[cols["day"]])
        elif cols["start"]:
            d = parse_date(row[cols["start"]])
        else:
            d = preamble_date
        st["dates"].add(d)
        vals = {m: to_num(row[c]) for m, c in metric_col.items() if c}
        if rule is None:
            u = st["unmapped"].setdefault((src, str(d), names[0]), {m: 0.0 for m in METRICS})
            for m, v in vals.items():
                u[m] += v
            continue
        apply_rule(rule, d, vals, cfg, st["agg"])


def fmt_val(m, v):
    if v is None:
        return ""
    return fmt_money(v) if m == "chi_phi" else round(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", help="file Facebook (khong kem co)")
    ap.add_argument("--part", default="qh", type=str.lower, help="qh | dnd | ... (thu muc trong parts/)")
    ap.add_argument("--fb", action="append", default=[], help="file Facebook Ads")
    ap.add_argument("--google", action="append", default=[], help="file Google Ads")
    ap.add_argument("--tiktok", action="append", default=[], help="file TikTok Ads")
    ap.add_argument("--date", help="DD/MM/YYYY — ep ngay cho toan bo file")
    ap.add_argument("--clicks", choices=["link", "all"], default="link")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    cfg = load_part(a.part)
    jobs = ([("facebook", f) for f in a.files + a.fb] + [("google", f) for f in a.google]
            + [("tiktok", f) for f in a.tiktok])
    if not jobs:
        sys.exit("Can it nhat 1 file (--fb / --google / --tiktok).")
    forced = datetime.strptime(a.date, "%d/%m/%Y").date() if a.date else None
    st = {"agg": {}, "unmapped": {}, "dates": set(), "warnings": [], "files": []}
    if not cfg["rules"]:
        st["warnings"].append(f"Part '{a.part}' CHUA CO mapping — tat ca campaign se vao UNMAPPED. Lam onboarding theo parts/{a.part}/PART.md.")
    for src, f in jobs:
        process_file(src, Path(f), cfg, a, forced, st)

    order = cfg["_order"]
    if forced:
        st["dates"].add(forced)
    if cfg["fill_all_rows"]:
        dates = sorted(st["dates"], key=lambda d: (d is None, str(d)))
        rids = sorted(order, key=order.get)
        optional = {rid(r) for r in cfg["rules"] if r.get("optional")}
        keys = [(d, r) for d in dates for r in rids if r not in optional or (d, r) in st["agg"]]
        sources = {s for s, _ in jobs}
        missing = sorted({r.get("source") for r in cfg["rules"] if r.get("source")} - sources)
        if missing:
            st["warnings"].append(f"Khong co file nguon: {missing} -> cac dong nguon nay de TRONG.")
    else:
        keys = sorted(st["agg"], key=lambda k: (str(k[0]), order[k[1]]))

    out = []
    for d, r in keys:
        g = st["agg"].get((d, r), {})
        row = {"ngay": d.strftime("%d/%m/%Y") if d else "?", "week": WEEKDAYS_VI[d.weekday()] if d else "?",
               "month": d.month if d else "?", "iso_week": d.isocalendar()[1] if d else "?",
               "year": d.year if d else "?", "date_mdy": d.strftime("%m/%d/%Y") if d else "?",
               "thu": WEEKDAYS_VI[d.weekday()] if d else "?",
               "hinh_thuc": r[0], "tkqc": r[1], "target": r[2]}
        for m in METRICS:
            row[m] = fmt_val(m, g.get(m))
        out.append(row)

    meta = {
        "part": a.part,
        "columns": cfg["columns"],
        "files": st["files"],
        "warnings": st["warnings"],
        "unmapped": [
            {"source": k[0], "ngay": k[1], "name": k[2], **{m: fmt_val(m, v) for m, v in u.items()}}
            for k, u in st["unmapped"].items()
        ],
    }

    if a.json:
        print(json.dumps({"rows": [{c: r[c] for c in cfg["columns"]} for r in out], **meta},
                         ensure_ascii=False, indent=2))
        return
    labels = LABELS | cfg.get("labels", {})
    print("\t".join(labels[c] for c in cfg["columns"]))
    for r in out:
        print("\t".join(str(r[c]) for c in cfg["columns"]))
    print("\n# part:", a.part)
    for f in st["files"]:
        print(f"# file: [{f['source']}] {f['file']} | currency: {f['currency']} | columns_used: "
              + json.dumps(f["columns_used"], ensure_ascii=False))
    for w in st["warnings"]:
        print("# WARNING:", w)
    if meta["unmapped"]:
        print("# UNMAPPED (khong khop mapping, KHONG dua vao bao cao): nguon | ngay | ten | chi phi | reach | impression | click | tin nhan")
        for u in meta["unmapped"]:
            print(f"#   {u['source']} | {u['ngay']} | {u['name']} | {u['chi_phi']} | {u['reach']} | "
                  f"{u['impression']} | {u['click']} | {u['tin_nhan']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
