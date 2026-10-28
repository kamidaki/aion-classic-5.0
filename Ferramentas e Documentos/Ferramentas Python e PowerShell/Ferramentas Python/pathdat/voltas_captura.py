"""Compara as voltas oficiais (após S 183 = desistir) com o A* da grade: voltas_captura.py <captura.pkl> <mapa>"""
import sys, pickle, struct, math, collections
from pathdat_50 import PathDat
from astar_50 import Grade
P=pickle.load(open(sys.argv[1],"rb")); t0=P[0][0]; MAPA=int(sys.argv[2])
EXPORTA=open(sys.argv[3],"a",encoding="utf-8") if len(sys.argv)>3 else None   # <saida.tsv>: casos para o teste Java
G=Grade(PathDat(MAPA))
mapa=None; ev=collections.defaultdict(list)
for t,s,op,p in P:
    if s and op==15: mapa=struct.unpack_from("<I",p,0)[0]
    if mapa!=MAPA or not s or len(p)<4: continue
    o=struct.unpack_from("<I",p,0)[0]
    if op==183: ev[o].append((t,'desiste'))
    elif op==40: ev[o].append((t,'alvo'))
    elif op==55 and len(p)>=18: ev[o].append((t,'mov',p[17],struct.unpack_from("<3f",p,4),struct.unpack_from("<3f",p,18) if len(p)>=30 else None))
def dist_ao_caminho(q,C):
    best=1e9
    for a,b in zip(C,C[1:]):
        ax,ay=a[0],a[1]; bx,by=b[0],b[1]; dx,dy=bx-ax,by-ay; L=dx*dx+dy*dy
        f=0 if L==0 else max(0,min(1,((q[0]-ax)*dx+(q[1]-ay)*dy)/L))
        best=min(best,math.hypot(ax+dx*f-q[0],ay+dy*f-q[1]))
    return best
for o,E in ev.items():
    for i,e in enumerate(E):
        if e[1]!='desiste': continue
        pts=[]
        for f in E[i+1:]:
            if f[1]=='alvo' or (f[1]=='mov' and f[2] not in (0xe0,0xe2)) or f[0]-e[0]>25: break
            if f[1]=='mov' and f[4]: pts.append((f[0],f[3],f[4]))
        if len(pts)<1: continue
        ini=pts[0][1]; fim=pts[-1][2]; ofic=[ini]+[q[2] for q in pts]
        if EXPORTA:
            EXPORTA.write("\t".join([str(MAPA), hex(o), f"{e[0]-t0:.1f}", ";".join(",".join(f"{v:.3f}" for v in q) for q in ofic)]) + "\n")
        lo=sum(math.dist(a[:2],b[:2]) for a,b in zip(ofic,ofic[1:]))
        a=G.no_em(*ini); b=G.no_em(*fim)
        if not a or not b: print(hex(o),"sem nó",ini,fim); continue
        c=G.caminho(a,b)
        if not c: print(f"{hex(o)} t={e[0]-t0:.1f}: A* sem caminho ({ini[0]:.1f},{ini[1]:.1f},{ini[2]:.1f})->({fim[0]:.1f},{fim[1]:.1f},{fim[2]:.1f})"); continue
        C=G.alisa(c); la=sum(math.dist(p[:2],q[:2]) for p,q in zip(C,C[1:]))
        desvio=max(dist_ao_caminho(q,C) for q in ofic)
        dzmax=max(abs(p[2]-q[2]) for p,q in zip(C,C[1:]))
        print(f"{hex(o)} t={e[0]-t0:6.1f}: oficial {len(ofic)-1} trechos {lo:6.1f} m | A* {len(C)-1} trechos {la:6.1f} m | maior afastamento {desvio:4.2f} m | z {ofic[0][2]:.1f}->{fim[2]:.1f}")
        if desvio>1.5:
            print("     oficial:",[tuple(round(v,2) for v in q) for q in ofic])
            print("     A*     :",[tuple(round(v,2) for v in q) for q in C])
