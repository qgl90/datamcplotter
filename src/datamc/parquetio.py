from __future__ import annotations

import os
from typing import Iterable

import numpy as np
import pandas as pd


def _import_root():
    try:
        import ROOT  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "PyROOT is required but could not be imported. Install ROOT with Python bindings (PyROOT)."
        ) from e
    return ROOT


def resolve_tree_name_root(root_path: str, preferred: str | None) -> str:
    ROOT = _import_root()
    f = ROOT.TFile.Open(root_path)
    if not f or f.IsZombie():
        raise FileNotFoundError(f"Could not open ROOT file: {root_path}")

    try:
        if preferred:
            obj = f.Get(preferred)
            if obj and obj.InheritsFrom("TTree"):
                return preferred
            raise KeyError(f"TTree {preferred!r} not found in {root_path}")

        keys = f.GetListOfKeys()
        for i in range(keys.GetEntries()):
            key = keys.At(i)
            name = key.GetName()
            obj = f.Get(name)
            if obj and obj.InheritsFrom("TTree"):
                return str(name)
    finally:
        f.Close()

    raise RuntimeError(f"No TTree found in {root_path}")


def data_to_parquet(
    *,
    data_path: str,
    data_tree: str,
    sweight_path: str,
    sweight_tree: str,
    sweight_var: str,
    variables: Iterable[str],
    out_parquet: str,
    friend_alias: str = "sw",
):
    ROOT = _import_root()

    os.makedirs(os.path.dirname(out_parquet), exist_ok=True)

    f_data = ROOT.TFile.Open(data_path)
    if not f_data or f_data.IsZombie():
        raise FileNotFoundError(f"Could not open data ROOT file: {data_path}")

    f_sw = ROOT.TFile.Open(sweight_path)
    if not f_sw or f_sw.IsZombie():
        raise FileNotFoundError(f"Could not open sWeight ROOT file: {sweight_path}")

    try:
        # Keep both files alive for the lifetime of the dataframe evaluation.
        t_data = f_data.Get(data_tree)
        t_sw = f_sw.Get(sweight_tree)
        if not t_data or not t_data.InheritsFrom("TTree"):
            raise KeyError(f"Data tree {data_tree!r} not found in {data_path}")
        if not t_sw or not t_sw.InheritsFrom("TTree"):
            raise KeyError(f"sWeight tree {sweight_tree!r} not found in {sweight_path}")

        if int(t_data.GetEntries()) != int(t_sw.GetEntries()):
            raise RuntimeError(
                f"Data/sWeight entry mismatch: {int(t_data.GetEntries())} vs {int(t_sw.GetEntries())}. "
                "Friend trees must be aligned entry-by-entry."
            )

        t_data.AddFriend(t_sw, friend_alias)

        rdf = ROOT.RDataFrame(t_data)
        sw_expr = f"{friend_alias}.{sweight_var}"
        rdf = rdf.Define("__sweight", sw_expr)

        cols = [str(v) for v in variables] + ["__sweight"]
        arrays = rdf.AsNumpy(cols)

        df = pd.DataFrame({k: np.asarray(v) for k, v in arrays.items()})
        df.to_parquet(out_parquet, index=False)
    finally:
        f_sw.Close()
        f_data.Close()


def mc_to_parquet(
    *,
    mc_files: list[str],
    mc_tree: str,
    variables: Iterable[str],
    mc_weight_var: str | None,
    out_parquet: str,
):
    ROOT = _import_root()

    if not mc_files:
        raise ValueError("No MC files provided")
    os.makedirs(os.path.dirname(out_parquet), exist_ok=True)

    chain = ROOT.TChain(mc_tree)
    for path in mc_files:
        chain.Add(path)
    if int(chain.GetEntries()) <= 0:
        raise RuntimeError(f"MC chain has 0 entries for tree {mc_tree!r}")

    rdf = ROOT.RDataFrame(chain)
    if mc_weight_var:
        rdf = rdf.Define("__mc_weight", mc_weight_var)
    else:
        rdf = rdf.Define("__mc_weight", "1.0")

    cols = [str(v) for v in variables] + ["__mc_weight"]
    arrays = rdf.AsNumpy(cols)
    df = pd.DataFrame({k: np.asarray(v) for k, v in arrays.items()})
    df.to_parquet(out_parquet, index=False)

