#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Restore the official OGKI modversions CRCs of the exported LZ4 symbols inside
a CI-built GKI Image (one table per KMI branch).

Why: the repo's ZRAM patch stack (upgraded LZ4 + lz4k/lz4kd) changes the LZ4
header context, so genksyms emits NEW CRCs for every exported LZ4 symbol.
HyperOS vendor modules (e.g. MTK/Qualcomm node_cache.ko, which imports
LZ4_decompress_safe + LZ4_compress_default) carry the OFFICIAL CRCs and get
rejected:

    node_cache: disagrees about version of symbol LZ4_decompress_safe
    node_cache: Unknown symbol LZ4_decompress_safe (err -22)
    init: Failed to load kernel modules
    Kernel panic - not syncing: Attempted to kill init!

Fix: overwrite the __kcrctab slots of the symbols listed in the branch table
with the official values (KMI-frozen, valid for every sublevel of that branch)
- the same proven approach as the v3 "lz4crc12" build.  MODVERSIONS stays
ENABLED so the vendor modules' vermagic ("modversions" token) keeps matching.
Which symbols exist differs per branch: android14-6.1 exports two, android15-6.6
all twelve of the list below.

Layout facts this relies on (same as crc_restore.py):
  - struct kernel_symbol = 12 bytes {value_offset; name_offset; namespace_offset}
    with PREL32 (s32 relative to the field itself) name pointers;
  - __kcrctab is index-parallel to the ksymtab array: crc slot for entry idx
    sits at ksymtab_base + 12*count + 4*idx (the crc array directly follows).

usage: python3 a17_crc_restore.py <Image>
"""
import struct
import sys

OFFICIAL = {
    b"LZ4_compress_HC":               0xDDF86133,
    b"LZ4_compress_HC_continue":      0x38F7B6E0,
    b"LZ4_compress_default":          0x4F4D78C5,
    b"LZ4_compress_fast":             0x6004858D,
    b"LZ4_compress_fast_continue":    0xF9ECED44,
    b"LZ4_decompress_safe":           0xC7C1107A,
    b"LZ4_decompress_safe_continue":  0x8A47043D,
    b"LZ4_decompress_safe_partial":   0x15BED7A5,
    b"LZ4_loadDict":                  0x749849D8,
    b"LZ4_loadDictHC":                0x93FF008C,
    b"LZ4_resetStreamHC":             0xD25422CD,
    b"LZ4_setStreamDecode":           0x3B321462,
}

# android16-6.12 (KMI android16-5/6) official LZ4 CRCs - read out of a real
# CI-built 6.12.69 Image WITHOUT the zram stack (clean branch-native CRCs,
# device-proven: that exact build boots HyperOS4/A17 vendor modules).
OFFICIAL_612 = {
    b"LZ4_compress_HC":               0x2CF136FA,
    b"LZ4_compress_HC_continue":      0x16AA5F1F,
    b"LZ4_compress_default":          0xE04B6E87,
    b"LZ4_compress_fast":             0x932EDF0D,
    b"LZ4_compress_fast_continue":    0x755C86A3,
    b"LZ4_decompress_safe":           0x7AA9B8BF,
    b"LZ4_decompress_safe_continue":  0x1ADA4747,
    b"LZ4_decompress_safe_partial":   0x1633528F,
    b"LZ4_loadDict":                  0xCAE7EB86,
    b"LZ4_loadDictHC":                0xF4C1D9FC,
    b"LZ4_resetStreamHC":             0x930EF13E,
    b"LZ4_setStreamDecode":           0xB0AC7316,
}

# android14-6.1 (KMI android14-11) official LZ4 CRCs - read out of the real
# Redmi K80 (zorn) stock boot.img (6.1.157-android14-11-g2de7246565ac-mi,
# header v4, ramdisk_size=0).  That KMI exports ONLY these two LZ4 symbols -
# the other ten of the android15-8 list do not exist there - and their values
# equal the android15-8 ones because genksyms hashes the symbol prototype,
# which is unchanged between 6.1 and 6.6.  The extra LZ4 exports that the zram
# (lz4k) stack adds need no restore: vendor modules were built against the
# official KMI and never import them.
OFFICIAL_61 = {
    b"LZ4_compress_default":          0x4F4D78C5,
    b"LZ4_decompress_safe":           0xC7C1107A,
}

TABLES = {
    "6.1": OFFICIAL_61,
    "6.6": OFFICIAL,
    "6.12": OFFICIAL_612,
}


def s32(b, off):
    return struct.unpack_from("<i", b, off)[0]


def u32(b, off):
    return struct.unpack_from("<I", b, off)[0]


def entries_for(b, names):
    """All struct kernel_symbol entries whose PREL32 name field resolves to one
    of `names`.  Single pass over every s32 field; almost all fail the bounds
    check so the scan stays fast even in pure python."""
    import array
    a = array.array("i")
    a.frombytes(b[: len(b) & ~3])
    n = len(a)
    res = []
    for fi in range(n):
        t = fi * 4 + a[fi]
        if t <= 0 or t >= len(b) - 64:
            continue
        if not (0x41 <= b[t] <= 0x5A):
            continue
        end = b.find(b"\0", t, t + 200)
        if end < 0:
            continue
        nm = b[t:end]
        if nm in names:
            res.append((fi * 4 - 4, t, nm))
    return res


def array_of(b, entry, limit=64):
    """Walk +/-12 while the entry still carries a valid PREL32 name field."""
    def valid(e):
        if e < 0 or e + 12 > len(b):
            return False
        f = e + 4
        t = f + s32(b, f)
        if not (0 < t < len(b)):
            return False
        k = t
        while k < len(b) and (chr(b[k]).isalnum() or b[k] == 0x5F):
            k += 1
        if k == t or k - t > 200 or k >= len(b) or b[k] != 0:
            return False
        return True

    base = entry
    while valid(base - 12):
        base -= 12
    end = entry
    while valid(end + 12):
        end += 12
    return base, (end - base) // 12 + 1


def resolve(b, names):
    """Locate the ONE ksymtab array holding all of `names`."""
    names = set(names)
    cands = entries_for(b, names)
    if not cands:
        raise SystemExit("::error::no LZ4 ksymtab entries found in Image")
    groups = {}
    for entry, _name_off, name in cands:
        base, count = array_of(b, entry)
        if count < 100:
            continue
        groups.setdefault((base, count), {}).setdefault(name, []).append(entry)
    for (base, count), members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        found = {}
        for name, ents in members.items():
            ents = [e for e in ents if (e - base) % 12 == 0]
            if ents:
                found[name] = (min(ents), (min(ents) - base) // 12)
        if len(found) == len(names):
            return base, count, found
    raise SystemExit(
        "::error::could not locate a ksymtab array with all %d LZ4 symbols (%s)"
        % (len(names), ", ".join(sorted(n.decode() for n in names)))
    )


def restore(path, table):
    b = open(path, "rb").read()
    print("Image: %d bytes" % len(b))
    names = sorted(table)
    base, count, found = resolve(b, names)
    crc_base = base + 12 * count
    print("  ksymtab array 0x%x  count %d  ->  kcrctab_base 0x%x" % (base, count, crc_base))

    out = bytearray(b)
    changed = 0
    for name in names:
        _e, idx = found[name]
        off = crc_base + 4 * idx
        cur = u32(out, off)
        want = table[name]
        if cur == want:
            print("    %-30s already official 0x%08x" % (name.decode(), cur))
            continue
        struct.pack_into("<I", out, off, want)
        changed += 1
        print("    %-30s 0x%08x -> 0x%08x (official)" % (name.decode(), cur, want))

    if changed == 0:
        print("::notice title=CRC restore::all %d LZ4 CRCs already official, Image unchanged" % len(names))
        return

    open(path, "wb").write(bytes(out))

    # verify with a fresh parse
    nb = open(path, "rb").read()
    _b2, _c2, n_found = resolve(nb, names)
    crc2 = _b2 + 12 * _c2
    bad = [n for n in names if u32(nb, crc2 + 4 * n_found[n][1]) != table[n]]
    if bad:
        raise SystemExit("::error::CRC readback mismatch for %s" % [x.decode() for x in bad])
    print("restored %d/%d LZ4 symbol CRCs to official values (read back OK)" % (changed, len(names)))
    print("::notice title=CRC restore::%d/%d LZ4 symbol CRCs restored to official OGKI values" % (changed, len(names)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: a17_crc_restore.py <Image> <kernel-version, e.g. 6.1|6.6|6.12>")
    img, kv = sys.argv[1], sys.argv[2]
    if kv not in TABLES:
        raise SystemExit("::error::no official CRC table for kernel version %s" % kv)
    restore(img, TABLES[kv])
