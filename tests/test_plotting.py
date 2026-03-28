import numpy as np

from datamc.plotting import build_2d_comparison_figure, build_comparison_figure


def test_build_comparison_figure_smoke():
    x = np.linspace(0, 1, 100)
    w = np.ones_like(x)
    fig = build_comparison_figure(
        title="t",
        xlabel="x",
        data_values=x,
        data_weights=w,
        data_label="d",
        mc_values=x,
        mc_weights=w,
        mc_label="m",
        bins=10,
        xrange=(0.0, 1.0),
    )
    assert fig is not None


def test_build_2d_comparison_figure_smoke():
    x = np.linspace(0, 1, 200)
    y = np.linspace(0, 1, 200)
    w = np.ones_like(x)
    fig = build_2d_comparison_figure(
        title="t",
        xlabel="x",
        ylabel="y",
        data_x=x,
        data_y=y,
        data_weights=w,
        mc_x=x,
        mc_y=y,
        mc_weights=w,
        xbins=10,
        ybins=10,
        xrange=(0.0, 1.0),
        yrange=(0.0, 1.0),
        zscale="linear",
    )
    assert fig is not None
