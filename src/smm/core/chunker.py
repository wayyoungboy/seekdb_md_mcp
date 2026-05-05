from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    text: str
    index: int
    heading: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def chunk_document(
    content: str,
    file_type: str,
    cfg: dict[str, Any],
) -> list[Chunk]:
    strategy = cfg["chunking"]["strategy"]
    max_size = cfg["chunking"].get("max_chunk_size", 2000)
    overlap = cfg["chunking"].get("overlap", 200)

    if strategy == "semantic":
        chunks = _semantic_chunk(content, file_type, cfg)
    else:
        chunk_size = cfg["chunking"]["fixed"].get("chunk_size", 1000)
        chunk_overlap = cfg["chunking"]["fixed"].get("chunk_overlap", 200)
        chunks = _fixed_chunk(content, chunk_size, chunk_overlap)

    result = []
    idx = 0
    for chunk in chunks:
        if len(chunk.text) > max_size:
            sub_chunks = _split_oversized(chunk.text, max_size, overlap)
            for sc in sub_chunks:
                result.append(Chunk(
                    text=sc,
                    index=idx,
                    heading=chunk.heading,
                    metadata=chunk.metadata,
                ))
                idx += 1
        else:
            chunk.index = idx
            result.append(chunk)
            idx += 1

    return result


def _semantic_chunk(content: str, file_type: str, cfg: dict[str, Any]) -> list[Chunk]:
    if file_type == "md":
        return _chunk_markdown(content)
    elif file_type == "rst":
        return _chunk_rst(content)
    else:
        return _chunk_txt(content)


def _chunk_markdown(content: str) -> list[Chunk]:
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    chunks: list[Chunk] = []
    positions = [(m.start(), m.group(0)) for m in heading_pattern.finditer(content)]

    if not positions:
        text = content.strip()
        if text:
            chunks.append(Chunk(text=text, index=0))
        return chunks

    if positions[0][0] > 0:
        pre = content[: positions[0][0]].strip()
        if pre:
            chunks.append(Chunk(text=pre, index=0))

    for i, (pos, heading_line) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(content)
        section_text = content[pos:end].strip()
        if section_text:
            chunks.append(Chunk(text=section_text, index=0, heading=heading_line.strip()))

    return chunks


def _chunk_rst(content: str) -> list[Chunk]:
    section_pattern = re.compile(
        r"^(.+)\n([=\-~`:'\"^_*+#]{3,})$", re.MULTILINE
    )
    chunks: list[Chunk] = []
    positions = []
    for m in section_pattern.finditer(content):
        title_start = m.start()
        positions.append((title_start, m.group(1).strip()))

    if not positions:
        text = content.strip()
        if text:
            chunks.append(Chunk(text=text, index=0))
        return chunks

    if positions[0][0] > 0:
        pre = content[: positions[0][0]].strip()
        if pre:
            chunks.append(Chunk(text=pre, index=0))

    for i, (pos, title) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(content)
        section_text = content[pos:end].strip()
        if section_text:
            chunks.append(Chunk(text=section_text, index=0, heading=title))

    return chunks


def _chunk_txt(content: str) -> list[Chunk]:
    paragraphs = re.split(r"\n\s*\n", content)
    chunks: list[Chunk] = []
    for para in paragraphs:
        text = para.strip()
        if text:
            chunks.append(Chunk(text=text, index=0))
    return chunks


def _fixed_chunk(content: str, chunk_size: int, overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    start = 0
    while start < len(content):
        end = start + chunk_size
        text = content[start:end].strip()
        if text:
            chunks.append(Chunk(text=text, index=0))
        start = end - overlap if overlap < chunk_size else end
    return chunks


def _split_oversized(text: str, max_size: int, overlap: int) -> list[str]:
    sentences = re.split(r"(?<=[.!?。！？\n])\s+", text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 > max_size and current:
            chunks.append(current.strip())
            overlap_text = current[-overlap:] if len(current) > overlap else current
            current = overlap_text + " " + sentence
        else:
            current = current + " " + sentence if current else sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks if chunks else [text[:max_size]]
