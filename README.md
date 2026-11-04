# Boston HeatShield

Code, documentation and an interactive demo for the Boston HeatShield extreme-heat tabletop exercise. DBbun LLC's Boston HeatShield Situation Manual was selected as one of 40 winners of NOAA's 2026 Heat Tabletop Design Challenge, with a $25,000 prize. The challenge was run by NOAA's Climate Program Office through NIHHIS, the National Integrated Heat Health Information System. Announcement of the winners: [2026 NIHHIS Heat Tabletop Design Challenge Awardees](https://heat.gov/news-events/2026-nihhis-heat-tabletop-design-challenge-awardees/). Author's article on the award: [LinkedIn](https://www.linkedin.com/pulse/dbbun-named-noaa-heat-tabletop-design-challenge-uri-kartoun-phd-qj55c/).

Live map: https://dbbun.github.io/BostonHeatShield/demo/

Status: planning. Public data only. Everything simulated is labeled as simulated or assumed. Synthetic data is never presented as clinical or operational evidence.

## Layout

- `scripts/` data download and probe scripts (honest client name, manifest of what was fetched)
- `src/` pipeline and simulation code (Python)
- `demo/` static map-based demo
- `docs/` data-source table, method notes
- `data_raw/` downloaded data, not tracked (only `manifest.json` is)

## Facilitator board

`board/index.html` is a single-page tool for running a short online heat exercise (timer, risk board, decision log, improvement sorter, role and persona cards). It has no dependencies; open the file in a browser. Notes stay in the browser's local storage on that device. Every tab and step has a Listen button with a short voice explanation of what is happening and what to do, plus the words to read instead; sound only plays when you press play. The voice is AI-generated (Kokoro-82M, run locally). To re-render after editing a script in `board/audio/*.txt`, run `scripts/build_board_audio.py` with a Python that has Kokoro installed. It is a fictional exercise tool, not an official NOAA, NIHHIS or City of Boston product.

## Not in this repository

The Situation Manual, correspondence with NOAA and other organizations, raw data files, credentials and participant records.

## License

Code: MIT (see LICENSE). Written exercise materials (for example the role envelopes, persona cards and rules text in the facilitator board): CC BY 4.0 (see LICENSE-MATERIALS.md). Public datasets the code downloads keep their own licenses and terms, and the Situation Manual is not included. The names "HeatShield" and "DBbun" are not licensed; "based on Boston HeatShield" is fine.

## AI disclosure

Developed by DBbun LLC with assistance from Claude Code (Anthropic), model claude-sonnet-5-5; board voice narration by Kokoro-82M text-to-speech and earlier Claude models used in this project. Update this list as tools change.





