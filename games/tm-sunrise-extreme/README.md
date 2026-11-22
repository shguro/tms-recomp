# TrackMania Sunrise eXtreme 0.1.5.0

This Recomp Toolkit profile uses the supplied unpacked PE32 executable with entry point `0x0040259a` and SHA-256 `e59dfc7eaa5314e85b2b0df6f40ef7ba01a23bd5a9525f84407f5dff301df4fe`. Keep the acquired executable and its accompanying game data under `local/tmsx_install/TMSX/`. The profile includes the Ghidra 12.1.3 code map and a native replacement that routes the legacy Unicode import resolver through the toolkit’s `GetProcAddress`.

The tested portable edition is listed on the [Internet Archive](https://archive.org/details/tmsx-portable). Select the folder containing `TmSunrise.exe` and `GameData/` from a copy you are entitled to use. Follow the [root setup instructions](../../README.md#build-from-source) to prepare the matching toolkit checkout.

From the project root, with the patched toolkit and local LLVM and Python toolchains installed, configure the game and generate the Linux build. Omit `--regenerate` on routine rebuilds with the same executable, translator, and code map.

```sh
export PATH="$PWD/local/tools/llvm/bin:$PWD/recomp-toolkit/.venv/bin:$PATH"
export CARGO_BUILD_JOBS=2 RAYON_NUM_THREADS=2

recomp-toolkit/.venv/bin/python recomp-toolkit/tools/setup.py \
  --game-dir "$PWD/games/tm-sunrise-extreme" \
  --build-root "$PWD/local/build/tm-sunrise-extreme" \
  --install "$PWD/local/tmsx_install/TMSX"

recomp-toolkit/.venv/bin/python recomp-toolkit/tools/build.py \
  --game-dir "$PWD/games/tm-sunrise-extreme" \
  --build-root "$PWD/local/build/tm-sunrise-extreme" \
  --jobs 2 --regenerate --target app
```

Launch on the desktop with the host GPU and display.

```sh
RECOMP_EXE="$PWD/local/tmsx_install/TMSX/TmSunrise.exe" \
  ./local/build/tm-sunrise-extreme/package/TmSunriseExtremeRecomp/TmSunriseExtremeRecomp
```

The profile selects the game's PC0 graphics path for the supplied portable data. This path restores the track materials that depend on missing PC2 shader files and uses simpler effects. The renderer keeps the higher-detail texture mips available and paces fullscreen presents to the display refresh.

For stage-by-stage verification results and Android build instructions, see the [desktop report](../../docs/desktop-report.md) and [Android report](../../docs/android-report.md).
