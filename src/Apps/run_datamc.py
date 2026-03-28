#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

# Allow running without installing the package
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from datamc import (  # noqa: E402
    load_config,
    data_to_parquet,
    make_comparison_plot,
    mc_to_parquet,
    resolve_mc_files,
    resolve_tree_name_root,
)

def main() -> int:
    parser = argparse.ArgumentParser(description="Compare data (sWeighted) vs MC for configured variables.")
    parser.add_argument("--yaml", required=True, help="Path to YAML config, e.g. configs.yaml")
    args = parser.parse_args()

    cfg = load_config(args.yaml)

    data_tree = resolve_tree_name_root(cfg.data_path, cfg.data_tree)
    sweight_tree = resolve_tree_name_root(cfg.sweight_path, cfg.sweight_tree)

    mc_files = resolve_mc_files(cfg.mc_spec, base_dir=cfg.base_dir, data_path=cfg.data_path)
    mc_tree = resolve_tree_name_root(mc_files[0], cfg.mc_tree)

    os.makedirs(cfg.outdir, exist_ok=True)

    parquet_dir = os.path.join(cfg.outdir, "parquet")
    data_parquet = os.path.join(parquet_dir, "data.parquet")
    mc_parquet = os.path.join(parquet_dir, "mc.parquet")

    var_names = [v.name for v in cfg.variables]

    data_to_parquet(
        data_path=cfg.data_path,
        data_tree=data_tree,
        sweight_path=cfg.sweight_path,
        sweight_tree=sweight_tree,
        sweight_var=cfg.sweight_var,
        variables=var_names,
        out_parquet=data_parquet,
    )
    mc_to_parquet(
        mc_files=mc_files,
        mc_tree=mc_tree,
        variables=var_names,
        mc_weight_var=cfg.mc_weight,
        out_parquet=mc_parquet,
    )

    data_df = pd.read_parquet(data_parquet)
    mc_df = pd.read_parquet(mc_parquet)

    for var in cfg.variables:
        if var.name not in data_df.columns:
            raise KeyError(f"Variable {var.name!r} not found in data parquet: {data_parquet}")
        if var.name not in mc_df.columns:
            raise KeyError(f"Variable {var.name!r} not found in MC parquet: {mc_parquet}")

        data_values = data_df[var.name].to_numpy()
        data_weights = data_df["__sweight"].to_numpy()

        mc_values = mc_df[var.name].to_numpy()
        mc_weights = mc_df["__mc_weight"].to_numpy()

        outpath_noext = os.path.join(cfg.outdir, var.name)
        make_comparison_plot(
            outpath_noext=outpath_noext,
            formats=cfg.formats,
            title=cfg.tagplot,
            xlabel=var.xlabel,
            data_values=data_values,
            data_weights=data_weights,
            data_label=f"data sweighted {cfg.label_data}",
            mc_values=mc_values,
            mc_weights=mc_weights,
            mc_label=f"mc {cfg.mc_label}",
            bins=var.bins,
            xrange=var.xrange,
        )

        print(f"Wrote {outpath_noext}.[{', '.join(cfg.formats)}]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
