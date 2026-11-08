"""Part 2a: collusion.wiki introductions (added text per revision) and masking."""
import re, base64
import pandas as pd

CUTOFF = pd.Timestamp("2026-07-03", tz="UTC")
HUBS = {"dse/WillkommenImWiki", "dse/StartSeite", "dse/TestSeite", "dse/RecentChanges"}
TEMPLATE = re.compile(r"Beschreibe hier die neue Seite\.?", re.I)


def get_body(r):
    b = r.get("body") or ""
    enc = str(r.get("body_encoding") or "").lower()
    if "base64" in enc:
        try:
            b = base64.b64decode(b).decode("utf-8", "replace")
        except Exception:
            pass
    return b


def introduction(r):
    body = get_body(r)
    hunks = r.get("hunks") or []
    if r.get("diff_base_reason") == "page_created" or not hunks:
        return body, "created" if r.get("diff_base_reason") == "page_created" else "no_hunks"
    lines = body.split("\n")
    added, bad = [], 0
    for h in hunks:
        if h.get("op") in ("insert", "replace"):
            b0, b1 = int(h.get("b0", 0)), int(h.get("b1", 0))
            if b1 > len(lines):
                bad += 1
            added.extend(lines[b0:b1])
    return "\n".join(added), ("bad_index" if bad else "hunks")


def intro_frame(cw):
    rows = []
    for r in cw:
        text, how = introduction(r)
        rows.append({"rev_id": r["rev_id"], "page_id": r["page_id"], "label": r.get("label") or "",
                     "time": r.get("time"), "time_grade": r.get("time_grade"), "how": how,
                     "intro": text, "body_len": len(get_body(r)),
                     "relation_type": r.get("relation_type"), "related_event_id": r.get("related_event_id")})
    I = pd.DataFrame(rows)
    I["t"] = pd.to_datetime(I["time"], utc=True, errors="coerce")
    return I


def window_filter(I):
    return I[(I.t < CUTOFF) & (I.time_grade == "reqlog") & (I.how != "bad_index")].copy()


class Masker:
    re_url = re.compile(r"(https?://[^/\s'\"]+)[^\s'\"]*")
    re_date = re.compile(r"(?i)\b(19|20)\d\d[-/.]\d{1,2}[-/.]\d{1,2}\b|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s?\d{1,2}\b")
    re_long = re.compile(r"[A-Za-z0-9+/=_-]{24,}")
    re_num = re.compile(r"\d+")

    def __init__(self, labels):
        labels = sorted({l for l in labels if isinstance(l, str) and len(l) >= 4}, key=len, reverse=True)
        self.re_labels = re.compile(r"(?<![A-Za-z0-9])(" + "|".join(map(re.escape, labels)) + r")(?![A-Za-z0-9])") if labels else None

    def __call__(self, t):
        if self.re_labels is not None:
            t = self.re_labels.sub(" <AGENT> ", t)
        t = self.re_url.sub(r"\1/<PATH>", t)
        t = self.re_date.sub(" <DATE> ", t)
        t = self.re_long.sub(" <TOK> ", t)
        t = self.re_num.sub("0", t)
        return re.sub(r"\s+", " ", t).strip()
