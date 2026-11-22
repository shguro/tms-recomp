#include "mslu.h"
#include "runtime/imports.h"

// 0x0040f8fa is Microsoft Layer for Unicode (unicows.lib)'s internal PE export
// directory walker used on Windows NT/XP to resolve native *W APIs from system
// DLL handles (0x60000000+ pseudo-modules in recomp-toolkit). Forward directly
// to KERNEL32.dll!GetProcAddress.
extern "C" void tmsx_mslu_get_proc_address(X86 *c) {
    uint32_t gp = imports_resolve("KERNEL32.dll", "GetProcAddress");
    recomp_call(c, gp);
}
