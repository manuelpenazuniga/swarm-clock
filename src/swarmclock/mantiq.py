"""Mantiq replication (PREREG_MANTIQ.md). Builds per-run introduction frames for U-M (messages) and U-F (file intros).

Times are represented so that `io.hours(t)` returns lag as a FRACTION OF RUN DURATION (t = frac * 3.6e12 ns),
which lets the wiki window/permutation code run unchanged with windows [0, 1/3), [1/3, inf), [2/3, inf).
"""
import re, difflib, glob
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from .io import ROOT
from .wiki import Masker

MDIR = ROOT / "data" / "mantiq"
NO_FAULT_PRACTICE = {"practice_01", "practice_02", "practice_04", "practice_05", "practice_07", "practice_08", "practice_09"}
TEXT_EXT_BAD = re.compile(r"\.(pyc|png|jpg|gz|zip|bin|pack|idx|sqlite|db)$|\.\d{6,}$", re.I)
EXCL_PATH = re.compile(r"(^|/)\.git(/|$)|upstream\.git|__pycache__|(^|/)sed[A-Za-z0-9]{6}$")
STATUS_FILES = re.compile(r"(^|/)(JUDGE\.md|round\.txt)$")


def load(cfg, cols=None):
    fs = sorted(glob.glob(str(MDIR / cfg / "*" / "*.parquet")))
    return pd.concat([pq.read_table(f, columns=cols).to_pandas() for f in fs], ignore_index=True)


def event_times(needed):
    """needed: DataFrame[run, event_id] -> Series indexed by (run, event_id) of ts_wall_ns."""
    out = []
    for f in sorted(glob.glob(str(MDIR / "events" / "*" / "*.parquet"))):
        d = pq.read_table(f, columns=["run", "event_id", "ts_wall_ns"]).to_pandas()
        run = d.run.iloc[0]
        ids = set(needed.event_id[needed.run == run])
        out.append(d[d.event_id.isin(ids)])
    E = pd.concat(out, ignore_index=True)
    return E.set_index(["run", "event_id"]).ts_wall_ns


class MantiqMasker(Masker):
    re_agent = re.compile(r"(?<![A-Za-z0-9])(?:ws/)?a\d{2}(?![A-Za-z0-9])")
    re_reltime = re.compile(r"T\+\d+(?:\.\d+)?s|\b\d{1,2}:\d{2}(?::\d{2})?\b")
    re_hex = re.compile(r"\b[0-9a-f]{7,}\b")
    re_pathtok = re.compile(r"(?<!\S)\S*/\S*")

    def __init__(self):
        super().__init__([])

    def __call__(self, t):
        t = self.re_reltime.sub(" <DATE> ", t)
        t = self.re_agent.sub(" <AGENT> ", t)
        t = self.re_hex.sub(" <HASH> ", t)
        t = self.re_url.sub(r"\1/<PATH>", t)
        t = self.re_pathtok.sub(" <PATH> ", t)
        t = self.re_date.sub(" <DATE> ", t)
        t = self.re_long.sub(" <TOK> ", t)
        t = self.re_num.sub("0", t)
        return re.sub(r"\s+", " ", t).strip()


def added_lines(prev, cur):
    a, b = prev.split("\n"), cur.split("\n")
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op in ("insert", "replace"):
            out.extend(b[j1:j2])
    return "\n".join(out)


def build_units():
    runs = load("runs")[["run", "seconds", "agents"]]
    dur = dict(zip(runs.run, runs.seconds))
    blobs = load("blobs", ["run", "sha256", "text"])
    btext = dict(zip(zip(blobs.run, blobs.sha256), blobs.text))
    mk = MantiqMasker()
    # ---- U-M messages
    M = load("messages")
    M["text"] = [btext.get((r, s)) for r, s in zip(M.run, M.body_sha256)]
    um_cov = M.text.notna().mean()
    M = M[M.text.notna()].copy()
    M["event_id"] = M.sent_event
    M = M.rename(columns={"from_agent_id": "label", "message_id": "rev_id"})
    M["page_id"] = M.rev_id
    M["path"] = ""
    # ---- U-F file intros
    FV = load("file_versions")
    sha_of = dict(zip(zip(FV.run, FV.version_id), FV.sha256))
    A = FV[(FV.made_by == "agent") & FV.kind.isin(["create", "write"])].copy()
    A["npath"] = A.apply(lambda r: r.path if r.mount == "shared" else r.path, axis=1)
    A = A[~A.path.str.contains(EXCL_PATH) & ~A.path.str.contains(TEXT_EXT_BAD)]
    A["text"] = [btext.get((r, s)) for r, s in zip(A.run, A.sha256)]
    uf_cov = A.text.notna().mean()
    A = A[A.text.notna()].copy()
    intros, how = [], []
    for r, pv, kind, txt in zip(A.run, A.prev_version_id, A.kind, A.text):
        prev = btext.get((r, sha_of.get((r, pv)))) if isinstance(pv, str) else None
        if kind == "create" or prev is None:
            intros.append(txt); how.append("full")
        else:
            intros.append(added_lines(prev, txt)); how.append("added")
    A["text"] = intros; A["how"] = how
    A = A.rename(columns={"agent_id": "label", "version_id": "rev_id"})
    A["path"] = A.mount.where(A.mount == "shared", "ws") + ":" + A.path
    A["page_id"] = A.label.astype(str) + "|" + A.path
    # ---- times
    need = pd.concat([M[["run", "event_id"]], A[["run", "event_id"]]])
    ts = event_times(need)
    out = {}
    for name, U, cov in [("U-M", M, um_cov), ("U-F", A, uf_cov)]:
        U = U.copy()
        U["ts_ns"] = [ts.get((r, e), np.nan) for r, e in zip(U.run, U.event_id)]
        U = U[U.ts_ns.notna()]
        U["D_s"] = U.run.map(dur)
        frac = U.ts_ns / (U.D_s * 1e9)
        U["t"] = pd.to_datetime((frac * 3.6e12).astype("int64"), utc=True)   # hours(t) == fraction of run
        U["m"] = U.text.map(mk)
        U["ntok"] = U.m.str.split().str.len()
        U = U[U.ntok >= 8].reset_index(drop=True)
        U["coverage"] = cov
        out[name] = U[["run", "rev_id", "page_id", "label", "path", "t", "ts_ns", "D_s", "m", "ntok"]
                      + (["how"] if "how" in U else [])]
    return out, {"U-M": um_cov, "U-F": uf_cov}
