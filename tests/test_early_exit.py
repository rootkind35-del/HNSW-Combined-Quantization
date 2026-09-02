"""Unit tests for AdaptiveEarlyExitController module."""

import unittest
from ann_index.early_exit import AdaptiveEarlyExitController


class TestAdaptiveEarlyExit(unittest.TestCase):

    def test_active_convergence_does_not_terminate(self):
        controller = AdaptiveEarlyExitController(tau=3, epsilon=0.01, min_steps=3)
        # Sequence of significantly decreasing distances: 10.0 -> 8.0 -> 5.0 -> 2.0 -> 0.5
        distances = [10.0, 8.0, 5.0, 2.0, 0.5]
        should_exits = [controller.update(d) for d in distances]

        # In all steps, improvement was > epsilon, so it should never terminate early
        self.assertFalse(any(should_exits))

    def test_plateau_triggers_early_exit(self):
        controller = AdaptiveEarlyExitController(tau=3, epsilon=0.01, min_steps=4)
        # Decreases then plateaus: 10.0 -> 5.0 -> 2.0 -> 1.005 -> 1.002 -> 1.001 -> 1.000
        distances = [10.0, 5.0, 2.0, 1.005, 1.002, 1.001, 1.000]
        results = []
        for d in distances:
            res = controller.update(d)
            results.append(res)

        # After step 4, the delta over tau=3 steps is 1.005 - 1.000 = 0.005 < 0.01 -> triggers exit!
        self.assertTrue(controller.terminated_early)
        self.assertTrue(results[-1])

    def test_reset(self):
        controller = AdaptiveEarlyExitController(tau=2, epsilon=0.1, min_steps=2)
        controller.update(1.0)
        controller.update(1.0)
        controller.update(1.0)
        self.assertTrue(controller.terminated_early)

        controller.reset()
        self.assertEqual(controller.step_count, 0)
        self.assertFalse(controller.terminated_early)


if __name__ == "__main__":
    unittest.main()
