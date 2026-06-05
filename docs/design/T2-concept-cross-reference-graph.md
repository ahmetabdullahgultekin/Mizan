# Design: Concept Cross-Reference Graph (Mizan Tier 2)

> **How we build features (the process this doc enforces).**
> 1. **Design-doc first** — no non-trivial feature starts as code. This doc is reviewed before implementation.
> 2. **ADR for each significant decision** — `docs/adr/NNNN-title.md`, immutable, numbered (Context / Decision / Consequences).
> 3. **Diagrams** — component view and key flows in `docs/diagrams/*.mmd` (mermaid).
> 4. **Contract-first** — Alembic migration, API shape, and TypeScript types are defined here *before* implementation; tests assert the contract.
> 5. **Vertical-slice agile** — break the feature into thin end-to-end slices (S1…Sn), each independently shippable **behind a feature flag** (default OFF).
> 6. **Reversible rollout** — flag default-OFF = byte-identical to today; dark → staging → canary → broad; kill-switch by flag, never a redeploy.
> 7. **TDD + green CI gate** — tests written against the contract; CI (ruff + mypy --strict + pytest) must be green.
> 8. **Verify in the real product** — a slice is "done" only when demonstrated end-to-end in the running app, not just when unit tests pass.

| | |
|---|---|
| **Status** | Draft — for review |
| **Author** | Engineering (2026-06-05) |
| **Reviewers** | (owner) |
| **Feature flag** | `CONCEPT_GRAPH_ENABLED` (default **OFF**) |
| **ADRs** | [ADR-0001 Graph storage: Postgres vs dedicated graph DB](../adr/0001-graph-storage-postgres-vs-graphdb.md), [ADR-0002 Edge derivation strategy](../adr/0002-edge-derivation-strategy.md) |
| **Tracking** | ROADMAP Phase 4 "Concept/graph view" → ships as 4 vertical slices (S1–S4) |

---

## 1. Context & problem

Mizan's hybrid search (vector + BM25 + RRF, live in prod) finds *which* passages relate to a query.
What it cannot yet answer is *how* the corpus hangs together conceptually: why does verse 2:177 cite the same Arabic root (صبر) as fifteen other verses, which tafsir passages comment on that root cluster, and which hadith reinforce or nuance the same concept?

Today a scholar must:
1. Run a semantic search.
2. Manually chase cross-references in the tafsir text.
3. Separately look up hadith on the same root.

The result is an unnested list with no structural relationships visible. The ROADMAP (Phase 4) calls explicitly for a "concept/graph view (verse → similar verses → tafsir → hadith) on existing `/similar` + `search_similar_to_verse` endpoints."

This design delivers that feature as a **queryable graph API + interactive browser-based graph explorer**, grounded entirely in existing corpus data (6,236 verses, 1,988 tafsir chunks, 34,516 hadith chunks, verse embeddings, MASAQ morphology preview, ISRI stemmer).

---

## 2. Goals / Non-goals

### Goals

- A `GET /api/v1/concepts/{anchor}/graph?depth=` endpoint that returns a typed, weighted multigraph centred on any verse, tafsir chunk, or hadith chunk (the "anchor").
- Three derivable edge kinds, each independently toggleable:
  - **SHARED_ROOT** — two nodes share an Arabic root (via ISRI stemmer fallback; MASAQ `morphology.root` column when populated).
  - **SEMANTIC** — cosine similarity between existing `verse_embeddings` / `text_chunks.embedding` vectors exceeds a configurable threshold (default 0.75).
  - **EXPLICIT_REF** — tafsir/hadith chunk's `metadata_` JSONB carries `surah_number`/`verse_number` pointing to a specific verse (already populated by `ingest_tafsir.py` and `ingest_hadith.py`).
- A persistent `concept_edges` table in Postgres (additive Alembic migration) to pre-materialise heavy edge computations; recursive CTE traversal at query time for depth > 1.
- A frontend **graph explorer** component in the Next.js website (`website/components/graph/`) backed by **cytoscape.js** (the dominant graph-rendering library for the web; no backend dependency).
- Eval integration: a new `eval/graph_queries.json` + a `--mode graph` flag on `eval/run_eval.py` to measure graph precision (are the expected related verses within 2 hops?).

### Non-goals (this tier)

- Real-time graph updates triggered by new ingestion. The `concept_edges` table is rebuilt by a background script; live re-derivation on every ingest is deferred.
- User-editable edges (scholarly annotation layer). Deferred to a future "annotation" tier.
- Embedding-model upgrade (e.g., `BAAI/bge-m3`). This feature uses the *existing* 768-dim `intfloat/multilingual-e5-base` embeddings without change.
- Exporting the graph as RDF/OWL. Deferred.
- Root-sense disambiguation (the same Arabic root can carry multiple unrelated concepts — e.g., ع-ل-م covers both "knowledge" and "flag/sign"). Only direct root matching is implemented; word-sense disambiguation is deferred to Phase 5.

---

## 3. Current state (what exists)

| Artefact | Relevance to this feature |
|---|---|
| `verse_embeddings` table (6,236 rows, 768-dim) | Ready for cosine SEMANTIC edges between verses |
| `text_chunks.embedding` column (36,504 rows) | Ready for cosine SEMANTIC edges between library chunks |
| `text_chunks.metadata_` JSONB (`surah_number`, `verse_number`, `source`) | EXPLICIT_REF edges: already encode which verse a tafsir/hadith chunk comments on |
| `morphology.root` column (MASAQ, currently null in prod — data pending) | SHARED_ROOT edges: MASAQ-quality when populated, ISRI fallback always available |
| ISRI Arabic stemmer (`domain/services/`) | Root extraction for SHARED_ROOT edges without MASAQ data |
| `SemanticSearchService.find_similar_verses` | Computes cosine top-N for one verse; reused for S1 batch derivation |
| `SemanticSearchService.search_similar_to_verse` | Finds library chunks similar to a verse; reused for S2 |
| Existing pgvector HNSW indexes on both embedding columns | Fast ANN search for SEMANTIC edge derivation |
| `SourceType` enum: `QURAN`, `TAFSIR`, `HADITH`, `OTHER` | Node type taxonomy |
| `eval/run_eval.py` + `eval/queries.json` | Eval harness to extend for graph quality |

**What does NOT yet exist:**

- `concept_edges` table.
- A graph traversal query (recursive CTE).
- `GET /api/v1/concepts/{anchor}/graph` endpoint.
- `website/components/graph/` cytoscape explorer.
- Background edge-derivation scripts.

---

## 4. Proposed design

### 4.1 High-level architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 16 / React 19)                               │
│   website/app/concepts/[anchor]/page.tsx                        │
│   website/components/graph/ConceptGraphExplorer.tsx             │
│     └── cytoscape.js (client-side, lazy-loaded)                 │
│           ↕ fetch                                               │
└─────────────────────────────────────────────────────────────────┘
           │  GET /api/v1/concepts/{anchor}/graph?depth=2
           ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI (async SQLAlchemy)                                     │
│   api/routers/concepts.py                                       │
│   application/services/concept_graph_service.py                 │
│     └── ConceptGraphRepository (out-port)                       │
│           └── PostgresConceptGraphRepository (adapter)          │
│                 └── concept_edges table (recursive CTE)         │
│                     + verse_embeddings / text_chunks            │
│                       (pgvector HNSW ANN queries)               │
└─────────────────────────────────────────────────────────────────┘
           │  build / refresh (offline script)
           ▼
┌─────────────────────────────────────────────────────────────────┐
│  scripts/build_concept_graph.py                                 │
│   (three edge-derivation strategies, see §4.3)                  │
└─────────────────────────────────────────────────────────────────┘
```

See `docs/diagrams/concept-graph.mmd` for the mermaid C4 + sequence diagram.

### 4.2 Node taxonomy

Every node in the graph is one of three types, corresponding to existing tables:

| `node_type` | `node_id` | Backing table |
|---|---|---|
| `VERSE` | `verses.id` (UUID) | `verses` |
| `TAFSIR` | `text_chunks.id` (UUID) | `text_chunks` where `source_type = TAFSIR` |
| `HADITH` | `text_chunks.id` (UUID) | `text_chunks` where `source_type = HADITH` |

### 4.3 Edge derivation strategies

Three strategies, each stored as rows in `concept_edges` with a `relation` label:

**Strategy A — EXPLICIT_REF (exact, zero-cost)**

Tafsir and hadith chunks already carry `metadata_->>'surah_number'` and `metadata_->>'verse_number'` from the ingestion scripts (`ingest_tafsir.py` line 285–290, `ingest_hadith.py` same pattern). A single SQL insert derives all EXPLICIT_REF edges in one pass:

```sql
INSERT INTO concept_edges (src_type, src_id, dst_type, dst_id, relation, weight, derived_at)
SELECT
    tc.source_type  AS src_type,
    tc.id           AS src_id,
    'VERSE'         AS dst_type,
    v.id            AS dst_id,
    'EXPLICIT_REF'  AS relation,
    1.0             AS weight,
    now()           AS derived_at
FROM text_chunks tc
JOIN verses v
  ON v.surah_number = (tc.metadata_ ->> 'surah_number')::int
 AND v.verse_number = (tc.metadata_ ->> 'verse_number')::int
WHERE tc.metadata_ ? 'surah_number'
  AND tc.metadata_ ? 'verse_number'
ON CONFLICT (src_type, src_id, dst_type, dst_id, relation) DO UPDATE
    SET weight = EXCLUDED.weight, derived_at = EXCLUDED.derived_at;
```

Expected yield: ~36,504 edges (one per tafsir/hadith chunk referencing a verse).

**Strategy B — SEMANTIC (cosine similarity via pgvector)**

Uses the existing HNSW indexes on `verse_embeddings.embedding` and `text_chunks.embedding` to find the top-K nearest neighbours of every node. Only pairs with cosine similarity ≥ `CONCEPT_GRAPH_SEMANTIC_THRESHOLD` (default 0.75, configurable via env) are stored.

Derivation is done in `scripts/build_concept_graph.py` using the existing `IVerseEmbeddingRepository.find_similar_verses` logic (already implemented for the `/similar` endpoint) and an analogous chunk-to-chunk ANN scan. The script runs in batches to avoid OOM.

Expected yield: O(N × K) edges where N = 6,236 verses + 36,504 chunks and K ≤ 10. At K=5, threshold=0.75: roughly 15,000–25,000 verse-to-verse edges + 50,000–80,000 chunk-to-chunk edges (empirical; actual count depends on corpus density).

**Strategy C — SHARED_ROOT (Arabic root, ISRI fallback + MASAQ when available)**

For each verse, extract the set of Arabic roots using:
1. `morphology.root` (per-word MASAQ root, when non-null — currently preview/null in prod).
2. ISRI stemmer (`domain/services/` pure-Python) as the fallback for any word without a MASAQ root.

Two nodes sharing ≥ 1 root get a SHARED_ROOT edge with weight = (number of shared roots) / (union of roots), i.e. Jaccard similarity. Only verse-to-verse SHARED_ROOT edges are built in S3; tafsir/hadith SHARED_ROOT is deferred (the Arabic root density in tafsir prose is noisier).

Edge blow-up risk: the Arabic corpus has ~1,600 distinct roots; high-frequency roots like ع-ل-م (knowledge) appear in ~200+ verses. A naïve all-pairs comparison over 6,236 verses yields ~38M pairs — a tractable 30-second batch but produces a dense graph. Mitigation: apply a minimum shared-root count ≥ 2 filter (configurable `CONCEPT_GRAPH_MIN_SHARED_ROOTS`, default 2) which reduces edges by ~80%.

### 4.4 Recursive CTE traversal (query-time)

The `GET /api/v1/concepts/{anchor}/graph?depth=` endpoint expands the graph from the anchor node outward up to `depth` hops (default 2, max 3) using a PostgreSQL recursive CTE:

```sql
WITH RECURSIVE graph AS (
    -- Base case: edges touching the anchor
    SELECT src_type, src_id, dst_type, dst_id, relation, weight, 1 AS hop
    FROM concept_edges
    WHERE (src_type = :anchor_type AND src_id = :anchor_id)
       OR (dst_type = :anchor_type AND dst_id = :anchor_id)

    UNION ALL

    -- Recursive step: expand one hop further
    SELECT e.src_type, e.src_id, e.dst_type, e.dst_id, e.relation, e.weight, g.hop + 1
    FROM concept_edges e
    JOIN graph g
      ON (e.src_type = g.dst_type AND e.src_id = g.dst_id)
     OR (e.dst_type = g.src_type AND e.dst_id = g.src_id)
    WHERE g.hop < :max_depth
)
SELECT DISTINCT src_type, src_id, dst_type, dst_id, relation, weight
FROM graph;
```

A `LIMIT 500` guard caps the response for very well-connected anchors (e.g., Fatiha verse 1:1). Response payloads above 500 edges are truncated with a `truncated: true` flag in the JSON envelope.

---

## 5. Data model

### 5.1 New table: `concept_edges`

**Alembic migration:** `alembic/versions/2026_06_05_0005_concept_edges.py`

```sql
CREATE TABLE concept_edges (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source node
    src_type     TEXT         NOT NULL,   -- 'VERSE' | 'TAFSIR' | 'HADITH'
    src_id       UUID         NOT NULL,

    -- Destination node
    dst_type     TEXT         NOT NULL,   -- 'VERSE' | 'TAFSIR' | 'HADITH'
    dst_id       UUID         NOT NULL,

    -- Edge metadata
    relation     TEXT         NOT NULL,   -- 'EXPLICIT_REF' | 'SEMANTIC' | 'SHARED_ROOT'
    weight       FLOAT        NOT NULL DEFAULT 1.0,
                                          -- EXPLICIT_REF: 1.0
                                          -- SEMANTIC: cosine similarity (0.0–1.0)
                                          -- SHARED_ROOT: Jaccard similarity (0.0–1.0)

    -- Audit
    derived_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Uniqueness: one edge per (src, dst, relation) pair
CREATE UNIQUE INDEX uq_concept_edges_src_dst_rel
    ON concept_edges (src_type, src_id, dst_type, dst_id, relation);

-- Traversal indexes (recursive CTE scans both directions)
CREATE INDEX ix_concept_edges_src  ON concept_edges (src_type, src_id);
CREATE INDEX ix_concept_edges_dst  ON concept_edges (dst_type, dst_id);

-- Filtering by relation type (graph explorer panel filters)
CREATE INDEX ix_concept_edges_relation ON concept_edges (relation);
```

**Invariants:**
- `src_id` and `dst_id` are not foreign-key-constrained to their respective tables; the derivation script validates referential integrity. This avoids a composite FK across three tables while keeping the migration simple and additive.
- Edges are undirected at the data model level; the API exposes them directionally but the frontend treats them symmetrically. EXPLICIT_REF is the only logically directed edge (tafsir/hadith → verse); SEMANTIC and SHARED_ROOT are symmetric.
- The table is **truncate-and-rebuild** safe: `scripts/build_concept_graph.py --rebuild` truncates and repopulates atomically inside a transaction.

### 5.2 No changes to existing tables

The migration is purely additive. `verses`, `text_chunks`, `verse_embeddings`, `verse_translations`, and `morphology` are unchanged.

---

## 6. API / protocol / contract

### 6.1 New endpoint

```
GET /api/v1/concepts/{anchor_type}/{anchor_id}/graph
```

**Path parameters:**

| Parameter | Type | Values | Example |
|---|---|---|---|
| `anchor_type` | string | `verse`, `tafsir`, `hadith` | `verse` |
| `anchor_id` | UUID | UUID of the anchor node | `3f2a...` |

**Query parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `depth` | int (1–3) | `2` | Number of hops to traverse |
| `relations` | CSV | all | Filter edge types: `EXPLICIT_REF`, `SEMANTIC`, `SHARED_ROOT` |
| `min_weight` | float (0–1) | `0.0` | Exclude edges below this weight |

**Convenience shorthand** (verse references are the most common anchor):
```
GET /api/v1/concepts/verse/{surah_number}/{verse_number}/graph?depth=2
```
This resolves the verse by `(surah_number, verse_number)` to its UUID and delegates to the primary endpoint. A 404 is returned if no verse exists at that location.

**Response shape (`ConceptGraphResponse`):**

```json
{
  "anchor": {
    "type": "VERSE",
    "id": "3f2a-...",
    "reference": "2:255",
    "label": "آيَةُ الكُرسِيّ",
    "content_preview": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ…"
  },
  "nodes": [
    {
      "id": "3f2a-...",
      "type": "VERSE",
      "reference": "2:255",
      "label": "2:255",
      "content_preview": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ…"
    },
    {
      "id": "9c1b-...",
      "type": "TAFSIR",
      "reference": "Ibn Kathir 2:255",
      "label": "Ibn Kathir 2:255",
      "content_preview": "قَوْلُهُ تَعَالَى اللَّهُ لَا إِلَٰهَ…"
    }
  ],
  "edges": [
    {
      "source_id": "9c1b-...",
      "target_id": "3f2a-...",
      "relation": "EXPLICIT_REF",
      "weight": 1.0
    },
    {
      "source_id": "3f2a-...",
      "target_id": "7d4e-...",
      "relation": "SEMANTIC",
      "weight": 0.83
    }
  ],
  "depth": 2,
  "total_nodes": 24,
  "total_edges": 31,
  "truncated": false,
  "edge_counts": {
    "EXPLICIT_REF": 18,
    "SEMANTIC": 9,
    "SHARED_ROOT": 4
  }
}
```

**HTTP status codes:**
- `200 OK` — graph returned (possibly empty if anchor has no edges yet).
- `404 Not Found` — anchor does not exist in its table.
- `400 Bad Request` — invalid `anchor_type`, `depth` out of range.
- `503 Service Unavailable` — `CONCEPT_GRAPH_ENABLED=false` (feature flag OFF).

**Rate limit:** inherits the global `120/minute` ceiling; the graph endpoint is additionally throttled to `10/minute` per IP via the existing `slowapi` limiter, because depth-3 CTE traversals are heavier than a single-vector search.

### 6.2 Modified endpoint (no breaking change)

`GET /api/v1/search/verses/{surah}/{verse}/similar` — unchanged. The graph endpoint supersedes it for multi-hop exploration but the existing endpoint remains for single-hop verse-to-verse similarity.

### 6.3 TypeScript types (frontend contract)

Located in `website/types/api.ts` (additive, no existing type modified):

```typescript
export type NodeType = 'VERSE' | 'TAFSIR' | 'HADITH';
export type RelationType = 'EXPLICIT_REF' | 'SEMANTIC' | 'SHARED_ROOT';

export interface ConceptGraphNode {
  id: string;
  type: NodeType;
  reference: string;
  label: string;
  content_preview: string;
}

export interface ConceptGraphEdge {
  source_id: string;
  target_id: string;
  relation: RelationType;
  weight: number;
}

export interface ConceptGraphResponse {
  anchor: ConceptGraphNode;
  nodes: ConceptGraphNode[];
  edges: ConceptGraphEdge[];
  depth: number;
  total_nodes: number;
  total_edges: number;
  truncated: boolean;
  edge_counts: Record<RelationType, number>;
}
```

---

## 7. Files to add / change

```
src/mizan/
  domain/
    entities/
      graph.py                                  (+)  ConceptNode, ConceptEdge, ConceptGraph value objects
    repositories/
      graph_interfaces.py                       (+)  IConceptGraphRepository (out-port)
  application/
    services/
      concept_graph_service.py                  (+)  ConceptGraphService (use case)
    dtos/
      graph_requests.py                         (+)  ConceptGraphRequest DTO
      graph_responses.py                        (+)  ConceptGraphResponse, ConceptGraphNode, ConceptGraphEdge DTOs

  infrastructure/
    persistence/
      graph_repository.py                       (+)  PostgresConceptGraphRepository (implements IConceptGraphRepository)
                                                     — recursive CTE traversal + anchor resolution
      models.py                                 (~)  + ConceptEdgeModel (new SQLAlchemy model)

  api/
    routers/
      concepts.py                               (+)  GET /api/v1/concepts/{anchor_type}/{anchor_id}/graph
                                                     GET /api/v1/concepts/verse/{surah}/{verse}/graph
    main.py                                     (~)  register concepts router

alembic/versions/
  2026_06_05_0005_concept_edges.py              (+)  creates concept_edges table + indexes

scripts/
  build_concept_graph.py                        (+)  offline edge derivation:
                                                     --strategy explicit_ref|semantic|shared_root|all
                                                     --rebuild (truncate + repopulate)
                                                     --semantic-threshold (float, default 0.75)
                                                     --min-shared-roots (int, default 2)
                                                     --dry-run (report counts, no write)

website/
  types/
    api.ts                                      (~)  + ConceptGraphNode/Edge/Response types
  lib/
    api/
      client.ts                                 (~)  + fetchConceptGraph() helper
  components/
    graph/
      ConceptGraphExplorer.tsx                  (+)  cytoscape.js wrapper (client component, lazy import)
      ConceptGraphPanel.tsx                     (+)  sidebar: anchor info + edge-type filters + legend
      ConceptGraphToolbar.tsx                   (+)  depth slider, edge-type toggles, reset/export
      GraphLegend.tsx                           (+)  colour/shape key for node/edge types
      useConceptGraph.ts                        (+)  data-fetching hook (SWR or native fetch)
      index.ts                                  (+)  barrel export
  app/
    concepts/
      [anchor_type]/
        [anchor_id]/
          page.tsx                              (+)  server component: anchor resolution + graph page
    layout.tsx                                  (=)  unchanged

eval/
  graph_queries.json                            (+)  labelled graph test cases (anchor → expected reachable refs)
  run_eval.py                                   (~)  + --mode graph flag

docs/
  design/T2-concept-cross-reference-graph.md   (+)  this doc
  adr/0001-graph-storage-postgres-vs-graphdb.md (+)
  adr/0002-edge-derivation-strategy.md         (+)
  diagrams/concept-graph.mmd                   (+)
```

Legend: `(+)` new file, `(~)` modified file, `(=)` unchanged.

---

## 8. Rollout & flags

**Feature flag:** `CONCEPT_GRAPH_ENABLED` (environment variable, default `false`).

With the flag `false`:
- The `GET /api/v1/concepts/…` router returns `503` immediately.
- The `concept_edges` table exists (migration is additive and always applied) but is never queried from the live API.
- `scripts/build_concept_graph.py` can be run at any time to pre-populate edges; the flag only gates the API.

**Rollout sequence (reversible, per the project's posture):**

1. **Dark** — migration applied, `build_concept_graph.py --dry-run` run to measure edge counts and performance. Flag stays `false`.
2. **Staging** — flag `true` on the local dev environment; end-to-end test via graph eval (`eval/run_eval.py --mode graph`).
3. **Canary one user** — flag `true` in prod; manual inspection of the frontend graph explorer for 3–5 anchor verses (Fatiha 1:1, Ayat al-Kursi 2:255, 17:23 parents).
4. **Broad** — flag remains `true` for all users; no further infra change.

**Kill-switch:** set `CONCEPT_GRAPH_ENABLED=false` in the Docker compose env and restart the API container. No migration rollback needed (the table is additive and harmless when not queried).

**Backwards compatibility:** All existing endpoints (`/search/semantic`, `/search/verses/{s}/{v}/similar`, etc.) are unchanged. The new `concept_edges` table has no FK dependency from existing tables.

---

## 9. Agile iteration plan (vertical slices)

### S1 — Explicit-reference edges + raw API (1 sprint)

**Scope:** Alembic migration + `ConceptEdgeModel` + `build_concept_graph.py --strategy explicit_ref` + `PostgresConceptGraphRepository` (depth-1 CTE only) + `GET /api/v1/concepts/{anchor_type}/{anchor_id}/graph` + unit tests.

**Done =** running `build_concept_graph.py --strategy explicit_ref` populates ~36,504 EXPLICIT_REF edges in under 60 seconds; `GET /api/v1/concepts/verse/{id}/graph` returns those edges correctly; unit tests green.

### S2 — Semantic edges + depth-N traversal (1 sprint)

**Scope:** `build_concept_graph.py --strategy semantic` batched derivation using pgvector ANN; recursive CTE traversal to `depth=2`; `depth` and `relations` query params; rate-limiting on the new endpoint.

**Done =** a graph centred on verse 2:255 at depth 2 returns semantically related verses AND the tafsir/hadith that comment on them (via combined EXPLICIT_REF + SEMANTIC edges); `eval/run_eval.py --mode graph` reports precision ≥ 0.5 on the labelled set.

### S3 — Shared-root edges + eval harness (1 sprint)

**Scope:** ISRI root extraction for all verses; `build_concept_graph.py --strategy shared_root`; `eval/graph_queries.json` with ≥ 20 labelled anchors; `eval/run_eval.py --mode graph`.

**Done =** SHARED_ROOT edges visible in the API response; eval harness reports edge-level precision/recall by relation type; CI runs eval as a non-blocking check.

### S4 — Frontend graph explorer (1 sprint)

**Scope:** `website/components/graph/ConceptGraphExplorer.tsx` (cytoscape.js, lazy-loaded); depth slider; edge-type filter toggles; node colour/shape by type; `website/app/concepts/[anchor_type]/[anchor_id]/page.tsx`; mobile-responsive layout; i18n keys in `en.json` / `tr.json`.

**Done =** navigating to `/concepts/verse/{surah}/{verse}` renders an interactive graph in the browser; filter toggles show/hide each edge type; depth slider re-fetches; the page degrades gracefully (static list) when `cytoscape.js` is not loaded.

---

## 10. Test plan

### Unit tests

- `ConceptGraphService`: given a mock repository returning a fixed edge set, verify recursive expansion to depth 1 / 2 / 3; verify `truncated=true` is set when edge count > 500; verify `relations` filter excludes correct edges.
- `PostgresConceptGraphRepository`: SQL structure of the recursive CTE (inject a real but empty Postgres instance via pytest-asyncio + the test suite's existing conftest pattern); verify the `depth` parameter bounds the CTE recursion.
- `build_concept_graph.py`: EXPLICIT_REF SQL correctness (unit-testable with a small in-memory fixture: 3 chunks with known `metadata_` → 3 expected edges); SEMANTIC batch derivation for 5 mock embeddings at threshold 0.75; SHARED_ROOT Jaccard weight computation.

### Integration tests

- Full-stack: `POST /api/v1/library/spaces` → ingest 2 tafsir chunks with `metadata_` pointing to verse 2:1 → `build_concept_graph.py --strategy explicit_ref` → `GET /api/v1/concepts/verse/{2:1 UUID}/graph?depth=1` returns those 2 chunks. Runs in the existing pytest-asyncio conftest with a real (test) Postgres.
- Feature-flag gate: with `CONCEPT_GRAPH_ENABLED=false`, all concept graph endpoints return `503`.
- `depth=3` guard: anchor with >500 reachable edges (constructed fixture) returns `truncated: true` and exactly 500 edges.

### Eval (search-quality harness)

`eval/graph_queries.json` format (mirrors `eval/queries.json`):

```json
{
  "cases": [
    {
      "anchor": {"type": "verse", "surah": 2, "verse": 255},
      "depth": 2,
      "expected_reachable_refs": ["2:256", "2:285", "3:2", "3:18"],
      "note": "Ayat al-Kursi: adjacent throne/tawhid cluster"
    }
  ]
}
```

Metric: for each anchor, **graph-precision@depth** = (expected refs found within depth hops) / (expected refs total). Target: ≥ 0.6 overall by S3 completion.

### Security

- `anchor_id` is a UUID: FastAPI validation rejects non-UUID strings before the DB query.
- Recursive CTE `depth` is validated server-side (1–3); a depth-0 or depth-100 request returns `400`.
- Rate limit (10/minute) prevents graph-traversal DoS. Depth-3 query on a dense anchor (e.g., 2:255) was benchmarked at ~180ms on CX43 with the HNSW indexes in place; 10/minute per IP is a conservative ceiling.

---

## 11. Risks & open questions

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| **Edge count explosion at depth 3** on well-connected verses (e.g., 2:255 has ~40 EXPLICIT_REF, ~25 SEMANTIC, potentially ~80 SHARED_ROOT edges; at depth 3 this can fan out to thousands) | Medium | Medium | Hard cap of 500 edges in the CTE + `LIMIT 500` guard; `truncated` flag informs the client; depth default is 2, max is 3 |
| **SHARED_ROOT precision** — ISRI stemmer over-stems ~15% of words (e.g., roots that differ by one letter may collide). This generates false edges that link unrelated verses. | High (ISRI is a heuristic) | Medium | Require ≥ 2 shared roots (Jaccard filter); label this edge type as "approximate" in the UI; fall back to MASAQ roots when the corpus is loaded (transparent upgrade, no migration needed) |
| **Semantic similarity at 0.75 threshold** may still connect verses that share surface phrasing (e.g., formulaic openings بِسْمِ اللَّهِ) rather than deep concepts | Medium | Low | Threshold is a configurable env var; S3 eval will surface this; a higher threshold (0.82) can be deployed without a migration |
| **Build script runtime** — SEMANTIC edge derivation for 36,504 chunks × top-5 ANN = ~182,000 candidate pairs. At 10ms/query (pgvector HNSW): ~30 minutes on CX43. | High | Low | Run offline on the self-hosted runner; skip if `concept_edges` already has SEMANTIC edges (idempotent `ON CONFLICT DO UPDATE`) |
| **MASAQ data still absent** — SHARED_ROOT will be ISRI-only for the foreseeable future | High | Low | Documented in API response metadata; MASAQ upgrade is transparent once data is loaded |
| **cytoscape.js lazy loading** — the package (~0.5MB min+gzip) adds to the concepts page bundle | Medium | Low | Dynamic `import()` in `ConceptGraphExplorer.tsx`; Next.js code-splits it automatically; the rest of the site is unaffected |

---

## 12. Rollback

1. Set `CONCEPT_GRAPH_ENABLED=false` → restart `mizan-api` container. Existing endpoints are unaffected.
2. The `concept_edges` table is unused by any live query path once the flag is off.
3. To fully remove: `alembic downgrade` to revision `0004_bm25_search_indexes` drops the table. However, because the migration is purely additive, rollback is only needed if disk space is a concern.
4. No seed data is destroyed; the `verse_embeddings`, `text_chunks`, `verses`, and `morphology` tables are never modified by this feature.
