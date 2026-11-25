import re,json,sys,collections
src=sys.argv[1]; out=sys.argv[2]
rows=[]
for l in open(src,encoding='utf-8'):
    l=l.strip()
    if not l: continue
    i,f,r,p,n=l.split('|',4)
    rows.append(dict(id=i,f=f,rank=int(r),price=int(p),name=n))
WET=re.compile(r'罐|餐包|軟包|肉包|慕斯|餐盒|主食泥|濕糧|肉醬|主食杯|凍乾鮮肉餐')
RX=re.compile(r'處方|VetLife|\bVC\d?|k/d|c/d|獸醫')
def brand(n):
    m=re.match(r'【([^】]+)】',n)
    if m: return m.group(1)
    return re.split(r'[-\s]',n)[0]
def kg(n):
    t=n.replace('＊','*').replace('ｘ','x').replace('Ｘ','x')
    m=re.search(r'(\d+(?:\.\d+)?)\s*(kg|KG|Kg|公斤|千克)',t)
    if m: return float(m.group(1))
    m=re.search(r'(\d+(?:\.\d+)?)\s*(lb|LB|lbs|磅)',t)
    if m: return round(float(m.group(1))*0.4536,2)
    m=re.search(r'(\d+(?:\.\d+)?)\s*(g|G|公克|克)',t)
    if m: return float(m.group(1))/1000
    return None
def mult(n):
    if re.search(r'\d(kg|KG|Kg)\s*/包\s*[（(]',n): return 1
    m=re.search(r'[*xX×]\s*(\d+)\s*(入|包|罐|件)?',n)
    if m: return int(m.group(1))
    m=re.search(r'(\d+)\s*(入|包組|包入|罐組|罐|件組|包)',n)
    if m: return int(m.group(1))
    m=re.search(r'(\d+)包組|二入|兩箱',n)
    if m: return int(m.group(1)) if m.group(1) else 2
    return 1
for x in rows:
    n=x['name']
    if x['f']=='dry' and WET.search(n): x['f']='wet'; x['fix']='dry→wet'
    x['rx']=bool(RX.search(n))
    x['brand']=brand(n)
    u=kg(n); m=mult(n)
    x['unit_kg']=u; x['packs']=m
    x['total_kg']=round(u*m,3) if u else None
    x['ntd_per_kg']=round(x['price']/x['total_kg']) if x['total_kg'] else None
json.dump(rows,open(out,'w',encoding='utf-8'),ensure_ascii=False,indent=0)
C=collections.Counter
print('listings',len(rows),C(x['f'] for x in rows))
print('fixed',[ (x['id'],x['name'][:20]) for x in rows if x.get('fix')])
print('rx',[(x['id'],x['name'][:25]) for x in rows if x['rx']])
print('no size',sum(1 for x in rows if not x['total_kg']))
for f in ('dry','wet'):
    b=C(x['brand'] for x in rows if x['f']==f)
    print(f,'brands',len(b)); print(b.most_common(40))
