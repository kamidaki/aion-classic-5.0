"""Teste: A* na grade 0,5 m do DF1-path.dat reproduz a volta/queda oficial do mob 210365 (captura 27/10)."""
import struct, heapq, math, sys
from PIL import Image
from pathdat_leitor import *
S=setores()
img=Image.open(r"G:/Projetos AION/Classic/Código Fonte - Emulador/game-server/data/geo/220010000.png")
W,H=img.size; px=img.load()
def hz(i,j): return px[j,i]*2048/65536  # linha = x, coluna = y
def terreno(x,y):
    i,j=int(x//2),int(y//2); fx,fy=x/2-i,y/2-j
    z1,z2,z3,z4=hz(i,j),hz(i,j+1),hz(i+1,j),hz(i+1,j+1)
    if fx+fy<=1: return z1+(z3-z1)*fx+(z2-z1)*fy
    return z4+(z2-z4)*(1-fx)+(z3-z4)*(1-fy)
DX=[(1,0),(0,1),(-1,0),(0,-1)]
# nós explícitos
EXP={}  # (cx,cy) -> lista de (z, id)
NODE={} # id -> (cx,cy,z, links[(id|('T',li),...)])
for k,v in S.items():
    for li,L in enumerate(v):
        if L[0]!=16: continue
        R,_=nos(L[1],L[2]); base=('E',k,li)
        for r in R:
            nid=base+(r[0],); NODE[nid]=[r[2],r[3],r[1],r[5],k,li]; EXP.setdefault((r[2],r[3]),[]).append((r[1],nid))
def sec(cx,cy): return ((cx//32)*16,(cy//32)*16)
def eh16(cx,cy): return any(L[0]==16 for L in S.get(sec(cx,cy),[]))
def melhor(cx,cy,z):
    c=EXP.get((cx,cy));
    return min(c,key=lambda a:abs(a[0]-z)) if c else None
def vizinhos(n):
    if n[0]=='E':
        cx,cy,z,lig,k,li=NODE[n]
        for d,t,v in lig:
            tx,ty=cx+DX[d][0],cy+DX[d][1]
            if t==1: q=('E',k,li,v); yield q, NODE[q][2]
            else:
                L=S.get(sec(tx,ty),[]); l2=v[0]&0x7f
                if l2<len(L) and L[l2][0]==16:
                    m=melhor(tx,ty,z)
                    if m: yield m[1], m[0]
                else:
                    tz=terreno(tx*.5+.25,ty*.5+.25); yield ('T',tx,ty), tz
    else:
        _,cx,cy=n; z=terreno(cx*.5+.25,cy*.5+.25)
        for dx,dy in DX:
            tx,ty=cx+dx,cy+dy
            if eh16(tx,ty) and not any(L[0]!=16 for L in S.get(sec(tx,ty),[])):
                m=melhor(tx,ty,z)
                if m and -1.9<=m[0]-z<=1.9: yield m[1],m[0]
            else:
                tz=terreno(tx*.5+.25,ty*.5+.25)
                if tz-z<=1.9: yield ('T',tx,ty),tz
def pos(n):
    if n[0]=='E': c=NODE[n]; return c[0]*.5+.25,c[1]*.5+.25,c[2]
    return n[1]*.5+.25,n[2]*.5+.25,terreno(n[1]*.5+.25,n[2]*.5+.25)
def no_em(x,y,z):
    cx,cy=int(x/.5),int(y/.5); m=melhor(cx,cy,z)
    return m[1] if m and abs(m[0]-z)<2 else ('T',cx,cy)
def astar(a,b,lim=400000):
    pb=pos(b); fila=[(0,0,a)]; g={a:0}; pai={a:None}; n=0
    while fila:
        _,ga,u=heapq.heappop(fila); n+=1
        if u==b or n>lim: break
        pu=pos(u)
        for v,vz in vizinhos(u):
            pv=(pos(v)[0],pos(v)[1],vz); c=ga+math.dist(pu[:2],pv[:2])
            if c<g.get(v,1e18):
                g[v]=c; pai[v]=u; heapq.heappush(fila,(c+math.dist(pv[:2],pb[:2]),c,v))
    if b not in pai: return None,n
    cam=[];u=b
    while u: cam.append(u); u=pai[u]
    return cam[::-1],n
if __name__=="__main__":
    a=no_em(523.55,2802.27,309.07); b=no_em(492.25,2798.75,296.92)
    print("início",a,pos(a)," fim",b,pos(b))
    cam,n=astar(a,b); print("expandidos",n)
    if not cam: print("sem caminho"); sys.exit()
    P=[pos(u) for u in cam]
    # pontos de quebra: mudança de direção ou salto de z > 1 m
    cant=[P[0]]
    for i in range(1,len(P)-1):
        d1=(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]); d2=(P[i+1][0]-P[i][0],P[i+1][1]-P[i][1])
        if d1!=d2 or abs(P[i+1][2]-P[i][2])>1: cant.append(P[i])
    cant.append(P[-1])
    print("células",len(P),"comprimento 2D",round(sum(math.dist(p[:2],q[:2]) for p,q in zip(P,P[1:])),1))
    for i in range(1,len(P)):
        if abs(P[i][2]-P[i-1][2])>1: print("QUEDA",P[i-1],"->",P[i])
    print("quinas", [tuple(round(c,2) for c in p) for p in cant][:40])
