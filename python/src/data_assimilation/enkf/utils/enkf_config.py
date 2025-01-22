import dataclasses
import inspect
import json
import os

import torch
import yaml


@dataclasses.dataclass()
class EnKFPOConfig:
    n_ensemble: int  # ensemble num
    inflation_coefficient: float  # inflation coefficient
    obs_std: float  # standard deviation of observation noise
    obs_matrix: list  # observation matrix
    device: str  # cpu, cuda, cuda:0, cuda:1 etc.
    precision: str  # single or double

    def __post_init__(self):
        dic = dataclasses.asdict(self)

        assert self.n_ensemble >= 1
        assert self.inflation_coefficient > 0.0
        assert self.obs_std > 0.0
        assert len(self.obs_matrix) == 3
        assert self.precision in ["single", "double"]
        assert self.device == "cpu" or self.device.startswith("cuda")

    def to_json_str(self, indent: int = 2) -> str:
        return json.dumps(dataclasses.asdict(self), indent=indent)

    def save(self, config_path: str):
        # Ref: https://qiita.com/kzmssk/items/483f25f47e0ed10aa948
        #

        def convert_dict(data):
            for key, val in data.items():
                if isinstance(val, dict):
                    data[key] = convert_dict(val)
            return data

        with open(config_path, "w") as f:
            yaml.safe_dump(convert_dict(dataclasses.asdict(self)), f)

    @classmethod
    def load(cls, config_path: str):
        # Ref: https://qiita.com/kzmssk/items/483f25f47e0ed10aa948
        #
        assert os.path.exists(config_path), f"YAML config {config_path} does not exist"

        def convert_from_dict(parent_cls, data):
            for key, val in data.items():
                child_class = parent_cls.__dataclass_fields__[key].type
                if inspect.isclass(child_class) and issubclass(child_class, Config):
                    data[key] = child_class(**convert_from_dict(child_class, val))
            return data

        with open(config_path) as f:
            config_data = yaml.safe_load(f)
            # recursively convert config item to Config
            config_data = convert_from_dict(cls, config_data)
            return cls(**config_data)
