from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class UniverseSpec:
    instrument: str
    sector_name: str
    benchmark: str


UNIVERSE_SPECS = {
    "csi300": UniverseSpec(instrument="csi300", sector_name="沪深300", benchmark="SH000300"),
    "csi500": UniverseSpec(instrument="csi500", sector_name="中证500", benchmark="SH000905"),
    "sz50": UniverseSpec(instrument="sz50", sector_name="上证50", benchmark="SH000016"),
}

_ALIASES = {
    "csi300": "csi300",
    "hs300": "csi300",
    "沪深300": "csi300",
    "000300": "csi300",
    "sh000300": "csi300",
    "csi500": "csi500",
    "zz500": "csi500",
    "中证500": "csi500",
    "000905": "csi500",
    "sh000905": "csi500",
    "sz50": "sz50",
    "上证50": "sz50",
    "000016": "sz50",
    "sh000016": "sz50",
}


def _compact_key(value: str) -> str:
    return re.sub(r"[\s_.-]+", "", value).lower()


def canonical_universe_name(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    alias = _ALIASES.get(_compact_key(stripped))
    if alias is not None:
        return alias
    return stripped.strip().lower()


def get_universe_spec(value: str | None) -> UniverseSpec | None:
    canonical = canonical_universe_name(value)
    if canonical is None:
        return None
    return UNIVERSE_SPECS.get(canonical)


def resolve_universe_name(
    universe_name: str | None = None,
    sector_name: str | None = None,
    default: str = "csi300",
) -> str:
    for candidate in (universe_name, sector_name):
        canonical = canonical_universe_name(candidate)
        if canonical is not None:
            return canonical
    return canonical_universe_name(default) or default


def default_xtquant_out_root(universe_name: str) -> Path:
    return Path(f"./data/xtquant_{resolve_universe_name(universe_name)}")


def default_constituents_output_dir(universe_name: str) -> Path:
    return Path(f"./outputs/{resolve_universe_name(universe_name)}_constituents")
