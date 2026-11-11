"""Deterministic SVG renderer for the accompanying workflow specification."""
import json
import sys
import unicodedata
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
source = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT/'temporal_workflow.json'
spec = json.loads(source.read_text())
W, H = spec['canvas']['width'], spec['canvas']['height']
colors = spec['palette']
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<title>'+escape(spec['title'])+'</title>',
       '<desc>Source-grounded contract analysis and repair, followed by recorded outcomes, candidate experience development, human editing, exact-version screening and activation.</desc>',
       '<defs>']
for name, color in [('flow','#526575'),('memory','#b47436'),('edit','#80679e')]:
    svg.append(f'<marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="{color}"/></marker>')
svg += ['</defs>', '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="Arial, Helvetica, PingFang SC, Noto Sans CJK SC, sans-serif" fill="#243441">']
def text(x,y,label,size=20,anchor='middle',color='#243441',weight='400'):
    svg.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" fill="{color}">{escape(label)}</text>')
text(W/2,45,spec['title'],29,weight='600')
for g in spec['groups']:
    svg.append(f'<rect x="{g["x"]}" y="{g["y"]}" width="{g["w"]}" height="{g["h"]}" rx="10" fill="white" stroke="#cbd3d9" stroke-width="1.6"/>')
    text(g['x']+22,g['y']+34,g['label'],24,'start',weight='600')
for e in spec['edges']:
    kind=e.get('kind','flow'); color={'flow':'#526575','memory':'#b47436','edit':'#80679e'}[kind]
    points=' '.join(f'{x},{y}' for x,y in e['points'])
    dash=' stroke-dasharray="8 6"' if kind=='memory' else ''
    svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.1" stroke-linejoin="round"{dash} marker-end="url(#{kind})"/>')
    if 'label' in e:
        x,y=e['label_at']; label=e['label']; width=sum(18 if unicodedata.east_asian_width(c) in ('W','F') else 9.5 for c in label)+14
        svg.append(f'<rect x="{x-width/2}" y="{y-17}" width="{width}" height="24" fill="white"/>')
        text(x,y,label,18,color=color)
for n in spec['nodes']:
    x,y,w,h=n['x'],n['y'],n['w'],n['h']; fill,stroke=colors[n['type']]
    svg.append(f'<g id="{n["id"]}"><rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>')
    labels=n['label'].split('\n'); subtitles=n.get('sub','').split('\n') if n.get('sub') else []
    line=26; subline=23; total=len(labels)*line+len(subtitles)*subline+(8 if subtitles else 0)
    start=y-total/2+20
    for i,label in enumerate(labels):text(x,start+i*line,label,n.get('font',22),weight='600')
    start+=len(labels)*line+8
    for i,label in enumerate(subtitles):text(x,start+i*subline,label,n.get('sub_font',18),color='#52606b')
    svg.append('</g>')
for note in spec['notes']:
    for i,line in enumerate(note['text'].split('\n')):text(note['x'],note['y']+i*24,line,note.get('size',18),note.get('anchor','start'),color='#596773',weight=note.get('weight','400'))
for item in spec.get('legend', []):
    x,y=item['x'],item['y']; fill,stroke=colors[item['type']]
    svg.append(f'<rect x="{x}" y="{y-20}" width="26" height="26" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>')
    text(x+38,y,item['label'],18,'start',weight='600')
    text(x+38,y+26,item['sub'],16,'start',color='#596773')
svg.append('</g></svg>')
out=ROOT.parent/(source.stem+'.svg')
out.write_text('\n'.join(svg)+'\n')
print(out)
