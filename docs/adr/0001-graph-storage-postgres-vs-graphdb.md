# ADR-0001: Graph Storage — PostgreSQL vs Dedicated Graph Database

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06-05 |
| **Deciders** | Engineering |
| **Feature** | T2 Concept Cross-Reference Graph |

---

## Context

The Concept Cross-Reference Graph feature requires storing and traversing a typed, weighted multigraph whose nodes are Quranic verses (`verses` table, 6,236 rows), tafsir chunks, and hadith chunks (`text_chunks` table, 36,504 rows), and whose edges are derived by three strategies (EXPLICIT_REF, SEMANTIC, SHARED_ROOT).

We must choose where to persist the edge set and how to evaluate traversal queries at API request time.

**Options considered:**

**Option A — Stay on PostgreSQL with a `concept_edges` adjacency table**

Add one new table (`concept_edges`) with `src_type/src_id → dst_type/dst_id + relation + weight`. Traversal uses a PostgreSQL recursive CTE (`WITH RECURSIVE`). No new infrastructure dependency.

**Option B — Introduce a dedicated graph database (Neo4j, Apache AGE for Postgres, Amazon Neptune, etc.)**

Store the same graph in a purpose-built graph database optimised for traversal. Neo4j Community Edition is self-hosted; Apache AGE is a PostgreSQL extension that adds Cypher support on top of the existing Postgres instance.

---

## Decision

**Option A — Stay on PostgreSQL with a `concept_edges` adjacency table.**

---

## Rationale

**Scale is small.** The graph has at most ~43,000 nodes and an estimated upper bound of ~300,000 edges (EXPLICIT_REF ~36,500 + SEMANTIC ~100,000 + SHARED_ROOT ~180,000 before the ≥2-root filter). This is well within the range where a well-indexed adjacency table + recursive CTE performs acceptably. Benchmarks on the existing CX43 server (8 vCPU / 16 GB) show PostgreSQL recursive CTEs on tables of this size running in 50–300ms at depth 2.

**Depth is bounded.** The API caps traversal at depth 3. Unbounded or very deep traversal (e.g., 10+ hops across a social graph of millions of nodes) is the primary use case where dedicated graph databases win decisively. Depth-3 bounded traversal on ~300K edges is an easy case for any relational engine.

**Infrastructure simplicity.** Mizan already runs PostgreSQL 17 + pgvector on the CX43 host. Adding Neo4j or another graph database would require:
- A new Docker container (Neo4j Community Edition: ~1 GB RAM baseline).
- A new connection pool, new client library, a second migration system, and a second backup strategy.
- Keeping the adjacency table (edges must still be derived from Postgres data) or a full ETL pipeline from Postgres to the graph DB.

All of this on a single-server solo-developer deployment, for a feature used in exploratory reading sessions, is engineering overhead with no measurable user benefit at current scale.

**Apache AGE (Postgres extension) is an attractive middle ground but immature.** AGE adds openCypher support to Postgres. However, it is not yet packaged in the `pgvector/pgvector` Docker image that Mizan uses, requires a compile-time build, and carries a stability risk on a production database that also stores the verified Quran text corpus.

**Recursive CTE is sufficient and already well-understood.** The team has working knowledge of PostgreSQL recursive CTEs. The query structure is auditable, debuggable with `EXPLAIN ANALYZE`, and maintainable by any developer familiar with SQL.

**pgvector HNSW indexes already exist** on the embedding columns used for SEMANTIC edge derivation. The `concept_edges` table reuses these indexes during the offline build script; no additional vector infrastructure is needed.

**Future migration path is easy.** If the graph grows beyond the adjacency-table approach (e.g., after incorporating full tafsir commentary networks and cross-hadith citation graphs, an order-of-magnitude larger), migrating to Apache AGE or Neo4j is a well-defined ETL step. The domain model (`ConceptNode`, `ConceptEdge`) is fully decoupled from the storage layer behind `IConceptGraphRepository`; swapping the Postgres adapter for a Neo4j adapter would not change domain or application code.

---

## Consequences

**Positive:**
- No new infrastructure: no new container, no new backup routine, no new monitoring target.
- `concept_edges` is a plain SQL table: readable with `psql`, backed up by the existing `pg_dump` runbook, indexed normally, and included in the existing Alembic migration chain.
- The recursive CTE approach is transparent and debuggable.

**Negative / accepted:**
- Traversal performance degrades for very deep graphs (depth > 3) or graphs with millions of edges. Mitigated by the depth-3 cap and the 500-edge hard limit.
- The `concept_edges` table does not enforce referential integrity via foreign keys (the source nodes span two tables: `verses` and `text_chunks`). The derivation script validates existence; a periodic integrity check script is recommended.
- PostgreSQL does not natively support graph algorithms (PageRank, betweenness centrality, community detection). If these are needed in a future tier, the adjacency table can be exported to NetworkX (Python) or Apache Spark GraphX for offline computation, then results stored back in Postgres.

**Deferred:**
- Apache AGE or Neo4j re-evaluation at Phase 6, if the edge count exceeds 5 million or traversal depth requirements exceed 5 hops.
