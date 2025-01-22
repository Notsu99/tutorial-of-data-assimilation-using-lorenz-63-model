import copy
from logging import getLogger

import torch

from .utils.lorenz63_config import Lorenz63Config
from .utils.time_integration import integrate_one_step_rk4

logger = getLogger()


class Lorenz63:
    def __init__(self, conf: Lorenz63Config, show_input_cfg_info: bool = True):
        #
        if show_input_cfg_info:
            logger.info("Input config to Lorenz63 is in the following:")
            logger.info(f"{conf.to_json_str()}")

        if conf.precision == "double":
            self.complex_dtype = torch.complex128
            self.real_dtype = torch.float64
        elif conf.precision == "single":
            self.complex_dtype = torch.complex64
            self.real_dtype = torch.float32
        else:
            raise ValueError(f"{conf.precision} is not supported")

        self.device = conf.device
        self.n_batch = conf.n_batch
        self.noise_amplitude = conf.noise_amplitude
        self.conf = copy.deepcopy(conf)

        self.X = None
        self.t = None

    def reset(self):
        self.X = None
        self.t = None

    def initialize(self, X: torch.Tensor):
        assert len(X) == 3

        self.reset()

        if self.n_batch > 1:
            noise = self.noise_amplitude * torch.randn(
                size=(self.n_batch - 1,) + (X.shape),
                dtype=self.real_dtype,
                device=self.device,
            )

            self.X = torch.cat([X.unsqueeze(0), (X + noise)])

        else:
            self.X = X[None, :]

        self.t = 0.0

    def set_state(self, X: torch.Tensor):
        self.X = X.to(self.device)

    def get_state(self) -> torch.Tensor:
        return self.X.cpu()

    def integrate_n_steps(self, dt_per_step: float, n_steps: int):
        assert isinstance(dt_per_step, float) and dt_per_step > 0
        assert isinstance(n_steps, int) and n_steps > 0

        for _ in range(n_steps):
            self.X = integrate_one_step_rk4(
                x=self.X, dt=dt_per_step, dxdt=self._lorenz63_dxdt
            )
            self.t += dt_per_step

    # The following are private methods.

    def _lorenz63_dxdt(
        self, X: torch.Tensor, SIGMA=10, RHO=28, BETA=8 / 3
    ) -> torch.Tensor:
        #
        # X.shape is (batch, (x, y, z))
        assert X.ndim == 2

        dx0dt = SIGMA * (X[..., 1] - X[..., 0])
        dx1dt = X[..., 0] * (RHO - X[..., 2]) - X[..., 1]
        dx2dt = X[..., 0] * X[..., 1] - BETA * X[..., 2]

        return torch.stack([dx0dt, dx1dt, dx2dt], dim=-1)
