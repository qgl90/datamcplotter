from __future__ import annotations

import os
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors

from .hist import pull_distribution, scale_factor_match_yield, weighted_histogram, weighted_histogram2d

try:  # optional, for HEP styling
    import mplhep as hep  # type: ignore
except Exception:  # pragma: no cover
    hep = None
else:
    try:
        hep.style.use("LHCb2")
    except Exception:
        pass


def build_comparison_figure(
    *,
    title: str,
    xlabel: str,
    data_values: np.ndarray,
    data_weights: np.ndarray | None,
    data_label: str,
    mc_values: np.ndarray,
    mc_weights: np.ndarray | None,
    mc_label: str,
    bins: int,
    xrange: tuple[float, float],
    figsize: tuple[float, float] = (7.2, 6.4),
) -> Any:
    edges, centers, data_counts, data_err = weighted_histogram(
        data_values, weights=data_weights, bins=bins, xrange=xrange
    )
    _, _, mc_counts, mc_err = weighted_histogram(mc_values, weights=mc_weights, bins=bins, xrange=xrange)

    mc_scale = scale_factor_match_yield(data_counts, mc_counts)
    mc_counts_plot = mc_scale * mc_counts
    mc_err_plot = mc_scale * mc_err

    pulls = pull_distribution(data_counts, data_err, mc_counts, mc_err, mc_scale=mc_scale)

    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[3.5, 1.2], hspace=0.05)
    ax = fig.add_subplot(gs[0])
    ax_pull = fig.add_subplot(gs[1], sharex=ax)

    ax.set_title(title)

    bin_left = edges[:-1]
    bin_right = edges[1:]
    ax.step(
        edges,
        np.r_[mc_counts_plot, mc_counts_plot[-1]],
        where="post",
        color="C1",
        linewidth=1.6,
        label=mc_label,
    )
    ax.fill_between(
        np.r_[bin_left, bin_right[-1]],
        np.r_[mc_counts_plot - mc_err_plot, (mc_counts_plot - mc_err_plot)[-1]],
        np.r_[mc_counts_plot + mc_err_plot, (mc_counts_plot + mc_err_plot)[-1]],
        step="post",
        color="C1",
        alpha=0.25,
        linewidth=0,
    )
    ax.errorbar(
        centers,
        data_counts,
        yerr=data_err,
        fmt="o",
        color="black",
        markersize=4,
        capsize=0,
        label=data_label,
    )

    ax.set_ylabel("Entries")
    ax.legend(frameon=False)
    ax.tick_params(axis="x", labelbottom=False)

    ax_pull.axhline(0.0, color="0.2", linewidth=1.0)
    colors = []
    for p in pulls:
        ap = abs(float(p))
        if ap >= 5.0:
            colors.append("tab:red")
        elif ap >= 3.0:
            colors.append("tab:orange")
        else:
            colors.append("0.75")

    widths = np.diff(edges)
    ax_pull.bar(
        centers,
        pulls,
        width=widths,
        align="center",
        color=colors,
        edgecolor="0.3",
        linewidth=0.6,
    )
    ax_pull.axhline(3.0, color="tab:orange", linestyle="--", linewidth=1.0)
    ax_pull.axhline(-3.0, color="tab:orange", linestyle="--", linewidth=1.0)
    ax_pull.axhline(5.0, color="tab:red", linestyle="--", linewidth=1.0)
    ax_pull.axhline(-5.0, color="tab:red", linestyle="--", linewidth=1.0)
    ax_pull.set_ylim(-5, 5)
    ax_pull.set_ylabel("Pull")
    ax_pull.set_xlabel(xlabel)

    return fig


def make_comparison_plot(
    *,
    outpath_noext: str,
    formats: tuple[str, ...],
    title: str,
    xlabel: str,
    data_values: np.ndarray,
    data_weights: np.ndarray | None,
    data_label: str,
    mc_values: np.ndarray,
    mc_weights: np.ndarray | None,
    mc_label: str,
    bins: int,
    xrange: tuple[float, float],
):
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
        xrange=xrange,
    )

    for ext in formats:
        outpath = f"{outpath_noext}.{ext}"
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        fig.savefig(outpath, dpi=150, bbox_inches="tight")

    plt.close(fig)


def build_2d_comparison_figure(
    *,
    title: str,
    xlabel: str,
    ylabel: str,
    data_x: np.ndarray,
    data_y: np.ndarray,
    data_weights: np.ndarray | None,
    mc_x: np.ndarray,
    mc_y: np.ndarray,
    mc_weights: np.ndarray | None,
    xbins: int,
    ybins: int,
    xrange: tuple[float, float],
    yrange: tuple[float, float],
    zscale: str = "linear",
    pull_range: tuple[float, float] = (-5.0, 5.0),
    figsize: tuple[float, float] = (13.0, 4.6),
) -> Any:
    xedges, yedges, d_counts, d_err = weighted_histogram2d(
        data_x,
        data_y,
        weights=data_weights,
        xbins=xbins,
        ybins=ybins,
        xrange=xrange,
        yrange=yrange,
    )
    _, _, m_counts, m_err = weighted_histogram2d(
        mc_x,
        mc_y,
        weights=mc_weights,
        xbins=xbins,
        ybins=ybins,
        xrange=xrange,
        yrange=yrange,
    )

    mc_scale = scale_factor_match_yield(d_counts, m_counts)
    m_counts_plot = mc_scale * m_counts
    m_err_plot = mc_scale * m_err

    denom = np.sqrt(np.square(d_err) + np.square(m_err_plot))
    pull = np.zeros_like(d_counts, dtype=float)
    mask = denom > 0
    pull[mask] = (d_counts[mask] - m_counts_plot[mask]) / denom[mask]

    fig, (ax_d, ax_m, ax_p) = plt.subplots(1, 3, figsize=figsize, constrained_layout=True, sharex=True, sharey=True)
    fig.suptitle(title)

    if zscale == "log":
        d_show = np.where(d_counts > 0, d_counts, np.nan)
        m_show = np.where(m_counts_plot > 0, m_counts_plot, np.nan)
        positive = np.concatenate([d_counts[d_counts > 0], m_counts_plot[m_counts_plot > 0]])
        vmin = float(np.min(positive)) if positive.size else 1e-3
        vmax = float(np.nanmax([np.nanmax(d_show), np.nanmax(m_show), 1e-12]))
        norm = colors.LogNorm(vmin=max(vmin, 1e-12), vmax=vmax)
    else:
        d_show = d_counts
        m_show = m_counts_plot
        norm = colors.Normalize(vmin=0.0, vmax=float(max(np.max(d_counts), np.max(m_counts_plot), 0.0)))

    im_d = ax_d.pcolormesh(xedges, yedges, d_show.T, shading="auto", norm=norm)
    ax_d.set_title("Data")
    ax_d.set_xlabel(xlabel)
    ax_d.set_ylabel(ylabel)
    fig.colorbar(im_d, ax=ax_d, fraction=0.046, pad=0.04)

    im_m = ax_m.pcolormesh(xedges, yedges, m_show.T, shading="auto", norm=norm)
    ax_m.set_title("MC")
    ax_m.set_xlabel(xlabel)
    fig.colorbar(im_m, ax=ax_m, fraction=0.046, pad=0.04)

    pr0, pr1 = pull_range
    im_p = ax_p.pcolormesh(
        xedges,
        yedges,
        np.clip(pull.T, pr0, pr1),
        shading="auto",
        cmap="RdBu_r",
        vmin=pr0,
        vmax=pr1,
    )
    ax_p.set_title("Pull")
    ax_p.set_xlabel(xlabel)
    fig.colorbar(im_p, ax=ax_p, fraction=0.046, pad=0.04)

    return fig


def make_2d_comparison_plot(
    *,
    outpath_noext: str,
    formats: tuple[str, ...],
    title: str,
    xlabel: str,
    ylabel: str,
    data_x: np.ndarray,
    data_y: np.ndarray,
    data_weights: np.ndarray | None,
    mc_x: np.ndarray,
    mc_y: np.ndarray,
    mc_weights: np.ndarray | None,
    xbins: int,
    ybins: int,
    xrange: tuple[float, float],
    yrange: tuple[float, float],
    zscale: str = "linear",
):
    fig = build_2d_comparison_figure(
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        data_x=data_x,
        data_y=data_y,
        data_weights=data_weights,
        mc_x=mc_x,
        mc_y=mc_y,
        mc_weights=mc_weights,
        xbins=xbins,
        ybins=ybins,
        xrange=xrange,
        yrange=yrange,
        zscale=zscale,
    )

    for ext in formats:
        outpath = f"{outpath_noext}.{ext}"
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        fig.savefig(outpath, dpi=150, bbox_inches="tight")

    plt.close(fig)
