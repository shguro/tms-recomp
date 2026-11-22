# Nintendo Switch Homebrew Feasibility Report

**Milestone 5 deliverable.** Evaluation of porting the Recomp Toolkit runtime and TrackMania Sunrise profile to Nintendo Switch homebrew (Horizon OS, ARM64 Cortex-A57, Maxwell Tegra X1 GPU), grounded directly in `recomp-toolkit` at commit `05392effc17c354a7315fd0102d2a304925be80d`.

---

## 1. Test Environment & Hardware Status

| Prerequisite | Status in Current Environment |
| --- | --- |
| Configured Nintendo Switch test device | **Not present** (no Switch hardware attached) |
| devkitPro / `devkitA64` (`aarch64-none-elf-gcc`) + `libnx` | **Not installed** (build-only evaluation; no hardware verification possible) |
| Minimal Switch runtime test binary | **Not executed on hardware** (unverified on hardware; blocked on upstream toolkit graphics/platform gaps identified below) |

---

## 2. First Verified Architectural Blockers

Inspection of `recomp-toolkit`'s runtime, platform layer, graphics crates, and build system identifies **four concrete, source-verified blockers** before a Switch homebrew prototype can run graphics or translated game code:

### Blocker 1 (Primary / Hard Blocker): Graphics Backend — `wgpu` Has No Horizon OS / NVN / deko3d Backend
- **Evidence in `recomp-toolkit`:**
  - `docs/architecture.md` (lines 148–164) confirms that all legacy native backends (OpenGL / D3D11) were **removed**; the entire D3D7/D3D8/D3D9 renderer (`graphics/d3d8-wgpu`) and compositor (`graphics/compositor`) are implemented exclusively in Rust on **`wgpu` v30.0.1** (`graphics/gpu/Cargo.toml`).
  - `wgpu` supports Vulkan, Metal, DirectX 12, and OpenGL ES 3 / WebGPU.
  - Nintendo Switch homebrew under Horizon OS (`libnx`) exposes **deko3d** (low-level Maxwell GPU command submission) and **Mesa Nouveau OpenGL / GLES** (via `libdrm_nouveau` + `mesa` in devkitPro pacman packages), **NOT Vulkan 1.1+**. (`wgpu`'s `gles` backend targets EGL/GLES 3.0+ via `glow` on Linux/Android/macOS, not `libnx`/switch-mesa out of the box, and `wgpu-hal` has no `target_os = "horizon"` platform glue or `raw-window-handle` support for `NWindow`.)
- **Impact:** Without either (a) porting `wgpu-hal`'s GLES backend + `raw-window-handle` to Switch `NWindow`/EGL/switch-mesa, or (b) writing a new C++/Rust `deko3d` backend behind `host/gpu/gpu.h` and `d3d9`, **no rendering is possible on Horizon OS**.

### Blocker 2: Rust Target Tier & CMake Cross-Compilation (`aarch64-nintendo-switch-freestanding` / `horizon`)
- **Evidence in `recomp-toolkit`:**
  - `cmake/RustGraphics.cmake` (lines 2–5) explicitly fails on cross-compilation (we had to patch it even for Android Tier-2 `aarch64-linux-android`).
  - Nintendo Switch Horizon OS is **not** an official Tier-1/Tier-2 Rust `std` target (`aarch64-nintendo-switch-freestanding` is Tier-3 `no_std`, while `recomp-gpu`, `d3d8-wgpu`, `recomp-compositor`, and `naga` all require full Rust `std`, `std::thread`, `std::sync`, and `parking_lot`).
  - Building Rust `std` for Horizon OS requires a custom nightly `-Z build-std` toolchain (e.g., `cargo-nx` / `aarch64-nintendo-switch-freestanding` + `newlib`/`pthread` shims) and patching every transitive crate (`wgpu`, `gpu-allocator`, `ndk-sys`, `libc`) that checks `cfg(unix)` / `target_os`.

### Blocker 3: Platform Layer (`platform/os.h`) & SDL3 on Switch
- **Evidence in `recomp-toolkit`:**
  - `platform/os.h` requires POSIX/Win32 services: `os_vm_reserve` / `os_vm_reserve_at` (contiguous virtual memory reservation for the 32-bit guest arena, `guest_size = 0x18000000` = 384 MiB for TrackMania Sunrise), `os_thread_*`, `os_dlopen` (dynamic plugins — unsupported on static `.nro` Switch homebrew), `os_spawn`/`os_wait`, and `os_directory_watch_*`.
  - Under `libnx`, `os_vm_reserve` cannot use Linux `mmap(MAP_ANONYMOUS)` directly with demand-paged overcommit; Switch has **~3.2 GiB usable applet/application RAM** (and only ~400–500 MiB in applet mode — full **title-override / NSP / atmosphere takeover mode** is mandatory!) and uses `virtmemReserve` + `svcSetHeapSize` / `svcMapMemory`.
  - `recomp-toolkit` vendors **SDL 3.4.16** (`_deps/sdl3-src`). Upstream SDL3 does **not** ship an official Nintendo Switch (`libnx`) video/audio/input driver (Switch ports historically used community forks of SDL2). A Switch port would require implementing or integrating a `libnx` platform/SDL3 backend for `NWindow`, `audren`, and `hid` (`PadState`).

### Blocker 4: Runtime-Generated Code / Cranelift JIT Fallback on Horizon OS
- **Evidence in `recomp-toolkit`:**
  - `docs/architecture.md` (lines 288–293): *"Mobile, web and Windows builds currently omit this linkage too (`--no-pcode`). A complete static map does not cover heap-generated code, which still requires the baseline when used by the guest."*
  - Horizon OS enforces strict **W^X** on user code pages. Dynamic JIT compilation on Switch homebrew requires `libnx`'s `jitCreate` / `jitTransitionToWritable` / `jitTransitionToExecutable` (backed by `svcMapProcessCodeMemory` / dual-mapped RW+RX aliases), which is **not** supported in `rk-pcode-ffi` / Cranelift out of the box and fails under certain firmware/applet environments unless JIT permissions are granted.
  - **Consequence for TrackMania Sunrise:** Before committing to any Switch graphics backend port, an unpacked TrackMania Sunrise eXtreme build on desktop **must** be verified with `RECOMP_INTERP=off` and `--no-pcode` across the full menu → reference track → restart loop to prove **zero reliance on heap-generated code or Cranelift JIT**. If static translation alone covers 100% of executed gameplay code (matching `4x4-evo2` and the Android/iOS build model), JIT is unnecessary on Switch.

---

## 3. Subsystem-by-Subsystem Port Effort Estimate (Once Desktop & Android Pass)

| Subsystem | Difficulty | Concrete Work Required |
| --- | --- | --- |
| **Static translated C code (`librecomp_gen.a`)** | **Low** | Pure C11 targeting ARM64 (`aarch64-none-elf-clang` / `aarch64-none-elf-gcc`); no x86 dependencies if `--no-pcode` holds. |
| **Platform OS shim (`platform/os_switch.cpp`)** | **Medium** | Implement `os.h` over `libnx` (`virtmemReserve`/heap arena, `pthreads`, `sdmc:/` file I/O, stub `dlopen`/`spawn`). Must enforce title-override mode (full 3.2 GiB RAM). |
| **Input & Audio (`hid` + `audren`)** | **Medium** | Map `libnx` `PadState` directly into `host/controls/vpad` (which already feeds DirectInput8/XInput cleanly) and `audren` into `host/audio/mixer.cpp`. |
| **Graphics (`D3D9` → `wgpu` → Switch GPU)** | **Very High (Primary Blocker)** | Either (1) build Rust `std` + `wgpu-hal` GLES3 on Switch Mesa/EGL/NWindow, or (2) write a C++ `deko3d` renderer + SPIR-V/GLSL shader translation replacing `d3d8-wgpu` and `recomp_compositor`. |

---

## 4. Recommendation & Resume Gate

1. **Verdict:** **Blocked / Not feasible for immediate prototype** in the current toolkit architecture due to `wgpu` lacking Horizon OS support and Rust `std` lacking a Tier-1/2 Switch target, compounded by the missing Switch hardware and devkitA64 toolchain.
2. **Concrete gate to revisit Switch:**
   - First confirm an unpacked TrackMania Sunrise eXtreme build completes the reference track on desktop and Android ARM64 with `--no-pcode` (`RECOMP_INTERP=off`, zero JIT hits).
   - Provide a configured Switch test device (Atmosphère title-override mode) and `devkitA64`/`libnx` toolchain.
   - Build a standalone minimal `libnx` test `.nro` verifying: (a) 384 MiB contiguous guest arena allocation, (b) `audren` PCM playback, (c) `hid` controller input, (d) `sdmc:/` file I/O, and (e) an EGL/GLES3 or `deko3d` triangle/textured quad before attempting any `wgpu` or renderer port.
