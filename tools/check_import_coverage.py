#!/usr/bin/env python3
"""Compare PE imports against recomp-toolkit's registered shims."""
import json
import os
import re
import sys
from pathlib import Path
import pefile


def collect_toolkit_shims(toolkit_root: Path) -> tuple[dict[str, dict[str, str]], set[str]]:
    """Scan runtime/ and dx/ for ImportShim table entries and registered DLLs."""
    # Map lowercase_dll -> {lowercase_symbol: status ("implemented" | "unsupported")}
    shims: dict[str, dict[str, str]] = {}
    dlls_seen: set[str] = set()

    # Match {"DLL.dll", "FuncName", handler_fn, argc}
    entry_re = re.compile(
        r'\{\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*([A-Za-z0-9_:&]+)\s*,',
    )
    # Match macros like SHIM("KERNEL32.dll", "Foo", ...) or IMP(...)
    # Also scan runtime/ and dx/ .cpp/.h/.inc files
    scan_dirs = [toolkit_root / "runtime", toolkit_root / "dx"]
    for d in scan_dirs:
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if p.suffix not in (".cpp", ".h", ".inc", ".c"):
                continue
            if "tests" in p.parts:
                continue
            text = p.read_text(errors="ignore")
            for m in entry_re.finditer(text):
                dll, sym, handler = m.group(1), m.group(2), m.group(3)
                dl = dll.lower()
                if not (dl.endswith(".dll") or dl.endswith(".drv") or dl.endswith(".exe")):
                    continue
                dlls_seen.add(dl)
                status = "unsupported_stub" if "unsupported" in handler.lower() else "implemented"
                shims.setdefault(dl, {})[sym.lower()] = status

    # Also check imports_register_data("dll", "sym", ...)
    data_re = re.compile(r'imports_register_data\(\s*"([^"]+)"\s*,\s*"([^"]+)"')
    for d in scan_dirs:
        for p in sorted(d.rglob("*.cpp")):
            if "tests" in p.parts:
                continue
            for m in data_re.finditer(p.read_text(errors="ignore")):
                dl = m.group(1).lower()
                dlls_seen.add(dl)
                shims.setdefault(dl, {})[m.group(2).lower()] = "implemented_data"

    # Also check wide auto-generated / helper registrations in kernel32_wide / user32_wide / d3dx9
    # Check d3d9/dinput/dsound/bink specific registration helpers
    bink_re = re.compile(r'BINK_SHIM\(\s*"?([^",\)]+)"?')
    bink_cpp = toolkit_root / "dx" / "bink.cpp"
    if bink_cpp.exists():
        for m in bink_re.finditer(bink_cpp.read_text(errors="ignore")):
            shims.setdefault("binkw32.dll", {})[m.group(1).lower()] = "implemented"

    # Check if DSOUND ordinal #12 or similar is handled
    dsound_cpp = toolkit_root / "dx" / "dsound.cpp"
    if dsound_cpp.exists():
        txt = dsound_cpp.read_text(errors="ignore")
        for m in re.finditer(r'"(ord#\d+|#\d+)"', txt):
            shims.setdefault("dsound.dll", {})[m.group(1).lower()] = "implemented"

    return shims, dlls_seen


def analyze_pe_coverage(pe_path: Path, shims: dict[str, dict[str, str]]) -> dict:
    pe = pefile.PE(str(pe_path))
    report = {
        "file": pe_path.name,
        "path": str(pe_path),
        "dlls": {},
        "summary": {"total": 0, "implemented": 0, "unsupported_stub": 0, "missing": 0},
    }
    if not hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
        return report
    for imp in pe.DIRECTORY_ENTRY_IMPORT:
        dll = imp.dll.decode("latin1")
        dl = dll.lower()
        dll_shims = shims.get(dl, {})
        dll_entry = {"dll_registered": dl in shims, "implemented": [], "unsupported_stub": [], "missing": []}
        for sym in imp.imports:
            name = sym.name.decode("latin1") if sym.name else f"#{sym.ordinal}"
            key = name.lower()
            alt_key = f"ord#{sym.ordinal}" if not sym.name else key
            status = dll_shims.get(key) or dll_shims.get(alt_key)
            # Also check without leading underscore / stdcall @N suffix for Bink
            if not status and dl == "binkw32.dll":
                for k, v in dll_shims.items():
                    if k == key:
                        status = v
                        break
            report["summary"]["total"] += 1
            if status in ("implemented", "implemented_data"):
                dll_entry["implemented"].append(name)
                report["summary"]["implemented"] += 1
            elif status == "unsupported_stub":
                dll_entry["unsupported_stub"].append(name)
                report["summary"]["unsupported_stub"] += 1
            else:
                dll_entry["missing"].append(name)
                report["summary"]["missing"] += 1
        report["dlls"][dll] = dll_entry
    return report


def main():
    toolkit_root = Path(sys.argv[1])
    pe_paths = [Path(p) for p in sys.argv[2:]]
    shims, dlls = collect_toolkit_shims(toolkit_root)
    print(f"Scanned recomp-toolkit shims: {len(dlls)} DLLs, {sum(len(v) for v in shims.values())} symbols")
    print("Registered DLLs:", ", ".join(sorted(dlls)))

    all_reports = []
    for pe_path in pe_paths:
        rep = analyze_pe_coverage(pe_path, shims)
        all_reports.append(rep)
        s = rep["summary"]
        print("\n" + "=" * 80)
        print(f"TARGET: {rep['file']}  (Total={s['total']}, Implemented={s['implemented']}, "
              f"UnsupportedStub={s['unsupported_stub']}, Missing={s['missing']})")
        for dll, info in rep["dlls"].items():
            tag = "DLL-KNOWN" if info["dll_registered"] else "DLL-UNKNOWN"
            print(f"  {dll} [{tag}]: {len(info['implemented'])} impl, "
                  f"{len(info['unsupported_stub'])} stub, {len(info['missing'])} missing")
            if info["unsupported_stub"]:
                print(f"    STUB:    {', '.join(info['unsupported_stub'])}")
            if info["missing"]:
                print(f"    MISSING: {', '.join(info['missing'])}")

    out_json = os.environ.get("COVERAGE_JSON_OUT")
    if out_json:
        with open(out_json, "w") as f:
            json.dump(all_reports, f, indent=2)


if __name__ == "__main__":
    main()
