#!/usr/bin/env python3
"""
Search-quality evaluation harness for Mizan semantic search.

Runs a labelled query set (``eval/queries.json``) against a running Mizan API
and reports precision@k, recall@k, and Mean Reciprocal Rank (MRR), broken down
by language (en / tr / ar) and overall. Use it to *prove* a ranking change helps
(or regresses) instead of eyeballing one query.

Why this exists
---------------
Arabic and Turkish search quality used to be invisible: there was no metric, so
the English-only-reranker bias and the min_similarity scale bug were only caught
by manually inspecting a single "mercy" query. This harness makes quality a
number that can be tracked over time and compared between configurations
(e.g. raw RRF vs +rerank, ms-marco vs jina).

Usage
-----
    # Against production
    python eval/run_eval.py

    # Against a local API
    python eval/run_eval.py --base-url http://localhost:8000

    # Compare reranking on vs off (uses the per-request `rerank` flag)
    python eval/run_eval.py --rerank true
    python eval/run_eval.py --rerank false

    # Tighter / looser cutoffs and machine-readable output
    python eval/run_eval.py --k 5 --json

Exit code is non-zero if mean MRR falls below ``--min-mrr`` (default 0.0, i.e.
reporting-only), so the harness can gate a ranking change in CI when desired.

No heavy deps: stdlib ``urllib`` only.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = "https://mizan-api.rollingcatsoftware.com"
QUERIES_PATH = Path(__file__).resolve().parent / "queries.json"


def _post_search(
    base_url: str,
    query: str,
    limit: int,
    rerank: bool | None,
    timeout: float,
) -> list[dict[str, Any]]:
    """Call POST /api/v1/search/semantic and return the result list."""
    url = base_url.rstrip("/") + "/api/v1/search/semantic"
    body: dict[str, Any] = {"query": query, "limit": limit, "min_similarity": 0.2}
    if rerank is not None:
        body["rerank"] = rerank
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        payload = json.loads(resp.read().decode("utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        results = payload.get("results")
        if isinstance(results, list):
            return results
    return []


def _refs(results: list[dict[str, Any]]) -> list[str]:
    """Extract the surah:verse reference from each Quran result, in order."""
    out: list[str] = []
    for r in results:
        ref = r.get("reference")
        # Only Quran verses use the surah:verse format we label against.
        if isinstance(ref, str) and ":" in ref and r.get("source_type") == "QURAN":
            out.append(ref)
    return out


def _precision_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    top = ranked[:k]
    if not top:
        return 0.0
    hits = sum(1 for r in top if r in relevant)
    return hits / len(top)


def _recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    top = set(ranked[:k])
    return len(top & relevant) / len(relevant)


def _reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    for i, r in enumerate(ranked, start=1):
        if r in relevant:
            return 1.0 / i
    return 0.0


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Mizan search-quality eval harness")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--queries", default=str(QUERIES_PATH))
    parser.add_argument("--k", type=int, default=10, help="cutoff for P@k / R@k")
    parser.add_argument("--limit", type=int, default=10, help="results to request")
    parser.add_argument(
        "--rerank",
        choices=["true", "false", "default"],
        default="default",
        help="per-request rerank override (true/false bypasses or forces it)",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--min-mrr",
        type=float,
        default=0.0,
        help="exit non-zero if mean MRR < this (CI gate; default 0 = report only)",
    )
    args = parser.parse_args()

    rerank: bool | None
    rerank = None if args.rerank == "default" else (args.rerank == "true")

    cases = json.loads(Path(args.queries).read_text(encoding="utf-8"))["cases"]

    per_case: list[dict[str, Any]] = []
    by_lang: dict[str, list[dict[str, float]]] = {}

    for case in cases:
        query = case["query"]
        lang = case.get("lang", "en")
        relevant = set(case["relevant"])
        try:
            results = _post_search(args.base_url, query, args.limit, rerank, args.timeout)
        except (urllib.error.URLError, TimeoutError) as exc:  # pragma: no cover
            print(f"ERROR querying {query!r}: {exc}", file=sys.stderr)
            results = []
        ranked = _refs(results)
        metrics = {
            "p_at_k": _precision_at_k(ranked, relevant, args.k),
            "r_at_k": _recall_at_k(ranked, relevant, args.k),
            "rr": _reciprocal_rank(ranked, relevant),
        }
        per_case.append(
            {"query": query, "lang": lang, "top": ranked[: args.k], **metrics}
        )
        by_lang.setdefault(lang, []).append(metrics)

    overall = {
        "p_at_k": _mean([c["p_at_k"] for c in per_case]),
        "r_at_k": _mean([c["r_at_k"] for c in per_case]),
        "mrr": _mean([c["rr"] for c in per_case]),
        "n": len(per_case),
    }
    lang_summary = {
        lang: {
            "p_at_k": _mean([m["p_at_k"] for m in ms]),
            "r_at_k": _mean([m["r_at_k"] for m in ms]),
            "mrr": _mean([m["rr"] for m in ms]),
            "n": len(ms),
        }
        for lang, ms in by_lang.items()
    }

    report = {
        "base_url": args.base_url,
        "k": args.k,
        "rerank": args.rerank,
        "overall": overall,
        "by_lang": lang_summary,
        "cases": per_case,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Mizan search eval — {args.base_url}  (k={args.k}, rerank={args.rerank})")
        print("-" * 64)
        print(f"{'lang':<6}{'P@k':>8}{'R@k':>8}{'MRR':>8}{'n':>5}")
        for lang in sorted(lang_summary):
            s = lang_summary[lang]
            print(f"{lang:<6}{s['p_at_k']:>8.3f}{s['r_at_k']:>8.3f}{s['mrr']:>8.3f}{s['n']:>5}")
        print("-" * 64)
        print(
            f"{'ALL':<6}{overall['p_at_k']:>8.3f}{overall['r_at_k']:>8.3f}"
            f"{overall['mrr']:>8.3f}{overall['n']:>5}"
        )
        print()
        for c in per_case:
            mark = "ok " if c["rr"] > 0 else "MISS"
            print(
                f"  [{mark}] {c['lang']} {c['query']!r:18} "
                f"P@k={c['p_at_k']:.2f} MRR={c['rr']:.3f} top={c['top'][:5]}"
            )

    if overall["mrr"] < args.min_mrr:
        print(
            f"\nFAIL: mean MRR {overall['mrr']:.3f} < min-mrr {args.min_mrr:.3f}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
