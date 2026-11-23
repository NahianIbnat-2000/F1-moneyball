"""Write reproducibility_manifest.json: what was run, with which data, code, settings and outputs.

    python scripts/repro_manifest.py [--out reproducibility_manifest.json]

`deterministic` holds everything that must be identical on every run from the same commit (data hashes, settings,
seeds, hashes of generated datasets). `volatile` holds what is expected to vary: timestamps, the machine, and the PDF,
whose bytes change with the build date and TeX version even when its content does not.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as md
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from f1moneyball.econometrics import robustness as rob  # noqa: E402
from f1moneyball.econometrics.models import SPECS  # noqa: E402

PACKAGES = ["pandas", "numpy", "statsmodels", "scipy", "patsy", "pyarrow", "matplotlib", "pyyaml"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reproducibility_manifest.json")
    out = ROOT / ap.parse_args().out
    data = ROOT / "website" / "public" / "data"
    published = json.loads((data / "manifest.json").read_text()) if (data / "manifest.json").exists() else {}
    versions = {k: v.get("version") for k, v in published.get("datasets", {}).items()}
    inputs = sorted((ROOT / "data" / "manual").glob("*.csv")) + sorted((ROOT / "data" / "processed").glob("*.parquet"))
    pdf = ROOT / "paper" / "main.pdf"
    manifest = {
        "deterministic": {
            "git_commit": git("rev-parse", "HEAD"),
            "git_dirty": bool(git("status", "--porcelain")),
            "inputs_sha256": {p.relative_to(ROOT).as_posix(): sha256(p) for p in inputs},
            "dataset_versions": versions,
            "outputs_sha256": {p.name: sha256(p) for p in sorted(data.glob("*.csv"))},
            "model_configuration": {
                "specifications": [{"id": i, "label": label, "formula": f} for i, label, f in SPECS],
                "bootstrap": {"type": "wild cluster restricted (null imposed)", "weights": "Webb six-point",
                              "draws": rob.B_DRAWS, "seed": 20261119, "cluster": "team_id",
                              "t_statistic": "CR1, G/(G-1)*(N-1)/(N-K)"},
                "multiple_testing": "Holm step-down over the six two-way tests (3 resources x 2 outcomes)",
                "rule_reset_seasons": list(rob.RESET_SEASONS),
            },
            "python": ".".join(map(str, sys.version_info[:3])),
            "packages": {p: md.version(p) for p in PACKAGES if _installed(p)},
        },
        "volatile": {
            "built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "platform": platform.platform(),
            "paper_pdf_sha256": sha256(pdf) if pdf.exists() else None,
        },
    }
    out.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {out}: {len(manifest['deterministic']['inputs_sha256'])} inputs, "
          f"{len(manifest['deterministic']['outputs_sha256'])} outputs")


def _installed(p: str) -> bool:
    try:
        md.version(p)
        return True
    except md.PackageNotFoundError:
        return False


if __name__ == "__main__":
    main()
