#!/usr/bin/env python3
"""
fetch_leads.py — Dem Lead Tong / Dat lich / Da kham tu Supabase (bang status_data, project data-ads)
theo cau hinh "leads" trong parts/<part>/mapping.json, gop theo (Ngay, dong sheet = Hinh thuc | TKQC).

CHI DOC (session read-only). Dung doc lap hoac duoc parse_ads.py goi tu dong.

Usage:
  python fetch_leads.py --part dnd --date 03/11/2026 [--date 04/11/2026]
  python fetch_leads.py --part dnd --from 01/11/2026 --to 03/11/2026 [--json]

macOS / chua cai psycopg global:
  uv run -q --with "psycopg[binary]" python3 fetch_leads.py --part dnd --date 03/11/2026

Ket noi DB (thu theo thu tu):
  1. env DATA_ADS_DB_URL = postgres URL day du.
  2. Thu muc repo data-ads: env DATA_ADS_DIR -> di nguoc len tu CWD -> ~/Downloads/data-ads.
     Doc host/user tu `supabase/.temp/pooler-url`, password tu `.env.local` (SUPABASE_DB_PASSWORD).

Cau hinh "leads" (mapping.json):
  timezone      : mui gio de cat ngay (mac dinh Asia/Ho_Chi_Minh).
  zero_as_blank : true = so 0 xuat la o trong.
  metrics       : {ten: {"date": "created_at"|"updated_at", "statuses": [..] | null (= moi trang thai)}}
  groups        : list {nguon: [..], loai_dich_vu: [..] (bo trong = moi loai con lai), hinh_thuc, tkqc}
                  -> khop group DAU TIEN (theo thu tu trong list), so sanh khong phan biet hoa thuong.
  Dem theo SO DONG status_data (giong bo loc tab Khach hang), khong gop theo SDT.
"""
import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse

HERE = Path(__file__).resolve().parent.parent
PARTS_DIR = HERE / "parts"
LEAD_LABELS = {"lead_tong": "Lead Tổng", "dat_lich": "Đặt Lịch / XN tham gia", "da_kham": "Đã Khám"}


class LeadsError(RuntimeError):
    pass


def load_leads_cfg(part: str) -> dict | None:
    f = PARTS_DIR / part / "mapping.json"
    if not f.exists():
        raise LeadsError(f"Khong co parts/{part}/mapping.json")
    cfg = json.loads(f.read_text(encoding="utf-8"))
    return cfg.get("leads")


def _find_data_ads_dir() -> Path | None:
    cands = []
    if os.environ.get("DATA_ADS_DIR"):
        cands.append(Path(os.environ["DATA_ADS_DIR"]).expanduser())
    cwd = Path.cwd().resolve()
    cands += [cwd, *cwd.parents]
    cands.append(Path.home() / "Downloads" / "data-ads")
    for c in cands:
        if (c / "supabase" / ".temp" / "pooler-url").exists() and (c / ".env.local").exists():
            return c
    return None


def _conn_kwargs() -> dict:
    url = os.environ.get("DATA_ADS_DB_URL")
    if url:
        return {"conninfo": url}
    root = _find_data_ads_dir()
    if not root:
        raise LeadsError("Khong tim thay repo data-ads (can supabase/.temp/pooler-url + .env.local). "
                         "Dat env DATA_ADS_DIR=<duong dan repo> hoac DATA_ADS_DB_URL=<postgres url>.")
    u = urlparse((root / "supabase" / ".temp" / "pooler-url").read_text(encoding="utf-8").strip())
    pw = None
    for line in (root / ".env.local").read_text(encoding="utf-8").splitlines():
        if line.startswith("SUPABASE_DB_PASSWORD="):
            pw = line.split("=", 1)[1].strip()
    if not pw:
        raise LeadsError(f"{root}/.env.local thieu SUPABASE_DB_PASSWORD")
    return {"host": u.hostname, "port": u.port or 5432, "user": unquote(u.username or ""),
            "password": pw, "dbname": "postgres", "sslmode": "require", "connect_timeout": 15}


def _fetch_rows(cfg: dict, dates: list[date]) -> list[tuple]:
    try:
        import psycopg  # noqa: PLC0415
    except ImportError as e:
        raise LeadsError('Thieu thu vien psycopg — chay qua: uv run -q --with "psycopg[binary]" python3 ...') from e
    tz = cfg.get("timezone", "Asia/Ho_Chi_Minh")
    nguon = sorted({n.lower() for g in cfg["groups"] for n in g["nguon"]})
    lo, hi = min(dates), max(dates) + timedelta(days=1)
    sql = """
        SELECT lower(coalesce(nguon, '')), lower(coalesce(loai_dich_vu, '')), coalesce(trang_thai_lead, ''),
               (created_at AT TIME ZONE %(tz)s)::date, (updated_at AT TIME ZONE %(tz)s)::date
        FROM status_data
        WHERE lower(nguon) = ANY(%(nguon)s)
          AND ((created_at AT TIME ZONE %(tz)s)::date >= %(lo)s AND (created_at AT TIME ZONE %(tz)s)::date < %(hi)s
            OR (updated_at AT TIME ZONE %(tz)s)::date >= %(lo)s AND (updated_at AT TIME ZONE %(tz)s)::date < %(hi)s)
    """
    kw = _conn_kwargs()
    conninfo = kw.pop("conninfo", "")
    try:
        with psycopg.connect(conninfo, **kw) as conn:
            conn.read_only = True
            with conn.cursor() as cur:
                cur.execute(sql, {"tz": tz, "nguon": nguon, "lo": lo, "hi": hi})
                return cur.fetchall()
    except psycopg.Error as e:
        raise LeadsError(f"Loi truy van Supabase: {e}") from e


def _group_for(cfg: dict, nguon: str, ldv: str) -> dict | None:
    for g in cfg["groups"]:
        if nguon not in {n.lower() for n in g["nguon"]}:
            continue
        if g.get("loai_dich_vu") and ldv not in {x.lower() for x in g["loai_dich_vu"]}:
            continue
        return g
    return None


def fetch_leads(cfg: dict, dates) -> dict:
    """Tra ve {(date, (hinh_thuc, tkqc, "")): {metric: int}} cho moi ngay x moi group (ke ca 0)."""
    dates = sorted({d for d in dates if d})
    if not dates:
        return {}
    metrics = cfg["metrics"]
    out = {(d, (g["hinh_thuc"], g["tkqc"], "")): {m: 0 for m in metrics} for d in dates for g in cfg["groups"]}
    want = set(dates)
    for nguon, ldv, status, d_created, d_updated in _fetch_rows(cfg, dates):
        g = _group_for(cfg, nguon, ldv)
        if g is None:
            continue
        key_row = (g["hinh_thuc"], g["tkqc"], "")
        for m, spec in metrics.items():
            d = d_created if spec["date"] == "created_at" else d_updated
            if d not in want:
                continue
            sts = spec.get("statuses")
            if sts is not None and status not in sts:
                continue
            out[(d, key_row)][m] += 1
    return out


def fmt_count(cfg: dict, v):
    if v is None:
        return ""
    return "" if (v == 0 and cfg.get("zero_as_blank")) else int(v)


def _parse_d(s: str) -> date:
    return datetime.strptime(s, "%d/%m/%Y").date()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", default="dnd", type=str.lower)
    ap.add_argument("--date", action="append", default=[], help="DD/MM/YYYY (lap lai duoc)")
    ap.add_argument("--from", dest="d_from", help="DD/MM/YYYY")
    ap.add_argument("--to", dest="d_to", help="DD/MM/YYYY")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    cfg = load_leads_cfg(a.part)
    if not cfg:
        sys.exit(f"Part '{a.part}' khong co cau hinh 'leads' trong mapping.json.")
    dates = [_parse_d(s) for s in a.date]
    if a.d_from:
        d, end = _parse_d(a.d_from), _parse_d(a.d_to or a.d_from)
        while d <= end:
            dates.append(d)
            d += timedelta(days=1)
    if not dates:
        sys.exit("Can --date hoac --from/--to.")
    try:
        res = fetch_leads(cfg, dates)
    except LeadsError as e:
        sys.exit(f"LOI: {e}")

    metrics = list(cfg["metrics"])
    rows = []
    for (d, r), vals in sorted(res.items(), key=lambda kv: (kv[0][0], [g["hinh_thuc"] for g in cfg["groups"]].index(kv[0][1][0]))):
        rows.append({"date_mdy": d.strftime("%m/%d/%Y"), "hinh_thuc": r[0], "tkqc": r[1],
                     **{m: fmt_count(cfg, vals[m]) for m in metrics}})
    if a.json:
        print(json.dumps({"part": a.part, "rows": rows}, ensure_ascii=False, indent=2))
        return
    print("\t".join(["Date", "Hình thức", "TKQC"] + [LEAD_LABELS.get(m, m) for m in metrics]))
    for r in rows:
        print("\t".join(str(r[c]) for c in ["date_mdy", "hinh_thuc", "tkqc"] + metrics))
    print(f"\n# part: {a.part} | nguon: Supabase status_data | tz: {cfg.get('timezone', 'Asia/Ho_Chi_Minh')}"
          f" | 0 -> {'trong' if cfg.get('zero_as_blank') else '0'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
