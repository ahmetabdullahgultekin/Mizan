# Mizan — Roadmap

> Last updated: 2026-03-15

## Current Status

**API:** https://mizan-api.rollingcatsoftware.com (Python 3.11 / FastAPI)
**Website:** https://mizan.rollingcatsoftware.com (Next.js 16, standalone)
**Health:** Both services running, HTTPS active

### What's Working

- [x] FastAPI backend deployed with Docker
- [x] Next.js website deployed (standalone mode)
- [x] PostgreSQL + pgvector for semantic search
- [x] Quran text ingested (114 surahs, 6,236 verses)
- [x] Verse embeddings indexed (6,236 vectors via `embed_quran.py`)
- [x] Quran semantic search working (Arabic / Turkish / English)
- [x] Verse analysis fully working (letter count, word count, Abjad values, frequency)
- [x] Playground shows verse text in analysis results
- [x] CORS handling with global exception handler (returns JSON on 500s)
- [x] pgvector queries fixed (`CAST(:embedding AS vector)`)
- [x] asyncio session conflicts resolved (sequential execution)
- [x] Favicon and PWA manifest on website
- [x] `NEXT_PUBLIC_API_URL` correctly passed as build arg

---

## Planned Work

### Website Features

- [x] i18n support: Turkish and Arabic UI translations (client-side, en/tr/ar + RTL)
- [x] Playground: Translate all remaining hard-coded English strings (verse selector, hero stats, tip cards)
- [x] Playground: Similar verse cards show Arabic verse text, surah name, clickable navigation
- [ ] Multi-verse playground: surah dropdown + verse multi-select
- [x] Landing page: Translate remaining hard-coded strings in features/stats/demo/CTA sections
- [x] Fix remaining TypeScript build errors (tsc --noEmit passes cleanly)

### Data & AI

- [x] Ingest library sources: Tafsir Ibn Kathir (1,988 chunks via `scripts/ingest_tafsir.py`)
- [x] Ingest library sources: Hadith Kutub al-Sittah (34,516 chunks via `scripts/ingest_hadith.py`)
- [ ] Library embeddings: 7,876/36,504 embedded (Tafsir done, Hadith in progress via `scripts/embed_library.py`)
- [ ] Gemini embedding cascade (primary) with local model fallback
- [ ] MASAQ morphology data ingestion

### Infrastructure

- [ ] Sentry error tracking
- [ ] CI/CD pipeline (GitHub Actions)
- [x] Automated database backups (pg_dump — daily cron at 3 AM)

---

## Known Behaviors

- Library text_chunks: Tafsir Ibn Kathir (1,988 chunks, fully embedded) + Kutub al-Sittah hadith (34,516 chunks, embedding in progress). Semantic search returns results from all embedded sources.
- Embedding runs via `embed_library.py` inside the mizan-api container (~10 chunks/s on CPU, auto-recoverable with frequent commits).
- `lockdown-install.js SES` warning in browser console is from browser extensions (MetaMask/Brave), not Mizan code.
