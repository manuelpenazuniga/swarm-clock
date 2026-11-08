"""Synthetic lineages for calibration: token-level edits; `clock` (copy recent member) vs `star` (independent edits of root)."""
import numpy as np
import pandas as pd


class Synth:
    def __init__(self, R, rng, days_default=5):
        self.rng = rng
        self.vocab = np.array([w for t in R.m.sample(min(3000, len(R)), random_state=0) for w in t.split()])
        self.roots_pool = R[R.m.str.split().str.len().between(25, 120)].m.tolist()
        self.T_LO, self.T_HI = R.t.min().value, R.t.max().value

    def mutate(self, toks, p):
        rng, vocab = self.rng, self.vocab
        out = []
        for w in toks:
            u = rng.random()
            if u < p / 2:
                continue  # deletion
            out.append(vocab[rng.integers(len(vocab))] if u < p else w)  # substitution
            if rng.random() < p / 2:
                out.append(vocab[rng.integers(len(vocab))])  # insertion
        return out

    def plant(self, kind, p, n_lin=20, L=30, days=5):
        rng = self.rng
        rows = []
        for li in range(n_lin):
            root = self.roots_pool[rng.integers(len(self.roots_pool))].split()
            t0 = rng.integers(self.T_LO, self.T_HI - int(days * 86400e9))
            times = np.sort(t0 + rng.integers(0, int(days * 86400e9), L))
            members = []
            for i in range(L):
                if kind == "clock":
                    parent = root if i == 0 else members[rng.integers(max(0, i - 5), i)]
                    members.append(self.mutate(parent, p))
                else:
                    members.append(self.mutate(root, 3 * p))
            if kind == "star":
                times = rng.permutation(times)
            for i in range(L):
                rows.append({"rev_id": f"SYN{kind}{p}_{li}_{i}", "page_id": f"SYN/{kind}{p}_{li}_{i}",
                             "label": f"syn{li}_{i}", "t": pd.Timestamp(int(times[i]), tz="UTC"),
                             "m": " ".join(members[i]), "lin": li})
        return pd.DataFrame(rows)

    def synth_like(self, sub, p, window=5):
        """Sampling-matched clock: reuse a real family's times/labels/size; root = earliest real introduction."""
        toks0 = sub.m.iloc[0].split()
        members = []
        for i in range(len(sub)):
            parent = toks0 if i == 0 else members[self.rng.integers(max(0, i - window), i)]
            members.append(self.mutate(parent, p))
        return sub.assign(m=[" ".join(x) for x in members])

    def star_like(self, sub, p):
        """Sampling-matched null: each member is an independent edit of the root (rate 3p), real times kept."""
        toks0 = sub.m.iloc[0].split()
        return sub.assign(m=[" ".join(self.mutate(toks0, 3 * p)) for _ in range(len(sub))])
