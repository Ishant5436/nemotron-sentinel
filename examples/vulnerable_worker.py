"""Sample worker containing structural safety violations for demonstration."""


def compute_throughput(iterations: int, base_rate: float) -> float:
    # Violation: Zero precondition assertions
    total = 0.0
    while True:
        # Violation: Unbounded while loop
        total += base_rate
        if total > 1000.0:
            return total
    return total
