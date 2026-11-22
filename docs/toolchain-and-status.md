# Toolchain Record & Platform Milestone Status

**Milestone 1 deliverable & overall project handoff tracker.**

---

## 1. Pinned Upstream & Local Toolchain Versions

| Component | Exact Version / Revision | Location |
| --- | --- | --- |
| Upstream `recomp-toolkit` | `05392effc17c354a7315fd0102d2a304925be80d` (`main` / `latest-nightly`) | `recomp-toolkit/` |
| Reusable toolkit patch | Linux and Android builds, translator and Win32 runtime compatibility, DirectInput and D3D9 | [`patches/recomp-toolkit-linux-android.patch`](../patches/recomp-toolkit-linux-android.patch) |
| Host OS & Architecture | Linux `x86_64` (Freedesktop SDK 26.08 runtime; Apple Silicon macOS not present) | Host |
| C / C++ Compiler & Linker | LLVM Clang `23.1.6` + LLD `23.1.6` (system GCC `16.2.0` libstdc++) | `local/tools/llvm/bin/` |
| Rust Toolchain | `rustc 1.100.0` (`0ef1bc386 2026-11-09`), targets: `x86_64-unknown-linux-gnu`, `aarch64-linux-android` | Cargo (`rustup`) |
| Python & Dev Dependencies | Python `3.14.9`, `cmake==4.1.2`, `ninja==1.13.0`, `pefile==2024.8.26`, `capstone==5.0.9`, `unicorn==2.1.4`, `pytest==8.4.2`, `clang-format==23.1.1` | `recomp-toolkit/.venv/` |
| Parser / Shader Tools | Flex `2.6.4`, Bison `3.8.2`, `glslc`, NASM, Mesa Lavapipe Vulkan ICD (`lvp_icd.x86_64.json`) | `/usr/bin/` |
| JDK | Eclipse Temurin OpenJDK `21.0.13.1+2-LTS` | `local/tools/jdk21/` |
| Ghidra | **Ghidra `12.1.3` PUBLIC** (`ghidra_12.1.3_PUBLIC_20260817`) | `local/tools/ghidra/` |
| Android NDK | **Android NDK `r27c`** (`12479018`, Clang `18.0.3`, `ANDROID_PLATFORM=android-29`, `arm64-v8a`, `c++_static`) | `local/tools/android-ndk/android-ndk-r27c/` |
| Android SDK & Gradle | `platforms;android-36`, `build-tools;36.0.0` & `37.0.0`, `platform-tools` (`adb`), Gradle `9.7.1` | `local/tools/android-sdk/` |
| Installer Extractor | `innoextract 1.9` | `local/tools/innoextract/` |

---

## 2. Platform Milestone Tracker

| Platform | Build Succeeded | Process Launched | Menu Reached | Reference Track Completed | Blocking Prerequisite / Notes |
| --- | :---: | :---: | :---: | :---: | --- |
| **eXtreme desktop (`x86_64` Linux)** | **Yes**, headless and windowed | **Yes** | **Yes**, confirmed interactively | **SkidOrDie finished in 1:52.950** | Steering, respawn, and mixer output verified. GoodMorning, preference persistence, and rendering defects remain open. See the [desktop report](desktop-report.md). |
| **eXtreme Android (`arm64-v8a`)** | **Yes**, debug APK verified | **Yes**, emulator and phone | **Yes** | **ParadiseIsland replay** | Physical phone benchmark at 1196×540. See the [Android report](android-report.md). |
| **Retail desktop (`x86_64` Linux)** | **Yes**, headless and windowed | **Yes** | **Blocked** | **Pending** | StarForce 3.04.071.019 import `TMSUNRISE.DLL!ord1` at `0x00c42005`. |
| **Retail and stub Android (`arm64-v8a`)** | **Yes**, debug APKs built | **Pending** | **Pending** | **Pending** | Device verification pending. |
| **Nintendo Switch (Homebrew)** | **NO (Feasibility evaluated)** | **NO** | **NO** | **NO** | Blocked by upstream `wgpu` having no Horizon OS/NVN/deko3d backend, no Tier-1/2 Rust `std` Switch target, no SDL3 Switch driver, and missing Switch test hardware + `devkitA64`. See [Switch Feasibility Report](switch-feasibility-report.md). |

---

## 3. Toolkit Verification Results on Linux Host

The eXtreme patch passed the repository boundary and link checks, all 29 synthetic translator cases with 200 Unicorn inputs per case, the translator relocation integration test, and all 28 Linux `nogame` and `gpu` CTest suites with video enabled. The separately selected `runtime_tests` suite passed its standalone checks and skipped game-backed checks because the stub guest executable was absent.

The eXtreme original-byte differential sample covered 200 translated functions. Of these, 98 matched, 94 were unreached with the sampled inputs, and eight diverged. The discrepancies include flags, memory writes, and an unresolved indirect call. The runner now links the Linux static archive into its isolated harness and records native import resolution as an escape.

All verification suites were run directly on this Linux `x86_64` host:

| Suite | Command | Result | Notes |
| --- | --- | --- | --- |
| Python tooling unit tests | `.venv/bin/python -m unittest discover -s tools/recomp/tests -p 'test_*.py'` | **PASS (4/4)** | Clean |
| Repository boundary & doc link checks | `.venv/bin/python tools/check_repo.py` | **PASS** | Clean |
| Rust translator unit tests (`cargo test`) | `.venv/bin/python tools/test.py --translator` | **PASS (12/12)** | Clean |
| Translator Unicorn differential cases | `.venv/bin/python tools/test.py --translator` | **PASS (29/29 cases, 5 groups, 200 iterations each, + reloc integration)** | Required 3 reusable Linux/Clang-23 fixes (below) |
| Native `linux-stub` CTest (`-L "nogame\|gpu"`) | `SDL_VIDEODRIVER=dummy VK_ICD_FILENAMES=.../lvp_icd.x86_64.json ctest --preset linux-stub -L "nogame\|gpu"` | **27/28 PASS** (`-DRECOMP_VIDEO=OFF`); **28/28 PASS** (`dx_tests` **141,438/141,438 checks PASS** with `RECOMP_VIDEO=ON`) | Includes all 7 Vulkan/wgpu GPU tests (`d3d9_guest_tests`, `d3d8_render_tests`, `d3d8_surface_tests`, `d3d7_mipmap_tests`, `gpu_wgpu_tests`, `compositor_tests`, `host_tests`) plus `interp_tests` (Cranelift JIT), `seh_tests`, `pad_tests`, `controls_tests` |
| Live TrackMania Sunrise Bink video decode | `RECOMP_TEST_BINK_CONTAINER=.../GoodMorning.bik,0 dx_tests` | **Video decode PASS** (`open from handle`, `realtime`, `rects and pause` ok) | Audio sub-assertions N/A because `GoodMorning.bik` is a silent track preview |

---

## 4. Reusable Upstream Fixes Produced (`patches/recomp-toolkit-linux-android.patch`)

Every fix addresses a verified, reproducible gap on Linux or Android ARM64 without any game-specific logic:

1. **`tools/build.py` (Linux harness linkage):** Added `-lstdc++` to the non-Darwin shared-library link flags in `build_translator_harness()` and `build_diff_harness()` (both compile C++ sources with `-x c++ -std=c++17`, which previously failed to `dlopen` on Linux with `undefined symbol: _Znwm`).
2. **`tools/recomp/diff/run.py` (Linux ELF symbol isolation):** Loaded `harness.so` with `RTLD_LOCAL` on non-Darwin platforms (`RTLD_GLOBAL` caused ELF global symbol interposition between sequential test groups on Linux, making groups 1–4 collide with group 0's `recomp_table`/`g_mem`).
3. **`tests/translator/cases/call_method_fact.s` (Clang 23 Intel assembler compatibility):** Reordered `push offset object_va; mov edx, offset object_va` to `mov edx, offset object_va; push edx` so LLVM 23's integrated i386 assembler does not reject `push offset <equ>` as a 16-bit immediate overflow.
4. **`cmake/RustGraphics.cmake`, `tools/cargo_build.py`, `tools/build_d3d8_wgpu.py`, `tools/build_compositor.py` (Android `arm64-v8a` cross-compilation):**
   - Enabled `ANDROID` (`arm64-v8a` → `aarch64-linux-android`) in `RustGraphics.cmake` instead of aborting on `CMAKE_CROSSCOMPILING`.
   - Propagated Android NDK Clang/LLD/llvm-ar environment variables (`CC_aarch64_linux_android`, `CXX_aarch64_linux_android`, `AR_aarch64_linux_android`, `CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER`) in `cargo_build.py`.
   - Set `CXXSTDLIB=c++_static` for Android builds so `link-cplusplus` matches `CMakePresets.json`'s `ANDROID_STL=c++_static` and does not emit an unpackaged `DT_NEEDED: libc++_shared.so` that would crash on Android startup.
   - Passed `--no-default-features` when building `d3d8-wgpu` `--lib` for Android (dropping the unused `windowing`/`winit` binary feature that pulled in unconfigured `android-activity`), and skipped the host-only `shader-corpus` binary during cross-compilation.
