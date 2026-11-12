"""Importa folhas do Aren em grade NxM (fundo verde) para o formato AREN_A, ancorando pela cabeça laranja."""
import sys,json; sys.path.insert(0,'/home/claude/work')
import numpy as np
from PIL import Image
from scipy import ndimage
from ai_import import fgmask, downscale, to_frame
def import_grid(path, pal, ncol, nrow, target_h=46, factor=None, ref=0):
    a=np.array(Image.open(path).convert('RGB')); H,W=a.shape[:2]; fg=fgmask(a)
    lab,n=ndimage.label(fg,structure=np.ones((3,3))); objs=ndimage.find_objects(lab); sizes=ndimage.sum(fg,lab,range(1,n+1))
    boxes=[(c*W//ncol,r*H//nrow,(c+1)*W//ncol,(r+1)*H//nrow) for r in range(nrow) for c in range(ncol)]
    masks=[]
    for (x0,y0,x1,y1) in boxes:
        ks=[k for k in range(n) if sizes[k]>=10 and not ((objs[k][0].stop-objs[k][0].start)<=6 and (objs[k][1].stop-objs[k][1].start)>25) and x0<=(objs[k][1].start+objs[k][1].stop)/2<x1 and y0<=(objs[k][0].start+objs[k][0].stop)/2<y1]
        masks.append(np.isin(lab,[k+1 for k in ks]))
    if factor is None:
        ys=np.where(masks[ref].any(1))[0]; factor=(ys[-1]-ys[0]+1)/target_h
    out=[]
    for m in masks:
        ys,xs=np.where(m); bx0=xs.min()-2; ground=ys.max()+1
        arr=downscale(a,m,(bx0,ys.min()-2,xs.max()+3,ground),factor,ground)
        r_,g_,b_=[arr[...,i].astype(int) for i in range(3)]
        arr[(g_>r_+60)&(g_>b_+60),3]=0
        om=(arr[...,3]>0)&(r_>150)&(g_>70)&(g_<175)&(b_<90)&(r_>g_+40)
        ax=int(round(np.where(om)[1].mean())) if om.sum()>8 else arr.shape[1]//2
        f=to_frame(arr,pal,ax); f={k:(int(v) if k!='r' else v) for k,v in f.items()}; f['ay']=f['h']; out.append(f)
    return out,factor
