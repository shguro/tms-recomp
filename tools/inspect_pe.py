#!/usr/bin/env python3
"""Inspect PE executables/DLLs in a TrackMania Sunrise installation."""
import hashlib
import json
import math
import os
import sys
import pefile


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in counts if c)


def inspect_file(path: str) -> dict:
    info = {"path": path, "size": os.path.getsize(path)}
    with open(path, "rb") as f:
        raw = f.read()
    info["sha256"] = hashlib.sha256(raw).hexdigest()
    try:
        pe = pefile.PE(data=raw)
    except Exception as e:
        info["error"] = str(e)
        return info

    info["machine"] = f"0x{pe.FILE_HEADER.Machine:04x}"
    info["subsystem"] = pe.OPTIONAL_HEADER.Subsystem
    info["timestamp"] = f"0x{pe.FILE_HEADER.TimeDateStamp:08x}"
    info["image_base"] = f"0x{pe.OPTIONAL_HEADER.ImageBase:08x}"
    info["entry_point_rva"] = f"0x{pe.OPTIONAL_HEADER.AddressOfEntryPoint:08x}"
    info["entry_point_va"] = f"0x{pe.OPTIONAL_HEADER.ImageBase + pe.OPTIONAL_HEADER.AddressOfEntryPoint:08x}"
    info["size_of_image"] = f"0x{pe.OPTIONAL_HEADER.SizeOfImage:08x}"

    sections = []
    for s in pe.sections:
        name = s.Name.rstrip(b"\x00").decode("latin1")
        sdata = s.get_data()
        sections.append({
            "name": name,
            "va": f"0x{s.VirtualAddress:08x}",
            "vsize": f"0x{s.Misc_VirtualSize:08x}",
            "raw_offset": f"0x{s.PointerToRawData:08x}",
            "raw_size": f"0x{s.SizeOfRawData:08x}",
            "characteristics": f"0x{s.Characteristics:08x}",
            "entropy": round(shannon_entropy(sdata), 3),
        })
    info["sections"] = sections

    versions = {}
    if hasattr(pe, "FileInfo"):
        for fi in pe.FileInfo:
            for entry in fi:
                if hasattr(entry, "StringTable"):
                    for st in entry.StringTable:
                        for k, v in st.entries.items():
                            versions[k.decode("latin1")] = v.decode("latin1")
    info["version_info"] = versions

    imports = {}
    if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
        for imp in pe.DIRECTORY_ENTRY_IMPORT:
            dll = imp.dll.decode("latin1")
            syms = [
                i.name.decode("latin1") if i.name else f"ord#{i.ordinal}"
                for i in imp.imports
            ]
            imports[dll] = syms
    info["imports"] = imports

    delay_imports = {}
    if hasattr(pe, "DIRECTORY_ENTRY_DELAY_IMPORT"):
        for imp in pe.DIRECTORY_ENTRY_DELAY_IMPORT:
            dll = imp.dll.decode("latin1")
            syms = [
                i.name.decode("latin1") if i.name else f"ord#{i.ordinal}"
                for i in imp.imports
            ]
            delay_imports[dll] = syms
    info["delay_imports"] = delay_imports

    exports = []
    if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
        for e in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            exports.append(e.name.decode("latin1") if e.name else f"ord#{e.ordinal}")
    info["exports"] = exports

    overlay = pe.get_overlay_data_start_offset()
    if overlay is not None:
        info["overlay"] = {"offset": f"0x{overlay:x}", "size": len(raw) - overlay}
    return info


def main():
    paths = sys.argv[1:]
    results = []
    for p in paths:
        res = inspect_file(p)
        results.append(res)
        print("=" * 80)
        print(f"FILE: {res['path']}  SIZE: {res['size']:,} bytes")
        print(f"SHA256: {res['sha256']}")
        if "error" in res:
            print(f"NOT A VALID PE: {res['error']}")
            continue
        print(
            f"Machine: {res['machine']}  Subsystem: {res['subsystem']}  "
            f"Timestamp: {res['timestamp']}"
        )
        print(
            f"ImageBase: {res['image_base']}  EntryRVA: {res['entry_point_rva']}  "
            f"EntryVA: {res['entry_point_va']}  SizeOfImage: {res['size_of_image']}"
        )
        if res["version_info"]:
            print("Version:", res["version_info"])
        print(f"Sections ({len(res['sections'])}):")
        for s in res["sections"]:
            print(
                f"  {s['name']:10s} VA={s['va']} VSize={s['vsize']} "
                f"Raw={s['raw_offset']} RSize={s['raw_size']} "
                f"Chars={s['characteristics']} Ent={s['entropy']:.3f}"
            )
        if res["imports"]:
            total_syms = sum(len(v) for v in res["imports"].values())
            print(f"Imports ({len(res['imports'])} DLLs, {total_syms} symbols):")
            for dll, syms in res["imports"].items():
                preview = ", ".join(syms[:12])
                suffix = f" ... (+{len(syms)-12})" if len(syms) > 12 else ""
                print(f"  {dll} ({len(syms)}): {preview}{suffix}")
        if res["delay_imports"]:
            print(f"Delay Imports ({len(res['delay_imports'])} DLLs):")
            for dll, syms in res["delay_imports"].items():
                print(f"  {dll} ({len(syms)}): {', '.join(syms[:12])}")
        if res["exports"]:
            print(f"Exports ({len(res['exports'])}): {', '.join(res['exports'][:20])}")
        if "overlay" in res:
            print(f"Overlay: offset={res['overlay']['offset']} size={res['overlay']['size']:,} bytes")

    out_json = os.environ.get("INSPECT_JSON_OUT")
    if out_json:
        with open(out_json, "w") as f:
            json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
