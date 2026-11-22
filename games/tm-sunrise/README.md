# TrackMania Sunrise — Recomp Toolkit Profile (`--game-dir`)

Version-bound external game profile for **TrackMania Sunrise** built against [Recomp Toolkit](https://github.com/wraitii/recomp-toolkit) (pinned upstream commit `05392effc17c354a7315fd0102d2a304925be80d`).

## Supported executable identity

| Field | Value |
| --- | --- |
| Supplied edition | TrackMania Sunrise 1.4.6 (May 2005 retail ISO `TMSUNRISE`) |
| Assignment target edition | TrackMania Sunrise eXtreme (1.5.x — **not present** in supplied ISO) |
| Executable | `TmSunrise.exe` |
| Size | 8,742,980 bytes |
| SHA-256 | `a6820000345824e961e4cee9a88a7fdb8261d890b4eb7bc1f0657a2996ed2d64` |
| Architecture | PE32 (`0x014c`, Intel i386, Windows GUI subsystem) |
| Image base | `0x00400000` |
| Entry point | `0x00c42000` (RVA `0x00842000`, `.start`) |
| Copy protection | **StarForce 3.04.071.019 (`tmsunrise.dll` / `PROTECT.DLL`)** |

> **Copy-protection blocker:** The supplied retail `TmSunrise.exe` encrypts all main `.sforce3` code/data sections (Shannon entropy `7.950–8.000`) and hides its real Win32/DirectX imports behind `TMSUNRISE.DLL!ord#1`. The entry stub at `0x00c42000` is 11 bytes (`push 0x65b2b827; jmp dword ptr [0x00c421bc]`) and immediately transfers control to StarForce `PROTECT.DLL`, which requires Windows kernel-mode drivers (`sfsync03.sys`, `sfhlp02.sys`, `sfdrv01.sys`). Static translation cannot progress past `0x00c42000` without an authorized, unpacked/DRM-free TrackMania Sunrise eXtreme executable.

## Local data preparation

Keep original game files and generated builds strictly local (`local/` is gitignored):

```sh
# 1. Extract the Inno Setup installer from the local ISO
#    (or use local/iso_extracted/TMSUNRIS.EXE)
local/tools/innoextract/bin/amd64/innoextract -d local/game_install local/iso_extracted/TMSUNRIS.EXE

# 2. Verify executable hash and link local game files (no copying or modification)
recomp-toolkit/.venv/bin/python recomp-toolkit/tools/setup.py \
  --game-dir "$PWD/games/tm-sunrise" \
  --build-root "$PWD/local/build/tm-sunrise" \
  --install "$PWD/local/game_install/app"
```

## Build

```sh
export PATH="$PWD/local/tools/llvm/bin:$PWD/recomp-toolkit/.venv/bin:$PATH"

# Desktop headless and windowed app (Linux x86_64)
recomp-toolkit/.venv/bin/python recomp-toolkit/tools/build.py \
  --game-dir "$PWD/games/tm-sunrise" \
  --build-root "$PWD/local/build/tm-sunrise" \
  --regenerate --target headless

recomp-toolkit/.venv/bin/python recomp-toolkit/tools/build.py \
  --game-dir "$PWD/games/tm-sunrise" \
  --build-root "$PWD/local/build/tm-sunrise" \
  --target app
```

## Reference single-player track

Once an authorized unpacked edition is supplied, the candidate reference track in the local installation is:
- `GameData/Tracks/Campaigns/Nadeo/Sunrise/Race/Holidays/GoodMorning.Challenge.Gbx` (paired with `GoodMorning.bik` preview and `GoodMorning.Replay.gbx`).

## Documentation

- [Toolchain and Milestone Status](../../docs/toolchain-and-status.md)
- [Version-Specific Dependency Report](../../docs/dependency-report.md)
- [Desktop Build and Runtime Report](../../docs/desktop-report.md)
- [Android ARM64 Prototype Report](../../docs/android-report.md)
- [Nintendo Switch Homebrew Feasibility Report](../../docs/switch-feasibility-report.md)
