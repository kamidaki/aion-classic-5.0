import struct, re, sys

class PE:
    def __init__(self, path):
        self.data = d = open(path,'rb').read()
        e_lfanew = struct.unpack_from('<I', d, 0x3C)[0]
        assert d[e_lfanew:e_lfanew+4] == b'PE\0\0', "not PE"
        coff = e_lfanew + 4
        self.machine, self.nsec, _, _, _, self.optsize, self.chars = struct.unpack_from('<HHIIIHH', d, coff)
        opt = coff + 20
        magic = struct.unpack_from('<H', d, opt)[0]
        self.pe32plus = (magic == 0x20b)
        self.imagebase = struct.unpack_from('<Q', d, opt+24)[0] if self.pe32plus else struct.unpack_from('<I', d, opt+28)[0]
        sec = opt + self.optsize
        self.sections = []
        for i in range(self.nsec):
            off = sec + i*40
            name = d[off:off+8].rstrip(b'\0').decode(errors='replace')
            vsize, vaddr, rawsize, rawptr = struct.unpack_from('<IIII', d, off+8)
            self.sections.append(dict(name=name, vaddr=vaddr, vsize=vsize, rawptr=rawptr, rawsize=rawsize))

    def off2rva(self, off):
        for s in self.sections:
            if s['rawptr'] <= off < s['rawptr'] + s['rawsize']:
                return s['vaddr'] + (off - s['rawptr'])
        return None

    def rva2off(self, rva):
        for s in self.sections:
            if s['vaddr'] <= rva < s['vaddr'] + max(s['vsize'], s['rawsize']):
                o = s['rawptr'] + (rva - s['vaddr'])
                if o < s['rawptr'] + s['rawsize']:
                    return o
        return None

    def sec_of_rva(self, rva):
        for s in self.sections:
            if s['vaddr'] <= rva < s['vaddr'] + max(s['vsize'], s['rawsize']):
                return s['name']
        return None

if __name__ == '__main__':
    pe = PE(sys.argv[1])
    print(f"PE32+={pe.pe32plus} ImageBase=0x{pe.imagebase:x} sections={pe.nsec}")
    for s in pe.sections:
        print(f"  {s['name']:<9} vaddr=0x{s['vaddr']:08x} vsize=0x{s['vsize']:08x} rawptr=0x{s['rawptr']:08x} rawsize=0x{s['rawsize']:08x}")
