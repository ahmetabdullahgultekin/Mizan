"""
Model-aware embedding prefix policy.

Different embedding models expect different *instruction prefixes* on the text
they encode. Getting this wrong silently degrades retrieval quality, so the
prefix convention must travel with the embedding backend rather than being
hardcoded by the caller.

Conventions implemented here
----------------------------
* **e5 family** (``intfloat/multilingual-e5-*``, ``intfloat/e5-*``) — asymmetric
  retrieval: queries are prefixed ``"query: "`` and passages ``"passage: "``.
  This is required for good results; e5 was trained with these exact prefixes.
  ``multilingual-e5-base`` (current prod default) and ``multilingual-e5-large``
  both belong here, so switching between them keeps the prefixing correct.
* **BGE-M3 / BGE-*-m3** — uses no prefix for retrieval (it ships its own
  instruction handling), so we emit empty prefixes.
* **GTE multilingual** (``Alibaba-NLP/gte-multilingual-*``) — no prefix.
* **Gemini / text-embedding-*** — task type is passed via the API, not a text
  prefix, so we emit empty prefixes.
* **Anything else / unknown** — empty prefixes (safe default: never inject a
  prefix a model was not trained on).

The policy is derived purely from the model *name* so it is a single source of
truth shared by the indexing path (passages) and the search path (queries),
and so a model swap via ``EMBEDDING_MODEL`` automatically carries the right
convention.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingPrefixPolicy:
    """Query/passage prefixes an embedding model expects.

    ``query_prefix`` is prepended to search queries before embedding;
    ``passage_prefix`` is prepended to documents/passages at index time.
    Empty strings mean "no prefix" (the model was not trained with one).
    """

    query_prefix: str = ""
    passage_prefix: str = ""

    def for_query(self, text: str) -> str:
        """Return *text* with the query prefix applied."""
        return f"{self.query_prefix}{text}"

    def for_passage(self, text: str) -> str:
        """Return *text* with the passage prefix applied."""
        return f"{self.passage_prefix}{text}"


# Canonical policies (named so they can be referenced/compared in tests).
E5_POLICY = EmbeddingPrefixPolicy(query_prefix="query: ", passage_prefix="passage: ")
NO_PREFIX_POLICY = EmbeddingPrefixPolicy(query_prefix="", passage_prefix="")


def prefix_policy_for(model_name: str) -> EmbeddingPrefixPolicy:
    """Resolve the prefix policy for an embedding model by its name.

    The match is case-insensitive and substring-based on the lowered model id
    so both ``intfloat/multilingual-e5-large`` and a bare ``e5-large`` resolve
    correctly. Unknown models get :data:`NO_PREFIX_POLICY` — the conservative
    default that never injects a prefix the model was not trained on.
    """
    name = (model_name or "").lower()

    # e5 family — asymmetric query/passage prefixes are REQUIRED for good recall.
    # Match "e5-" so e5-small/base/large + multilingual-e5-* all resolve, while
    # avoiding accidental hits on unrelated names.
    if "e5-" in name or name.endswith("-e5") or "/e5" in name:
        return E5_POLICY

    # Models that explicitly use no retrieval prefix.
    #   bge-m3 / bge-*-m3, gte multilingual, gemini / google text-embedding-*
    # These all fall through to the conservative no-prefix default below, but we
    # keep the comment so the intent is documented and a future contributor does
    # not "helpfully" add e5 prefixes to them.
    return NO_PREFIX_POLICY
