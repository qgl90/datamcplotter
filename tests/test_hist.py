import numpy as np

from datamc.hist import pull_distribution, weighted_histogram2d


def test_pull_distribution_basic():
    d = np.array([10.0, 8.0])
    m = np.array([7.0, 8.0])
    derr = np.array([1.0, 2.0])
    merr = np.array([2.0, 2.0])
    p = pull_distribution(d, derr, m, merr)
    assert p.shape == (2,)
    assert np.isclose(p[0], (10.0 - 7.0) / np.sqrt(1.0**2 + 2.0**2))
    assert np.isclose(p[1], 0.0)

    p2 = pull_distribution(d, derr, m, merr, mc_scale=2.0)
    assert np.isclose(p2[0], (10.0 - 2.0 * 7.0) / np.sqrt(1.0**2 + (2.0 * 2.0) ** 2))


def test_weighted_histogram2d_shapes():
    x = np.array([0.1, 0.2, 0.8])
    y = np.array([0.1, 0.9, 0.8])
    w = np.array([1.0, 2.0, 3.0])
    xedges, yedges, counts, errs = weighted_histogram2d(
        x, y, weights=w, xbins=2, ybins=2, xrange=(0.0, 1.0), yrange=(0.0, 1.0)
    )
    assert xedges.shape == (3,)
    assert yedges.shape == (3,)
    assert counts.shape == (2, 2)
    assert errs.shape == (2, 2)
