"""Part 1: Swarm Traces timestamp anchors and Gate 1. Payload text is treated as inert data only."""
import re, json, base64, struct, collections, datetime as dt
import numpy as np
import pandas as pd
from datasketch import MinHash, MinHashLSH

LO, HI = 1777593600, 1785456000  # 2026-05-01 .. 2026-07-31 UTC (NOT 2024)
re_epoch_s = re.compile(r'(?<!\d)(17[78]\d{7})(?!\d)')
re_epoch_ms = re.compile(r'(?<!\d)(17[78]\d{10})(?!\d)')
re_jwt = re.compile(r'eyJ[A-Za-z0-9_-]{8,}\.(eyJ[A-Za-z0-9_-]{8,})\.[A-Za-z0-9_-]*')
re_gz = re.compile(r'H4sI[A-Za-z0-9+/]{8,}')
MON = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
       'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
re_iso = re.compile(r'(?<!\d)2026-(0[5-7])-([0-3]\d)(?:[T ]([0-2]\d):([0-5]\d))?')
re_mon = re.compile(r'(?i)\b(may|jun|jul)[a-z]*\.?\s?([0-3]?\d)\b(?:\s+([0-2]?\d):([0-5]\d))?')


def b64url_json(s):
    s += "=" * (-len(s) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(s))
    except Exception:
        return None


def gzip_mtime(b64):
    try:
        raw = base64.b64decode(b64[:16] + "=" * (-len(b64[:16]) % 4))
        return struct.unpack("<I", raw[4:8])[0]
    except Exception:
        return None


def anchors(text):
    out = []
    for m in re_jwt.finditer(text):
        p = b64url_json(m.group(1))
        if isinstance(p, dict) and isinstance(p.get("iat"), (int, float)) and LO <= p["iat"] <= HI:
            out.append(("jwt_iat", int(p["iat"])))
    for m in re_gz.finditer(text):
        t = gzip_mtime(m.group(0))
        if t and LO <= t <= HI:
            out.append(("gzip_mtime", t))
    for m in re_epoch_ms.finditer(text):
        t = int(m.group(1)) // 1000
        if LO <= t <= HI:
            out.append(("epoch_ms", t))
    for m in re_epoch_s.finditer(text):
        t = int(m.group(1))
        if LO <= t <= HI:
            out.append(("epoch_s", t))
    for m in re_iso.finditer(text):
        mo, d = int(m.group(1)), int(m.group(2))
        hh = int(m.group(3) or 12); mm = int(m.group(4) or 0)
        try:
            out.append(("date_str", int(dt.datetime(2026, mo, d, hh, mm, tzinfo=dt.timezone.utc).timestamp())))
        except ValueError:
            pass
    for m in re_mon.finditer(text):
        mo = MON[m.group(1).lower()[:3]]; d = int(m.group(2))
        if not 1 <= d <= 31:
            continue
        hh = int(m.group(3) or 12); mm = int(m.group(4) or 0)
        try:
            out.append(("date_str", int(dt.datetime(2026, mo, d, min(hh, 23), mm, tzinfo=dt.timezone.utc).timestamp())))
        except ValueError:
            pass
    return out


re_redact = re.compile(r'\[[A-Z][A-Z0-9 _\-]{2,}(?: \d+)?\]')
re_mask = re.compile(r'[A-Za-z0-9+/=_-]{24,}|\b[0-9a-f]{12,}\b|\d+')


def normalize(t):
    t = re_redact.sub(" <RED> ", t)
    t = re_mask.sub(" <N> ", t)
    return re.sub(r'\s+', ' ', t).strip()


def shingles(t, k=5):
    toks = t.split()
    return {" ".join(toks[j:j + k]) for j in range(max(1, len(toks) - k + 1))}


def anchor_table(st, text_field="text"):
    rows = []
    for i, r in enumerate(st):
        for kind, ts in anchors(r.get(text_field) or ""):
            rows.append((i, kind, ts))
    A = pd.DataFrame(rows, columns=["rec", "kind", "ts"])
    vc = A.groupby(["kind", "ts"]).rec.nunique().rename("n_recs").reset_index()
    A = A.merge(vc, on=["kind", "ts"])
    A["inherited"] = A.n_recs > 1
    A["day"] = pd.to_datetime(A.ts, unit="s", utc=True).dt.date
    return A


def anchor_families(st, A, text_field="text", nperm=128, thr=0.5):
    anchored = sorted(A.rec.unique())
    lsh = MinHashLSH(threshold=thr, num_perm=nperm)
    mh = {}
    for i in anchored:
        m = MinHash(num_perm=nperm)
        for x in shingles(normalize(st[i].get(text_field) or "")):
            m.update(x.encode())
        mh[i] = m; lsh.insert(str(i), m)
    parent = {i: i for i in anchored}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for i in anchored:
        for j in lsh.query(mh[i]):
            a, b = find(i), find(int(j))
            if a != b:
                parent[a] = b
    return {i: find(i) for i in anchored}
