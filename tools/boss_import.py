import sys,json; sys.path.insert(0,'.')
import numpy as np
from PIL import Image
from scipy import ndimage
from ai_import import fgmask, cells, stitch, downscale
CH='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
def prep(top,bot,out):
    for a,b,h in ((top,'/tmp/_t.png',470),(bot,'/tmp/_b.png',468)):
        Image.open(a).convert('RGB').resize((1376,h),Image.NEAREST).save(b)
    stitch('/tmp/_t.png','/tmp/_b.png',out)
def import_boss(path, target_h, ncolors=40, flip=True):
    a,fg,boxes=cells(Image.open(path),4,2)
    lab,n=ndimage.label(fg,structure=np.ones((3,3)))
    objs=ndimage.find_objects(lab); sizes=ndimage.sum(fg,lab,range(1,n+1))
    masks=[]
    for (x0,y0,x1,y1) in boxes:
        comps=[k for k in range(n) if sizes[k]>=10 and x0<=(objs[k][1].start+objs[k][1].stop)/2<x1 and y0<=(objs[k][0].start+objs[k][0].stop)/2<y1]
        keep=[k for k in comps if not ((objs[k][0].stop-objs[k][0].start)<=5 and (objs[k][1].stop-objs[k][1].start)>40)]
        masks.append(np.isin(lab,[k+1 for k in keep]))
    ys=np.where(masks[0].any(1))[0]; factor=(ys[-1]-ys[0]+1)/target_h
    arrs=[]; anch=[]
    for (x0,y0,x1,y1),m in zip(boxes,masks):
        yy,xx=np.where(m); ground=yy.max()+1; bx0=max(0,xx.min()-2)
        arr=downscale(a,m,(bx0,yy.min()-2,xx.max()+3,ground),factor,ground)
        R,G,B=[arr[...,i].astype(int) for i in range(3)]
        spill=(G>R+35)&(G>B+35)&(G>110)
        arr[spill,3]=0
        al=arr[...,3]>0; lb,nn=ndimage.label(al,structure=np.ones((3,3)))
        if nn>1:
            sz=ndimage.sum(al,lb,range(1,nn+1))
            for k in range(nn):
                if sz[k]<6: arr[lb==k+1,3]=0
        gy=np.where(arr[...,3].any(1))[0]
        # remove linha de chão residual (última linha muito larga e fina)
        # âncora: centro da metade inferior (pés)
        lo=m[ground-max(2,int((ground-yy.min())*0.25)):ground]; lx=np.where(lo.any(0))[0]
        if len(lx)==0: lx=xx
        arrs.append(arr); anch.append(((lx[0]+lx[-1])/2-bx0)/factor)
    stack=np.concatenate([x[x[...,3]>0][:,:3] for x in arrs]).astype('uint8')
    pim=Image.fromarray(stack.reshape(-1,1,3)).quantize(ncolors,method=Image.Quantize.MEDIANCUT)
    pal=np.array(pim.getpalette()[:ncolors*3]).reshape(-1,3)
    frames=[]
    for arr,ax in zip(arrs,anch):
        if flip: arr=arr[:,::-1]; ax=arr.shape[1]-1-ax
        yy,xx=np.where(arr[...,3]>0); x0_,x1_,y0_=xx.min(),xx.max()+1,yy.min()
        rows=[]
        for y in range(y0_,arr.shape[0]):
            r=''
            for x in range(x0_,x1_):
                if arr[y,x,3]==0: r+='.'; continue
                c=arr[y,x,:3].astype(int); r+=CH[int(((pal-c)**2).sum(1).argmin())]
            rows.append(r)
        frames.append({'w':int(x1_-x0_),'h':len(rows),'ax':int(round(ax-x0_)),'r':rows})
    return {'pal':['#%02x%02x%02x'%tuple(int(v) for v in p) for p in pal],'f':frames}
def preview(d,path,sc=3):
    P=[tuple(int(h[k:k+2],16) for k in (1,3,5))+(255,) for h in d['pal']]
    W=max(f['w'] for f in d['f'])+10; H=max(f['h'] for f in d['f'])+6
    S=Image.new('RGBA',(W*len(d['f'])*sc,H*sc),(40,34,38,255))
    for i,f in enumerate(d['f']):
        im=Image.new('RGBA',(f['w'],f['h']),(0,0,0,0))
        for y,r in enumerate(f['r']):
            for x,c in enumerate(r):
                if c!='.': im.putpixel((x,y),P[CH.index(c)])
        im=im.resize((f['w']*sc,f['h']*sc),Image.NEAREST); S.alpha_composite(im,((i*W+W//2-f['ax'])*sc,(H-3-f['h'])*sc))
    S.save(path)
