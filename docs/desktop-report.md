# Desktop Build & Runtime Report (Linux `x86_64`)

**Milestone 3 deliverable.** Documents Ghidra 12.1.3 code map export, desktop build via `--game-dir`, live execution trace of the copy-protection stop point, standalone runtime/translator verification, and Wine evaluation.

## Active target, eXtreme 0.1.5.0

The Ghidra `recomp-code-map-v3` export covers 21,132 functions, 1,447,167 instructions, 657 jump tables and 5,561 interior entries. The translated build contains 26,698 dispatch entries, 108 body chunks, 95 entry chunks and 33 functions using fallback. Both the Linux headless executable and the `TmSunriseExtremeRecomp` windowed package built and launched. [eXtreme game profile and launch instructions](../games/tm-sunrise-extreme/README.md)

The headless Vulkan run rendered the 1920×1080 loading screen, loaded the menu assets and displayed the first-run **Enter your name** dialog. The guest previously exited after `mmioDescend` returned `MMIOERR_CHUNKNOTFOUND` while reading the on-disk menu selection WAV. The toolkit now walks the RIFF chunks from the live file position and moves the underlying stream when descending or ascending. [Microsoft WinMM documentation](https://learn.microsoft.com/en-us/windows/win32/api/mmiscapi/nf-mmiscapi-mmiodescend)

The runtime now recognizes the Unicode DirectInput 8 interface and describes keyboard keys and mouse axes and buttons in the standard device formats. Interactive testing completed first-run name entry and reached the main menu. The first windowed test reported graphic artifacts and an empty campaign list. [Microsoft DirectInput object lookup documentation](https://learn.microsoft.com/es-es/previous-versions/windows/desktop/ee417906(v=vs.85))

Directory scans use `lstrcmpW` to exclude the dot entries. The added Unicode comparison lets the game examine the real entries. Both Linux runners subsequently opened and read the saved profile and the installed `GoodMorning.Challenge.Gbx`. Reading a track during the catalog scan is an earlier milestone than playing it. [Microsoft Unicode string comparison documentation](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-lstrcmpw)

The saved-profile relaunch now passes the 1920×1080 D3D9 reset. The reset drops resources held solely by pipeline bindings on commit. Application-owned default-pool resources still require release before reset. [Microsoft D3D9 Reset documentation](https://learn.microsoft.com/en-us/windows/win32/api/d3d9/nf-d3d9-idirect3ddevice9-reset)

The Bink rectangle copy now starts on the bottom row of a negative-stride destination and supports legacy packed 24-bit output. Both the intro sequence and the menu background exercised that path. Preview movies now rewind at the end of the stream, matching the Windows Bink playback loop. The windowed test cycled through SkidOrDie, ParadiseIsland, NightFlight, and GoodMorning previews. [Bink development history](https://www.radgametools.com/bnkhist.htm)

The windowed run opened `SkidOrDie.Challenge.Gbx` from Solo → Race → Holidays and loaded its race assets. The first race draw reached the toolkit’s unsupported constant depth-bias path. The renderer now converts the D3D9 normalized offset to WebGPU depth units using the attachment format. The float-depth conversion uses the spacing near 1.0 as an approximation. The renderer applies both constant and slope-scaled bias only to triangle primitives, including wireframe triangles. [Microsoft D3D9 depth bias documentation](https://learn.microsoft.com/en-us/windows/win32/direct3d9/depth-bias)

After the depth-bias fix, the race advanced to a call to `IDirect3DDevice9::ValidateDevice`. The added binding reports one pass for an operational device, matching the renderer's single-pass model. Validation of specific state combinations still occurs when preparing a draw. [Microsoft D3D9 ValidateDevice documentation](https://learn.microsoft.com/en-us/windows/win32/api/d3d9/nf-d3d9-idirect3ddevice9-validatedevice)

SkidOrDie then reached texture sampling with a nonzero mipmap LOD bias. The renderer now passes each sampler's bias in a pixel uniform and applies it during fixed-function, specialized, and interpreted texture sampling. [Microsoft D3D9 sampler state documentation](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dsamplerstatetype)

The windowed run completed SkidOrDie and quit cleanly. The temporary profile contains the autosaved replay with a time of 1:52.950 and one respawn. Scripted captures separately show the car accelerating, steering, and returning to the start after Enter before the first checkpoint. A debugger trace found two already-released surface views passed to `GetDesc` and `SetRenderTarget` on the profile screen.

The player's frame showed a flat road and signs and translucent rectangles in the race HUD. A headless run reproduced them and traced a failed open of `IslandHighWayPC2_2.VHlsl.cry`. That shader file is absent from both the local installation and its portable ZIP. The eXtreme profile now advertises the fixed-function pixel path so the game selects its PC0 materials. The rebuilt Linux package includes this setting. Headless SkidOrDie captures show textured roads and signs and a readable HUD at the start, while driving, and after a restart. PC0 uses the game's lower-detail effects, and the water still looks flat in some views.

The original windowed trace recorded 881 shader-variant evictions and 840 pipeline evictions. Four pipeline builds in one frame took 245 ms in total. The renderer now supplies changing texture-factor colors as draw uniforms and excludes disabled fixed-function texture stages from shader cache keys. The PC0 software Vulkan run compiled 70 distinct pipelines with zero evictions. One loading frame still spent 382 ms compiling pipelines. All 28 toolkit tests in the `nogame` and `gpu` groups passed.

The follow-up reproduced blurry textures and intermittent HUD rectangles on a copy of the player's profile using Radeon Vulkan. The game requested up to five skipped mip levels and supplied positive sampler LOD biases above seven on several draws. The eXtreme profile now keeps the highest-detail managed mip available and suppresses positive LOD bias while retaining ordinary distance-based mip selection. The test restored road markings, signs, and a readable HUD while driving. Flat-looking water remains visible in some views.

The profile also paces fullscreen immediate presents to the display refresh. The driver benchmark starts windowed and retains immediate presentation. In the first 40 seconds of the two windowed traces on the 60 Hz Radeon setup, the presenter dropped 1,063 frames before pacing and 11 with pacing enabled. The runs reached different gameplay phases at different wall times, and loading and frame-time spikes remain visible.

A Platform session later aborted with `DrawFlush: occlusion query slots are exhausted`. The renderer was retaining GPU slots until the guest read every pending result. It now copies results to separate readback buffers and reuses the GPU slots in submission order. A long query resolves in chunks and combines the counts. A temporary regression check passed on Radeon Vulkan and Lavapipe. It issued 4,101 queries while a prior result remained unread, then verified the count from one query spanning 4,101 draw batches. [Direct3D 9 query lifecycle](https://learn.microsoft.com/en-us/windows/win32/direct3d9/queries)

The EAX audio probe falls back to `CoCreateInstance(CLSID_DirectSound8, IID_IDirectSound8)`. The runtime previously registered the interface with the wrong final byte and returned `E_NOINTERFACE`. After correcting the identifier, the scripted SkidOrDie run mixed game audio. The capture measured 111.3 seconds of nonzero output across 153.3 seconds, peaking at 0.622 of full scale. Speaker playback during the windowed session remains unverified. [DirectSound 8 interface identifier in Wine's header](https://github.com/wine-mirror/wine/blob/master/include/dsound.h#L66)

The saved profile and score files reload. In two tests, Configure driving inputs accepted `P` as a second binding for **Give up**, but the binding showed only `Delete` after relaunch. The second test used the on-screen Back and Quit controls. A selected car also reverted after relaunch in a separate test.

Run the following from the project root for a bounded headless capture. The frames and discovery trace are local working files.

```sh
build_root="$PWD/local/build/tm-sunrise-extreme"
run_dir=$(mktemp -d /tmp/tmsx-run.XXXXXX)
cd "$run_dir"
RECOMP_DISCOVERY="$run_dir/discovery.tsv" RECOMP_MAX_FRAMES=300 \
  SDL_VIDEODRIVER=dummy LIBGL_ALWAYS_SOFTWARE=1 \
  VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.x86_64.json \
  "$build_root/recomp/recomp_headless"
```

---

## 1. Ghidra 12.1.3 Code Map Export (`recomp-code-map-v3`)

Upstream `recomp-toolkit` references `ExportCodeMap.java` in a sibling `ghidra_scripts/` directory that is not shipped inside the `recomp-toolkit` repository. We implemented a format-exact `recomp-code-map-v3` exporter in [`ghidra_scripts/ExportCodeMap.java`](../ghidra_scripts/ExportCodeMap.java) verified against `recomp-toolkit/translator/crates/rk-image/src/code_map.rs`, and ran it headlessly via Ghidra 12.1.3 (`analyzeHeadless` on Temurin JDK 21.0.13.1):

| Target Binary | ImageBase | SHA-256 | Ghidra Functions | Instructions | Jump Tables | Interior Entries | Interpretation |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `TmSunrise.exe` (8.74 MB) | `0x00400000` | `a6820000345824e961e4cee9a88a7fdb8261d890b4eb7bc1f0657a2996ed2d64` | **10** | **171** | 0 | 0 | **StarForce encrypted:** only the 11-byte `.start` stub (`0x00c42000`) is real code; the remaining 9 addresses are encrypted C++ exports inside entropy-8.000 `.sforce3` sections. |
| `TmSunriseLauncher.exe` (1.66 MB) | `0x00400000` | `b09a34121f121eca89ef70055c17f92a1c3657518354d727e01416389dcea63b` | **8,506** | **286,246** | **238** | **977** | Unpacked PE32 from the same disc — confirms `ExportCodeMap.java` recovers functions, switch tables, and interior entries cleanly on real Nadeo/MSVC binaries. |

The exported `TmSunrise.exe` map is stored at [`games/tm-sunrise/metadata/`](../games/tm-sunrise/metadata/).

---

## 2. Static Translation & Desktop Build (`--game-dir`)

```sh
export PATH="$PWD/local/tools/llvm/bin:$PWD/recomp-toolkit/.venv/bin:$PATH"

recomp-toolkit/.venv/bin/python recomp-toolkit/tools/setup.py \
  --game-dir "$PWD/games/tm-sunrise" \
  --build-root "$PWD/local/build/tm-sunrise" \
  --install "$PWD/local/game_install/app"

recomp-toolkit/.venv/bin/python recomp-toolkit/tools/build.py \
  --game-dir "$PWD/games/tm-sunrise" \
  --build-root "$PWD/local/build/tm-sunrise" \
  --regenerate --target headless

recomp-toolkit/.venv/bin/python recomp-toolkit/tools/build.py \
  --game-dir "$PWD/games/tm-sunrise" \
  --build-root "$PWD/local/build/tm-sunrise" \
  --target app
```

### Translation Report Summary (`local/build/tm-sunrise/recomp/translate-report.json`)
- **Engine:** Rust translator (`recomp-translate`), completed in `0.49s`
- **Functions:** 10 mapped, 9 lifted cleanly, 10 bodies emitted, 0 trapping
- **Ciphertext evidence:** The 9 exported addresses inside `.sforce3` produced 1 `decoder_cannot_tile` diagnostic (`0x0063e4e6`) and spurious privileged/legacy opcodes (`IN`, `INSB`, `INSD`, `OUT`, `OUTSB`, `OUTSD`, `CLI`, `INTO`, `LES`, `BOUND`, `LCALL`, `RETF`), confirming they are encrypted ciphertext rather than valid Win32 user-mode code.
- **Desktop artifacts built (local, gitignored):**
  - `local/build/tm-sunrise/recomp/recomp_headless` (with full vendored FFmpeg Bink/AVI/MP3/Ogg support)
  - `local/build/tm-sunrise/recomp/TmSunriseRecomp` + `local/build/tm-sunrise/package/TmSunriseRecomp`

---

## 3. Blocking Failure Trace (Exact Guest Address & Import)

Launching both `local/build/tm-sunrise/recomp/recomp_headless` and the windowed `local/build/tm-sunrise/package/TmSunriseRecomp/TmSunriseRecomp` succeeds through display/GPU initialization (`wgpu`, 60.030 Hz display, `1368x1025` drawable, 3 in-flight submissions), audio mixer & TinySoundFont initialization, Lua 5.4.6 core mod init, PE hash verification, 32-bit guest arena mapping (`0x00400000..0x00cae000`), and guest entry point execution (`0x00c42000`), then stops deterministically at instruction #2:

| Field | Captured Value |
| --- | --- |
| **Module** | `TmSunrise.exe` → `TMSUNRISE.DLL` (`PROTECT.DLL`, StarForce 3.04.071.019) |
| **Guest entry & site** | `0x00c42000`: `push 0x65b2b827` → `0x00c42005`: `jmp dword ptr [0x00c421bc]` |
| **Affected import** | `TMSUNRISE.DLL!ord1` (IAT slot `0x00c421bc`) |
| **Observed runtime diagnostic** | `unsupported import TMSUNRISE.DLL!ord1` (`ESP=0x0effffd8`, `return_address[0]=0x65b2b827`, exit code `6` / `SIGABRT`) |
| **Root cause classification** | **Copy-protection component** (not code map, translator, runtime, or host backend) |
| **JIT fallback (`rk-pcode-ffi`) used?** | **No** — entry stub `0x00c42000` was statically translated (`chunk_00c40000_16.c`) |
| **Reproduction steps** | Run `local/build/tm-sunrise/recomp/recomp_headless` after the setup/build commands above |

---

## 4. Standalone Runtime, ABI & Translator Verification

Because gameplay execution stops at StarForce `TMSUNRISE.DLL!ord1`, we verified the full toolkit runtime, ABI boundary, Direct3D 9 / DirectInput 8 / DirectSound / Bink subsystems, and Cranelift JIT baseline via standalone fixtures on this Linux host:

1. **x86-32 Calling Conventions, 32-bit Pointers, Data Layouts, Flags, x87 & Callbacks (`tools/test.py --translator`):**
   - **29/29 assembly fixtures (5 groups, 200 randomized + structured inputs each) + relocation integration: PASS** against Unicorn x86-32 oracle.
   - Explicitly exercises `call_conventions.s`, `call_frames.s`, `call_indirect_tail.s`, `call_return_adjust.s`, `call_method_fact.s` (COM vtable calls), `cf_jump_table.s`, `stack_pointer_alias.s`, `x87_*`, and `mem_*`.
2. **Direct3D 9, HLSL (`vkd3d-shader`), wgpu Vulkan (Lavapipe), DirectInput 8, DirectSound, Bink, Win32 & SEH:**
   - `d3d9_guest_tests`: **PASS** (32-bit guest COM views, D3D9 device/surface/texture/shader/state-block/present lifecycle on `wgpu`)
   - `dx_tests` (with `RECOMP_VIDEO=ON`): **141,438 / 141,438 checks PASS** (DirectDraw, D3D7/8, DirectInput8, DirectSound, DirectShow, Media Foundation, Bink/Smacker)
   - Live TrackMania Sunrise asset test (`RECOMP_TEST_BINK_CONTAINER=.../GoodMorning.bik,0`): **`Bink open from handle`, `Bink realtime`, and `Bink rects and pause` PASS** decoding the real game `.bik` preview video.
   - `interp_tests`: **PASS** (Cranelift JIT baseline verified independently on Linux `x86_64`).
   - `seh_tests`, `pad_tests`, `controls_tests`, `compositor_tests`, `host_tests`, `headless_tests`, `gpu_wgpu_tests`, `platform_tests`, `entry_dispatch_tests`: **ALL PASS**.

---

## 5. Wine / Hangover Integration Evaluation

- **Decision for current phase:** Retain Recomp Toolkit's native runtime (`runtime/` + `dx/` + `graphics/d3d8-wgpu`).
- **Rationale:**
  1. Static analysis of `TmSunrise.exe`'s 15-DLL import surface shows that **12 of the 14 non-DRM DLLs** (including `D3D9.DLL`, `DINPUT8.DLL`, `DSOUND.DLL`, `BINKW32.DLL`, `KERNEL32.DLL`, `USER32.DLL`, `GDI32.DLL`, `ADVAPI32.DLL`, `OLE32.DLL`, `WINMM.DLL`, `AVIFIL32.DLL`, `WS2_32.DLL`) are already implemented in `recomp-toolkit` and verified passing in our test runs.
  2. The only unimplemented non-DRM DLLs visible so far are `RPCRT4.DLL!UuidCreate` (trivial shim), `WININET.DLL!InternetOpenA` (offline failure stub), and `DSOUND.DLL!ord#12` (`DirectSoundCaptureCreate8`).
  3. Direct Wine / Hangover integration is not justified until an unpacked TrackMania Sunrise eXtreme binary demonstrates a deep Win32/COM subsystem gap that cannot be cleanly bridged in `recomp-toolkit`. Wine source remains the authoritative behavioral reference when implementing any newly observed APIs.

---

## 6. Pending Checks

The active eXtreme profile has a completed SkidOrDie replay, verified steering and respawn, and nonzero race audio in the mixer capture. Remaining work covers the GoodMorning reference track, in-game preference persistence, and the reported rendering and performance issues. The static-only probe currently stops before the loading screen. [Android report](android-report.md)
