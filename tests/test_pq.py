"""Unit tests for ProductQuantizer module."""

import unittest
import numpy as np
from ann_index.pq import ProductQuantizer


class TestProductQuantizer(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        self.num_vectors = 80
        self.dim = 16
        self.num_subvectors = 4
        self.num_clusters = 16  # smaller for fast testing
        self.vectors = np.random.randn(self.num_vectors, self.dim).astype(np.float32)
        self.pq = ProductQuantizer(num_subvectors=self.num_subvectors, num_clusters=self.num_clusters)
        self.pq.fit(self.vectors)

    def test_fit_codebook_shape(self):
        self.assertTrue(self.pq.is_fitted)
        self.assertEqual(self.pq.codebooks.shape, (self.num_subvectors, self.num_clusters, self.dim // self.num_subvectors))

    def test_encode_and_decode_shapes(self):
        codes = self.pq.encode(self.vectors)
        self.assertEqual(codes.shape, (self.num_vectors, self.num_subvectors))
        self.assertEqual(codes.dtype, np.uint8)

        reconstructed = self.pq.decode(codes)
        self.assertEqual(reconstructed.shape, self.vectors.shape)

    def test_distance_table_and_adc(self):
        q = np.random.randn(1, self.dim).astype(np.float32)
        lut = self.pq.compute_distance_table(q)
        self.assertEqual(lut.shape, (self.num_subvectors, self.num_clusters))

        codes = self.pq.encode(self.vectors)
        adc_dists = self.pq.asymmetric_distance(lut, codes)

        self.assertEqual(len(adc_dists), self.num_vectors)
        self.assertTrue(np.all(adc_dists >= 0.0))

        # Check correlation with true distances
        true_dists = np.sum((self.vectors - q) ** 2, axis=1)
        corr = np.corrcoef(true_dists, adc_dists)[0, 1]
        self.assertGreater(corr, 0.70)  # Strong positive correlation with ADC


if __name__ == "__main__":
    unittest.main()
