"""I/O helpers and project paths. All stages read and write artifacts on disk."""
import gzip, json, hashlib, os
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
TABLES = ROOT / "outputs" / "tables"
FIGS = ROOT / "outputs" / "figs"
SEED = 20261108

FILES = {
    "st_redacted.jsonl.gz": "https://swarmtraces.org/data/final/redacted.jsonl.gz",
    "cw_revisions.jsonl.gz": "https://collusion.wiki/explorer/download/revisions.jsonl.gz",
    "cw_events.jsonl.gz": "https://collusion.wiki/explorer/download/events.jsonl.gz",
    "cw_manifest.json.gz": "https://collusion.wiki/explorer/download/manifest.json.gz",
}

for _d in (RAW, INTERIM, TABLES, FIGS):
    _d.mkdir(parents=True, exist_ok=True)


def rng():
    """Fresh generator per stage (notebooks shared one generator across cells)."""
    return np.random.default_rng(SEED)


def read_jsonl_gz(p):
    with gzip.open(p, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    pass


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch():
    import requests
    rows = []
    for fn, url in FILES.items():
        p = RAW / fn
        if not p.exists():
            r = requests.get(url, headers={"User-Agent": "research-notebook"}, timeout=300)
            r.raise_for_status()
            p.write_bytes(r.content)
        rows.append({"file": fn, "url": url, "bytes": os.path.getsize(p), "sha256": sha256(p)})
    df = pd.DataFrame(rows)
    save(df, "inputs_sha256")
    return df


def save(df, name, index=False):
    p = TABLES / f"{name}.csv"
    df.to_csv(p, index=index)
    print(f"[saved] {p.relative_to(ROOT)}")
    return p


def hours(ts):
    """Datetime-like Series/array -> float hours since epoch (resolution-safe)."""
    v = pd.to_datetime(pd.Series(ts), utc=True).values.astype("datetime64[ns]").astype("int64")
    return v / 3.6e12
