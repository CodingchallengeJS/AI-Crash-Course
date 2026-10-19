import sys,io,re,json,shutil
from pathlib import Path
sys.path.insert(0,str(Path('.tools').resolve()))
import pymupdf
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
OUT=Path('ai-exam/dist'); (OUT/'exams').mkdir(exist_ok=True)
def sig(f,n):
 p=DecomposingRecordingPen(f.getGlyphSet());f.getGlyphSet()[n].draw(p);return repr(p.value)
def recover(doc):
 maps={}
 for page in doc:
  for xref,ext,typ,font,res,enc in page.get_fonts():
   if font.split('+')[-1] in maps:continue
   if '+' not in font:maps[font]={};continue
   filename='timesbi.ttf' if 'BoldItalic' in font else 'timesbd.ttf' if 'Bold' in font else 'timesi.ttf' if 'Italic' in font else 'times.ttf'
   if 'Cambria' in font:maps[font]={};continue
   f=TTFont(io.BytesIO(doc.extract_font(xref)[3]));base=TTFont('C:/Windows/Fonts/'+filename); lookup={}
   for c,n in sorted(base.getBestCmap().items(),reverse=True):lookup[sig(base,n)]=chr(c)
   glyphmap={c:lookup.get(sig(f,n),'?') for c,n in f['cmap'].tables[0].cmap.items()}
   obj=doc.xref_object(xref); uni=re.search(r'/ToUnicode (\d+)',obj);mapping={}
   if uni:
    s=doc.xref_stream(int(uni[1])).decode()
    for a,b,c in re.findall(r'<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>',s):
     a,b,c=int(a,16),int(b,16),int(c,16)
     for i in range(a,min(b+1,256)):
      if i in glyphmap:mapping[chr(c+i-a)]=glyphmap[i]
   maps[font.split('+')[-1]]=mapping
 return maps
allq=[]
for source,path,lo,hi in [('VOAI','real-test/CV gui cac so GDDT_Olympic Tri tue nhan tao.pdf',2,18),('VAIC','real-test/VAIC 2025.pdf',0,12)]:
 doc=pymupdf.open(path);maps=recover(doc) if source=='VOAI' else {};pages=[];starts=[]
 for pi in range(lo,hi):
  page=doc[pi]; lines=[]
  for block in page.get_text('dict')['blocks']:
   if 'lines' not in block:continue
   for line in block['lines']:
    text=''.join(''.join(maps.get(sp['font'],{}).get(c,c) for c in sp['text']) for sp in line['spans'])
    lines.append((line['bbox'][1],line['bbox'][3],text))
  lines.sort(key=lambda l:l[0]);pages.append(lines)
  for y,y2,text in lines:
   m=re.search(r'Câu\s*(\d+)\s*[.:]',text)
   if m:starts.append((int(m[1]),pi,y))
 Path('exam-extracted/'+source+'-decoded.txt').write_text('\n'.join('=== PAGE '+str(lo+i+1)+' ===\n'+'\n'.join(t[2] for t in ls) for i,ls in enumerate(pages)),encoding='utf-8')
 for idx,(num,pi,y) in enumerate(starts):
  nxt=starts[idx+1] if idx+1<len(starts) else (0,hi-1,doc[hi-1].rect.height-30)
  parts=[];texts=[]
  for j in range(pi,nxt[1]+1):
   top=y-3 if j==pi else 35; bottom=nxt[2]-4 if j==nxt[1] else doc[j].rect.height-40
   if bottom<=top:continue
   for ly,ly2,t in pages[j-lo]:
    if ly>=top and ly<bottom:texts.append(t)
   clip=pymupdf.Rect(35,top,doc[j].rect.width-30,bottom)
   fname=f'exams/{source.lower()}-{num}-{j+1}.webp';doc[j].get_pixmap(matrix=pymupdf.Matrix(1.65,1.65),clip=clip).pil_save(OUT/fname,format='WEBP',quality=86);parts.append(fname)
  allq.append({'id':source.lower()+'-'+str(num),'source':source,'number':num,'page':pi+1,'raw':'\n'.join(texts),'images':parts})
 shutil.copyfile(path,OUT/'exams'/(source.lower()+'.pdf'))
Path('exam-extracted/questions-raw.json').write_text(json.dumps(allq,ensure_ascii=False,indent=2),encoding='utf-8')
print('Extracted',len(allq),'questions')
