from __future__ import annotations

import numpy as np


def weighted_histogram(values: np.ndarray, *, weights: np.ndarray | None, bins: int, xrange: tuple[float, float]):
    if weights is None:
        weights = np.ones_like(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    values = np.asarray(values, dtype=float)

    counts, edges = np.histogram(values, bins=bins, range=xrange, weights=weights)
    sumw2, _ = np.histogram(values, bins=bins, range=xrange, weights=weights * weights)
    errors = np.sqrt(sumw2)
    centers = 0.5 * (edges[:-1] + edges[1:])
    return edges, centers, counts, errors


def weighted_histogram2d(
    x: np.ndarray,
    y: np.ndarray,
    *,
    weights: np.ndarray | None,
    xbins: int,
    ybins: int,
    xrange: tuple[float, float],
    yrange: tuple[float, float],
):
    if weights is None:
        weights = np.ones_like(x, dtype=float)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    weights = np.asarray(weights, dtype=float)

    counts, xedges, yedges = np.histogram2d(x, y, bins=[xbins, ybins], range=[xrange, yrange], weights=weights)
    sumw2, _, _ = np.histogram2d(
        x, y, bins=[xbins, ybins], range=[xrange, yrange], weights=weights * weights
    )
    errors = np.sqrt(sumw2)
    return xedges, yedges, counts, errors


def pull_distribution(data_counts: np.ndarray, data_err: np.ndarray, mc_counts: np.ndarray, mc_err: np.ndarray) -> np.ndarray:
    denom = np.sqrt(np.square(data_err) + np.square(mc_err))
    pull = np.zeros_like(data_counts, dtype=float)
    mask = denom > 0
    pull[mask] = (data_counts[mask] - mc_counts[mask]) / denom[mask]
    return pull
