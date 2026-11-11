"""Exporta os sprites embutidos no Pinegrave.html para PNG + JSON editáveis (Aseprite, LibreSprite, Piskel).

Uso:  python tools/exportar_sprites.py Pinegrave.html assets
Gera: assets/aren/<anim>.png  (uma tira por animação, fundo transparente, 1 quadro por célula)
      assets/inimigos/<tipo>/<anim>.png
      assets/*.json  (largura, altura e ponto dos pés de cada quadro)
Só leitura: não altera o jogo. Requer Pillow (pip install pillow).
"""
import json, os, re, sys
from PIL import Image

AREN_CH = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&*+-/:;<=>?@^_~'
ENEMY_CH = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'

def hex_rgba(h):
    return tuple(int(h[i:i+2], 16) for i in (1, 3, 5)) + (255,)

def json_na_linha(linhas, prefixo):
    for l in linhas:
        if l.startswith(prefixo):
            return json.loads(l[l.index('{'):l.rindex('}') + 1])
    raise SystemExit('Não achei ' + prefixo)

def frame_img(f, pal, ch):
    im = Image.new('RGBA', (f['w'], f['h']), (0, 0, 0, 0))
    for y, row in enumerate(f['r']):
        for x, c in enumerate(row):
            if c != '.':
                im.putpixel((x, y), hex_rgba(pal[ch.index(c)]))
    return im

def salvar_tira(frames, pal, ch, caminho):
    cw = max(f['w'] for f in frames); chh = max(f['h'] for f in frames)
    tira = Image.new('RGBA', (cw * len(frames), chh), (0, 0, 0, 0))
    meta = []
    for i, f in enumerate(frames):
        im = frame_img(f, pal, ch)
        # pés alinhados na base da célula
        tira.alpha_composite(im, (i * cw + (cw - f['w']) // 2, chh - f['h']))
        meta.append({'w': f['w'], 'h': f['h'], 'ax': f.get('ax'), 'ay': f.get('ay'), 'celula_x': i * cw + (cw - f['w']) // 2, 'celula_y': chh - f['h']})
    tira.save(caminho)
    return {'celula': [cw, chh], 'quadros': meta}

def main(html, saida):
    linhas = open(html, encoding='utf8').read().split('\n')
    pal_linha = next(l for l in linhas if l.startswith('const AREN_PAL'))
    aren_pal = json.loads(re.search(r'const AREN_PAL ?= ?(\[[^\]]*\])', pal_linha).group(1))
    aren = json_na_linha(linhas, 'const AREN_A')
    inim = json_na_linha(linhas, 'const DATA = {"soldado"')
    os.makedirs(os.path.join(saida, 'aren'), exist_ok=True)
    idx = {'aren': {}, 'inimigos': {}}
    for anim, frames in aren.items():
        idx['aren'][anim] = salvar_tira(frames, aren_pal, AREN_CH, os.path.join(saida, 'aren', anim + '.png'))
    for tipo, d in inim.items():
        pasta = os.path.join(saida, 'inimigos', tipo); os.makedirs(pasta, exist_ok=True)
        idx['inimigos'][tipo] = {}
        for anim, frames in d['a'].items():
            idx['inimigos'][tipo][anim] = salvar_tira(frames, d['pal'], ENEMY_CH, os.path.join(pasta, anim + '.png'))
    json.dump(idx, open(os.path.join(saida, 'sprites.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    n = sum(len(v) for v in idx['aren'].values()) + sum(len(a) for t in idx['inimigos'].values() for a in t.values())
    print('exportados', len(idx['aren']), 'animações do Aren e', len(idx['inimigos']), 'inimigos;', n, 'quadros em', saida)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
