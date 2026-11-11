import sys,json; sys.path.insert(0,'.')
import numpy as np
from PIL import Image
from scipy import ndimage
from ai_import import fgmask, cells, stitch, downscale, to_frame
def import_cells(path, pal, factor, ncol=4, nrow=2, ground_mode='own'):
    a,fg,boxes=cells(Image.open(path),ncol,nrow)
    lab,n=ndimage.label(fg,structure=np.ones((3,3)))
    objs=ndimage.find_objects(lab); sizes=ndimage.sum(fg,lab,range(1,n+1))
    out=[]
    for (x0,y0,x1,y1) in boxes:
        comps=[k for k in range(n) if sizes[k]>=12 and x0<=(objs[k][1].start+objs[k][1].stop)/2<x1 and y0<=(objs[k][0].start+objs[k][0].stop)/2<y1]
        big=max(comps,key=lambda k:sizes[k]); top=objs[big][0].start
        keep=[k for k in comps if objs[k][0].stop>top+2]
        # remove linhas de chão finas (altura <=4 e larga)
        keep=[k for k in keep if not ((objs[k][0].stop-objs[k][0].start)<=5 and (objs[k][1].stop-objs[k][1].start)>40)]
        m=np.isin(lab,[k+1 for k in keep])
        ys,xs=np.where(m); bx0=xs.min()-2; ground=ys.max()+1
        arr=downscale(a,m,(bx0,ys.min()-2,xs.max()+3,ground),factor,ground)
        cx=(x0+x1)/2
        out.append(to_frame(arr,pal,int(round((cx-bx0)/factor))))
        out[-1]={k:(int(v) if k!='r' else v) for k,v in out[-1].items()}
    return out
