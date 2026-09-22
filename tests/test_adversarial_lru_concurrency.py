"""Empirical Adversarial Concurrency and Torture Test Suite for ApplicationLRUCache and DirectIOManager.

Authored by: Challenger 1 - Iteration 2 (LRU Concurrency Verifier)
Purpose: Independent verification and stress-testing under extreme thread contention,
cache churn, eviction races, and interleaved clear/len/get/put calls.
"""

import concurrent.futures
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
import numpy as np

# Ensure src is in sys.path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SRC_DIR = os.path.join(_REPO_ROOT, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from ann_index.io_manager import ApplicationLRUCache, DirectIOManager


class TestAdversarialLRUConcurrency(unittest.TestCase):
    """Torture tests targeting concurrency race conditions in ApplicationLRUCache."""

    def test_extreme_concurrent_get_put_churn(self):
        """Torture test: 40 threads doing rapid get and put on tiny capacity under 1us context switch."""
        old_switch = sys.getswitchinterval()
        sys.setswitchinterval(1e-7)
        capacity = 5
        cache = ApplicationLRUCache(capacity=capacity)
        errors = []
        stop_event = threading.Event()

        def reader(tid: int):
            while not stop_event.is_set():
                key = (tid * 7 + int(time.time() * 1000)) % 20
                try:
                    val = cache.get(key)
                    if val is not None and not isinstance(val, np.ndarray):
                        errors.append(f"Reader {tid}: invalid value type {type(val)}")
                        break
                except Exception as e:
                    errors.append(f"Reader {tid} exception: {type(e).__name__}: {e}")
                    break

        def writer(tid: int):
            vec = np.ones(8, dtype=np.float32) * tid
            while not stop_event.is_set():
                key = (tid * 13 + int(time.time() * 1000)) % 20
                try:
                    cache.put(key, vec)
                    c_len = len(cache)
                    if c_len > capacity:
                        errors.append(f"Writer {tid}: cache length {c_len} exceeded capacity {capacity}")
                        break
                except Exception as e:
                    errors.append(f"Writer {tid} exception: {type(e).__name__}: {e}")
                    break

        try:
            threads = []
            for i in range(20):
                threads.append(threading.Thread(target=reader, args=(i,)))
            for i in range(20):
                threads.append(threading.Thread(target=writer, args=(i,)))

            for t in threads:
                t.start()

            # Run torture for 2 seconds
            time.sleep(2.0)
            stop_event.set()

            for t in threads:
                t.join(timeout=5.0)

            self.assertEqual(len(errors), 0, f"Concurrency torture failed: {errors[:5]}")
            self.assertLessEqual(len(cache), capacity)
        finally:
            sys.setswitchinterval(old_switch)

    def test_concurrent_clear_and_interleaved_operations(self):
        """Stress test: Interleave get, put, len, and clear across multiple threads simultaneously."""
        old_switch = sys.getswitchinterval()
        sys.setswitchinterval(1e-7)
        cache = ApplicationLRUCache(capacity=10)
        errors = []
        stop_event = threading.Event()

        def reader():
            while not stop_event.is_set():
                try:
                    _ = cache.get(np.random.randint(0, 30))
                except Exception as e:
                    errors.append(f"Reader: {type(e).__name__}: {e}")
                    break

        def writer():
            dummy = np.zeros(4, dtype=np.float32)
            while not stop_event.is_set():
                try:
                    cache.put(np.random.randint(0, 30), dummy)
                except Exception as e:
                    errors.append(f"Writer: {type(e).__name__}: {e}")
                    break

        def clearer():
            while not stop_event.is_set():
                try:
                    cache.clear()
                    time.sleep(0.001)
                except Exception as e:
                    errors.append(f"Clearer: {type(e).__name__}: {e}")
                    break

        def inspector():
            while not stop_event.is_set():
                try:
                    l = len(cache)
                    if l > 10:
                        errors.append(f"Inspector: cache size {l} > 10")
                        break
                except Exception as e:
                    errors.append(f"Inspector: {type(e).__name__}: {e}")
                    break

        try:
            threads = [
                threading.Thread(target=reader) for _ in range(8)
            ] + [
                threading.Thread(target=writer) for _ in range(8)
            ] + [
                threading.Thread(target=clearer) for _ in range(4)
            ] + [
                threading.Thread(target=inspector) for _ in range(4)
            ]

            for t in threads:
                t.start()

            time.sleep(1.5)
            stop_event.set()

            for t in threads:
                t.join(timeout=5.0)

            self.assertEqual(len(errors), 0, f"Concurrent clear/interleaved ops failed: {errors[:5]}")
        finally:
            sys.setswitchinterval(old_switch)

    def test_boundary_capacities(self):
        """Verify capacity edge cases: capacity <= 0 is safely clamped to 1, exact eviction works."""
        cache_zero = ApplicationLRUCache(capacity=0)
        self.assertEqual(cache_zero.capacity, 1)

        cache_neg = ApplicationLRUCache(capacity=-10)
        self.assertEqual(cache_neg.capacity, 1)

        # Capacity 1 behavior
        v1 = np.array([1.0], dtype=np.float32)
        v2 = np.array([2.0], dtype=np.float32)

        cache_zero.put(100, v1)
        self.assertEqual(len(cache_zero), 1)
        np.testing.assert_array_equal(cache_zero.get(100), v1)

        cache_zero.put(200, v2)
        self.assertEqual(len(cache_zero), 1)
        self.assertIsNone(cache_zero.get(100))
        np.testing.assert_array_equal(cache_zero.get(200), v2)

    def test_same_key_overwrite_concurrency(self):
        """Multiple threads writing different vectors to the EXACT SAME key concurrently."""
        cache = ApplicationLRUCache(capacity=10)
        errors = []

        def worker(tid: int):
            for i in range(1000):
                vec = np.full(4, float(tid * 1000 + i), dtype=np.float32)
                try:
                    cache.put(42, vec)
                    res = cache.get(42)
                    if res is None:
                        errors.append(f"Worker {tid}: got None for key 42 immediately after put")
                        break
                except Exception as e:
                    errors.append(f"Worker {tid}: {type(e).__name__}: {e}")
                    break

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(16)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Same key overwrite failed: {errors[:5]}")
        self.assertEqual(len(cache), 1)


class TestAdversarialDirectIOConcurrency(unittest.TestCase):
    """Stress tests targeting DirectIOManager under concurrent read/write and churn."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="adv_io_")
        self.dim = 64
        self.file_path = os.path.join(self.test_dir, "vectors.bin")
        self.num_vectors = 200
        self.ground_truth = np.random.randn(self.num_vectors, self.dim).astype(np.float32)

        self.io = DirectIOManager(filepath=self.file_path, dim=self.dim, cache_capacity=4)
        self.io.write_batch(self.ground_truth)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_concurrent_async_read_and_continuous_write(self):
        """Concurrent reader threads calling async_read_batch while writer threads append new vectors."""
        errors = []
        stop_event = threading.Event()

        def reader(tid: int):
            rng = np.random.RandomState(tid * 999 + 7)
            while not stop_event.is_set():
                ids = rng.choice(self.num_vectors, size=6, replace=False).tolist()
                try:
                    res = self.io.async_read_batch(ids)
                    if len(res) != 6:
                        errors.append(f"Reader {tid}: incomplete result {len(res)} vs 6")
                        break
                    for vid in ids:
                        if not np.array_equal(res[vid], self.ground_truth[vid]):
                            errors.append(f"Reader {tid}: data mismatch at vid {vid}")
                            break
                except Exception as e:
                    errors.append(f"Reader {tid} exception: {type(e).__name__}: {e}")
                    break

        def writer(tid: int):
            while not stop_event.is_set():
                new_vec = np.random.randn(self.dim).astype(np.float32)
                try:
                    _ = self.io.write_vector(new_vec)
                except Exception as e:
                    errors.append(f"Writer {tid} exception: {type(e).__name__}: {e}")
                    break
                time.sleep(0.005)

        threads = [threading.Thread(target=reader, args=(i,)) for i in range(16)] + [
            threading.Thread(target=writer, args=(i,)) for i in range(4)
        ]

        for t in threads:
            t.start()

        time.sleep(2.0)
        stop_event.set()

        for t in threads:
            t.join(timeout=5.0)

        self.assertEqual(len(errors), 0, f"Concurrent read/write test failed: {errors[:5]}")


if __name__ == "__main__":
    unittest.main()
