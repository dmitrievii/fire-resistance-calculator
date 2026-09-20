from __future__ import annotations
import struct, json, re, hashlib
from pathlib import Path

PAGE_SIZE=2048

def iter_records(path:Path):
    b=path.read_bytes()
    assert b[:4]==b'\x00\x01\x00\x00' and b[4:19].startswith(b'Standard Jet DB')
    for pg in range(1, len(b)//PAGE_SIZE):
        x=b[pg*PAGE_SIZE:(pg+1)*PAGE_SIZE]
        if not x or x[0]!=1: continue
        n=struct.unpack_from('<H',x,8)[0]
        if n>200: continue
        raw=[]
        ok=True
        for i in range(n):
            off_raw=struct.unpack_from('<H',x,10+2*i)[0]
            off=off_raw & 0x0fff
            if not (10+2*n <= off < PAGE_SIZE): ok=False; break
            raw.append((off_raw,off))
        if not ok: continue
        for i,(off_raw,off) in enumerate(raw):
            end=PAGE_SIZE if i==0 else raw[i-1][1]
            if off>=end: continue
            yield pg,i,off_raw,x[off:end]

def clean_caption_bytes(b:bytes)->str:
    # Main rows have trailing variable-column offset/null metadata. Keep the
    # leading CP1251 text; known captions are printable Russian/ASCII.
    s=b.decode('cp1251','ignore')
    # strip common binary tails by first control char
    s=''.join(ch for ch in s if ch=='\t' or ord(ch)>=32)
    # Captions sometimes have digits appended from column-offset bytes; remove
    # only obvious repeated 8/9/: artefacts at end, preserving grade digits.
    s=re.sub(r'(?:888|:::|999|\x05\x03\x03)$','',s)
    return s.strip('\x00\xff\t \r\n')

def extract(path:Path):
    mains={}
    data=[]
    for pg,i,offraw,rec in iter_records(path):
        # Main: byte count 4, int32 id, caption starts immediately at 5.
        if len(rec)>=8 and rec[0]==4:
            ident=struct.unpack_from('<I',rec,1)[0]
            if 1 <= ident <= 1000:
                tail=rec[5:]
                # stop at common var-column metadata bytes. Captions in these DBs
                # are single CP1251 strings; infer tail using terminal patterns.
                # We accept only strings containing a Cyrillic C/Latin C and grade digits.
                txt=tail.decode('cp1251','ignore')
                m=re.match(r'([^\x00-\x1f\xff]+)',txt)
                if m:
                    cap=m.group(1)
                    cap=re.sub(r'(888|:::|999)+$','',cap).strip()
                    cap=re.sub(r'([#$]{3,})$','',cap).strip()
                    if re.search(r'[СC]\s*\d{3}',cap) or 'Сталь' in cap:
                        mains[ident]={'id_main':ident,'caption':cap,'page':pg,'row':i}
        # Data: byte count 8, IDs then 5 IEEE single floats, then condition text.
        if len(rec)>=29 and rec[0]==8:
            ident=struct.unpack_from('<I',rec,1)[0]
            main=struct.unpack_from('<I',rec,5)[0]
            vals=struct.unpack_from('<5f',rec,9)
            if 1<=ident<=1000 and 1<=main<=1000 and all(0<=v<=2000 for v in vals) and sum(vals[:4]) > 100:
                # Text starts at 29 and ends before 4-byte-ish var-column metadata.
                rawtxt=rec[29:]
                # In observed Jet3 rows tail is 27/39/3a,1d,01,ff etc.
                # Find final metadata marker 0x1d,0x01,0xff if present.
                k=rawtxt.rfind(b'\x1d\x01\xff')
                if k>=0: rawtxt=rawtxt[:k]
                txt=rawtxt.decode('cp1251','ignore').strip('\x00\xff \r\n')
                txt=re.sub(r"(мм)[0-9%$':]+$", r'\1', txt).strip()
                data.append({
                    'id_data':ident,'id_main':main,
                    'Ryn_MPa':round(vals[0],6),'Run_MPa':round(vals[1],6),
                    'Ry_MPa':round(vals[2],6),'Ru_MPa':round(vals[3],6),
                    'Rs_MPa':round(vals[4],6),'condition_raw':txt,
                    'page':pg,'row':i,'record_hex':rec.hex(),
                })
    # second pass: names may not have been recognized if artefacts; directly scan
    # records with rec[0]=4 and link only IDs referenced by data.
    need={r['id_main'] for r in data}
    for pg,i,offraw,rec in iter_records(path):
        if len(rec)>=8 and rec[0]==4:
            ident=struct.unpack_from('<I',rec,1)[0]
            if ident in need and ident not in mains:
                tail=rec[5:]
                # Trim last 3-5 bytes by testing longest valid cp1251 prefix.
                best=''
                for cut in range(0,min(8,len(tail)) + 1):
                    q=tail[:len(tail)-cut if cut else None]
                    s=q.decode('cp1251','ignore').strip('\x00\xff \r\n')
                    if (re.search(r'[СC]\s*\d{3}',s) or 'Сталь' in s) and len(s)>len(best): best=s
                mains[ident]={'id_main':ident,'caption':best,'page':pg,'row':i}
    for r in data:
        r['caption']=mains.get(r['id_main'],{}).get('caption')
    data.sort(key=lambda r:r['id_data'])
    return {
        'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'format':'Microsoft Access Jet3 / 2048-byte pages',
        'main_count':len(mains),'data_count':len(data),
        'main':sorted(mains.values(),key=lambda x:x['id_main']),
        'rows':data,
    }

if __name__=='__main__':
    import sys
    outdir=Path(sys.argv[2]) if len(sys.argv)>2 else Path('.')
    outdir.mkdir(parents=True,exist_ok=True)
    for arg in sys.argv[1:2]:
        p=Path(arg); d=extract(p)
        q=outdir/(p.stem+'.json'); q.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
        print(q, d['main_count'], d['data_count'])
