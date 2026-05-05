from smm.core.chunker import chunk_document, Chunk


class TestMarkdownChunking:
    def test_single_heading(self):
        content = "# Title\nSome content here."
        chunks = chunk_document(content, "md", {"chunking": {"strategy": "semantic", "max_chunk_size": 2000, "overlap": 200}})
        assert len(chunks) == 1
        assert "Title" in chunks[0].heading

    def test_multiple_headings(self):
        content = "# First\nContent one.\n\n## Second\nContent two."
        chunks = chunk_document(content, "md", {"chunking": {"strategy": "semantic", "max_chunk_size": 2000, "overlap": 200}})
        assert len(chunks) >= 2

    def test_no_headings(self):
        content = "Just some plain text without headings."
        chunks = chunk_document(content, "md", {"chunking": {"strategy": "semantic", "max_chunk_size": 2000, "overlap": 200}})
        assert len(chunks) == 1
        assert chunks[0].heading == ""


class TestTxtChunking:
    def test_paragraph_split(self):
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = chunk_document(content, "txt", {"chunking": {"strategy": "semantic", "max_chunk_size": 2000, "overlap": 200}})
        assert len(chunks) == 3

    def test_empty_content(self):
        chunks = chunk_document("", "txt", {"chunking": {"strategy": "semantic", "max_chunk_size": 2000, "overlap": 200}})
        assert len(chunks) == 0


class TestRstChunking:
    def test_section_split(self):
        content = "Title\n=====\nContent one.\n\nSection\n-------\nContent two."
        chunks = chunk_document(content, "rst", {"chunking": {"strategy": "semantic", "max_chunk_size": 2000, "overlap": 200}})
        assert len(chunks) >= 2

    def test_no_sections(self):
        content = "Plain RST text without section markers."
        chunks = chunk_document(content, "rst", {"chunking": {"strategy": "semantic", "max_chunk_size": 2000, "overlap": 200}})
        assert len(chunks) == 1


class TestFixedChunking:
    def test_fixed_size(self):
        content = "A" * 3000
        chunks = chunk_document(content, "txt", {
            "chunking": {
                "strategy": "fixed",
                "fixed": {"chunk_size": 1000, "chunk_overlap": 100},
                "max_chunk_size": 2000,
                "overlap": 200,
            }
        })
        assert len(chunks) > 1
        for ch in chunks:
            assert len(ch.text) <= 2000


class TestOversizedSplit:
    def test_split_large_chunk(self):
        content = "Sentence one. Sentence two. Sentence three. " * 50
        chunks = chunk_document(content, "txt", {"chunking": {"strategy": "semantic", "max_chunk_size": 200, "overlap": 50}})
        assert len(chunks) >= 1
        for ch in chunks:
            assert len(ch.text) <= 200
