import textwrap

from datamc.config import load_config


def test_inline_tree_names_are_parsed(tmp_path):
    yml = tmp_path / "cfg.yaml"
    yml.write_text(
        textwrap.dedent(
            """
            data: "data.root:DecayTree"
            data_sweight: "sw.root:sweightTree"
            sweight_var: "sw"
            label_data: "lbl"
            mc: "mc.root"
            mc_label: "mclbl"
            tagplot: "tag"
            variables:
              B_PT:
                xlabel: "pt"
                bins: 10
                xrange: [0, 1]
                option: "frac_entries"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    cfg = load_config(str(yml))
    assert cfg.data_path.endswith("data.root")
    assert cfg.data_tree == "DecayTree"
    assert cfg.sweight_path.endswith("sw.root")
    assert cfg.sweight_tree == "sweightTree"
    assert cfg.variables[0].option == "frac_entries"


def test_variables_2d_parsed(tmp_path):
    yml = tmp_path / "cfg.yaml"
    yml.write_text(
        textwrap.dedent(
            """
            data: "data.root:DecayTree"
            data_sweight: "sw.root:sweightTree"
            sweight_var: "sw"
            label_data: "lbl"
            mc: "mc.root"
            mc_label: "mclbl"
            tagplot: "tag"
            variables:
              X:
                xlabel: "x"
                bins: 10
                xrange: [0, 1]
            variables_2d:
              X_vs_Y:
                xvar: "X"
                yvar: "Y"
                xlabel: "x"
                ylabel: "y"
                xbins: 5
                ybins: 6
                xrange: [0, 1]
                yrange: [0, 2]
                zscale: "log"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    cfg = load_config(str(yml))
    assert len(cfg.variables_2d) == 1
    v2 = cfg.variables_2d[0]
    assert v2.name == "X_vs_Y"
    assert v2.xvar == "X"
    assert v2.yvar == "Y"
    assert v2.zscale == "log"
