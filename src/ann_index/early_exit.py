"""Adaptive Early-Exit Controller for dynamic graph traversal termination."""

from collections import deque
from typing import Optional


class AdaptiveEarlyExitController:
    """
    Monitors convergence during graph search and halts traversal early when distance
    reduction over tau consecutive hops drops below epsilon.
    """

    def __init__(self, tau: int = 3, epsilon: float = 1e-4, min_steps: int = 5):
        """
        Args:
            tau: Number of past steps over which to evaluate distance improvement.
            epsilon: Convergence threshold below which search terminates early.
            min_steps: Minimum exploration steps before early termination is eligible.
        """
        if tau < 1:
            raise ValueError("tau must be at least 1")
        if epsilon < 0:
            raise ValueError("epsilon must be non-negative")

        self.tau = tau
        self.epsilon = epsilon
        self.min_steps = min_steps
        self.history = deque(maxlen=self.tau + 1)
        self.step_count = 0
        self.terminated_early = False

    def reset(self) -> None:
        """Resets convergence tracking for a new query."""
        self.history.clear()
        self.step_count = 0
        self.terminated_early = False

    def update(self, current_best_distance: float) -> bool:
        """
        Records the best distance observed at current hop and decides whether to terminate.

        Args:
            current_best_distance: Smallest distance to query found so far.

        Returns:
            bool: True if early exit condition is met, False to continue search.
        """
        self.step_count += 1
        self.history.append(current_best_distance)

        if self.step_count < self.min_steps:
            return False

        if len(self.history) <= self.tau:
            return False

        oldest_dist = self.history[0]
        improvement = oldest_dist - current_best_distance

        # If improvement over past tau steps is less than threshold, terminate
        if improvement < self.epsilon:
            self.terminated_early = True
            return True

        return False
