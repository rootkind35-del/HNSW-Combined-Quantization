"""Unit tests for Embedder modules."""

import os
import unittest
import numpy as np
from ann_data.embedder import BatchEmbedder, MockEmbedder, SentenceTransformerEmbedder
from ann_data.storage import MemmapStorage


class TestEmbedder(unittest.TestCase):

    def setUp(self):
        self.test_dat = "tests/temp_test_embedder.dat"
        self.dim = 384
        self.storage = MemmapStorage(self.test_dat, max_records=20, dim=self.dim)

    def tearDown(self):
        self.storage.close()
        if os.path.exists(self.test_dat):
            try:
                os.remove(self.test_dat)
            except OSError:
                pass

    def test_mock_embedder_properties(self):
        embedder = MockEmbedder(dim=self.dim, seed=123)
        self.assertEqual(embedder.dim, self.dim)
        
        texts = ["Câu 1", "Câu 2", "Câu 3"]
        vectors = embedder.encode(texts)
        self.assertEqual(vectors.shape, (3, self.dim))
        self.assertEqual(vectors.dtype, np.float32)
        
        # Verify L2 normalization
        norms = np.linalg.norm(vectors, axis=1)
        np.testing.assert_allclose(norms, np.ones(3), rtol=1e-5)

    def test_batch_embedder_auto_flush(self):
        embedder = MockEmbedder(dim=self.dim)
        batch_embedder = BatchEmbedder(embedder=embedder, storage=self.storage, batch_size=3)

        # Adding 2 items: should remain in buffer
        batch_embedder.add("Văn bản 1")
        batch_embedder.add("Văn bản 2")
        self.assertEqual(len(batch_embedder.buffer), 2)
        self.assertEqual(self.storage.current_count, 0)

        # Adding 3rd item: triggers auto-flush
        batch_embedder.add("Văn bản 3")
        self.assertEqual(len(batch_embedder.buffer), 0)
        self.assertEqual(self.storage.current_count, 3)

        # Flush remaining
        batch_embedder.add("Văn bản 4")
        batch_embedder.flush()
        self.assertEqual(self.storage.current_count, 4)

    def test_sentence_transformer_fallback_safety(self):
        # Should initialize gracefully without crashing even if system has DLL policy blocks
        st_embedder = SentenceTransformerEmbedder(dim=self.dim)
        self.assertEqual(st_embedder.dim, self.dim)
        
        out = st_embedder.encode(["Thử nghiệm an toàn fallback"])
        self.assertEqual(out.shape, (1, self.dim))


if __name__ == "__main__":
    unittest.main()
