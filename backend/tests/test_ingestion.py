from app.rag.ingestion import _chunk_text


def test_chunk_text_basic():
    text = " ".join(["word"] * 1000)
    chunks = _chunk_text(text, chunk_size=200, overlap=50)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.split()) <= 200


def test_chunk_text_empty():
    assert _chunk_text("") == []


def test_chunk_text_short_input():
    text = "just a few words here"
    chunks = _chunk_text(text, chunk_size=200, overlap=50)
    assert len(chunks) == 1
    assert chunks[0] == text
