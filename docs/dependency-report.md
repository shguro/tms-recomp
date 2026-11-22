# TrackMania Sunrise — Version-Specific Dependency Report

**Milestone 2 deliverable.** Produced via static PE analysis (`tools/inspect_pe.py`), Capstone disassembly of the entry stub, Ghidra 12.1.3 headless analysis (`ghidra_scripts/ExportCodeMap.java`), and automated cross-referencing against Recomp Toolkit's shim registry (`tools/check_import_coverage.py`) at pinned commit `05392effc17c354a7315fd0102d2a304925be80d`.

## Active target, eXtreme 0.1.5.0

| Field | Observed value |
| --- | --- |
| Local executable | `local/tmsx_install/TMSX/TmSunrise.exe` |
| Size and SHA-256 | 7,904,768 bytes, `e59dfc7eaa5314e85b2b0df6f40ef7ba01a23bd5a9525f84407f5dff301df4fe` |
| PE layout | PE32 i386, four sections, image base `0x00400000`, entry `0x0040259a`, image end `0x00bde000` |
| Static imports | 252 across 16 DLLs, with no StarForce import |
| Graphics | `Direct3DCreate9` is provided by the toolkit. D3DX 9.2 is statically linked in the executable. |
| Sound | `dsound.dll` ordinal 12 resolves to the capture shim. Playback uses the registered DirectSound 8 COM class after an optional EAX probe. WinMM loads WAV effects. |

The static scanner reported 197 recognized imports and 55 unmatched entries. Manual registry inspection accounted for 24 scanner misses across Bink, DirectSound ordinal 12, OleAut, and User32. The remaining 31 are 14 `m4d.dll` ad-client imports, 13 `avifil32.dll` imports, `ReadFileEx`, `WriteFileEx`, `CancelIo`, and `SetClipboardData`. Static registration measures symbol availability. The Linux run exercised dynamic Unicode resolution, D3D9 presentation, WinMM RIFF parsing, and Bink playback. SkidOrDie finished with no unsupported import abort, and a later run captured game audio after fixing the DirectSound 8 interface identifier. The test covers the offline Solo path. [Desktop report](desktop-report.md)

---

## 1. Supplied Media & Edition Verification

| Field | Observed Value |
| --- | --- |
| Source image | `TMSunrise/TM-Sunrise.iso` (713,338,880 bytes, ISO 9660 volume `TMSUNRISE`) |
| Embedded installer | `TMSUNRIS.EXE` (531,070,585 bytes, SHA-256 `32915279f744b68b4ab545890cd10b3d22a1c66afc08c6389f73f9ea35b2169b`, Inno Setup 5.0.4) |
| Installer product title | **TrackMania Sunrise 1.4.6** (May 2005 English retail CD-ROM) |
| Assignment target edition | **TrackMania Sunrise eXtreme** (1.5.x expansion, Nov 2005) — **NOT present in supplied ISO** |
| Copy protection | **StarForce 3.04.071.019** (`tmsunrise.dll` / `PROTECT.DLL`, BuildSignature `3.04.071.019, 15.03.05`) |

> **Key finding:** There are two independent blockers on the supplied disc image:
> 1. **Edition mismatch:** The supplied ISO is base **TrackMania Sunrise 1.4.6**, not **TrackMania Sunrise eXtreme**.
> 2. **Copy-protection encryption:** `TmSunrise.exe` and `tmsunrise.dat` are encrypted with StarForce 3.04.071.019. As specified in the assignment plan, copy protection was **not** bypassed; the exact stopping point is documented below and standalone runtime/translator verification was continued in parallel.

---

## 2. Binary Inventory (Game vs. Installer, Launcher, and Auxiliary Modules)

| File | Role | Size (bytes) | SHA-256 | Arch / Subsys | ImageBase | Entry VA | Packed / Protected? |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| `TmSunrise.exe` | **Target game executable** | 8,742,980 | `a6820000345824e961e4cee9a88a7fdb8261d890b4eb7bc1f0657a2996ed2d64` | PE32 i386 / GUI | `0x00400000` | `0x00c42000` | **Yes — StarForce 3.04 (.sforce3, ent 7.95–8.00)** |
| `tmsunrise.dll` | **StarForce protection library (`PROTECT.DLL` 3.04.071.019)** | 19,357,005 | `c5aac0472e6f81e5006ba481b2e0583a21c84e70c1478cf559a0f2fe17449b1e` | PE32 i386 / GUI | `0x00400000` | `0x017dab6e` | **Yes — StarForce VM + 19.07 MB overlay** |
| `tmsunrise.dat` | **Encrypted game archive** | 134,668,312 | `ad8abf5f5ee34403c6e15ca912485ab4c3e75c04b698c0f969f635e9bcbbf9ad` | Data blob | N/A | N/A | **Yes — first-1MiB entropy 7.9998** |
| `TmSunriseLauncher.exe` | Configuration & update launcher (`Launcher.EXE` 1.0.0.1, MFC) | 1,667,072 | `b09a34121f121eca89ef70055c17f92a1c3657518354d727e01416389dcea63b` | PE32 i386 / GUI | `0x00400000` | `0x004d6bd0` | No (standard `.text` ent 6.535) |
| `binkw32.dll` | RAD Video Tools 1.7d (Bink video playback) | 338,944 | `c6c06e2d21f2179f0b7fbe829a4b17a7b371440d2c679253ec86b64d421185bd` | PE32 i386 / GUI | `0x18000000` | `0x18005fab` | No (86 Bink exports; replaced by toolkit `dx/bink.cpp`) |
| `unicows.dll` | Microsoft Layer for Unicode 1.0.4018.0 (Win9x shim) | 245,408 | `22f23cc65698741184ec34f46e6f69717644e0b5aabf5d5bd015101f2d72e56e` | PE32 i386 / CUI | `0x7f2d0000` | `0x7f2de153` | No (Win9x compatibility layer only) |
| `CDAUTORU.EXE` | Disc autorun utility (on ISO root) | 36,864 | `833f30eab3ab9532fa883606ee50f0b3d1344d71823c98b91490bc8ed37f7560` | PE32 i386 / GUI | `0x00400000` | `0x004011f7` | No |
| `TMSUNRIS.EXE` | Inno Setup 5.0.4 installer (on ISO root) | 531,070,585 | `32915279f744b68b4ab545890cd10b3d22a1c66afc08c6389f73f9ea35b2169b` | PE32 i386 / GUI | `0x00400000` | `0x00409408` | Installer archive (extracted via `innoextract 1.9`) |

---

## 3. Target Executable (`TmSunrise.exe`) Structural & Copy-Protection Analysis

### Section Layout (`SizeOfImage = 0x008ae000`)

| Section | Virtual Address | Virtual Size | Raw Offset | Raw Size | Characteristics | Shannon Entropy | Assessment |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| `.sforce3` | `0x00001000` | `0x00732000` | `0x00000400` | `0x00732000` | `0x60000040` | **8.000** | Encrypted main code/read-only data (7.54 MiB) |
| `.RDATA` | `0x00733000` | `0x00000c91` | `0x00732400` | `0x00000c91` | `0xe0000040` | 2.020 | Minimal unencrypted metadata / export directory |
| `.sforce3` | `0x00734000` | `0x0010c000` | `0x00733200` | `0x0010c000` | `0xe0000040` | **7.995** | Encrypted data/code (1.09 MiB) |
| `.RSRC` | `0x00840000` | `0x00000e7c` | `0x0083f200` | `0x00000e7c` | `0xe0000040` | 6.446 | Minimal Win32 resources (icon/manifest) |
| `.sforce3` | `0x00841000` | `0x00001000` | `0x00840200` | `0x00001000` | `0xe0000040` | **7.950** | Encrypted stub page |
| `.start` | `0x00842000` | `0x00001000` | `0x00841200` | `0x00001000` | `0xe0000020` | 1.209 | **Unencrypted 11-byte StarForce entry stub + stub IAT** |
| `.sforce3` | `0x00843000` | `0x000143c0` | `0x00842200` | `0x000143c0` | `0xe0000040` | **7.998** | Encrypted StarForce payload |
| `.idata` | `0x00858000` | `0x00000014` | `0x00856600` | `0x00000014` | `0xe0000040` | 1.657 | Minimal descriptor |
| `.brick` | `0x00859000` | `0x00055000` | `0x00000000` | `0x00000000` | `0xe0000040` | 0.000 | Uninitialized runtime buffer (340 KiB) |

### Entry Point Stub Disassembly (`0x00c42000`)

```asm
0x00c42000: 68 27 b8 b2 65       push 0x65b2b827
0x00c42005: ff 25 bc 21 c4 00    jmp  dword ptr [0x00c421bc]  ; -> TMSUNRISE.DLL!ord#1
```

There are only **11 bytes of unencrypted x86 instructions** at the executable entry point. Execution immediately jumps into `TMSUNRISE.DLL!ord#1` (`PROTECT.DLL`, StarForce 3.04.071.019), which depends on Windows Service Control Manager APIs (`OpenSCManagerA`, `CreateServiceA`, `StartServiceA`, `DeviceIoControl`) and `SETUPAPI.dll!SetupDiGetClassDevsA` to communicate with kernel-mode drivers (`sfsync03.sys`, `sfhlp02.sys`, `sfdrv01.sys`).

### Exported StarForce-Crypted C++ Functions in `TmSunrise.exe`

The PE export table exposes 9 mangled C++ symbols whose suffixes confirm StarForce FrontLine "Crypted Functions" integration at compile/link time (note also `CPlugFilePHlsl` / `CPlugFileVHlsl`, confirming **Direct3D 9 HLSL pixel/vertex shader** usage):

- `?AddDemoChallenges_CryptMax@CConstructionGame@@QAAXXZ`
- `?ApplyFidParameter_Crypted@CPlugFilePHlsl@@IAAXABUSParam_Id@CSystemFidParameters@@@Z`
- `?ApplyFidParameter_Crypted@CPlugFileVHlsl@@IAAXABUSParam_Id@CSystemFidParameters@@@Z`
- `?ArchiveOld1@SParam@CSceneFxColors@@QAAXAAVCClassicArchive@@@Z`
- `?CryptedCheckLimitedBlock@CConstructionChallenge@@QAAXPAVCConstructionBlock@@@Z`
- `?CryptedCheckLimitedChallenge@CConstructionChallenge@@QAAXXZ`
- `?MenuMultiPlayer_CryptSfNormal@CTrackManiaMenus@@AAAXPAVCControlContainer@@@Z`
- `?MenuProfile_CryptSfNormal@CTrackManiaMenus@@AAAXPAVCControlContainer@@@Z`
- `?MenuReplayEditor_CryptedConnect@CTrackManiaMenus@@AAAXPAVCControlContainer@@@Z`

---

## 4. Import Inventory vs. Recomp Toolkit Coverage

Static import scan across `recomp-toolkit/runtime/` and `recomp-toolkit/dx/` identified **60 registered DLLs / 1,254+ registered shims** (plus macro-registered Bink/Smacker entries in `dx/bink.cpp`).

### A. `TmSunrise.exe` Visible Stub Imports (15 DLLs, 1 placeholder import per DLL)

Because StarForce strips the real IAT and leaves one representative symbol per linked DLL so the Windows loader maps each DLL, this table proves the exact **DLL dependency surface** of the underlying engine (while hiding exact per-DLL symbol counts until an unpacked binary is available):

| Imported DLL | Visible Stub Symbol (Static) | Toolkit DLL Support | Visible Symbol Covered? | Priority / Notes |
| --- | --- | --- | --- | --- |
| `KERNEL32.DLL` | `Sleep` | Supported (`runtime/kernel32*.cpp`) | **Yes** | Core Win32 runtime |
| `USER32.DLL` | `GetDC` | Supported (`runtime/user32*.cpp`) | **Yes** | Windowing & message loop |
| `GDI32.DLL` | `DeleteDC` | Supported (`runtime/gdi32*.cpp`) | **Yes** | GDI font/surface helpers |
| `ADVAPI32.DLL` | `RegOpenKeyA` | Supported (`runtime/misc_dlls.cpp`) | **Yes** | Registry settings |
| `OLE32.DLL` | `CoInitialize` | Supported (`dx/com.cpp`) | **Yes** | COM initialization |
| `D3D9.DLL` | `Direct3DCreate9` | Supported (`dx/d3d9.cpp` + Rust `wgpu` + `vkd3d-shader`) | **Yes** | Primary renderer (DX9.0b + HLSL) |
| `DINPUT8.DLL` | `DirectInput8Create` | Supported (`dx/dinput.cpp` + `dinput_joystick.cpp`) | **Yes** | Keyboard / mouse / gamepad input |
| `DSOUND.DLL` | `ord#12` (`DirectSoundCaptureCreate8`) | Supported (`dx/dsound.cpp`) | **Gap** (`ord1,2,6,7,9,11` implemented; `ord12` missing) | Medium — audio capture (voice/mic) vs playback (`DirectSoundCreate8` = `ord11` is covered) |
| `BINKW32.DLL` | `_BinkOpen@8` | Supported (`dx/bink.cpp` via FFmpeg Bink demuxer/decoder) | **Yes** (macro-registered in `g_video_shims`) | Used for intro & 31 `.bik` track previews |
| `WINMM.DLL` | `mmioRead` | Supported (`runtime/misc_dlls.cpp`, `dx/waveout.cpp`) | **Yes** | Multimedia timers / RIFF I/O |
| `AVIFIL32.DLL` | `AVIFileInit` | Supported (`dx/avi.cpp`) | **Yes** | Replay/video export (non-critical for M1) |
| `WS2_32.DLL` | `WSACleanup` | Supported (`runtime/misc_dlls.cpp`, offline declined) | **Yes** | Networking (explicitly out of scope for offline M1) |
| `WININET.DLL` | `InternetOpenA` | **Not registered** | **Gap** | Low — online updates/news; can return offline failure on non-essential paths |
| `RPCRT4.DLL` | `UuidCreate` | **Not registered** | **Gap** | Medium — likely used for profile/replay/challenge GUIDs; trivial deterministic/random UUID shim |
| `TMSUNRISE.DLL` | `ord#1` | **Copy protection (`PROTECT.DLL`)** | **Blocker (by design)** | StarForce 3.04 entry — requires DRM-free/unpacked authorized binary |

### B. `TmSunriseLauncher.exe` (Unpacked MFC Configuration Launcher — 11 DLLs, 264 symbols)

| DLL | Total | Covered | Missing | Notes |
| --- | ---: | ---: | ---: | --- |
| `d3d9.dll` | 1 | 1 | 0 | `Direct3DCreate9` (GPU/mode probing) |
| `KERNEL32.dll` | 116 | 102 | 14 | `GetWindowsDirectoryA`, `lstrcmpA`, `lstrcmpiA`, `FindResourceA`, `ReadFileEx`, `WriteFileEx`, etc. |
| `USER32.dll` | 84 | 34 | 50 | MFC dialog/menu/caret/hook APIs (`DefDlgProcA`, `SendDlgItemMessageA`, `SetTimer`, etc.) |
| `GDI32.dll` | 30 | 8 | 22 | MFC dialog painting (`BitBlt`, `ExtTextOutA`, `CreateSolidBrush`, `GetStockObject`, etc.) |
| `WS2_32.dll` | 14 | 14 | 0 | Fully covered |
| `WININET.dll` | 10 | 0 | 10 | Online update checker (`HttpOpenRequestA`, `InternetOpenA`, etc.) |
| `WINMM.dll` | 4 | 4 | 0 | Fully covered |
| `COMCTL32.dll` | 2 | 0 | 2 | `ImageList_Destroy`, `#17` (`InitCommonControls`) |
| `ADVAPI32.dll` | 1 | 1 | 0 | `RegCloseKey` |
| `SHELL32.dll` | 1 | 0 | 1 | `ShellExecuteExA` (launches `TmSunrise.exe`) |
| `WINSPOOL.DRV` | 1 | 1 | 0 | `ClosePrinter` |

*Note:* The launcher is NOT required to reach gameplay; Recomp Toolkit provides its own `--configure` UI and invokes `TmSunrise.exe` directly.

### C. `tmsunrise.dll` (`PROTECT.DLL` StarForce 3.04.071.019 — 6 DLLs, 175 symbols)

`tmsunrise.dll` imports 12 Windows Service Control Manager / privilege APIs from `ADVAPI32.dll` (`OpenSCManagerA`, `CreateServiceA`, `StartServiceA`, `ControlService`, `DeleteService`, `ChangeServiceConfigA`, `QueryServiceConfigA`, `OpenProcessToken`, `LookupPrivilegeValueA`, `AdjustTokenPrivileges`), `KERNEL32.dll!DeviceIoControl`, and `SETUPAPI.dll!SetupDiGetClassDevsA` specifically to install and query the StarForce ring-0 drivers. None of these are implementable or desirable in a portable static recompilation runtime.

### D. `binkw32.dll` (RAD Video Tools 1.7d)

`binkw32.dll` does **not** need static translation: Recomp Toolkit intercepts `binkw32.dll` calls natively in `dx/bink.cpp` backed by vendored FFmpeg's Bink demuxer/decoder (`--enable-demuxer=bink`, verified compiled in our Linux desktop build).

---

## 5. Local Asset & Reference Track Inventory

Extracted `GameData/` contains 2,199 files across:
- **1,134 `.gbx`** Nadeo engine objects (blocks, vehicles, campaigns, challenges, replays, textures)
- **665 `.dds`**, **159 `.tga`** textures
- **110 `.wav`**, **17 `.ogg`** audio assets (confirms Vorbis/PCM audio decoding inside the game executable or OpenAL/DirectSound pipeline)
- **31 `.bik`** Bink preview videos
- **81 `.zip`** skin/ad archives
- **1 `.txt`** (`GfxDevicePerfs.txt`), **1 `.mo`** (`en.mo`)

**Candidate Reference Track (single-player offline milestone):**
- `GameData/Tracks/Campaigns/Nadeo/Sunrise/Race/Holidays/GoodMorning.Challenge.Gbx` (9,619 bytes, paired with `GoodMorning.bik` and `GoodMorning.Replay.gbx`).

---

## 6. Confirmed Findings & Open Questions

### Confirmed Findings
1. Target game uses **Direct3D 9** (`D3D9.DLL`, DirectX 9.0b redist on disc, `CPlugFilePHlsl`/`CPlugFileVHlsl` HLSL shaders), **DirectInput 8** (`DINPUT8.DLL`), **DirectSound** (`DSOUND.DLL`), **Bink 1.7d** (`BINKW32.DLL`), **WinMM** (`WINMM.DLL`), **AVIFile** (`AVIFIL32.DLL`), **Winsock2** (`WS2_32.DLL`), **WinINet** (`WININET.DLL`), and **RPC** (`RPCRT4.DLL`).
2. `TmSunrise.exe` in the supplied ISO is **TrackMania Sunrise 1.4.6** encrypted by **StarForce 3.04.071.019**, halting execution at instruction #2 (`0x00c42005: jmp dword ptr [0x00c421bc]` → `TMSUNRISE.DLL!ord#1`).
3. `tmsunrise.dat` (134.67 MiB) is also StarForce-encrypted (entropy `7.9998`); it is opened/decrypted by the protection layer at runtime.
4. `recomp-toolkit` already has deep D3D9 + vkd3d-shader HLSL + DirectInput8 + DirectSound + Bink (FFmpeg) coverage.

### Open Questions (Pending Unpacked Authorized TrackMania Sunrise eXtreme Executable)
1. **Full real IAT symbol list:** What exact `KERNEL32`, `USER32`, `D3D9`, `D3DX9`, `DINPUT8`, `DSOUND`, `WININET`, `RPCRT4`, and dynamically loaded (`LoadLibrary`/`GetProcAddress`) symbols does the unpacked eXtreme executable call on startup, menu, and race paths?
2. **Dynamic `D3DX9` / shader compiler usage:** Does the game ship precompiled shader bytecode inside `.gbx` / `.dat` or call `d3dx9_*.dll` (`D3DXCompileShader` / `D3DXAssembleShader`) at runtime? (Recomp Toolkit already supports `d3dx9_26`/`27`/`30`/`33` + vkd3d-shader 2.1.)
3. **Audio backend:** Does the unpacked engine stream `.ogg` music through DirectSound (`IDirectSoundBuffer8` + `IDirectSoundNotify`) or OpenAL (`OpenAL32.dll`, which is NOT in the stub IAT, strongly suggesting software Vorbis decode into DirectSound)?
4. **Runtime-generated / self-modifying code:** Does the unpacked eXtreme engine emit any heap code (requiring Cranelift baseline / reloc manifest), or is all gameplay code purely static `.text`?
5. **Working Windows installation trace:** No Windows host was available in this environment to capture live `LoadLibrary` / Process Monitor logs; once an unpacked eXtreme copy is supplied, runtime import tracing (`RECOMP_TRACE` / `RECOMP_OBSERVE`) will immediately enumerate every called symbol on the executed path.
