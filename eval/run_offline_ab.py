#!/usr/bin/env python3
"""
Offline A/B evaluation harness for embedding-model retrieval quality.

Unlike ``eval/run_eval.py`` (which scores the *live* API end-to-end over HTTP),
this harness compares **embedding models head-to-head, fully in-process**, with
no database, no Redis, and — crucially — **without touching any production
data or vectors**. It builds a small throwaway in-memory index from the local
Tanzil Arabic Quran text (``data/tanzil/quran-uthmani.xml``) and re-ranks the
labelled Arabic eval cases (``eval/queries.json``) by cosine similarity.

Why Arabic-only by default
--------------------------
The owner-flagged search-quality frontier is Arabic recall, and the Arabic
verse text is available *offline* in the repo. English/Turkish translations live
only in the prod DB, which this harness must not read or re-embed. So the
default A/B is on the Arabic retrieval path — exactly the weak spot we want to
move — using each model's own (model-aware) query/passage prefix convention.

What it measures
----------------
For each candidate model and each Arabic query, it embeds:
  * the query (with the model's ``query:`` prefix, if any), and
  * a candidate pool = (all labelled-relevant verses across the eval set)
    ∪ (a deterministic sample of distractor verses)
each verse with the model's ``passage:`` prefix, then ranks by cosine and
reports **MRR, nDCG@k, recall@k, precision@k** per model. A side-by-side table
is written to ``docs/EMBEDDING_AB_<date>.md``.

Safety / disk guard
-------------------
``sentence-transformers`` + ``torch`` and the model weights are large. This
script REFUSES to download anything if doing so would push the root filesystem
past ``--max-disk-pct`` (default 85%). In that case it prints the exact command
to run later (e.g. on a host with headroom) and exits 0 without downloading.

Usage
-----
    # Compare the prod default against e5-large (Arabic path)
    python eval/run_offline_ab.py \
        --models intfloat/multilingual-e5-base intfloat/multilingual-e5-large

    # Report-only dry run (no model load, just show the plan + disk check)
    python eval/run_offline_ab.py --dry-run

Dependencies: requires the ``ml`` extra (``pip install -e ".[ml]"``) to actually
run; ``--dry-run`` and the disk guard need only the stdlib.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
QUERIES_PATH = REPO_ROOT / "eval" / "queries.json"
TANZIL_XML = REPO_ROOT / "data" / "tanzil" / "quran-uthmani.xml"
DOCS_DIR = REPO_ROOT / "docs"

DEFAULT_MODELS = [
    "intfloat/multilingual-e5-base",  # current prod default (baseline)
    "intfloat/multilingual-e5-large",  # candidate
]

# Conservative on-disk estimate (GB) for downloading a model the first time,
# used only to warn before a download. e5-base ≈ 1.1 GB, e5-large ≈ 2.2 GB.
_MODEL_DISK_GB = {
    "intfloat/multilingual-e5-base": 1.2,
    "intfloat/multilingual-e5-large": 2.3,
}


# ---------------------------------------------------------------------------
# Prefix policy (imported from the app so the harness and prod agree exactly)
# ---------------------------------------------------------------------------


def _prefix_policy_for(model_name: str) -> tuple[str, str]:
    """Return (query_prefix, passage_prefix) for a model, via the app's policy."""
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from mizan.infrastructure.embeddings.prefix_policy import prefix_policy_for

    p = prefix_policy_for(model_name)
    return p.query_prefix, p.passage_prefix


# ---------------------------------------------------------------------------
# Corpus / labels
# ---------------------------------------------------------------------------


def _parse_arabic_verses() -> dict[str, str]:
    """Parse the local Tanzil Uthmani XML → {"surah:verse": arabic_text}."""
    if not TANZIL_XML.exists():
        raise FileNotFoundError(
            f"Tanzil Arabic text not found at {TANZIL_XML}. "
            "This harness reads only local repo data (never prod)."
        )
    tree = ET.parse(TANZIL_XML)
    root = tree.getroot()
    verses: dict[str, str] = {}
    for sura_el in root:
        if sura_el.tag.lower() not in ("sura", "surah", "chapter"):
            continue
        s_num = int(sura_el.get("index") or sura_el.get("number") or "0")
        if not 1 <= s_num <= 114:
            continue
        for aya_el in sura_el:
            if aya_el.tag.lower() not in ("aya", "ayah", "ayat", "verse"):
                continue
            a_num = int(aya_el.get("index") or aya_el.get("number") or "0")
            text = aya_el.get("text") or (aya_el.text or "").strip()
            if text:
                verses[f"{s_num}:{a_num}"] = text
    return verses


def _load_arabic_cases() -> list[dict[str, Any]]:
    cases = json.loads(QUERIES_PATH.read_text(encoding="utf-8"))["cases"]
    return [c for c in cases if c.get("lang") == "ar"]


def _build_candidate_pool(
    cases: list[dict[str, Any]],
    verses: dict[str, str],
    distractors: int,
) -> list[str]:
    """All relevant refs across cases + a deterministic distractor sample."""
    relevant: set[str] = set()
    for c in cases:
        relevant.update(c["relevant"])
    pool = sorted(r for r in relevant if r in verses)

    # Deterministic distractors: every Nth verse, skipping ones already in pool.
    all_refs = sorted(verses.keys(), key=lambda r: tuple(int(x) for x in r.split(":")))
    step = max(1, len(all_refs) // max(1, distractors))
    for ref in all_refs[::step]:
        if ref not in relevant:
            pool.append(ref)
        if len(pool) >= len(relevant) + distractors:
            break
    return pool


# ---------------------------------------------------------------------------
# Disk guard
# ---------------------------------------------------------------------------


def _disk_pct_after(extra_gb: float) -> tuple[float, float]:
    """Return (current_pct, projected_pct) for the root fs after adding extra_gb."""
    usage = shutil.disk_usage("/")
    total = usage.total
    used = usage.used
    cur = 100.0 * used / total
    proj = 100.0 * (used + extra_gb * 1024**3) / total
    return cur, proj


def _model_is_cached(model_name: str) -> bool:
    """Best-effort check whether the HF weights are already on disk."""
    cache = Path(
        os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")
    ) / "hub"
    slug = "models--" + model_name.replace("/", "--")
    return (cache / slug).exists()


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def _dcg(gains: list[float]) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def _ndcg_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    gains = [1.0 if r in relevant else 0.0 for r in ranked[:k]]
    ideal = [1.0] * min(len(relevant), k)
    idcg = _dcg(ideal)
    return _dcg(gains) / idcg if idcg else 0.0


def _recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    return len(set(ranked[:k]) & relevant) / len(relevant)


def _precision_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    top = ranked[:k]
    return (sum(1 for r in top if r in relevant) / len(top)) if top else 0.0


def _rr(ranked: list[str], relevant: set[str]) -> float:
    for i, r in enumerate(ranked, start=1):
        if r in relevant:
            return 1.0 / i
    return 0.0


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


# ---------------------------------------------------------------------------
# Per-model evaluation
# ---------------------------------------------------------------------------


def _evaluate_model(
    model_name: str,
    cases: list[dict[str, Any]],
    verses: dict[str, str],
    pool: list[str],
    k: int,
) -> dict[str, float]:
    """Embed the pool + queries with one model, rank by cosine, score metrics."""
    from sentence_transformers import SentenceTransformer
    from sentence_transformers.util import cos_sim

    q_prefix, p_prefix = _prefix_policy_for(model_name)
    model = SentenceTransformer(model_name)

    pool_texts = [p_prefix + verses[ref] for ref in pool]
    pool_emb = model.encode(pool_texts, normalize_embeddings=True, show_progress_bar=False)

    per_case: list[dict[str, float]] = []
    for c in cases:
        relevant = set(c["relevant"]) & set(pool)
        q_emb = model.encode(
            [q_prefix + c["query"]], normalize_embeddings=True, show_progress_bar=False
        )
        scores = cos_sim(q_emb, pool_emb)[0].tolist()
        ranked = [
            ref
            for ref, _ in sorted(
                zip(pool, scores, strict=True), key=lambda t: t[1], reverse=True
            )
        ]
        per_case.append(
            {
                "mrr": _rr(ranked, relevant),
                "ndcg": _ndcg_at_k(ranked, relevant, k),
                "recall": _recall_at_k(ranked, relevant, k),
                "precision": _precision_at_k(ranked, relevant, k),
            }
        )

    return {
        "mrr": _mean([m["mrr"] for m in per_case]),
        "ndcg": _mean([m["ndcg"] for m in per_case]),
        "recall": _mean([m["recall"] for m in per_case]),
        "precision": _mean([m["precision"] for m in per_case]),
        "n": float(len(per_case)),
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _write_report(
    results: dict[str, dict[str, float]],
    baseline: str,
    k: int,
    pool_size: int,
    out_path: Path,
) -> None:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    lines = [
        f"# Embedding-model A/B — offline Arabic retrieval ({today})",
        "",
        "Generated by `eval/run_offline_ab.py`. **In-process, offline, prod-data-safe:**",
        "the candidate pool is built from the local Tanzil Arabic text",
        "(`data/tanzil/quran-uthmani.xml`) and the labelled Arabic cases in",
        "`eval/queries.json`; no production vectors are read or written.",
        "",
        f"- Metric cutoff: **k = {k}**",
        f"- Candidate pool: **{pool_size}** verses (all labelled-relevant + distractors)",
        f"- Baseline (current prod default): `{baseline}`",
        "- Each model uses its own model-aware query/passage prefix policy.",
        "",
        "| model | MRR | nDCG@k | recall@k | precision@k | Δ MRR vs base |",
        "|---|---|---|---|---|---|",
    ]
    base_mrr = results.get(baseline, {}).get("mrr", 0.0)
    for name, m in results.items():
        delta = m["mrr"] - base_mrr
        flag = " (baseline)" if name == baseline else f" {delta:+.3f}"
        lines.append(
            f"| `{name}`{' (baseline)' if name == baseline else ''} "
            f"| {m['mrr']:.3f} | {m['ndcg']:.3f} | {m['recall']:.3f} "
            f"| {m['precision']:.3f} | {flag.strip() if name != baseline else '—'} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "- A candidate is only worth a prod cutover if it **beats the baseline MRR/nDCG**",
        "  here AND on the live end-to-end harness (`eval/run_eval.py`).",
        "- Switching `EMBEDDING_MODEL` to a different-dimension model (e5-large is",
        "  **1024-dim** vs e5-base's 768-dim) requires a `vector(768)→vector(1024)`",
        "  Alembic migration **and a full re-embed** of all verses/translations/chunks.",
        "  Keep the default unchanged until the owner signs off on that migration.",
        "- This A/B covers the **Arabic** path only (offline-available text). Re-run the",
        "  live harness for EN/TR before any cutover.",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline embedding-model A/B (Arabic)")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--baseline", default=DEFAULT_MODELS[0])
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--distractors", type=int, default=200)
    parser.add_argument("--max-disk-pct", type=float, default=85.0)
    parser.add_argument("--dry-run", action="store_true", help="plan + disk check only")
    parser.add_argument(
        "--out", default=None, help="report path (default docs/EMBEDDING_AB_<date>.md)"
    )
    args = parser.parse_args()

    cases = _load_arabic_cases()
    verses = _parse_arabic_verses()
    pool = _build_candidate_pool(cases, verses, args.distractors)

    print(f"Arabic eval cases: {len(cases)}  |  candidate pool: {len(pool)} verses")
    print(f"Models: {args.models}  (baseline: {args.baseline})")

    # Disk guard: estimate downloads needed (only models not already cached).
    needed_gb = 0.0
    for m in args.models:
        if not _model_is_cached(m):
            needed_gb += _MODEL_DISK_GB.get(m, 2.5)
    cur_pct, proj_pct = _disk_pct_after(needed_gb)
    print(
        f"Disk: {cur_pct:.1f}% used now; ~{needed_gb:.1f} GB of downloads needed "
        f"→ projected {proj_pct:.1f}% (limit {args.max_disk_pct:.0f}%)."
    )

    if args.dry_run:
        print("Dry run — no models loaded, no downloads. Plan looks valid.")
        return 0

    if proj_pct > args.max_disk_pct:
        print(
            "\nSKIPPED downloads: would exceed the disk limit. "
            "Run later on a host with headroom:\n"
            f"  python eval/run_offline_ab.py --models {' '.join(args.models)}\n"
            "(Install the ml extra first: pip install -e \".[ml]\")",
            file=sys.stderr,
        )
        return 0

    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        print(
            "\nsentence-transformers not installed. Install the ml extra:\n"
            '  pip install -e ".[ml]"\n'
            "then re-run this command.",
            file=sys.stderr,
        )
        return 0

    results: dict[str, dict[str, float]] = {}
    for m in args.models:
        print(f"\n=== Evaluating {m} ===")
        results[m] = _evaluate_model(m, cases, verses, pool, args.k)
        r = results[m]
        print(
            f"  MRR={r['mrr']:.3f}  nDCG@{args.k}={r['ndcg']:.3f}  "
            f"recall@{args.k}={r['recall']:.3f}  P@{args.k}={r['precision']:.3f}"
        )

    out = (
        Path(args.out)
        if args.out
        else DOCS_DIR / f"EMBEDDING_AB_{datetime.now(UTC):%Y-%m-%d}.md"
    )
    _write_report(results, args.baseline, args.k, len(pool), out)
    print(f"\nReport written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
