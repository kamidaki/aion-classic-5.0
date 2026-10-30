#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""levanta_50_parados_captura.py: varre todas as capturas oficiais 5.0 e grava parados.json para o liga_50_rotas_source_sphere.py --parados.

parados = objeto visto no mesmo ponto (0,3 m) por mais de 30 s sem S_MOVE (55); andam = objeto com S_MOVE ou visto em outro ponto.
Chave = id do mapa. Uso: python levanta_50_parados_captura.py (grava parados.json na pasta atual).
"""
import sys,os,struct,collections,math,json
sys.path.insert(0,r"G:\Projetos AION\Classic\Ferramentas e Documentos\Ferramentas Python e PowerShell\Ferramentas Python")
import aion_pcap
CAP=r"G:\Projetos AION\Classic\Ferramentas e Documentos\Client e Coletas\Wireshark - Oficial Classic 5.0"
parados=collections.defaultdict(list); andam=collections.defaultdict(list)
for pasta,_,arqs in sorted(os.walk(CAP)):
    for a in sorted(x for x in arqs if x.endswith(".pcapng")):
        try: ss=aion_pcap.abre_todas(os.path.join(pasta,a),sem_skey=True)
        except Exception as e: print("ERRO",a,e,flush=True); continue
        for s in ss:
            try: L=aion_pcap.intercalado(s)
            except Exception: continue
            no=None; vis=collections.defaultdict(list); mv=set(); obj={}
            for t,lado,op,p in L:
                if lado!="servidor": continue
                if op==0x0F and len(p)>=4: no=struct.unpack_from("<I",p,0)[0]
                elif op==0x14 and len(p)>5: no=struct.unpack_from("<I",p,1)[0]
                elif op==0x0E and len(p)>27 and no:
                    x,y,z,o,n=struct.unpack_from("<fffII",p,0); obj[o]=(no,n); vis[(no,o,n)].append((t/1e9,x,y))
                elif op==55 and len(p)>=4:
                    o=struct.unpack_from("<I",p,0)[0]
                    if o in obj: mv.add((obj[o][0],o,obj[o][1]))
            for k,v in vis.items():
                m,o,n=k
                if k in mv or max(math.hypot(b-v[0][1],c-v[0][2]) for _,b,c in v)>0.3:
                    andam[m].append((n,v[0][1],v[0][2]))
                elif len(v)>=2 and v[-1][0]-v[0][0]>30:
                    parados[m].append((n,v[0][1],v[0][2]))
        print("ok",a,flush=True)
json.dump({"parados":parados,"andam":andam},open("parados.json","w"))
print("FIM",{m:len(v) for m,v in parados.items()})
