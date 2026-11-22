// Export a Ghidra program's analyzed code map in recomp-toolkit's recomp-code-map-v3 format.
// Usage (headless or GUI):
//   ExportCodeMap.java <output-dir> <image-base-hex> <executable-sha256> [--data-entries-first]
//@category RecompToolkit

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

public class ExportCodeMap extends GhidraScript {

    private static String hex8(long v) {
        return String.format("%08x", v & 0xffffffffL);
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 3) {
            throw new IllegalArgumentException(
                "Usage: ExportCodeMap.java <out_dir> <image_base> <sha256> [--data-entries-first]");
        }
        Path outDir = Paths.get(args[0]);
        long expectedBase = Long.decode(args[1]);
        String sha256 = args[2].toLowerCase(Locale.ROOT);
        boolean dataEntriesFirst = args.length >= 4 && "--data-entries-first".equals(args[3]);

        if (Files.exists(outDir)) {
            throw new IOException("Refusing to overwrite existing output directory: " + outDir);
        }
        long actualBase = currentProgram.getImageBase().getOffset();
        if (actualBase != expectedBase) {
            throw new IllegalStateException(
                String.format("Image base mismatch: program=0x%08x expected=0x%08x", actualBase, expectedBase));
        }

        Listing listing = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();

        // Collect non-external, non-thunk functions sorted by entry address.
        TreeMap<Long, Function> funcs = new TreeMap<>();
        FunctionIterator fi = fm.getFunctions(true);
        while (fi.hasNext()) {
            Function f = fi.next();
            if (f.isExternal()) continue;
            Address entry = f.getEntryPoint();
            if (!entry.isMemoryAddress()) continue;
            // Ensure at least one instruction exists in the function body.
            InstructionIterator ii = listing.getInstructions(f.getBody(), true);
            if (!ii.hasNext()) continue;
            funcs.put(entry.getOffset(), f);
        }

        // Map every instruction address -> owning function entry.
        HashMap<Long, Long> insnOwner = new HashMap<>();
        TreeMap<Long, List<long[]>> funcSpans = new TreeMap<>();
        TreeMap<Long, List<String>> funcSpanLengths = new TreeMap<>();
        long totalInsns = 0;
        long totalBytes = 0;

        for (Map.Entry<Long, Function> e : funcs.entrySet()) {
            long fnAddr = e.getKey();
            Function f = e.getValue();
            List<long[]> spans = new ArrayList<>();
            List<String> lengths = new ArrayList<>();

            long curStart = -1;
            long curEnd = -1;
            StringBuilder curLens = new StringBuilder();

            InstructionIterator ii = listing.getInstructions(f.getBody(), true);
            while (ii.hasNext()) {
                Instruction insn = ii.next();
                long a = insn.getAddress().getOffset();
                int len = insn.getLength();
                if (len <= 0 || len > 15) continue;
                insnOwner.put(a, fnAddr);
                totalInsns++;
                totalBytes += len;

                if (curStart < 0) {
                    curStart = a;
                    curEnd = a + len;
                    curLens.append(Integer.toHexString(len));
                } else if (a == curEnd) {
                    curEnd += len;
                    curLens.append(Integer.toHexString(len));
                } else {
                    spans.add(new long[]{curStart, curEnd - curStart});
                    lengths.add(curLens.toString());
                    curStart = a;
                    curEnd = a + len;
                    curLens.setLength(0);
                    curLens.append(Integer.toHexString(len));
                }
            }
            if (curStart >= 0) {
                spans.add(new long[]{curStart, curEnd - curStart});
                lengths.add(curLens.toString());
            }
            if (!spans.isEmpty()) {
                funcSpans.put(fnAddr, spans);
                funcSpanLengths.put(fnAddr, lengths);
            }
        }

        // Collect jump tables, interior entries, and noreturn sites.
        TreeMap<String, List<Long>> tables = new TreeMap<>();
        TreeMap<Long, String[]> entries = new TreeMap<>(); // addr -> {ownerHex, kind}
        TreeSet<Long> noreturnFuncs = new TreeSet<>();
        TreeSet<Long> noreturnCalls = new TreeSet<>();

        for (Map.Entry<Long, Function> e : funcs.entrySet()) {
            long fnAddr = e.getKey();
            Function f = e.getValue();
            if (!funcSpans.containsKey(fnAddr)) continue;
            if (f.hasNoReturn()) {
                noreturnFuncs.add(fnAddr);
            }
            InstructionIterator ii = listing.getInstructions(f.getBody(), true);
            while (ii.hasNext()) {
                Instruction insn = ii.next();
                long site = insn.getAddress().getOffset();
                FlowType ft = insn.getFlowType();

                if (ft.isComputed() && ft.isJump()) {
                    TreeSet<Long> targets = new TreeSet<>();
                    for (Reference ref : rm.getReferencesFrom(insn.getAddress())) {
                        if (ref.getReferenceType().isJump() || ref.getReferenceType().isComputed()) {
                            Address to = ref.getToAddress();
                            if (to.isMemoryAddress() && insnOwner.containsKey(to.getOffset())) {
                                targets.add(to.getOffset());
                            }
                        }
                    }
                    if (!targets.isEmpty()) {
                        String key = hex8(fnAddr) + "\t" + hex8(site);
                        tables.put(key, new ArrayList<>(targets));
                        for (long t : targets) {
                            Long owner = insnOwner.get(t);
                            if (owner != null && t != owner) {
                                entries.put(t, new String[]{hex8(owner), "table"});
                            }
                        }
                    }
                }

                if (ft.isCall()) {
                    for (Reference ref : rm.getReferencesFrom(insn.getAddress())) {
                        if (ref.getReferenceType().isCall()) {
                            Function callee = fm.getFunctionAt(ref.getToAddress());
                            if (callee != null && callee.hasNoReturn()) {
                                noreturnCalls.add(site);
                            }
                        }
                    }
                }

                // Cross-function branch targets -> interior "branch" entries.
                if (ft.isJump() && !ft.isComputed()) {
                    for (Reference ref : rm.getReferencesFrom(insn.getAddress())) {
                        if (ref.getReferenceType().isJump()) {
                            long t = ref.getToAddress().getOffset();
                            Long owner = insnOwner.get(t);
                            if (owner != null && owner != fnAddr && t != owner) {
                                entries.putIfAbsent(t, new String[]{hex8(owner), "branch"});
                            }
                        }
                    }
                }
            }
        }

        // Data references to interior instructions.
        for (Map.Entry<Long, Long> e : insnOwner.entrySet()) {
            long a = e.getKey();
            long owner = e.getValue();
            if (a == owner) continue;
            Address addrObj = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(a);
            ReferenceIterator refs = rm.getReferencesTo(addrObj);
            while (refs.hasNext()) {
                Reference r = refs.next();
                if (r.getReferenceType().isData()) {
                    if (dataEntriesFirst) {
                        entries.put(a, new String[]{hex8(owner), "data"});
                    } else {
                        entries.putIfAbsent(a, new String[]{hex8(owner), "data"});
                    }
                    break;
                }
            }
        }

        Files.createDirectories(outDir);

        // 1. metadata.txt
        StringBuilder meta = new StringBuilder();
        meta.append("format=recomp-code-map-v3\n");
        meta.append("status=complete\n");
        meta.append("program=").append(currentProgram.getName()).append("\n");
        meta.append("executable_sha256=").append(sha256).append("\n");
        meta.append("language=").append(currentProgram.getLanguageID().getIdAsString()).append("\n");
        meta.append("image_base=").append(hex8(actualBase)).append("\n");
        meta.append("functions=").append(funcSpans.size()).append("\n");
        meta.append("instructions=").append(totalInsns).append("\n");
        meta.append("instruction_bytes=").append(totalBytes).append("\n");
        Files.writeString(outDir.resolve("metadata.txt"), meta.toString(), StandardCharsets.UTF_8);

        // 2. spans.tsv
        try (BufferedWriter w = Files.newBufferedWriter(outDir.resolve("spans.tsv"), StandardCharsets.UTF_8)) {
            w.write("function\tstart\tbytes\tlengths\n");
            for (Map.Entry<Long, List<long[]>> e : funcSpans.entrySet()) {
                long fnAddr = e.getKey();
                List<long[]> spans = e.getValue();
                List<String> lens = funcSpanLengths.get(fnAddr);
                for (int i = 0; i < spans.size(); i++) {
                    long start = spans.get(i)[0];
                    long sz = spans.get(i)[1];
                    String fnCol = (start == fnAddr) ? "" : hex8(fnAddr);
                    w.write(fnCol + "\t" + hex8(start) + "\t" + sz + "\t" + lens.get(i) + "\n");
                }
            }
        }

        // 3. tables.tsv
        try (BufferedWriter w = Files.newBufferedWriter(outDir.resolve("tables.tsv"), StandardCharsets.UTF_8)) {
            w.write("function\tsite\ttargets\n");
            for (Map.Entry<String, List<Long>> e : tables.entrySet()) {
                StringBuilder sb = new StringBuilder();
                for (int i = 0; i < e.getValue().size(); i++) {
                    if (i > 0) sb.append(',');
                    sb.append(hex8(e.getValue().get(i)));
                }
                w.write(e.getKey() + "\t" + sb + "\n");
            }
        }

        // 4. entries.tsv
        try (BufferedWriter w = Files.newBufferedWriter(outDir.resolve("entries.tsv"), StandardCharsets.UTF_8)) {
            w.write("address\towner\tkind\n");
            for (Map.Entry<Long, String[]> e : entries.entrySet()) {
                w.write(hex8(e.getKey()) + "\t" + e.getValue()[0] + "\t" + e.getValue()[1] + "\n");
            }
        }

        // 5. noreturn.tsv
        try (BufferedWriter w = Files.newBufferedWriter(outDir.resolve("noreturn.tsv"), StandardCharsets.UTF_8)) {
            w.write("address\tkind\n");
            for (long a : noreturnFuncs) {
                w.write(hex8(a) + "\tfunction\n");
            }
            for (long a : noreturnCalls) {
                w.write(hex8(a) + "\tcall\n");
            }
        }

        println(String.format(
            "Exported recomp-code-map-v3 to %s: %d functions, %d instructions, %d tables, %d interior entries",
            outDir, funcSpans.size(), totalInsns, tables.size(), entries.size()));
    }
}
