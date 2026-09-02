"""Bộ điều khiển dừng sớm thích ứng (Adaptive Early-Exit Controller) cho thuật toán duyệt đồ thị."""

from collections import deque
from typing import Optional


class AdaptiveEarlyExitController:
    """
    Theo dõi mức độ hội tụ khoảng cách trong quá trình duyệt đồ thị HNSW.
    Tự động ngắt vòng lặp tìm kiếm khi mức độ cải thiện khoảng cách qua tau bước nhảy liên tiếp nhỏ hơn ngưỡng epsilon.
    Cơ chế này loại bỏ các bước nhảy dư thừa ở vùng phẳng (plateau), giúp giảm đáng kể thời gian truy vấn.
    """

    def __init__(self, tau: int = 3, epsilon: float = 1e-4, min_steps: int = 5):
        """
        Khởi tạo bộ điều khiển dừng sớm thích ứng.

        Tham số:
            tau: Số bước nhảy trong quá khứ được dùng để đánh giá mức độ cải thiện khoảng cách (cửa sổ trượt).
            epsilon: Ngưỡng hội tụ tối thiểu; nếu độ thu hẹp khoảng cách < epsilon thì kích hoạt dừng sớm.
            min_steps: Số bước khám phá tối thiểu bắt buộc trước khi cho phép kích hoạt dừng sớm (tránh dừng non).
        """
        if tau < 1:
            raise ValueError("tau phải lớn hơn hoặc bằng 1")
        if epsilon < 0:
            raise ValueError("epsilon phải là số không âm")

        self.tau = tau
        self.epsilon = epsilon
        self.min_steps = min_steps
        self.history = deque(maxlen=self.tau + 1)
        self.step_count = 0
        self.terminated_early = False

    def reset(self) -> None:
        """Đặt lại toàn bộ trạng thái theo dõi để chuẩn bị cho câu truy vấn mới."""
        self.history.clear()
        self.step_count = 0
        self.terminated_early = False

    def update(self, current_best_distance: float) -> bool:
        """
        Cập nhật khoảng cách tốt nhất ghi nhận được ở bước nhảy hiện tại và đưa ra quyết định dừng sớm.

        Tham số:
            current_best_distance: Khoảng cách nhỏ nhất tới vector truy vấn tìm thấy tính đến thời điểm hiện tại.

        Trả về:
            bool: True nếu thỏa mãn điều kiện dừng sớm (kết thúc tìm kiếm), False nếu tiếp tục duyệt tiếp.
        """
        self.step_count += 1
        self.history.append(current_best_distance)

        # Chưa đạt số bước khám phá tối thiểu thì tiếp tục tìm kiếm
        if self.step_count < self.min_steps:
            return False

        # Chưa tích lũy đủ lịch sử kích thước tau bước
        if len(self.history) <= self.tau:
            return False

        oldest_dist = self.history[0]
        improvement = oldest_dist - current_best_distance

        # Nếu mức cải thiện sau tau bước nhỏ hơn ngưỡng epsilon thì kích hoạt dừng sớm
        if improvement < self.epsilon:
            self.terminated_early = True
            return True

        return False

