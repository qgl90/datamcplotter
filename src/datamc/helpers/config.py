from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Mapping

import yaml


@dataclass(frozen=True)
class VariableSpec:
    name: str
    xlabel: str
    bins: int
    xrange: tuple[float, float]


def _expand_path(path: str, base_dir: str) -> str:
    path = os.path.expandvars(os.path.expanduser(path))
    if not os.path.isabs(path):
        path = os.path.join(base_dir, path)
    return os.path.abspath(path)


_ROOT_TREE_HINT = re.compile(r"(?i)\.root:")


def _split_root_path_and_tree(spec: str) -> tuple[str, str | None]:
    """
    Accept either:
      - "/path/to/file.root"
      - "/path/to/file.root:TreeName"

    We only split when the string contains ".root:" (case-insensitive) to avoid
    mis-parsing e.g. URLs/ports or Windows drive letters.
    """
    if not _ROOT_TREE_HINT.search(spec):
        return spec, None

    left, right = spec.rsplit(":", 1)
    tree = right.strip()
    if not tree:
        raise ValueError(f"Invalid ROOT spec (empty tree name): {spec!r}")
    return left, tree


def _parse_xrange(xrange_value: Any) -> tuple[float, float]:
    if isinstance(xrange_value, (list, tuple)) and len(xrange_value) == 2:
        return float(xrange_value[0]), float(xrange_value[1])
    if isinstance(xrange_value, str):
        parts = [p.strip() for p in xrange_value.split(",")]
        if len(parts) == 2:
            return float(parts[0]), float(parts[1])
    raise ValueError(f"Invalid xrange: {xrange_value!r} (expected [min, max] or 'min, max')")


def _require(cfg: Mapping[str, Any], key: str) -> Any:
    if key not in cfg:
        raise KeyError(f"Missing required config key: {key!r}")
    return cfg[key]


@dataclass(frozen=True)
class AppConfig:
    yaml_path: str
    base_dir: str

    data_path: str
    data_tree: str | None

    sweight_path: str
    sweight_tree: str | None
    sweight_var: str

    label_data: str

    mc_spec: Any
    mc_tree: str | None
    mc_label: str
    mc_weight: str | None

    tagplot: str
    outdir: str
    formats: tuple[str, ...]

    variables: tuple[VariableSpec, ...]


def load_config(yaml_path: str) -> AppConfig:
    yaml_path = os.path.abspath(yaml_path)
    base_dir = os.path.dirname(yaml_path)

    with open(yaml_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    data_spec = str(_require(raw, "data"))
    data_path_raw, data_tree_inline = _split_root_path_and_tree(data_spec)
    data_path = _expand_path(data_path_raw, base_dir)

    sweight_spec = str(_require(raw, "data_sweight"))
    sweight_path_raw, sweight_tree_inline = _split_root_path_and_tree(sweight_spec)
    sweight_path = _expand_path(sweight_path_raw, base_dir)

    data_tree_cfg = raw.get("data_tree")
    if data_tree_inline and data_tree_cfg:
        raise ValueError("Specify the data tree either via 'data: file.root:Tree' or 'data_tree', not both.")
    data_tree = str(data_tree_inline) if data_tree_inline else (str(data_tree_cfg) if data_tree_cfg else None)

    sweight_tree_cfg = raw.get("sweight_tree")
    if sweight_tree_inline and sweight_tree_cfg:
        raise ValueError(
            "Specify the sWeight tree either via 'data_sweight: file.root:Tree' or 'sweight_tree', not both."
        )
    sweight_tree = (
        str(sweight_tree_inline) if sweight_tree_inline else (str(sweight_tree_cfg) if sweight_tree_cfg else None)
    )

    variables_raw = _require(raw, "variables")
    if not isinstance(variables_raw, Mapping) or not variables_raw:
        raise ValueError("'variables' must be a non-empty mapping")

    variables: list[VariableSpec] = []
    for var_name, spec in variables_raw.items():
        if not isinstance(spec, Mapping):
            raise ValueError(f"Variable {var_name!r} must be a mapping")
        xlabel = str(_require(spec, "xlabel"))
        bins = int(_require(spec, "bins"))
        xrange_tuple = _parse_xrange(_require(spec, "xrange"))
        variables.append(VariableSpec(name=str(var_name), xlabel=xlabel, bins=bins, xrange=xrange_tuple))

    outdir = raw.get("outdir", "plots")
    outdir = _expand_path(str(outdir), base_dir)

    formats_raw = raw.get("formats", ["png"])
    if isinstance(formats_raw, str):
        formats = (formats_raw,)
    else:
        formats = tuple(str(x) for x in formats_raw)
    if not formats:
        raise ValueError("'formats' must contain at least one format (e.g. ['png', 'pdf'])")

    mc_weight = raw.get("mc_weight")
    if mc_weight is not None:
        mc_weight = str(mc_weight)

    return AppConfig(
        yaml_path=yaml_path,
        base_dir=base_dir,
        data_path=data_path,
        data_tree=data_tree,
        sweight_path=sweight_path,
        sweight_tree=sweight_tree,
        sweight_var=str(_require(raw, "sweight_var")),
        label_data=str(_require(raw, "label_data")),
        mc_spec=_require(raw, "mc"),
        mc_tree=raw.get("mc_tree"),
        mc_label=str(_require(raw, "mc_label")),
        mc_weight=mc_weight,
        tagplot=str(_require(raw, "tagplot")),
        outdir=outdir,
        formats=formats,
        variables=tuple(variables),
    )
