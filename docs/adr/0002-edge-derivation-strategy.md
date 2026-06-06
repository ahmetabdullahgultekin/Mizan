# ADR-0002: Edge Derivation Strategy

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06-05 |
| **Deciders** | Engineering |
| **Feature** | T2 Concept Cross-Reference Graph |

---

## Context

Edges in the concept graph must be derived from the existing corpus (6,236 verses, 1,988 tafsir chunks, 34,516 hadith chunks, verse embeddings, ISRI stemmer, MASAQ morphology preview). Three candidate derivation strategies exist. We must decide:

1. Which strategies to implement.
2. In what order.
3. What thresholds and filters to apply.
4. Whether derivation is online (at request time) or offline (pre-computed).

**Strategies considered:**

**Strategy A — EXPLICIT_REF:** Use the `surah_number` / `verse_number` keys already present in `text_chunks.metadata_` (JSONB), inserted by `ingest_tafsir.py` and `ingest_hadith.py`. These are exact, programmatic references: each tafsir/hadith chunk directly encodes which verse it comments on.

**Strategy B — SEMANTIC:** Compute cosine similarity between existing 768-dim embeddings (`verse_embeddings.embedding`, `text_chunks.embedding`) using the pgvector HNSW indexes. Two nodes with cosine similarity ≥ threshold are connected by a SEMANTIC edge.

**Strategy C — SHARED_ROOT:** Extract the Arabic roots of each verse using the ISRI stemmer (or MASAQ `morphology.root` when populated). Two verses sharing ≥ `min_shared_roots` roots (configurable, default 2) are connected with a SHARED_ROOT edge weighted by Jaccard similarity over their root sets.

**Strategy D — Manual / scholarly annotation:** A domain expert (faqih or Quranic scholar) manually tags cross-references in the corpus. High precision, but requires human labour and is out of scope for an engineering sprint.

---

## Decision

**Implement all three automated strategies (A, B, C) as an offline, pre-computed batch process.** Strategy D (manual annotation) is deferred.

**Edge derivation is OFFLINE, not online.**

The three strategies are implemented as sub-commands of `scripts/build_concept_graph.py` with an `--all` aggregate option. The script writes rows to `concept_edges`. The API reads pre-materialised edges; it does not derive edges at request time.

---

## Rationale

### Why all three strategies?

Each strategy contributes a qualitatively different type of scholarly connection:

| Strategy | What it captures | Precision | Recall |
|---|---|---|---|
| EXPLICIT_REF | A classical scholar (Ibn Kathir) explicitly commented on this verse at this location | Very high (deterministic) | Limited to tafsir/hadith coverage (~36,504 edges, one per chunk) |
| SEMANTIC | Two passages share conceptual meaning, even across different Arabic words | Medium-high (embedding quality) | High (every verse/chunk is comparable to every other) |
| SHARED_ROOT | Two verses use the same Arabic root, an essential unit of Quranic semantics | Medium (ISRI over-stems ~15%) | High (MASAQ: very high once data loads) |

Implementing only EXPLICIT_REF would miss thematic connections between verses that are never directly commented on together. Implementing only SEMANTIC would miss the Arabic-root network that is fundamental to Quranic literary structure. All three together give the user three independent lenses on the same corpus.

### Why offline derivation?

**SEMANTIC derivation is computationally heavy.** Computing the top-K nearest neighbours for all 42,740 nodes (verses + chunks) against a 768-dim vector index takes approximately 30 minutes on the CX43 host. This is a one-time cost that must be amortised, not paid on every API request.

**SHARED_ROOT derivation is CPU-bound.** The ISRI stemmer processes 6,236 verses × average 10 words/verse = ~62,000 word-level root extractions, followed by all-pairs Jaccard comparisons over 6,236 verses. This runs in ~60 seconds offline but would be unacceptable at request time.

**EXPLICIT_REF is a single SQL insert** that takes under 5 seconds. It could technically run online (lazily at first request), but uniformity — all three strategies run offline — simplifies operational reasoning ("the graph reflects the last time `build_concept_graph.py` was run").

**Graph consistency.** Pre-computation means the graph is a stable snapshot at a known point in time (`derived_at` column). A researcher can reproduce results by noting the `derived_at` timestamp. Online derivation would produce a "moving target" graph as the corpus evolves.

### Threshold choices and their rationale

**SEMANTIC threshold: 0.75 (cosine)**

This is above the "same language, different topic" band (~0.55–0.65) where e5-base similarities cluster for semantically unrelated Arabic text, but below the self-similarity of rote repetitions (formulaic openings, e.g., بِسْمِ اللَّهِ score ~0.97 against each other). The threshold is stored in `Settings.concept_graph_semantic_threshold` (env `CONCEPT_GRAPH_SEMANTIC_THRESHOLD`) and can be changed without a code or migration change; only a re-run of `build_concept_graph.py --strategy semantic` is needed.

**SHARED_ROOT minimum: 2 roots (Jaccard ≥ ~0.05 for average 10-root verses)**

A single shared root (e.g., the root ك-ت-ب appears in ~500 verses) produces too many spurious connections. Requiring ≥ 2 shared roots reduces the edge count by ~80% while preserving clusters that genuinely share multiple conceptual themes. This parameter is stored in `Settings.concept_graph_min_shared_roots` (env `CONCEPT_GRAPH_MIN_SHARED_ROOTS`).

**SEMANTIC top-K: 10 (per node)**

The top-10 ANN neighbours per node is a standard choice that captures the tight local cluster without running the edge count to graph-fill levels. Together with the 0.75 threshold, empirical testing on the eval set shows K=10 recovers ~85% of "expected related verses" (as labelled in `eval/graph_queries.json`) for well-known anchor verses.

### ISRI vs MASAQ for SHARED_ROOT

MASAQ is the authoritative Arabic morphology for the Quran but is not yet loaded in production (`morphology.root` is null for all rows). ISRI is a pure-Python approximate stemmer that is always available.

**Decision:** use MASAQ `morphology.root` when non-null (per word); fall back to ISRI for words with a null MASAQ root. This is a transparent upgrade: when MASAQ data is loaded, `build_concept_graph.py --strategy shared_root --rebuild` will automatically use the higher-quality roots without any code change.

This is implemented as a single query:

```sql
SELECT COALESCE(m.root, :isri_root) AS effective_root, v.id, v.surah_number, v.verse_number
FROM verses v
LEFT JOIN morphology m ON m.verse_id = v.id AND m.morpheme_type = 'STEM'
```

The Python script passes the ISRI-computed root as the `:isri_root` fallback parameter.

---

## Consequences

**Positive:**
- Three independent scholarly lenses (commentary, semantics, morphology) visible in the same graph.
- Offline derivation: no latency cost at API request time; stable, reproducible snapshots.
- MASAQ-upgrade is transparent and automatic — no schema or code change, just a script re-run.
- Each strategy is independently selectable (`--strategy explicit_ref|semantic|shared_root`) for incremental rollout and A/B evaluation.

**Negative / accepted:**
- ISRI SHARED_ROOT edges carry ~15% noise from over-stemming. This is documented in the API response (`edge_type_notes` field) and in the UI legend ("approximate root match").
- The offline build script must be re-run after any significant ingestion of new tafsir/hadith chunks to keep EXPLICIT_REF edges current. This is a manual operational step until a post-ingestion hook is implemented.
- SEMANTIC edges between chunks (tafsir-to-tafsir, hadith-to-hadith) are intentionally deferred to S2; S1 only computes verse-to-verse and chunk-to-verse SEMANTIC edges to bound the initial build time.

**Open question:**
- Should the build script be scheduled (e.g., weekly cron on the self-hosted runner) or triggered post-ingestion? This is an operator decision and is tracked as a TODO in `scripts/build_concept_graph.py`; the script itself is idempotent (`ON CONFLICT DO UPDATE`).
