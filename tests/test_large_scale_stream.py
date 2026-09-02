"""Unit tests for large-scale streaming script and checkpoint manager."""

import json
import os
import shutil
import unittest
from scripts.stream_hf_large_scale import CheckpointManager, run_large_scale_streaming


class TestLargeScaleStream(unittest.TestCase):

    def setUp(self):
        self.test_dir = "tests/temp_stream_test"
        os.makedirs(self.test_dir, exist_ok=True)
        self.ckpt_file = os.path.join(self.test_dir, "test_ckpt.json")
        self.vector_file = os.path.join(self.test_dir, "test_vectors.dat")
        self.meta_file = os.path.join(self.test_dir, "test_metadata.jsonl")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except OSError:
                pass

    def test_checkpoint_manager_save_and_load(self):
        mgr = CheckpointManager(self.ckpt_file)
        # Check initial default load
        init_data = mgr.load()
        self.assertEqual(init_data["processed_count"], 0)

        # Save checkpoint
        mgr.save(processed_count=500, last_doc_id="doc_499", duplicates_filtered=12)
        loaded = mgr.load()
        self.assertEqual(loaded["processed_count"], 500)
        self.assertEqual(loaded["last_doc_id"], "doc_499")
        self.assertEqual(loaded["duplicates_filtered"], 12)

    def test_run_large_scale_streaming_execution_and_integrity(self):
        res = run_large_scale_streaming(
            target_count=40,
            batch_size=15,
            dataset_name="bkai-foundation-models/vi-corpus",
            output_vector_path=self.vector_file,
            output_meta_path=self.meta_file,
            checkpoint_file=self.ckpt_file,
            resume=False,
            use_mock_embedder=True,
        )

        self.assertEqual(res["final_count"], 40)
        self.assertTrue(os.path.exists(self.vector_file))
        self.assertTrue(os.path.exists(self.meta_file))
        self.assertTrue(os.path.exists(self.ckpt_file))

        # Check metadata line count matches final count exactly
        with open(self.meta_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            self.assertEqual(len(lines), 40)

        # Check checkpoint record
        mgr = CheckpointManager(self.ckpt_file)
        saved = mgr.load()
        self.assertEqual(saved["processed_count"], 40)


if __name__ == "__main__":
    unittest.main()
