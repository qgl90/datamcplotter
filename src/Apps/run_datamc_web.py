#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Allow running without installing the package
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from datamc import (  # noqa: E402
    build_2d_comparison_figure,
    build_comparison_figure,
    data_to_parquet,
    load_config,
    mc_to_parquet,
    resolve_mc_files,
    resolve_tree_name_root,
)


@st.cache_data(show_spinner=False)
def _read_parquet(path: str) -> pd.DataFrame:
    return pd.read_parquet(path)


def _ensure_parquet(cfg, *, force: bool) -> tuple[str, str]:
    parquet_dir = os.path.join(cfg.outdir, "parquet")
    data_parquet = os.path.join(parquet_dir, "data.parquet")
    mc_parquet = os.path.join(parquet_dir, "mc.parquet")

    need = force or (not os.path.exists(data_parquet)) or (not os.path.exists(mc_parquet))
    if not need:
        return data_parquet, mc_parquet

    var_names = {v.name for v in cfg.variables}
    for v2 in cfg.variables_2d:
        var_names.add(v2.xvar)
        var_names.add(v2.yvar)
    var_names = sorted(var_names)

    data_tree = resolve_tree_name_root(cfg.data_path, cfg.data_tree)
    sweight_tree = resolve_tree_name_root(cfg.sweight_path, cfg.sweight_tree)

    mc_files = resolve_mc_files(cfg.mc_spec, base_dir=cfg.base_dir, data_path=cfg.data_path)
    mc_tree = resolve_tree_name_root(mc_files[0], cfg.mc_tree)

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

    _read_parquet.clear()
    return data_parquet, mc_parquet


def main():
    st.set_page_config(page_title="datamc plotter", layout="wide")
    st.title("datamcplotter")

    with st.sidebar:
        st.header("Config")
        yaml_path = st.text_input("YAML path", value="configs.yaml")
        force_rebuild = st.checkbox("Rebuild parquet caches", value=False)
        st.divider()
        st.caption("Tip: use inline tree names like `file.root:DecayTree` in the YAML.")

    try:
        cfg = load_config(yaml_path)
    except Exception as e:
        st.error(f"Could not load YAML: {e}")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Data**")
        st.code(cfg.data_path, language=None)
        st.write("**sWeights**")
        st.code(cfg.sweight_path, language=None)
    with col2:
        st.write("**MC**")
        st.code(str(cfg.mc_spec), language=None)
        st.write("**Output dir**")
        st.code(cfg.outdir, language=None)

    try:
        data_parquet, mc_parquet = _ensure_parquet(cfg, force=force_rebuild)
    except Exception as e:
        st.error(f"Could not build parquet caches: {e}")
        st.stop()

    st.success(f"Parquet ready: {data_parquet} and {mc_parquet}")

    try:
        data_df = _read_parquet(data_parquet)
        mc_df = _read_parquet(mc_parquet)
    except Exception as e:
        st.error(f"Could not read parquet: {e}")
        st.stop()

    var_names = [v.name for v in cfg.variables]
    var_map = {v.name: v for v in cfg.variables}
    var2_names = [v.name for v in cfg.variables_2d]
    var2_map = {v.name: v for v in cfg.variables_2d}

    with st.sidebar:
        st.header("Plot")
        mode = st.selectbox("Mode", options=["1D", "2D"])
        if mode == "1D":
            var_name = st.selectbox("Variable", options=var_names)
            default = var_map[var_name]
            bins = int(st.number_input("Bins", min_value=1, value=int(default.bins), step=1))
            xmin = float(st.number_input("X min", value=float(default.xrange[0])))
            xmax = float(st.number_input("X max", value=float(default.xrange[1])))
            xlabel = st.text_input("X label", value=str(default.xlabel))
            if default.option:
                st.caption(f"Option: `{default.option}`")
            ylabel = None
            ybins = None
            ymin = None
            ymax = None
            zscale = "linear"
        else:
            if not var2_names:
                st.warning("No `variables_2d` configured in YAML.")
                st.stop()
            var2_name = st.selectbox("2D plot", options=var2_names)
            default2 = var2_map[var2_name]
            xlabel = st.text_input("X label", value=str(default2.xlabel))
            ylabel = st.text_input("Y label", value=str(default2.ylabel))
            bins = int(st.number_input("X bins", min_value=1, value=int(default2.xbins), step=1))
            ybins = int(st.number_input("Y bins", min_value=1, value=int(default2.ybins), step=1))
            xmin = float(st.number_input("X min", value=float(default2.xrange[0])))
            xmax = float(st.number_input("X max", value=float(default2.xrange[1])))
            ymin = float(st.number_input("Y min", value=float(default2.yrange[0])))
            ymax = float(st.number_input("Y max", value=float(default2.yrange[1])))
            zscale = st.selectbox("Z scale", options=["linear", "log"], index=0 if default2.zscale == "linear" else 1)
        title = st.text_input("Title", value=str(cfg.tagplot))
        data_label = st.text_input("Data label", value=f"data sweighted {cfg.label_data}")
        mc_label = st.text_input("MC label", value=f"mc {cfg.mc_label}")
        st.divider()
        save = st.button("Save plot")
        formats = st.multiselect("Save formats", options=["png", "pdf"], default=["png"])

    if "__sweight" not in data_df.columns:
        st.error("Column '__sweight' not found in data parquet (did parquet build succeed?).")
        st.stop()
    if "__mc_weight" not in mc_df.columns:
        st.error("Column '__mc_weight' not found in MC parquet (did parquet build succeed?).")
        st.stop()

    if mode == "1D":
        if var_name not in data_df.columns:
            st.error(f"Variable {var_name!r} not found in data parquet.")
            st.stop()
        if var_name not in mc_df.columns:
            st.error(f"Variable {var_name!r} not found in MC parquet.")
            st.stop()

        data_values = data_df[var_name].to_numpy()
        data_weights = data_df["__sweight"].to_numpy()
        mc_values = mc_df[var_name].to_numpy()
        mc_weights = mc_df["__mc_weight"].to_numpy()

        fig = build_comparison_figure(
            title=title,
            xlabel=xlabel,
            data_values=data_values,
            data_weights=data_weights,
            data_label=data_label,
            mc_values=mc_values,
            mc_weights=mc_weights,
            mc_label=mc_label,
            bins=bins,
            xrange=(xmin, xmax),
            option=default.option,
        )
        default_outname = var_name
    else:
        spec2 = var2_map[var2_name]
        for col in [spec2.xvar, spec2.yvar]:
            if col not in data_df.columns:
                st.error(f"Variable {col!r} not found in data parquet.")
                st.stop()
            if col not in mc_df.columns:
                st.error(f"Variable {col!r} not found in MC parquet.")
                st.stop()

        fig = build_2d_comparison_figure(
            title=title,
            xlabel=xlabel,
            ylabel=ylabel or spec2.ylabel,
            data_x=data_df[spec2.xvar].to_numpy(),
            data_y=data_df[spec2.yvar].to_numpy(),
            data_weights=data_df["__sweight"].to_numpy(),
            mc_x=mc_df[spec2.xvar].to_numpy(),
            mc_y=mc_df[spec2.yvar].to_numpy(),
            mc_weights=mc_df["__mc_weight"].to_numpy(),
            xbins=bins,
            ybins=int(ybins or spec2.ybins),
            xrange=(xmin, xmax),
            yrange=(float(ymin), float(ymax)),
            zscale=zscale,
        )
        default_outname = spec2.name

    if save:
        if not formats:
            st.warning("Pick at least one format to save.")
        else:
            outpath_noext = os.path.join(cfg.outdir, default_outname)
            os.makedirs(cfg.outdir, exist_ok=True)
            for ext in formats:
                fig.savefig(f"{outpath_noext}.{ext}", dpi=150, bbox_inches="tight")
            st.success(f"Saved: {outpath_noext}.[{', '.join(formats)}]")

    st.pyplot(fig, clear_figure=False, use_container_width=True)
    plt.close(fig)


if __name__ == "__main__":
    main()
