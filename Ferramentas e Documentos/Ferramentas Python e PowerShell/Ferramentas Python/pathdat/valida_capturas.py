"""Valida pathdat_50 contra pontos oficiais (S_MOVE/S_PUT_NPC) coletados das capturas: valida_capturas.py <pontos_z.pkl>"""
import sys, pickle, collections, math
from pathdat_50 import PathDat
T=pickle.load(open(sys.argv[1],"rb"))
por=collections.defaultdict(set)
for m,o,mask,x,y,z in T:
    if 100000000<m<1000000000 and not math.isnan(z): por[m].add((round(x,2),round(y,2),round(z,2),mask))
tot=collections.Counter()
for m,pts in sorted(por.items(),key=lambda a:-len(a[1])):
    try: M=PathDat(m)
    except FileNotFoundError: print(m,"sem path.dat"); continue
    r=collections.Counter(); difs=[]
    for x,y,z,mask in pts:
        if not(0<=x<M.tam and 0<=y<M.tam): continue
        c=M.pisos(x,y); d=min((abs(q[0]-z) for q in c if not math.isnan(q[0])),default=99)
        centro=abs((x*4)%2-1)<0.02 and abs((y*4)%2-1)<0.02
        if d<0.15:
            livre=any(q[1] for q in c if abs(q[0]-z)<0.15)
            r['ok_livre' if livre else 'ok_BLOQ']+=1
            if centro: r['centro_'+('livre' if livre else 'BLOQ')]+=1
        elif d<1.0: r['perto(<1m)']+=1
        else: r['longe(>=1m)']+=1; difs.append(d)
    n=sum(v for k,v in r.items() if not k.startswith('centro'))
    print(f"{m}: {n} pts  ok {100*(r['ok_livre']+r['ok_BLOQ'])/max(n,1):.2f}%  perto {r['perto(<1m)']}  longe {r['longe(>=1m)']}  bloq {r['ok_BLOQ']}  | centros livres {r['centro_livre']} bloq {r['centro_BLOQ']}")
    tot+=r
n=sum(v for k,v in tot.items() if not k.startswith('centro'))
print("TOTAL", n, dict(tot))
