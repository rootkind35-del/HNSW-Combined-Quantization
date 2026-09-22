"""Root alias for LocalShard, ShardedIVFHNSW, and TwoTierQuantizedHNSW backwards compatibility."""

import os
import sys

_SRC_DIR = os.path.join(os.path.dirname(__file__), "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from ann_index.two_tier_hnsw import LocalShard, ShardedIVFHNSW, TwoTierQuantizedHNSW

__all__ = ["LocalShard", "ShardedIVFHNSW", "TwoTierQuantizedHNSW"]
