"""Download the Mantiq tables needed for the replication (CC-BY-4.0). Skips links/fs_ops/reads."""
import sys, pandas as pd
from huggingface_hub import hf_hub_download
REPO = "zenml/mantiq-swarm-traces"
T = pd.read_csv("data/mantiq/tree.csv")
want = set(sys.argv[1:]) or {"runs","agents","sessions","messages","file_versions","blobs","events","coverage","model_calls","answer_keys"}
for p in T.path:
    if p.split("/")[0] in want and p.endswith(".parquet"):
        hf_hub_download(REPO, p, repo_type="dataset", local_dir="data/mantiq")
        print("ok", p, flush=True)
