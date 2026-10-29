# Boston HeatShield

Code, documentation and an interactive demo for the Boston HeatShield extreme-heat tabletop exercise, a 2026 winner of the NOAA Heat Tabletop Design Challenge (run through NIHHIS, the National Integrated Heat Health Information System).

Status: planning. Public data only. Everything simulated is labeled as simulated or assumed. Synthetic data is never presented as clinical or operational evidence.

## Layout

- `scripts/` data download and probe scripts (honest client name, manifest of what was fetched)
- `src/` pipeline and simulation code (Python)
- `demo/` static map-based demo
- `docs/` data-source table, method notes
- `data_raw/` downloaded data, not tracked (only `manifest.json` is)

## Not in this repository

The Situation Manual, correspondence with NOAA and other organizations, raw data files, credentials and participant records.

## License

MIT (see LICENSE). The license covers the code and documentation in this repository only. Public datasets it downloads keep their own licenses and terms, and the Situation Manual is not included.

## AI disclosure

Developed by DBbun LLC with assistance from Claude Code (Anthropic), model claude-sonnet-5-5 and earlier Claude models used in this project. Update this list as tools change.

