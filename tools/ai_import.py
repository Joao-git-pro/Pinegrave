import sys, json; sys.path.insert(0,'.')
import numpy as np
from PIL import Image
from aren_lib import *
def fgmask(a):
    r,g,b=a[...,0].astype(int),a[...,1].astype(int),a[...,2].astype(int)
    return ~((g>r+38)&(g>b+38))
def cells(img, ncol=4, nrow=2):
    a=np.array(img.convert('RGB')); H,W=a.shape[:2]; out=[]
    fg=fgmask(a)
    rows=fg.any(1); ys=np.where(rows)[0]
    # separa linhas pelo maior vão no meio
    gaps=[(ys[i+1]-ys[i],ys[i]) for i in range(len(ys)-1)]
    bounds=[0]
    if nrow==2:
        g=max(gaps,key=lambda z:z[0]); bounds=[0,g[1]+g[0]//2,H]
    else: bounds=[0,H]
    for ri in range(nrow):
        y0,y1=bounds[ri],bounds[ri+1]
        for ci in range(ncol):
            x0,x1=ci*W//ncol,(ci+1)*W//ncol
            out.append((x0,y0,x1,y1))
    return a,fg,out
def downscale(a,fg,box,factor,ground):
    x0,y0,x1,y1=box
    sub=a[y0:y1,x0:x1]; m=fg[y0:y1,x0:x1]
    h=int((ground-y0)/factor)+1; w=int((x1-x0)/factor)
    out=np.zeros((h,w,4),dtype=np.uint8)
    for j in range(h):
        for i in range(w):
            ya=int(ground-y0-(h-j)*factor); yb=int(ground-y0-(h-j-1)*factor)
            xa=int(i*factor); xb=int((i+1)*factor)
            ya=max(ya,0)
            cm=m[ya:yb,xa:xb]
            if cm.size==0 or cm.mean()<0.5: continue
            px=sub[ya:yb,xa:xb][cm]
            out[j,i,:3]=np.median(px,axis=0); out[j,i,3]=255
    return out
def to_frame(arr, pal, ax_abs):
    ys,xs=np.where(arr[...,3]>0)
    x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),arr.shape[0]
    P=np.array([rgb(p)[:3] for p in pal]).astype(int)
    rows=[]
    for y in range(y0,y1):
        r=''
        for x in range(x0,x1):
            if arr[y,x,3]==0: r+='.'; continue
            c=arr[y,x,:3].astype(int); k=int(((P-c)**2).sum(1).argmin()); r+=CH[k]
        rows.append(r)
    return {'w':x1-x0,'h':y1-y0,'ax':int(ax_abs-x0),'ay':y1-y0,'r':rows}
def assign(fg,boxes):
    from scipy import ndimage
    lab,n=ndimage.label(fg,structure=np.ones((3,3)))
    sizes=ndimage.sum(fg,lab,range(1,n+1)); cms=ndimage.center_of_mass(fg,lab,range(1,n+1))
    masks=[np.zeros_like(fg) for _ in boxes]; ext=[]
    for k in range(n):
        if sizes[k]<12: continue
        cy,cx=cms[k]
        bi=min(range(len(boxes)),key=lambda i:(0 if boxes[i][0]<=cx<boxes[i][2] and boxes[i][1]<=cy<boxes[i][3] else 1, abs((boxes[i][0]+boxes[i][2])/2-cx)+abs((boxes[i][1]+boxes[i][3])/2-cy)))
        masks[bi]|=(lab==k+1)
    return masks
def import_sheet(path,pal,target_h=47,ncol=4,nrow=2,factor=None):
    a,fg0,boxes=cells(Image.open(path),ncol,nrow); frames=[]
    masks=assign(fg0,boxes)
    H,W=fg0.shape
    # caixas expandidas pela máscara de cada quadro
    nb=[]
    for m in masks:
        ys,xs=np.where(m); nb.append((max(0,xs.min()-2),max(0,ys.min()-2),min(W,xs.max()+3),min(H,ys.max()+3)))
    boxes_orig=boxes; boxes=nb
    # altura do primeiro quadro define a escala
    x0,y0,x1,y1=boxes[0]; ys=np.where(masks[0][y0:y1,x0:x1].any(1))[0]
    factor=factor or (ys[-1]-ys[0]+1)/target_h
    for bi,(x0,y0,x1,y1) in enumerate(boxes):
        fg=masks[bi]; m=fg[y0:y1,x0:x1]
        # remove ruído: linhas/colunas isoladas
        ys=np.where(m.any(1))[0]; ground=y0+ys[-1]+1
        # âncora: centro da cabeça (topo 25% do personagem)
        top=ys[0]; hh=ys[-1]-ys[0]
        head=m[top:top+int(hh*0.25)]; hx=np.where(head.any(0))[0]
        arr=downscale(a,fg,(x0,y0,x1,y1),factor,ground)
        r_,g_,b_=arr[...,0].astype(int),arr[...,1].astype(int),arr[...,2].astype(int)
        om=(arr[...,3]>0)&(r_>150)&(g_>70)&(g_<175)&(b_<90)&(r_>g_+40)
        ax=int(round(np.where(om)[1].mean())) if om.sum()>8 else int(((hx[0]+hx[-1])/2)/factor)
        frames.append(to_frame(arr,pal,ax))
        frames[-1]={k:(int(v) if k!='r' else v) for k,v in frames[-1].items()}
    return frames, factor

def stitch(top,bot,out,off=300,W=1376,H=768):
    t=Image.open(top).convert('RGB'); b=Image.open(bot).convert('RGB')
    full=Image.new('RGB',(W,H),(0,255,0))
    full.paste(t.crop((0,0,W,470)),(0,0)); full.paste(b.crop((0,470-off,W,H-off)),(0,470))
    a=np.array(full); a[700:768,1270:1376]=[16,240,16]
    Image.fromarray(a).save(out)
