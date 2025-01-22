from logging import getLogger
from typing import Callable

import torch

logger = getLogger()


def integrate_one_step_rk4(
    *,
    x: torch.Tensor,
    dt: float,
    dxdt: Callable[[torch.Tensor], torch.Tensor],
) -> torch.Tensor:
    #
    k1 = dt * dxdt(x)
    k2 = dt * dxdt(x + k1 / 2)
    k3 = dt * dxdt(x + k2 / 2)
    k4 = dt * dxdt(x + k3 / 2)

    return x + (k1 + 2 * k2 + 2 * k3 + k4) / 6