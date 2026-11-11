import sys,json; sys.path.insert(0,'.')
import numpy as np
from PIL import Image
from scipy import ndimage
from ai_import import fgmask, cells, stitch, downscale
CH='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
stitch('ai/npc_top.png','ai/npc_bot.png','ai/npc_sheet_full.png')
a,fg,boxes=cells(Image.open('ai/npc_sheet_full.png'),4,2)
lab,n=ndimage.label(fg,structure=np.ones((3,3)))
objs=ndimage.find_objects(lab); sizes=ndimage.sum(fg,lab,range(1,n+1))
names=['garran','edda','tomas','soldado']
FACT=6.4; out={}
for ci,name in enumerate(names):
    frames=[]; allpx=[]
    arrs=[]
    for ri in range(2):
        x0,y0,x1,y1=boxes[ri*4+ci]
        # componentes cujo centro cai na célula
        comps=[k for k in range(n) if sizes[k]>=12 and x0<= (objs[k][1].start+objs[k][1].stop)/2 <x1 and y0<=(objs[k][0].start+objs[k][0].stop)/2<y1]
        big=max(comps,key=lambda k:sizes[k]); top=objs[big][0].start
        keep=[k for k in comps if objs[k][0].stop>top+2]   # tira rótulos acima
        m=np.isin(lab,[k+1 for k in keep])
        ys,xs=np.where(m); bx0,bx1,by0,ground=xs.min()-2,xs.max()+3,ys.min()-2,ys.max()+1
        arr=downscale(a,m,(bx0,by0,bx1,ground),FACT,ground)
        arrs.append(arr)
    # paleta por personagem
    stack=np.concatenate([x[x[...,3]>0][:,:3] for x in arrs]).astype('uint8')
    pim=Image.fromarray(stack.reshape(-1,1,3)).quantize(28,method=Image.Quantize.MEDIANCUT)
    pal=np.array(pim.getpalette()[:28*3]).reshape(-1,3)
    for arr in arrs:
        ys,xs=np.where(arr[...,3]>0); x0_,x1_=xs.min(),xs.max()+1; y0_=ys.min()
        rows=[]
        for y in range(y0_,arr.shape[0]):
            r=''
            for x in range(x0_,x1_):
                if arr[y,x,3]==0: r+='.'; continue
                c=arr[y,x,:3].astype(int); r+=CH[int(((pal-c)**2).sum(1).argmin())]
            rows.append(r)
        # âncora: centro do corpo na metade de baixo
        bot=arr[arr.shape[0]//2:,x0_:x1_,3]>0; bx=np.where(bot.any(0))[0]
        frames.append({'w':int(x1_-x0_),'h':len(rows),'ax':int((bx[0]+bx[-1])//2),'r':rows})
    out[name]={'pal':['#%02x%02x%02x'%tuple(int(v) for v in p) for p in pal],'f':frames}
    print(name,[(f['w'],f['h'],f['ax']) for f in frames])
json.dump(out,open('ai/npc_sprites.json','w'),separators=(',',':'))
# prévia
S=Image.new('RGBA',(8*70*4,60*4),(40,34,38,255)); i=0
for name in names:
    d=out[name]; P=[tuple(int(h[k:k+2],16) for k in (1,3,5))+(255,) for h in d['pal']]
    for f in d['f']:
        im=Image.new('RGBA',(f['w'],f['h']),(0,0,0,0))
        for y,r in enumerate(f['r']):
            for x,c in enumerate(r):
                if c!='.': im.putpixel((x,y),P[CH.index(c)])
        im=im.resize((f['w']*4,f['h']*4),Image.NEAREST); S.alpha_composite(im,(i*280+140-f['ax']*4,236-f['h']*4)); i+=1
S.save('npc_preview.png')
