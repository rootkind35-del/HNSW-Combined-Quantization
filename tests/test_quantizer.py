"""Unit tests for ScalarQuantizer module."""

import unittest
import numpy as np
from ann_index.quantizer import ScalarQuantizer


class TestScalarQuantizer(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        self.dim = 16
        self.vectors = np.random.uniform(-1.0, 1.0, size=(100, self.dim)).astype(np.float32)
        self.sq = ScalarQuantizer(per_channel=True)
        self.sq.fit(self.vectors)

    def test_quantize_output_bounds_and_dtype(self):
        q = self.sq.quantize(self.vectors)
        self.assertEqual(q.dtype, np.uint8)
        self.assertEqual(q.shape, self.vectors.shape)
        self.assertGreaterEqual(int(np.min(q)), 0)
        self.assertLessEqual(int(np.max(q)), 255)

    def test_reconstruction_error_bounded(self):
        q = self.sq.quantize(self.vectors)
        reconstructed = self.sq.dequantize(q)
        mae = np.mean(np.abs(self.vectors - reconstructed))
        # 8-bit quantization over [-1, 1] has step size 2 / 255 ~= 0.0078, MAE should be < 0.01
        self.assertLess(mae, 0.02)

    def test_quantized_distance_correlation(self):
        v1 = self.vectors[0]
        v2 = self.vectors[1]

        true_dist = float(np.sum((v1 - v2) ** 2))

        q1 = self.sq.quantize(v1.reshape(1, -1))[0]
        q2 = self.sq.quantize(v2.reshape(1, -1))[0]

        approx_dist = self.sq.compute_distance(q1, q2)
        # Relative error should be small (< 5%)
        relative_error = abs(true_dist - approx_dist) / max(true_dist, 1e-6)
        self.assertLess(relative_error, 0.05)


if __name__ == "__main__":
    unittest.main()
