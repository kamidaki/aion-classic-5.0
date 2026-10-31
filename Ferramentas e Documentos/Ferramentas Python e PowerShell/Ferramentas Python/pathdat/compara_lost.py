"""Leitura do NativePathMap (Lost Academy) reproduzida em Python x pathdat_50, contra pontos oficiais de chão."""
import sys, pickle, struct, collections, math
from pathdat_50 import PathDat
def lost(M, x, y):
    """[(z, livre)] como o NativePathSector.findBestLayer/getZ/isWalkable vê a célula."""
    f=M.f; s=(int(x)//16*16,int(y)//16*16); i=(int((y-s[1])/.5))*32+int((x-s[0])/.5)
    ter=M.ter.z(x,y); out=[]
    for c in M.cam.get(s,[]):
        if c[0]==16: continue                      # tipo 16 ignorado; bloco 1 pulado
        t,a=c; d=a+6                               # Lost: [tipo][sub][int elev] e os dados logo depois (real: +18)
        base=float('nan'); blk=None; sub=None
        if t in (6,7): blk=[(f[d+(j>>3)]>>(j&7))&1 for j in (i,)][0]
        elif t in (8,9):
            v=(f[d+8+(i>>2)]>>((i&3)*2))&3; blk=1 if v==3 else 0
        elif t in (10,11):
            b=f[d+56+(i>>1)]; v=(b>>4) if i&1 else b&15; blk=1 if v==15 else 0
        elif t in (12,13):
            e=struct.unpack_from("<i",f,d)[0]; base=e/100 if 100<abs(e)<5e6 else base
            v=f[d+4+i]; blk=1 if v==0xFF else 0; sub=-1 if v==0xFF else -2 if v==0xFE else v
        elif t in (14,15):
            e=struct.unpack_from("<i",f,d)[0]; base=e/100 if 100<abs(e)<5e6 else base
            w=struct.unpack_from("<H",f,d+4+2*i)[0]; blk=1 if w==0xFFFF else 0; sub=-1 if w==0xFFFF else -2 if w==0xFFFE else struct.unpack("<h",struct.pack("<H",w))[0]
        if sub is not None and sub not in (-1,-2) and abs(sub)<32000:
            z=base+sub/100 if not math.isnan(base) else ter+sub/100
        elif not math.isnan(base): z=base
        else: z=ter
        out.append((z, not blk))
    if not M.cam.get(s): out.append((ter,True))
    return out
def main():
    T=pickle.load(open(sys.argv[1],"rb"))
    OK={0xe0,0xe2,0xe4,0xe8,0xea,0x00,-1}
    pts=collections.defaultdict(set)
    for mm,o,mask,x,y,z in T:
        if mask in OK and z>1: pts[mm].add((x,y,z))
    tot=collections.Counter()
    for m in (800090000,800040000,210010000,220070000,120010000,220010000,110010000,220030000,210050000,210040000):
        M=PathDat(m); r=collections.Counter()
        for x,y,z in pts[m]:
            if not(0<=x<M.tam and 0<=y<M.tam): continue
            b=[q for q in M.pisos(x,y) if abs(q[0]-z)<0.15]
            if not b: continue
            L=lost(M,x,y)
            r['sem chão' if not L else 'livre' if any(q[1] for q in L) else 'bloqueado']+=1
            if b[0][2]==16: r['ponto em nó tipo 16 (Lost ignora)']+=1
        n=r['sem chão']+r['bloqueado']+r['livre']; tot+=r
        print(m,n,{k:f"{100*v/n:.1f}%" for k,v in r.items()},flush=True)
    n=tot['sem chão']+tot['bloqueado']+tot['livre']
    print("TOTAL",n,{k:f"{100*v/n:.1f}%" for k,v in tot.items()})
if __name__=="__main__":
    main()
