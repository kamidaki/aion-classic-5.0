"""Lista as passagens que o oficial fez e o grafo não tem: furos.py <captura.pkl> <mapa>"""
import sys, pickle, struct, math, collections
from pathdat_50 import PathDat
from astar_50 import Grade, SUBIDA
P=pickle.load(open(sys.argv[1],"rb")); MAPA=int(sys.argv[2]); M=PathDat(MAPA); G=Grade(M)
def celulas(a,b):
    out=[]; n=max(2,int(math.dist(a[:2],b[:2])*8))
    for k in range(n+1):
        f=k/n; c=(int((a[0]+(b[0]-a[0])*f)/.5),int((a[1]+(b[1]-a[1])*f)/.5))
        if not out or out[-1]!=c:
            if out and abs(c[0]-out[-1][0])+abs(c[1]-out[-1][1])==2: out.append((c[0],out[-1][1]))
            out.append(c)
    return out
mapa=None; furos=collections.Counter(); ex={}
for t,s,op,p in P:
    if s and op==15: mapa=struct.unpack_from("<I",p,0)[0]
    if mapa!=MAPA or not(s and op==55 and len(p)>=30) or p[17] not in (0xe0,0xe2,0xe8,0xea,0xe4): continue
    a=struct.unpack_from("<3f",p,4); b=struct.unpack_from("<3f",p,18)
    C=celulas(a,b); z=a[2]; ant=G.no_em(*a)
    if not ant: continue
    for c in C[1:]:
        cand=[(k,zz) for k,zz,l in G.pisos(*c) if l and abs(zz-z)<=SUBIDA]
        if not cand: break
        k,zz=min(cand,key=lambda q:abs(q[1]-z))
        if k not in {v for v,_ in G.vizinhos(ant)}:
            de=(ant[0],G.setor(*G.cel(ant))==G.setor(*c)); chave=(ant[0],k[0],'mesmo setor' if de[1] else 'divisa')
            furos[chave]+=1; ex.setdefault(chave,[]).append((G.ponto(ant),(c[0]*.5+.25,c[1]*.5+.25,round(zz,2))))
        ant,z=k,zz
print(furos)
for k,v in ex.items(): print(k, v[:3])
