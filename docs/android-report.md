# Android ARM64 (`arm64-v8a`) Prototype Report

**Milestone 4 deliverable.** Documents upstream Android build blockers discovered and fixed, local `arm64-v8a` debug APK builds for both the standalone runtime stub and the `tm-sunrise` profile, reproducible build/installation instructions, and pending physical-device checks.

## Active target, eXtreme 0.1.5.0

With the environment from section 3 and the configured [eXtreme game profile](../games/tm-sunrise-extreme/README.md), build the APK from the project root. The profile includes desktop discovery evidence for static Android builds. Keep that evidence with the code map and regenerate the translated source when it changes.

```sh
export CARGO_BUILD_JOBS=2 RAYON_NUM_THREADS=2
recomp-toolkit/.venv/bin/python recomp-toolkit/tools/build.py \
  --game-dir "$PWD/games/tm-sunrise-extreme" \
  --build-root "$PWD/local/build/tm-sunrise-extreme" \
  --jobs 2 --target android --no-install --regenerate
```

The `dev.recompkit.tmsunriseextreme` build uses static translation without the baseline Cranelift fallback. The original APK stopped during startup at an unmapped call to `0x0040256b`. A Linux run with `RECOMP_INTERP=off` reproduced that call from `0x00403898`.

The profile now feeds [merged desktop discovery evidence](../games/tm-sunrise-extreme/metadata/discovery.tsv) into the translator. It covers 4,888 observed call records and 7,121 jump records across startup, menus, and Solo races. Regeneration emitted 51,228 functions and added a callable entry at `0x0040256b`. It completed with two translator threads after removing the earlier 4 GiB address-space cap.

The signed debug APK is at `local/build/tm-sunrise-extreme/android/app/build/outputs/apk/debug/app-debug.apk`. Its package ID is `dev.recompkit.tmsunriseextreme`, its minimum API level is 29, and APK Signature Scheme v2 verification passed.

### Physical phone replay benchmark

The ARM64 build launched, reached Solo, and played the third Holidays track, ParadiseIsland, on a Nothing A059P with an Adreno 810. At the phone's 1196×540 render size, two runs of the same ParadiseIsland autosave averaged 36.7 and 36.9 FPS in the game's benchmark report. The slower run dipped to 14.9 FPS, and the other dipped to 12.2 FPS. The 95th-percentile frame time in the first run was 37 ms. Live driving can have different frame times from the replay.

To repeat a benchmark, add `RECOMP_GUEST_ARGS=/bench=Autosaves\<name>.Replay.gbx` to the Android app's `switches.txt` alongside any existing settings, then restart the game. The argument is relative to the game's Replays directory. The game exits after writing a numbered report under `profile/GameData/Bench/`. Remove the benchmark argument before starting a normal session. Keep replays and raw benchmark files local.

## Local Android 15 emulator

The `tmsx_api35` emulator runs the Google APIs Android 15 x86-64 image with KVM and host GPU acceleration. The image uses Android's native bridge to run the ARM64 APK. The emulator, device state, and staged game data are local to this workspace.

Start the emulator from the project root when it is stopped.

```sh
./local/android-test/start.sh
```

The eXtreme APK and local game files are already installed. When rebuilding for this emulator, export `ANDROID_USER_HOME="$PWD/local/android-test/user"` to use the same debug signing key and keep the installed app's data. Launch it and inspect its log with ADB.

```sh
adb="$PWD/local/tools/android-sdk/platform-tools/adb"
"$adb" -s emulator-5556 shell am start -W \
  -n dev.recompkit.tmsunriseextreme/dev.recompkit.RecompActivity
"$adb" -s emulator-5556 logcat -s recomp SDL
```

The native launcher selects a supported 8-bit UNORM surface format and omits the presentation callback when the caller leaves it empty. The Android stub rendered the launcher and opened Configure by touch. The eXtreme APK displayed the launcher, passed the original startup crash, opened the main menu, and listed the official Solo campaigns.

A wgpu timed-wait assertion stopped the GPU completion worker during an earlier race test. The worker now polls for completions without blocking on a submission index, with a short timed wait for new work between polls. This lets the worker keep delivering presentation callbacks while the guest submits graphics work.

The rebuilt eXtreme APK passed the Android 15 emulator retest. It reused the saved test profile, loaded SkidOrDie from Solo → Official Campaigns → Race, accepted acceleration and steering, and restarted from the grid with the timer reset. The road and signs were textured and the timer was legible in the captured frames. The test log recorded no GPU completion timeout or untranslated call. Initial track loading took about a minute on this emulator. The desktop regression suite passed all 28 tests.

The software graphics mode crashed before boot on this host, so the emulator uses the host GPU. Audio output was disabled for the emulator smoke test. Physical-device frame pacing and audible output remain unverified.


---

## 1. Upstream Android Build Blockers Discovered & Fixed

Upstream `recomp-toolkit` (commit `05392effc17c354a7315fd0102d2a304925be80d`) marks its Android target as untested. Attempting `cmake --preset android-stub` exposed **three distinct cross-compilation blockers**, all resolved cleanly in [`patches/recomp-toolkit-linux-android.patch`](../patches/recomp-toolkit-linux-android.patch):

1. **`cmake/RustGraphics.cmake` rejected all cross-compiles:**
   - Error: `Rust graphics integration requires a native single-architecture build`.
   - Fix: Recognized `ANDROID` (`ANDROID_ABI STREQUAL "arm64-v8a"`) and mapped it to Cargo target `aarch64-linux-android`, bypassing the host-only target guard while keeping desktop validation intact.
2. **`d3d8-wgpu` pulled `winit` → `android-activity` without an activity feature:**
   - Error: `android-activity-0.6.1`: `Either "game-activity" or "native-activity" must be enabled as features` (caused by `d3d8-wgpu`'s default `windowing` feature, which is only used by the desktop `probe-windowed` binary; Android uses SDL3's `SDLActivity` / `RecompActivity`).
   - Fix: Passed `--no-default-features` to `cargo rustc --lib` for Android targets in `tools/build_d3d8_wgpu.py`, skipped the host-only `shader-corpus` binary when cross-compiling, and configured NDK `CC`/`CXX`/`AR`/`LINKER` env vars in `tools/cargo_build.py`.
3. **Runtime `DT_NEEDED: libc++_shared.so` mismatch against `ANDROID_STL=c++_static`:**
   - Verified with `llvm-readelf -d`: the initial linked `libmain.so` depended on `libc++_shared.so` (emitted by Rust's `link-cplusplus` crate) even though `CMakePresets.json` specifies `ANDROID_STL=c++_static` and Gradle does not package `libc++_shared.so` — which would crash immediately on device with `UnsatisfiedLinkError`.
   - Fix: Set `CXXSTDLIB=c++_static` in `tools/cargo_build.py` for Android cross-compiles. Re-verified with `llvm-readelf -d`: `libmain.so` now depends **exclusively** on Android system libraries (`libandroid.so`, `libdl.so`, `liblog.so`, `libm.so`, `libc.so`, `libOpenSLES.so`, `libGLESv1_CM.so`, `libGLESv2.so`) and the packaged FFmpeg `.so` files.

---

## 2. Built `arm64-v8a` Artifacts (Local, Gitignored)

Both debug APKs assembled cleanly with **Android NDK r27c**, **Rust `aarch64-linux-android`**, **Temurin JDK 21.0.13.1**, **Android SDK `android-36` / `build-tools 37.0.0`**, and **Gradle 9.7.1**:

| Artifact | Package / Bundle ID | Size | Packaged `lib/arm64-v8a/` | Status |
| --- | --- | ---: | --- | --- |
| Standalone runtime stub APK (`recomp-toolkit/build/android/app/build/outputs/apk/debug/app-debug.apk`) | `dev.recompkit.stub` | 159,513,306 bytes | `libmain.so` (static `libc++`, `-DRECOMP_VIDEO=OFF`) | **Built & verified structurally** |
| TrackMania Sunrise prototype APK (`local/build/tm-sunrise/android/app/build/outputs/apk/debug/app-debug.apk`) | `dev.recompkit.tmsunrise` | 163,209,738 bytes | `libmain.so` (157.5 MB), `libavcodec.so`, `libavformat.so`, `libavutil.so` + `assets/ffmpeg-NOTICE.md` | **Built & verified structurally** |

*Note on JIT (`rk-pcode-ffi`):* Per `recomp-toolkit` architecture (`docs/architecture.md`), Android builds omit the Cranelift baseline JIT (`--no-pcode`). Every executed guest function on Android must come from static AOT translation in the code map (or a reloc manifest).

---

## 3. Reproducible Local Build, Installation & Data Setup Instructions

### Prerequisites
- Android NDK `r27c` (`ANDROID_NDK_HOME`)
- Android SDK with `platform-tools`, `platforms;android-36`, `build-tools;37.0.0` (`ANDROID_HOME` / `ANDROID_SDK_ROOT`)
- JDK 21 (`JAVA_HOME`)
- Rust `aarch64-linux-android` target (`rustup target add aarch64-linux-android`)
- Local extracted game files prepared via `tools/setup.py`

### Build the `arm64-v8a` Debug APK Locally

```sh
export JAVA_HOME="$PWD/local/tools/jdk21"
export ANDROID_HOME="$PWD/local/tools/android-sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export ANDROID_NDK_HOME="$PWD/local/tools/android-ndk/android-ndk-r27c"
export PATH="$JAVA_HOME/bin:$PWD/local/tools/llvm/bin:$PWD/recomp-toolkit/.venv/bin:$PATH"

# Minimal standalone Android runtime test APK (no game files required)
recomp-toolkit/.venv/bin/python recomp-toolkit/tools/build.py \
  --stub --target android --no-install

# TrackMania Sunrise profile arm64-v8a debug APK
recomp-toolkit/.venv/bin/python recomp-toolkit/tools/build.py \
  --game-dir "$PWD/games/tm-sunrise" \
  --build-root "$PWD/local/build/tm-sunrise" \
  --target android --no-install
```

### Install & Push Local Game Data on a Physical ARM64 Device

```sh
# 1. Connect an ARM64 Android 10+ (API 29+, Vulkan 1.1+) device with USB debugging enabled
local/tools/android-sdk/platform-tools/adb devices

# 2. Install the debug APK
local/tools/android-sdk/platform-tools/adb install -r \
  local/build/tm-sunrise/android/app/build/outputs/apk/debug/app-debug.apk

# 3. Push local game files (or import via RecompActivity's folder/ZIP picker on first launch)
recomp-toolkit/.venv/bin/python recomp-toolkit/tools/build.py \
  --game-dir "$PWD/games/tm-sunrise" \
  --build-root "$PWD/local/build/tm-sunrise" \
  --target android --push-game
```

---

## 4. Hardware Verification Status & Pending Checks

- **ADB check in current environment:** `emulator-5556` is online. Physical ARM64 testing remains pending.
- **Build succeeded:** **YES** (`dev.recompkit.stub` and `dev.recompkit.tmsunrise` `arm64-v8a` debug APKs).
- **Process launched / Menu reached / Reference track completed on device:** **PENDING** (requires physical ARM64 Android device + authorized unpacked TrackMania Sunrise eXtreme executable).

### Pending Physical-Device Verification Checklist
- [ ] Install & launch `dev.recompkit.stub` APK on physical ARM64 device; confirm Vulkan surface creation, SDL3 audio (`AAudio`/`OpenSL ES`), touch/controller input, and pause/resume lifecycle.
- [ ] Install `dev.recompkit.tmsunriseextreme` and import the local eXtreme game data.
- [ ] Verify offline load, completion, and restart of `GoodMorning.Challenge.Gbx` with controller input, audio, and persistent settings across background/foreground transitions and full process exit + relaunch.
- [ ] Record device model, Android version, display resolution, FPS, and frame-time percentiles on the reference track.
- [ ] Confirm zero runtime JIT fallback requirement (`--no-pcode` coverage).
