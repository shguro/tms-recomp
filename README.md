# TrackMania Sunrise Recompilation Project

Project-owned integration profile, Ghidra export tooling, reusable Recomp Toolkit patches, and platform engineering reports for statically translating **TrackMania Sunrise** with [Recomp Toolkit](https://github.com/wraitii/recomp-toolkit) (pinned commit `05392effc17c354a7315fd0102d2a304925be80d`).

Original game files, ISOs, local toolchains, and generated builds remain local (`TMSunrise/`, `tmsx-portable/`, `local/`, and `recomp-toolkit/build/` are excluded via `.gitignore`). The active profile targets the locally supplied eXtreme `0.1.5.0` executable.

## Build from source

Use a local copy of the eXtreme 0.1.5.0 game data that you are entitled to use. The tested portable edition is listed on the [Internet Archive](https://archive.org/details/tmsx-portable). See the [game profile](games/tm-sunrise-extreme/README.md) for the executable checksum and setup commands.

From this repository's root, prepare the pinned toolkit checkout:

```sh
git clone https://github.com/wraitii/recomp-toolkit.git recomp-toolkit
git -C recomp-toolkit checkout --detach 05392effc17c354a7315fd0102d2a304925be80d
git -C recomp-toolkit apply --check ../patches/recomp-toolkit-linux-android.patch
git -C recomp-toolkit apply ../patches/recomp-toolkit-linux-android.patch
python3 -m venv recomp-toolkit/.venv
recomp-toolkit/.venv/bin/python -m pip install -r recomp-toolkit/requirements-dev.txt
```

Install the platform prerequisites from the [toolkit contribution guide](https://github.com/wraitii/recomp-toolkit/blob/05392effc17c354a7315fd0102d2a304925be80d/CONTRIBUTING.md), then follow the [Linux build instructions](games/tm-sunrise-extreme/README.md) or the [Android build instructions](docs/android-report.md).

## Repository Layout

- [`games/tm-sunrise-extreme/`](games/tm-sunrise-extreme/README.md) — Active eXtreme `0.1.5.0` profile, Ghidra code map, build and launch instructions.
- [`games/tm-sunrise/`](games/tm-sunrise/README.md) — Archived retail `1.4.6` profile and code map.
- [`ghidra_scripts/ExportCodeMap.java`](ghidra_scripts/ExportCodeMap.java) — Ghidra 12.1.3 headless/GUI script exporting `recomp-code-map-v3` (`metadata.txt`, `spans.tsv`, `tables.tsv`, `entries.tsv`, `noreturn.tsv`).
- [`tools/inspect_pe.py`](tools/inspect_pe.py) — PE header, section entropy, version resource, import/export, and overlay analyzer.
- [`tools/check_import_coverage.py`](tools/check_import_coverage.py) — Cross-references PE imports against Recomp Toolkit's registered Win32/DirectX shims.
- [`patches/recomp-toolkit-linux-android.patch`](patches/recomp-toolkit-linux-android.patch) — Reusable translator, Win32, DirectX, and Bink fixes, plus Android `arm64-v8a` Rust `wgpu` and static `libc++` cross-compilation.
- [`docs/toolchain-and-status.md`](docs/toolchain-and-status.md) — Pinned tool versions, Linux test results, and platform milestone status matrix.
- [`docs/dependency-report.md`](docs/dependency-report.md) — Version-specific PE & import coverage report, StarForce 3.04.071.019 findings, and open questions.
- [`docs/desktop-report.md`](docs/desktop-report.md) — Desktop build, live StarForce stop-point capture, standalone runtime/Bink verification, and Wine evaluation.
- [`docs/android-report.md`](docs/android-report.md) — Android `arm64-v8a` build fixes, debug APK verification, and local installation instructions.
- [`docs/switch-feasibility-report.md`](docs/switch-feasibility-report.md) — Nintendo Switch homebrew feasibility and architectural blocker analysis.

## Current Milestone Summary

| Platform | Build Succeeded | Process Launched | Menu Reached | Reference Track Completed |
| --- | :---: | :---: | :---: | :---: |
| **eXtreme desktop (`x86_64` Linux)** | **YES** | **YES** | **YES**, official campaigns available | **SkidOrDie**, 1:52.950 |
| **eXtreme Android (`arm64-v8a`)** | **YES**, debug APK verified | **YES** on emulator and physical phone | **YES**, Solo campaigns available | **ParadiseIsland** replay benchmark completed on a physical phone. |
| **Retail desktop (`x86_64` Linux)** | **YES** | **YES** (`TmSunrise.exe` entry `0x00c42000`) | **BLOCKED** (`TMSUNRISE.DLL!ord1`, StarForce 3.04.071.019) | **PENDING** |
| **Retail and stub Android (`arm64-v8a`)** | **YES** (`dev.recompkit.stub` & `dev.recompkit.tmsunrise` debug APKs) | **PENDING** (no physical ADB device) | **PENDING** | **PENDING** |
| **Nintendo Switch (Homebrew)** | **NO** (feasibility blocked: no `wgpu` Horizon/deko3d backend, no Tier-1/2 Rust `std` Switch target, no SDL3 Switch driver, no hardware) | **NO** | **NO** | **NO** |
