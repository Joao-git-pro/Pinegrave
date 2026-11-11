import json,re
from PIL import Image
CH='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&*+-/:;<=>?@^_~'
def load(path):
    s=open(path,encoding='utf8').read().split('\n')
    li=next(i for i,l in enumerate(s) if l.startswith('const AREN_A'))
    pl=next(i for i,l in enumerate(s) if l.startswith('const AREN_PAL'))
    A=json.loads(s[li][s[li].index('{'):s[li].rindex('}')+1])
    pal=json.loads(re.search(r'const AREN_PAL ?= ?(\[[^\]]*\])',s[pl]).group(1))
    return s,li,A,pal
def rgb(h): return tuple(int(h[i:i+2],16) for i in (1,3,5))+(255,)
def toimg(f,pal):
    im=Image.new('RGBA',(f['w'],f['h']),(0,0,0,0))
    for y,row in enumerate(f['r']):
        for x,c in enumerate(row):
            if c!='.': im.putpixel((x,y),rgb(pal[CH.index(c)]))
    return im
def sheet(frames,pal,path,sc=6,bg=(40,34,38,255)):
    cw=max(max(f['w'] for f in frames), 1)+30; ch=max(f['h'] for f in frames)+10
    S=Image.new('RGBA',(cw*len(frames)*sc, ch*sc),bg)
    for i,f in enumerate(frames):
        im=toimg(f,pal).resize((f['w']*sc,f['h']*sc),Image.NEAREST)
        ox=(i*cw+cw//2-f['ax'])*sc; oy=(ch-4-f['ay'])*sc
        S.alpha_composite(im,(ox,oy))
    S.save(path)
