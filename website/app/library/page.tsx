'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Library,
  Plus,
  Loader2,
  BookOpen,
  CheckCircle2,
  Clock,
  XCircle,
  RefreshCw,
  Trash2,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { getApiClient } from '@/lib/api/client';
import type {
  LibrarySpaceResponse,
  TextSourceResponse,
  SourceType,
  IndexingStatus,
} from '@/types/api';

// ---------------------------------------------------------------------------
// Status badge
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: IndexingStatus }) {
  const map: Record<IndexingStatus, { icon: React.ReactNode; label: string; class: string }> = {
    PENDING:  { icon: <Clock className="h-3 w-3" />,        label: 'Pending',  class: 'text-muted-foreground border-border' },
    INDEXING: { icon: <Loader2 className="h-3 w-3 animate-spin" />, label: 'Indexing', class: 'text-blue-500 border-blue-500/30 bg-blue-500/5' },
    INDEXED:  { icon: <CheckCircle2 className="h-3 w-3" />, label: 'Indexed', class: 'text-emerald-500 border-emerald-500/30 bg-emerald-500/5' },
    FAILED:   { icon: <XCircle className="h-3 w-3" />,      label: 'Failed',  class: 'text-destructive border-destructive/30 bg-destructive/5' },
  };
  const { icon, label, class: cls } = map[status];
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs ${cls}`}>
      {icon} {label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Add Source Form (inline)
// ---------------------------------------------------------------------------

const SOURCE_TYPE_OPTIONS: { value: SourceType; label: string }[] = [
  { value: 'QURAN',  label: 'Quran'  },
  { value: 'TAFSIR', label: 'Tafsir' },
  { value: 'HADITH', label: 'Hadith' },
  { value: 'OTHER',  label: 'Other'  },
];

function AddSourceForm({
  spaceId,
  onAdded,
  onCancel,
}: {
  spaceId: string;
  onAdded: (src: TextSourceResponse) => void;
  onCancel: () => void;
}) {
  const [sourceType, setSourceType] = React.useState<SourceType>('QURAN');
  const [titleEn, setTitleEn] = React.useState('');
  const [titleAr, setTitleAr] = React.useState('');
  const [author, setAuthor] = React.useState('');
  const [content, setContent] = React.useState('');
  const [isSaving, setIsSaving] = React.useState(false);
  const [error, setError] = React.useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim() || !titleEn.trim()) {
      setError('Title and content are required.');
      return;
    }
    setIsSaving(true);
    setError('');
    try {
      const src = await getApiClient().addTextSource(spaceId, {
        source_type: sourceType,
        title_english: titleEn,
        title_arabic: titleAr || undefined,
        author: author || undefined,
        content: content.trim(),
      });
      // Trigger indexing immediately
      try { await getApiClient().indexTextSource(src.id); } catch { /* best-effort */ }
      onAdded(src);
    } catch {
      setError('Failed to add source. Make sure the backend is running.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border bg-card/50 p-5 space-y-4 mt-3">
      <h4 className="font-medium text-sm">Add Text Source</h4>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Source Type</label>
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value as SourceType)}
            className="w-full rounded-lg border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gold-500/50"
          >
            {SOURCE_TYPE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Title (English) *</label>
          <input
            value={titleEn}
            onChange={(e) => setTitleEn(e.target.value)}
            placeholder="e.g. Tafsir Ibn Kathir"
            className="w-full rounded-lg border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gold-500/50"
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Title (Arabic)</label>
          <input
            value={titleAr}
            onChange={(e) => setTitleAr(e.target.value)}
            placeholder="تفسير ابن كثير"
            dir="rtl"
            className="w-full rounded-lg border bg-background px-3 py-2 text-sm font-arabic focus:outline-none focus:ring-2 focus:ring-gold-500/50"
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Author</label>
          <input
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder="e.g. Ibn Kathir"
            className="w-full rounded-lg border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gold-500/50"
          />
        </div>
      </div>

      <div className="space-y-1">
        <label className="text-xs text-muted-foreground">Content *</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={6}
          placeholder="Paste Arabic text here… The system will chunk it automatically and create semantic embeddings."
          dir="auto"
          className="w-full rounded-lg border bg-background px-3 py-2 text-sm font-arabic leading-relaxed resize-y focus:outline-none focus:ring-2 focus:ring-gold-500/50"
        />
        <p className="text-xs text-muted-foreground">
          {content.length > 0 && `~${Math.ceil(content.split(/\s+/).length / 300)} chunks will be created`}
        </p>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="flex gap-3 justify-end">
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>Cancel</Button>
        <Button type="submit" size="sm" disabled={isSaving}>
          {isSaving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
          Add & Index
        </Button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// LibrarySpaceCard
// ---------------------------------------------------------------------------

function LibrarySpaceCard({ space, onDeleted }: {
  space: LibrarySpaceResponse;
  onDeleted: (id: string) => void;
}) {
  const [sources, setSources] = React.useState<TextSourceResponse[]>(space.sources ?? []);
  const [expanded, setExpanded] = React.useState(true);
  const [showAddForm, setShowAddForm] = React.useState(false);

  const handleAddSource = (src: TextSourceResponse) => {
    setSources((prev) => [src, ...prev]);
    setShowAddForm(false);
  };

  const handleDeleteSource = async (srcId: string) => {
    try {
      await getApiClient().deleteTextSource(srcId);
      setSources((prev) => prev.filter((s) => s.id !== srcId));
    } catch { /* ignore */ }
  };

  const handleReindex = async (srcId: string) => {
    try {
      await getApiClient().indexTextSource(srcId);
      setSources((prev) => prev.map((s) => s.id === srcId ? { ...s, status: 'INDEXING' } : s));
    } catch { /* ignore */ }
  };

  return (
    <div className="rounded-xl border bg-card">
      {/* Header */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between p-5 text-left"
      >
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-gold-500/10 p-2">
            <Library className="h-5 w-5 text-gold-500" />
          </div>
          <div>
            <h3 className="font-semibold">{space.name}</h3>
            {space.description && (
              <p className="text-sm text-muted-foreground">{space.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="text-xs">
            {sources.length} source{sources.length !== 1 ? 's' : ''}
          </Badge>
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </button>

      {/* Sources */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="border-t px-5 pb-5 space-y-3">
              {sources.length === 0 && !showAddForm && (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  <BookOpen className="h-8 w-8 mx-auto mb-2 opacity-30" />
                  No sources yet. Add your first text source below.
                </div>
              )}

              {sources.map((src) => (
                <div key={src.id} className="flex items-center justify-between gap-3 rounded-lg border p-3">
                  <div className="space-y-0.5 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm truncate">
                        {src.title_english || src.title_arabic || 'Untitled'}
                      </span>
                      {src.title_arabic && (
                        <span className="text-sm font-arabic text-muted-foreground" dir="rtl">
                          {src.title_arabic}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusBadge status={src.status} />
                      <span className="text-xs text-muted-foreground">
                        {src.indexed_chunks}/{src.total_chunks} chunks
                      </span>
                      {src.author && (
                        <span className="text-xs text-muted-foreground">· {src.author}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    {src.status === 'FAILED' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                        onClick={() => handleReindex(src.id)}
                        title="Retry indexing"
                      >
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                      onClick={() => handleDeleteSource(src.id)}
                      title="Delete source"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}

              {showAddForm ? (
                <AddSourceForm
                  spaceId={space.id}
                  onAdded={handleAddSource}
                  onCancel={() => setShowAddForm(false)}
                />
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full mt-2"
                  onClick={() => setShowAddForm(true)}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Text Source
                </Button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Library Page
// ---------------------------------------------------------------------------

export default function LibraryPage() {
  const [spaces, setSpaces] = React.useState<LibrarySpaceResponse[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [showCreateForm, setShowCreateForm] = React.useState(false);
  const [newName, setNewName] = React.useState('');
  const [newDesc, setNewDesc] = React.useState('');
  const [isCreating, setIsCreating] = React.useState(false);
  const [createError, setCreateError] = React.useState('');

  React.useEffect(() => {
    getApiClient()
      .listLibrarySpaces()
      .then(setSpaces)
      .catch(() => setSpaces([]))
      .finally(() => setIsLoading(false));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) { setCreateError('Name is required.'); return; }
    setIsCreating(true);
    setCreateError('');
    try {
      const space = await getApiClient().createLibrarySpace({
        name: newName.trim(),
        description: newDesc.trim() || undefined,
      });
      setSpaces((prev) => [space, ...prev]);
      setNewName('');
      setNewDesc('');
      setShowCreateForm(false);
    } catch {
      setCreateError('Failed to create library. Make sure the backend is running.');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="relative min-h-screen pt-20">
      <div className="mx-auto max-w-3xl px-4 py-12 space-y-8">

        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-2"
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Library className="h-5 w-5 text-gold-500" />
                <span className="text-sm text-gold-500 font-medium">Islamic Knowledge Library</span>
              </div>
              <h1 className="text-3xl font-bold tracking-tight">Libraries</h1>
              <p className="text-muted-foreground mt-1">
                Organize Islamic texts into libraries. Each source is automatically chunked
                and indexed for semantic search.
              </p>
            </div>
            <Button onClick={() => setShowCreateForm((v) => !v)}>
              <Plus className="h-4 w-4 mr-2" />
              New Library
            </Button>
          </div>
        </motion.div>

        {/* Create Library Form */}
        <AnimatePresence>
          {showCreateForm && (
            <motion.form
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              onSubmit={handleCreate}
              className="rounded-xl border bg-card p-5 space-y-4 overflow-hidden"
            >
              <h3 className="font-semibold">Create New Library</h3>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">Name *</label>
                  <input
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="e.g. Tafsir Collection"
                    className="w-full rounded-lg border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gold-500/50"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">Description</label>
                  <input
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    placeholder="Brief description…"
                    className="w-full rounded-lg border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gold-500/50"
                  />
                </div>
              </div>
              {createError && <p className="text-sm text-destructive">{createError}</p>}
              <div className="flex gap-3 justify-end">
                <Button type="button" variant="ghost" size="sm" onClick={() => setShowCreateForm(false)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={isCreating}>
                  {isCreating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Create Library
                </Button>
              </div>
            </motion.form>
          )}
        </AnimatePresence>

        {/* Library List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-16 gap-3 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            Loading libraries…
          </div>
        ) : spaces.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-xl border-2 border-dashed border-border p-16 text-center space-y-4"
          >
            <Library className="h-12 w-12 mx-auto text-muted-foreground/30" />
            <div className="space-y-2">
              <p className="font-medium">No libraries yet</p>
              <p className="text-sm text-muted-foreground">
                Create a library and add Islamic texts to enable semantic search.
              </p>
            </div>
            <Button onClick={() => setShowCreateForm(true)} variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              Create First Library
            </Button>
          </motion.div>
        ) : (
          <div className="space-y-4">
            {spaces.map((space) => (
              <LibrarySpaceCard
                key={space.id}
                space={space}
                onDeleted={(id) => setSpaces((prev) => prev.filter((s) => s.id !== id))}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
