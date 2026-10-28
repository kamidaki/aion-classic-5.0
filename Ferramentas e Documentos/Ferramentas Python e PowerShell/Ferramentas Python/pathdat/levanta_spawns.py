"""Spots de spawn x piso da grade, por mapa: levanta_spawns.py [<pasta de spawns>]"""
import re, collections, math, glob, os, sys, pickle
from pathdat_50 import PathDat, RAIZ
SP=sys.argv[1] if len(sys.argv)>1 else os.path.join(RAIZ,"static_data/spawns")
def faixa(d): return '<0,3' if abs(d)<=0.3 else '0,3-1' if abs(d)<1 else '1-3' if abs(d)<3 else '3-6' if abs(d)<6 else '>6'
tot=collections.Counter(); linhas=[]
porMapa=collections.defaultdict(list)
for f in glob.glob(SP+"/**/*.xml",recursive=True):
    x=re.sub(r"(?s)<!--.*?-->","",open(f,encoding="utf-8").read())
    for mapa,corpo in re.findall(r'(?s)<spawn_map\b[^>]*map_id="(\d+)"[^>]*>(.*?)</spawn_map>',x):
        porMapa[int(mapa)].append((f,corpo))
res={}
for mapa,blocos in sorted(porMapa.items()):
    try: M=PathDat(mapa)
    except FileNotFoundError: continue
    r=collections.Counter()
    for f,corpo in blocos:
        for npc,bloco in re.findall(r'(?s)<spawn\b[^>]*npc_id="(\d+)"[^>]*>(.*?)</spawn>',corpo):
            for sp in re.findall(r'<spot\b[^>]*>',bloco):
                if 'aerial_spawn="true"' in sp: r['aéreo (marcado)']+=1; continue
                X=float(re.search(r'\bx="([-\d.]+)"',sp).group(1)); Y=float(re.search(r'\by="([-\d.]+)"',sp).group(1)); Z=float(re.search(r'\bz="([-\d.]+)"',sp).group(1))
                if not(0<=X<M.tam and 0<=Y<M.tam): r['fora do mapa']+=1; continue
                cel=[p[0] for p in M.pisos(X,Y) if p[1] and not math.isnan(p[0])]
                if not cel: r['célula sem piso']+=1; continue
                d=min(cel,key=lambda z:abs(z-Z))-Z
                r[('no chão' if abs(d)<=0.3 else 'abaixo do piso '+faixa(d) if d>0 else 'acima do piso '+faixa(d))]+=1
    res[mapa]=r; tot+=r
    n=sum(r.values()); ok=r['no chão']
    print(f"{mapa}: {n:6d} spots, no chão {100*ok/max(n,1):5.1f}% | abaixo {sum(v for k,v in r.items() if k.startswith('abaixo')):5d} | acima {sum(v for k,v in r.items() if k.startswith('acima')):5d} | sem piso {r['célula sem piso']:4d} | aéreos {r['aéreo (marcado)']}",flush=True)
print("TOTAL"); [print(f"   {v:7d} {k}") for k,v in sorted(tot.items())]
pickle.dump(res,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"levanta_spawns.pkl"),"wb"))
