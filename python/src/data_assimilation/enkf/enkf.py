import copy
from logging import getLogger

import torch

from .utils.enkf_config import EnKFPOConfig

logger = getLogger()


class EnKFPO:
    def __init__(self, conf: EnKFPOConfig, show_input_cfg_info: bool = True):
        #
        if show_input_cfg_info:
            logger.info("Input config to EnKFPO is in the following:")
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
        self.n_ens = conf.n_ensemble
        self.inflation = conf.inflation_coefficient
        self.obs_std = conf.obs_std
        self.obs_matrix = torch.tensor(conf.obs_matrix, dtype=self.real_dtype).to(self.device)
        self.conf = copy.deepcopy(conf)

        # obs_matrix shape = (num_obs, (x, y, z))
        self.num_obs = self.obs_matrix.shape[0]

        self.obs = None

    def apply(self, *, Xf: torch.Tensor, Xtrue: torch.Tensor):
        assert Xf.shape == (self.n_ens, self.obs_matrix.shape[-1])
        assert Xtrue.shape == (self.obs_matrix[-1].shape)

        Xanarysis, obs = self._assimilate(
            Xf=Xf.to(self.device), Xtrue=Xtrue.to(self.device)
        )

        return Xanarysis.cpu(), obs.cpu()

    # The following are private methods.

    def _assimilate(self, *, Xf: torch.Tensor, Xtrue: torch.Tensor):
        obs = self._make_observation(Xtrue=Xtrue)
        obs, obs_noise_cov = self._add_noise_to_obs_and_calc_obs_noise_covariance(
            obs=obs
        )

        forecast_cov = self._calc_forecast_covariance(Xf=Xf)

        kalman_gain = self._calc_kalman_gain(
            forecast_cov=forecast_cov, obs_cov=obs_noise_cov, obs_matrix=self.obs_matrix
        )

        innovation = obs - Xf.mm(self.obs_matrix.t())
        analysis = Xf + innovation.mm(kalman_gain)

        return analysis, obs

    def _add_noise_to_obs_and_calc_obs_noise_covariance(
        self, obs
    ) -> tuple[torch.Tensor, torch.Tensor]:
        #
        # obs = (x, y, z)
        assert obs.ndim == 1

        noise = self.obs_std * torch.randn(self.n_ens, self.num_obs).to(obs.device)
        noise = noise - torch.mean(noise, dim=0, keepdim=True)
        assert noise.shape == (self.n_ens, self.num_obs)

        cov = noise.t().mm(noise) / (self.n_ens - 1)

        # add ensemble dim
        obs = obs[None, :]

        assert obs.shape[1] == noise.shape[1] == self.num_obs

        # This is one feature of EnKF PO (perturbed observations) method
        # 撹乱付き観測 p82より (https://www.asakura.co.jp/detail.php?book_code=12786)
        obs = obs + noise

        return obs, cov

    def _make_observation(self, Xtrue: torch.Tensor):
        obs = self.obs_matrix.mm(Xtrue.reshape(-1, 1)).reshape(-1)
        obs = obs + torch.randn(self.num_obs).to(Xtrue.device)

        assert obs.shape == Xtrue.shape

        return obs

    def _calc_forecast_covariance(self, Xf: torch.Tensor) -> torch.Tensor:
        forecast_mean = torch.mean(Xf, dim=0, keepdim=True)
        forecast_anomaly = Xf - forecast_mean

        forecast_covariance = forecast_anomaly.t().mm(forecast_anomaly) / (
            self.n_ens - 1
        )

        forecast_covariance = self.inflation * forecast_covariance

        assert forecast_covariance.shape == (Xf.shape[-1], Xf.shape[-1])

        return forecast_covariance

    def _calc_kalman_gain(
        self,
        *,
        forecast_cov: torch.Tensor,
        obs_cov: torch.Tensor,
        obs_matrix: torch.Tensor,
    ) -> torch.Tensor:
        #
        assert forecast_cov.ndim == obs_cov.ndim == obs_matrix.ndim == 2

        _cov = obs_matrix.mm(forecast_cov)
        _cov = _cov.mm(obs_matrix.t())

        _inv = torch.linalg.inv(_cov + obs_cov)

        kalman_gain = _inv.mm(obs_matrix).mm(forecast_cov)

        return kalman_gain
