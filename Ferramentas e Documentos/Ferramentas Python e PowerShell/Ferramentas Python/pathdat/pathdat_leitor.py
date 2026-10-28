"""Leitor do X-path.dat (cliente 5.0): setores 16 m, camadas, e nós explícitos (tipo 16) do bloco 1.
Nó: [i32 z cm][H cx][H cy][B máscara 2 bits x4 dir (x+1,y+1,x-1,y-1)]; 01 = H offset do vizinho na lista do setor, 10 = 4 b (byte0 = 0x80|camada do setor vizinho, célula implícita)."""
import struct, sys, collections
ARQ=sys.argv[1] if len(sys.argv)>1 else r"G:/Projetos AION/Classic/Código Fonte - Emulador/game-server/data/native-path/220010000_df1/DF1-path.dat"
f=open(ARQ,'rb').read(); size=3072
FIX={0:4,1:4,2:0,3:0,4:1024,5:1024,6:128,7:128,8:264,9:264,10:568,11:568,12:1028,13:1028,14:2052,15:2052}
B=132; c1=struct.unpack_from("<i",f,128)[0]
def setores():
    off=128; off+=4+c1; c2=struct.unpack_from("<i",f,off)[0]; off+=4+c2*4
    S={}
    for y in range(0,size,16):
      for x in range(0,size,16):
        n=f[off]; off+=1; L=[]
        for l in range(n):
            t=f[off]; off+=1
            if t==16: L.append((16,)+struct.unpack_from("<IH",f,off)); off+=6; continue
            d0=off; off+=5+FIX[t]
            if t%2==1 and t<=15: off+=512
            off+=12; L.append((t,d0))
        if L: S[(x,y)]=L
    return S
def nos(o,cnt):
    p=B+o; R=[]
    for i in range(cnt):
        z,x,y,m=struct.unpack_from("<iHHB",f,p); q=p+9; lig=[]
        for d in range(4):
            k=(m>>(2*d))&3
            if k==1: lig.append((d,1,struct.unpack_from("<H",f,q)[0])); q+=2
            elif k==2: lig.append((d,2,f[q:q+4])); q+=4
            elif k==3: lig.append((d,3,f[q:q+4])); q+=4
        R.append((p-B-o,z/100,x,y,m,lig)); p=q
    return R,p-B
if __name__=="__main__":
    S=setores()
    E=sorted([(e[1],e[2],k) for k,v in S.items() for e in v if e[0]==16])
    ok=0; ruim=[]
    k3=collections.Counter()
    for (o,c,k),(o2,_,_) in zip(E,E[1:]+[(c1,0,None)]):
        R,fim=nos(o,c)
        if fim==o2: ok+=1
        else: ruim.append((k,o,c,fim,o2))
        for r in R:
            for l in r[5]: k3[l[1]]+=1
    print("listas que fecham:",ok,"de",len(E)); print(ruim[:5]); print("tipos de ligação",k3)
