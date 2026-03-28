from __future__ import annotations

import glob
import os
from typing import Any

def _expand_path(path: str, base_dir: str) -> str:
    path = os.path.expandvars(os.path.expanduser(path))
    if not os.path.isabs(path):
        path = os.path.join(base_dir, path)
    return os.path.abspath(path)


def resolve_mc_files(mc_spec: Any, *, base_dir: str, data_path: str | None = None) -> list[str]:
    if isinstance(mc_spec, (list, tuple)):
        out: list[str] = []
        for item in mc_spec:
            out.extend(resolve_mc_files(item, base_dir=base_dir, data_path=data_path))
        return sorted(set(out))

    if not isinstance(mc_spec, str):
        raise TypeError("'mc' must be a string (path/glob/keyword) or a list of them")

    spec = mc_spec.strip()
    spec_path = _expand_path(spec, base_dir)

    if os.path.isfile(spec_path):
        return [spec_path]

    if any(ch in spec for ch in ["*", "?", "["]):
        matches = glob.glob(spec_path)
        matches = [os.path.abspath(m) for m in matches if os.path.isfile(m)]
        if not matches:
            raise FileNotFoundError(f"No MC files matched glob: {spec!r}")
        return sorted(matches)

    # keyword search
    search_dir = None
    if data_path:
        search_dir = os.path.dirname(os.path.abspath(data_path))
    if not search_dir:
        search_dir = base_dir

    matches = [
        os.path.join(search_dir, fn)
        for fn in os.listdir(search_dir)
        if fn.endswith(".root") and spec in fn
    ]
    matches = [os.path.abspath(m) for m in matches if os.path.isfile(m)]
    if not matches:
        raise FileNotFoundError(
            f"Could not resolve 'mc: {spec}'. Provide a ROOT file path, a glob, or place matching '*.root' files in {search_dir}"
        )
    return sorted(matches)
