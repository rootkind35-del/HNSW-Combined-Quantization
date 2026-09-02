"""Unit tests for MemmapStorage module."""

import os
import unittest
import numpy as np
from ann_data.storage import MemmapStorage


class TestMemmapStorage(unittest.TestCase):

    def setUp(self):
        self.test_file = "tests/temp_test_storage.dat"
        self.max_records = 100
        self.dim = 16
        self.storage = MemmapStorage(
            file_path=self.test_file,
            max_records=self.max_records,
            dim=self.dim,
            dtype="float32",
            mode="w+",
        )

    def tearDown(self):
        self.storage.close()
        if os.path.exists(self.test_file):
            try:
                os.remove(self.test_file)
            except OSError:
                pass

    def test_append_batch_and_read_slice(self):
        vectors = np.random.randn(10, self.dim).astype(np.float32)
        start, end = self.storage.append_batch(vectors)
        
        self.assertEqual(start, 0)
        self.assertEqual(end, 10)
        self.assertEqual(self.storage.current_count, 10)

        # Read back slice and verify numerical equality
        read_vectors = self.storage.read_slice(0, 10)
        np.testing.assert_allclose(read_vectors, vectors, rtol=1e-5)

    def test_read_specific_indices(self):
        vectors = np.arange(5 * self.dim, dtype=np.float32).reshape(5, self.dim)
        self.storage.append_batch(vectors)

        indices = [1, 3]
        retrieved = self.storage.read_indices(indices)
        np.testing.assert_allclose(retrieved, vectors[indices], rtol=1e-5)

    def test_dimension_mismatch_error(self):
        wrong_dim_vectors = np.random.randn(5, self.dim + 2).astype(np.float32)
        with self.assertRaises(ValueError):
            self.storage.append_batch(wrong_dim_vectors)

    def test_capacity_overflow_error(self):
        overflow_vectors = np.random.randn(self.max_records + 1, self.dim).astype(np.float32)
        with self.assertRaises(OverflowError):
            self.storage.append_batch(overflow_vectors)

    def test_context_manager(self):
        ctx_file = "tests/temp_ctx_storage.dat"
        with MemmapStorage(ctx_file, max_records=10, dim=4) as storage:
            storage.append_batch(np.ones((2, 4), dtype=np.float32))
            self.assertEqual(storage.current_count, 2)
            
        if os.path.exists(ctx_file):
            try:
                os.remove(ctx_file)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
