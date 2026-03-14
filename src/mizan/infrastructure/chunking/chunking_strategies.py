"""
Text chunking strategies for Islamic text sources.

Chunking is the process of splitting a text into segments before embedding.
The strategy chosen affects search quality significantly:
- Too large: context is diluted, relevant portions buried
- Too small: context is lost, chunks lack meaning

Each strategy yields (content, reference, metadata) tuples.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RawChunk:
    """
    A raw text segment ready to be persisted as a TextChunk.

    Attributes:
        chunk_index: Sequential position within the source
        content: The actual text content
        reference: Human-readable reference (e.g., '2:255', 'p. 12')
        metadata: Structured context data
    """

    chunk_index: int
    content: str
    reference: str
    metadata: dict


class VerseChunker:
    """
    Chunks Quran text verse by verse.

    1 verse = 1 chunk. This is the natural boundary for Quranic text
    and preserves the thematic and grammatical integrity of each verse.

    Each chunk carries its surah_number and verse_number as metadata
    for cross-referencing with the existing verses table.
    """

    def chunk(
        self,
        verses: list[tuple[int, int, str]],
    ) -> list[RawChunk]:
        """
        Convert a list of (surah_number, verse_number, text) to chunks.

        Args:
            verses: List of (surah_number, verse_number, text) tuples

        Returns:
            One RawChunk per verse
        """
        chunks = []
        for idx, (surah_no, verse_no, text) in enumerate(verses):
            reference = f"{surah_no}:{verse_no}"
            chunks.append(
                RawChunk(
                    chunk_index=idx,
                    content=text.strip(),
                    reference=reference,
                    metadata={
                        "surah_number": surah_no,
                        "verse_number": verse_no,
                    },
                )
            )
        return chunks


class ParagraphChunker:
    """
    Chunks text by paragraphs with an optional word-count cap.

    Suitable for Tafsir books and Hadith collections where paragraphs
    are natural semantic units. Respects paragraph boundaries (double
    newline) but also caps chunk size to avoid overly long chunks.

    Default: max 300 words per chunk.
    """

    def __init__(self, max_words: int = 300) -> None:
        self.max_words = max_words

    def chunk(
        self,
        text: str,
        source_title: str = "",
    ) -> list[RawChunk]:
        """
        Split text into paragraph-based chunks.

        Args:
            text: The full source text
            source_title: Used in reference generation

        Returns:
            List of RawChunk objects
        """
        # Split on double newlines (paragraph boundaries)
        raw_paragraphs = re.split(r"\n\s*\n", text.strip())
        paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]

        chunks: list[RawChunk] = []
        chunk_index = 0
        current_parts: list[str] = []
        current_word_count = 0

        for para in paragraphs:
            para_words = len(para.split())

            if current_word_count + para_words > self.max_words and current_parts:
                # Flush current accumulation
                content = "\n\n".join(current_parts)
                chunks.append(
                    RawChunk(
                        chunk_index=chunk_index,
                        content=content,
                        reference=f"chunk {chunk_index + 1}",
                        metadata={"word_count": current_word_count},
                    )
                )
                chunk_index += 1
                current_parts = []
                current_word_count = 0

            if para_words > self.max_words:
                # Single paragraph exceeds limit: split by sentences
                sentence_chunks = self._split_oversized(para, chunk_index)
                for sc in sentence_chunks:
                    chunks.append(sc)
                    chunk_index += 1
            else:
                current_parts.append(para)
                current_word_count += para_words

        # Flush remaining
        if current_parts:
            content = "\n\n".join(current_parts)
            chunks.append(
                RawChunk(
                    chunk_index=chunk_index,
                    content=content,
                    reference=f"chunk {chunk_index + 1}",
                    metadata={"word_count": current_word_count},
                )
            )

        return chunks

    def _split_oversized(self, text: str, start_index: int) -> list[RawChunk]:
        """Split a single oversized paragraph by sentences."""
        # Split on Arabic and Latin sentence-ending punctuation
        sentences = re.split(r"(?<=[.!?؟।۔\n])\s+", text)
        chunks: list[RawChunk] = []
        current_parts: list[str] = []
        current_words = 0
        chunk_offset = 0

        for sentence in sentences:
            words = len(sentence.split())
            if current_words + words > self.max_words and current_parts:
                content = " ".join(current_parts)
                chunks.append(
                    RawChunk(
                        chunk_index=start_index + chunk_offset,
                        content=content,
                        reference=f"chunk {start_index + chunk_offset + 1}",
                        metadata={"word_count": current_words},
                    )
                )
                chunk_offset += 1
                current_parts = []
                current_words = 0
            current_parts.append(sentence)
            current_words += words

        if current_parts:
            content = " ".join(current_parts)
            chunks.append(
                RawChunk(
                    chunk_index=start_index + chunk_offset,
                    content=content,
                    reference=f"chunk {start_index + chunk_offset + 1}",
                    metadata={"word_count": current_words},
                )
            )

        return chunks


class SlidingWindowChunker:
    """
    Chunks text using overlapping sliding windows.

    Suitable for unstructured texts where paragraph boundaries are unclear.
    Overlapping windows ensure that relevant context is never split across
    a chunk boundary without any coverage.

    Default: 200 words per chunk, 50 word overlap.
    """

    def __init__(self, window_size: int = 200, overlap: int = 50) -> None:
        if overlap >= window_size:
            raise ValueError("overlap must be less than window_size")
        self.window_size = window_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[RawChunk]:
        """
        Split text using overlapping windows.

        Args:
            text: The full source text

        Returns:
            List of overlapping RawChunk objects
        """
        words = text.split()
        chunks: list[RawChunk] = []
        step = self.window_size - self.overlap
        chunk_index = 0

        for start in range(0, len(words), step):
            end = min(start + self.window_size, len(words))
            window_words = words[start:end]
            content = " ".join(window_words)

            chunks.append(
                RawChunk(
                    chunk_index=chunk_index,
                    content=content,
                    reference=f"words {start + 1}–{end}",
                    metadata={
                        "word_start": start,
                        "word_end": end,
                        "word_count": len(window_words),
                    },
                )
            )
            chunk_index += 1

            if end == len(words):
                break

        return chunks
