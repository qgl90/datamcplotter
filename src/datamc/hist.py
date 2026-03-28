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


def pull_distribution(data_counts: np.ndarray, data_err: np.ndarray, mc_counts: np.ndarray, mc_err: np.ndarray) -> np.ndarray:
    denom = np.sqrt(np.square(data_err) + np.square(mc_err))
    pull = np.zeros_like(data_counts, dtype=float)
    mask = denom > 0
    pull[mask] = (data_counts[mask] - mc_counts[mask]) / denom[mask]
    return pull

