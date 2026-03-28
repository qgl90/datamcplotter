# datamc

Small helper app to compare sWeighted data vs MC from ROOT files, producing per-variable comparison plots with a pull panel.

## Layout

- `src/datamc/`: helpers (YAML config, ROOT IO, histogramming, plotting)
- `src/Apps/runners/run_datamc.py`: batch executable
- `src/Apps/runners/run_datamc_web.py`: interactive web UI
- `configs.yaml`: example config

## Setup

Requires a local ROOT installation with PyROOT enabled (i.e. `import ROOT` works).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Run

```bash
python3 src/Apps/runners/run_datamc.py --yaml configs.yaml
```

Outputs:

- Parquet caches: `plots/parquet/data.parquet`, `plots/parquet/mc.parquet` (path controlled by `outdir`)
- Plots: `outdir/<VARIABLE>.<format>` with a pull pad in `[-5, +5]`
- Optional 2D plots: configure `variables_2d` in the YAML (Data/MC/Pull panels)

Notes:

- Tree names can be provided either via `data_tree` / `sweight_tree` or inline in the path as `file.root:TreeName` (inline takes precedence and must not be combined with the separate key).

## Interactive web app

Run a small interactive web UI (variable selection, binning/range edits, preview, and optional saving):

```bash
streamlit run src/Apps/runners/run_datamc_web.py
```
