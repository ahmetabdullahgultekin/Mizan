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

- [ ] i18n support: Turkish and Arabic UI translations (next-intl)
- [ ] Multi-verse playground: surah dropdown + verse multi-select
- [ ] Fix remaining TypeScript build errors properly

### Data & AI

- [ ] Ingest library sources: Tafsir texts for semantic search
- [ ] Ingest library sources: Hadith collections for semantic search
- [ ] Gemini embedding cascade (primary) with local model fallback
- [ ] MASAQ morphology data ingestion

### Infrastructure

- [ ] Sentry error tracking
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Automated database backups (pg_dump)

---

## Known Behaviors

- Library text_chunks semantic search returns empty results until Tafsir/Hadith sources are ingested. Quran verse search works.
- `lockdown-install.js SES` warning in browser console is from browser extensions (MetaMask/Brave), not Mizan code.
