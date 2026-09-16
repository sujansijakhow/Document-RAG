from app.services.chunking import FixedSizeChunker, RecursiveParagraphChunker


def test_fixed_size_chunker_respects_size_and_overlap():
    text = "a" * 2500
    chunker = FixedSizeChunker(chunk_size=800, overlap=100)
    chunks = chunker.split(text)

    assert all(len(c) <= 800 for c in chunks)
    assert len(chunks) >= 3
    assert sum(len(c) for c in chunks) >= len(text)


def test_fixed_size_chunker_handles_empty_text():
    assert FixedSizeChunker().split("   ") == []


def test_recursive_paragraph_chunker_keeps_paragraphs_together():
    text = "Para one is short.\n\nPara two is also short.\n\nPara three wraps things up."
    chunker = RecursiveParagraphChunker(max_chunk_size=200, min_chunk_size=10)
    chunks = chunker.split(text)

    assert len(chunks) == 1
    assert "Para one" in chunks[0]
    assert "Para three" in chunks[0]


def test_recursive_paragraph_chunker_splits_oversized_paragraph_by_sentence():
    long_para = " ".join(f"Sentence number {i}." for i in range(60))
    chunker = RecursiveParagraphChunker(max_chunk_size=200, min_chunk_size=50)
    chunks = chunker.split(long_para)

    assert len(chunks) > 1
    assert all(len(c) <= 250 for c in chunks)
