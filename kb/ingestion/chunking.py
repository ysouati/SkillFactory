def chunk_text(text: str, chunk_chars: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks, preferring paragraph/sentence boundaries.

    Char-based (not token-based) for simplicity and zero tokenizer dependency.
    Good enough for retrieval; upgrade to token-aware chunking later if needed.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_chars, n)
        if end < n:
            # Prefer a paragraph break, then a sentence break, in the back half of the window.
            floor = start + chunk_chars // 2
            brk = text.rfind("\n\n", floor, end)
            if brk == -1:
                brk = text.rfind(". ", floor, end)
                if brk != -1:
                    brk += 1
            if brk != -1 and brk > start:
                end = brk
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks
