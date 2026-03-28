from __future__ import annotations

import os

import matplotlib
import mplhep as hep 
hep.style.use("LHCb2")
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .hist import pull_distribution, weighted_histogram


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
    edges, centers, data_counts, data_err = weighted_histogram(
        data_values, weights=data_weights, bins=bins, xrange=xrange
    )
    _, _, mc_counts, mc_err = weighted_histogram(mc_values, weights=mc_weights, bins=bins, xrange=xrange)

    pulls = pull_distribution(data_counts, data_err, mc_counts, mc_err)

    fig = plt.figure(figsize=(7.2, 6.4))
    gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[3.5, 1.2], hspace=0.05)
    ax = fig.add_subplot(gs[0])
    ax_pull = fig.add_subplot(gs[1], sharex=ax)

    ax.set_title(title)

    bin_left = edges[:-1]
    bin_right = edges[1:]
    ax.step(edges, np.r_[mc_counts, mc_counts[-1]], where="post", color="C1", linewidth=1.6, label=mc_label)
    ax.fill_between(
        np.r_[bin_left, bin_right[-1]],
        np.r_[mc_counts - mc_err, (mc_counts - mc_err)[-1]],
        np.r_[mc_counts + mc_err, (mc_counts + mc_err)[-1]],
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
    for ext in formats:
        outpath = f"{outpath_noext}.{ext}"
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        fig.savefig(outpath, dpi=150, bbox_inches="tight")

    plt.close(fig)
