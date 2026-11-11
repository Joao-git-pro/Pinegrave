"""Converte uma folha 4x2 de IA (fundo verde) em sprite de inimigo do Pinegrave.
Uso: import_enemy(sheet, target_h, mapping) -> {'pal':[...], 'a':{anim:[frames]}}
mapping: {'idle':[0], 'walk':[1,2,3,2], ...} com índices das 8 células (linha a linha)."""
import sys,json; sys.path.insert(0,'.')
import numpy as np
from PIL import Image
from scipy import ndimage
from ai_import import fgmask, cells, downscale
CH='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
def cell_masks(path):
    a,fg,boxes=cells(Image.open(path),4,2)
    lab,n=ndimage.label(fg,structure=np.ones((3,3)))
    objs=ndimage.find_objects(lab); sizes=ndimage.sum(fg,lab,range(1,n+1))
    res=[]
    for (x0,y0,x1,y1) in boxes:
        comps=[k for k in range(n) if sizes[k]>=10 and x0<=(objs[k][1].start+objs[k][1].stop)/2<x1 and y0<=(objs[k][0].start+objs[k][0].stop)/2<y1]
        thin=lambda k:(objs[k][0].stop-objs[k][0].start)<=6 and (objs[k][1].stop-objs[k][1].start)>30
        comps=[k for k in comps if not thin(k)]
        big=max(comps,key=lambda k:sizes[k]); bt,bb=objs[big][0].start,objs[big][0].stop
        # texto: componentes pequenos fora da faixa vertical do corpo
        def dark(k):
            sl=objs[k]; mm=(lab[sl]==k+1); px=a[sl][mm].astype(int)
            return ((px[:,0]+px[:,2])/2).mean()<75 and not ((px[:,0]>px[:,1]+40).mean()>0.2)
        keep=[k for k in comps if objs[k][0].stop>bt-60 and objs[k][0].start<bb-2 and (k==big or not dark(k))]
        m=np.isin(lab,[k+1 for k in keep]); res.append((m,(x0+x1)/2))
    return a,res
def import_enemy(path, target_h, mapping, ref_cell=0, ncolors=28):
    a,res=cell_masks(path)
    m0=res[ref_cell][0]; ys=np.where(m0.any(1))[0]; factor=(ys[-1]-ys[0]+1)/target_h
    arrs=[]
    for m,cx in res:
        ys,xs=np.where(m); bx0=xs.min()-2; ground=ys.max()+1
        arr=downscale(a,m,(bx0,ys.min()-2,xs.max()+3,ground),factor,ground)
        rr,gg,bb_=arr[...,0].astype(int),arr[...,1].astype(int),arr[...,2].astype(int)
        arr[(gg>rr+60)&(gg>bb_+60),3]=0
        lowdark=(gg>rr+10)&((rr+bb_)/2<70); lowdark[:-3]=False; arr[lowdark,3]=0
        arrs.append((arr,(cx-bx0)/factor))
    stack=np.concatenate([x[x[...,3]>0][:,:3] for x,_ in arrs]).astype('uint8')
    pim=Image.fromarray(stack.reshape(-1,1,3)).quantize(ncolors,method=Image.Quantize.MEDIANCUT)
    pal=np.array(pim.getpalette()[:ncolors*3]).reshape(-1,3).astype(int)
    frames=[]
    for arr,ax in arrs:
        ys,xs=np.where(arr[...,3]>0); x0,x1,y0=xs.min(),xs.max()+1,ys.min()
        rows=[]
        for y in range(y0,arr.shape[0]):
            r=''
            for x in range(x0,x1):
                if arr[y,x,3]==0: r+='.'; continue
                r+=CH[int(((pal-arr[y,x,:3].astype(int))**2).sum(1).argmin())]
            rows.append(r)
        frames.append({'w':int(x1-x0),'h':len(rows),'ax':int(round(ax-x0)),'r':rows})
    return {'pal':['#%02x%02x%02x'%tuple(p) for p in pal],'a':{k:[frames[i] for i in v] for k,v in mapping.items()}}
def preview(d,path,sc=4):
    P=[tuple(int(h[k:k+2],16) for k in (1,3,5))+(255,) for h in d['pal']]
    fr=[f for v in d['a'].values() for f in v]
    H=max(f['h'] for f in fr)+4; W=sum(max(f['w'],10)+6 for f in fr)
    S=Image.new('RGBA',(W,H),(40,34,38,255)); x=0
    for f in fr:
        im=Image.new('RGBA',(f['w'],f['h']),(0,0,0,0))
        for y,r in enumerate(f['r']):
            for i,c in enumerate(r):
                if c!='.': im.putpixel((i,y),P[CH.index(c)])
        S.alpha_composite(im,(x,H-2-f['h'])); x+=max(f['w'],10)+6
    S.resize((S.width*sc,S.height*sc),Image.NEAREST).save(path)
def embed(html_in, html_out, name, d):
    s=open(html_in,encoding='utf8',newline='').read().split('\n')
    i=next(k for k,x in enumerate(s) if x.startswith('const DATA = {"soldado"'))
    l=s[i]; D=json.loads(l[l.index('{'):l.rindex('}')+1]); D[name]=d
    s[i]=l[:l.index('{')]+json.dumps(D,separators=(',',':'))+l[l.rindex('}')+1:]
    open(html_out,'w',encoding='utf8',newline='').write('\n'.join(s))
