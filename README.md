# datamc

Small helper app to compare sWeighted data vs MC from ROOT files, producing per-variable comparison plots with a pull panel.

## Layout

- `src/datamc/`: helpers (YAML config, ROOT IO, histogramming, plotting)
- `src/Apps/run_datamc.py`: main executable
- `configs.yaml`: example config

## Setup

Requires a local ROOT installation with PyROOT enabled (i.e. `import ROOT` works).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python3 src/Apps/run_datamc.py --yaml configs.yaml
```

Outputs:

- Parquet caches: `plots/parquet/data.parquet`, `plots/parquet/mc.parquet` (path controlled by `outdir`)
- Plots: `outdir/<VARIABLE>.<format>` with a pull pad in `[-5, +5]`

Notes:

- Tree names can be provided either via `data_tree` / `sweight_tree` or inline in the path as `file.root:TreeName` (inline takes precedence and must not be combined with the separate key).
