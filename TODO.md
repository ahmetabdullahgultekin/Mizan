# Mizan - Remaining Tasks

## Deployment Status

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API | ✅ Code complete | Needs docker-compose + migrations to run |
| Semantic Search backend | ✅ Code complete | pgvector migration + embeddings needed |
| Frontend Playground | ✅ Real API | Mock removed |
| Frontend `/search` | ✅ Complete | Semantic search UI |
| Frontend `/library` | ✅ Complete | Library management UI |
| Quran data (verses table) | ⚠️ Script ready | Run `ingest_tanzil.py` |
| Verse embeddings | ⚠️ Script ready | Run `embed_quran.py` after ingest |
| Deployment (Railway) | ⏳ Pending | — |

---

## Priority 1: Runtime Setup (Local)

- [ ] `docker-compose up -d` — start pgvector PostgreSQL + Redis
- [ ] `alembic upgrade head` — apply all migrations (initial + library_embeddings)
- [ ] `python scripts/ingest_tanzil.py` — populate surahs + verses (6,236 rows)
- [ ] `python scripts/embed_quran.py` — generate verse embeddings (~5 min on CPU)
- [ ] Verify: `curl http://localhost:8000/api/v1/verses/1/1` returns Al-Fatiha verse 1
- [ ] Verify: `POST /api/v1/search/semantic` with `{"query": "mercy"}` returns results

---

## Priority 2: Content — Add Islamic Texts to Library

- [ ] Add Türkçe Diyanet Meali (Quran Turkish translation) as a TextSource
- [ ] Add Sahih International translation (Quran English) as a TextSource
- [ ] Add sample Tafsir passages (e.g. Ibn Kathir excerpts) as a TextSource
- [ ] Add sample Hadith collection (e.g. Riyazüssalihin) as a TextSource
- [ ] Create `scripts/ingest_library_source.py` for batch text file ingestion

---

## Priority 3: Embedding Quality Upgrade

- [ ] Evaluate `BAAI/bge-m3` (1024-dim) for Arabic-specific embedding quality
- [ ] Write new Alembic migration: `vector(768)` → `vector(1024)` columns
- [ ] Re-run `embed_quran.py` with new model after migration
- [ ] Update `EMBEDDING_MODEL` and `EMBEDDING_DIMENSION` in config

---

## Priority 4: Production Deployment

- [ ] Update GitHub Actions `NEXT_PUBLIC_API_URL` to Railway URL
- [ ] Enable GitHub Pages for frontend (Settings → Pages → GitHub Actions)
- [ ] Set `SECRET_KEY` to a strong random value in Railway
- [ ] Add `slowapi` rate limiting (semantic search: 30 req/min/IP)
- [ ] Review CORS settings for production domain
- [ ] Set up error tracking (Sentry)

---

## Priority 5: Feature Completion

### Coming Soon Pages
- [ ] `/docs/api` - Full API documentation
- [ ] `/docs/examples` - Code examples
- [ ] `/docs/changelog` - Version history
- [ ] `/docs/contributing` - Contribution guide
- [ ] `/privacy` - Privacy policy
- [ ] `/terms` - Terms of service
- [ ] `/license` - License details

### Future Features
- [ ] Word-by-word morphology endpoint (MASAQ dataset)
- [ ] Kavramsal harita / Graph view (ayet → benzer ayetler → tefsir → hadis)
- [ ] Comparative translation analysis (multiple meals side-by-side)
- [ ] Thematic tagging via embedding clustering
- [ ] API key authentication for admin endpoints

---

## Completed Tasks ✅

- [x] Railway deployment configured
- [x] Supabase PostgreSQL connected
- [x] Redis cache connected
- [x] PORT variable expansion fixed
- [x] Prepared statement cache disabled for pgbouncer
- [x] pg_trgm extension enabled
- [x] API health endpoint working
- [x] Abjad calculation working
- [x] GitHub Pages workflow created
- [x] Coming Soon pages created
- [x] Navigation links fixed
- [x] `scripts/ingest_tanzil.py` written (114 surahs, 6,236 verses, juz/hizb/manzil/sajdah)
- [x] `scripts/embed_quran.py` written (batch verse embeddings)
- [x] pgvector migration (library_spaces, text_sources, text_chunks, verse_embeddings)
- [x] `IEmbeddingService` interface + `SentenceTransformerEmbeddingService`
- [x] `GeminiEmbeddingService` + `CascadeEmbeddingService` with dimension guard
- [x] `get_embedding_service()` factory with lru_cache + cascade mode
- [x] Library API routers (spaces CRUD + source management + indexing)
- [x] Semantic search API (`POST /api/v1/search/semantic`, `GET similar`)
- [x] Frontend `/search` page (semantic search UI)
- [x] Frontend `/library` page (library management UI)
- [x] Frontend API client extended (library + search methods)
- [x] TypeScript types for Library + SemanticSearch responses
- [x] Navigation updated (Search + Library links in navbar)
- [x] Playground connected to real API (mock removed)
- [x] VerseSelector loads 114 surahs dynamically from API
- [x] `analyzeVerse()` URL corrected (`/api/v1/analysis/verse/`)
- [x] `getSurahList()` response shape corrected (plain array)

---

## Environment Variables

```env
# Core
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/mizan
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
SECRET_KEY=<change-in-production>

# Embedding (local only)
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=intfloat/multilingual-e5-base

# Embedding (cascade: Gemini primary, local fallback)
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=models/text-embedding-004
EMBEDDING_FALLBACK_PROVIDER=local
EMBEDDING_FALLBACK_MODEL=intfloat/multilingual-e5-base
GEMINI_API_KEY=your-key-here
```

---

*Last updated: 2026-03-11*
