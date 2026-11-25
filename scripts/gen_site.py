# 從 momo 盤點快照產生網站品項資料，寫進 public/index.html 的 GEN 區塊
import re,json,sys,collections
SNAP=sys.argv[1]; HTML=sys.argv[2]; DATE=sys.argv[3]
rows=json.load(open(SNAP,encoding='utf-8'))
html=open(HTML,encoding='utf-8').read()
AL={'Nutram紐頓':'Nutram 紐頓','德國Granatapet葛蕾特':'Granatapet 葛蕾特','LCB藍帶廚坊':'LCB 藍帶廚坊','Fantastic98% 超越汪喵':'汪喵星球','Hills 希爾思':"Hill's 希爾思",'Orijen':'Orijen 歐睿健','WELLNESS 寵物健康':'Wellness 寵物健康','Unicharm Pet 銀湯匙':'Unicharm 銀湯匙'}
SKIP=re.compile(r'凍乾鮮肉餐|MamaMia|HAVE FISH')
def bkey(b): return re.sub(r'[^a-z0-9]','',(re.findall(r'[A-Za-z][A-Za-z0-9\'&!.\- ]*',b) or [b])[0].lower()) or b
def clean(n):
    n=re.sub(r'【[^】]+】','',n)
    n=re.sub(r'^(義大利|德國)?\S*?(Schesir鮮時|Granatapet葛蕾特|Exclusion依克森)-?','',n)
    n=re.sub(r'官方直營|台灣公司貨|momo獨家|新客組|特惠兩箱組|網路獨家組|\d+包組|\d+入組|\d+箱|二入組|任選\d*包?|效期[^ ]*|寵物/貓罐頭/貓食|寵物/貓罐頭/貓餐包|寵物/貓飼料/貓食|大包裝','',n)
    n=re.sub(r'\d+(\.\d+)?\s*(kg|KG|Kg|公斤|lb|LB|lbs|磅|g|G|公克|克|oz|盎司)','',n)
    n=re.sub(r'[*xX×]\s*\d+\s*(入|包|罐|EA|件)?|\d+\s*(入|罐|包|件組)|\(\s*\)|（\s*）','',n)
    n=re.sub(r'[｜|]',' ',n); n=re.sub(r'[\s/／\-–,，、]+$','',n); n=re.sub(r'^[\s/／\-–,，、]+','',n)
    n=re.sub(r'\(\s*\)|（\s*）|\(\s*(全齡貓?)?\s*$','',n)
    return re.sub(r'\s{2,}',' ',n).strip(' -/')[:34]
def key(n): return re.sub(r'[\s/／｜|\-()（）〔〕《》,，、+.~]','',clean(n))[:14]
def prot(n):
    f=bool(re.search(r'魚|鮭|鮪|鱈|海|蝦|蟹|鰹|磷蝦',n)); m=bool(re.search(r'雞|鴨|火雞|牛|羊|鹿|豬|肉',n))
    return '魚' if f and not m else '雞' if re.search(r'雞',n) and not f and not re.search(r'牛|羊|鹿|鴨',n) else '綜合'
def pouch(n): return bool(re.search(r'餐包|軟包|肉包|懶人包|包',re.sub(r'【[^】]+】','',n))) and not re.search(r'罐',n)
def stage(n):
    if re.search(r'幼貓',n) and re.search(r'成貓',n): return 'all'
    if re.search(r'幼貓|離乳|kitten|BC34|K36|BSK38|幼母貓|成長',n,re.I) and not re.search(r'成幼|全齡|全貓|幼/成|幼貓/成貓|成貓/幼貓|全期',n): return 'kitten'
    if re.search(r'全齡|全貓|成幼|幼/成|全期',n) or (re.search(r'幼貓',n) and re.search(r'成貓',n)): return 'all'
    if re.search(r'成貓|熟齡|高齡|老貓|7\+|11\+|15\+|室內|結紮|絕育',n): return 'adult'
    return 'all'
groups=collections.OrderedDict()
for x in sorted(rows,key=lambda r:(r['f'],r['rank'])):
    if x['rx'] or not x['total_kg'] or SKIP.search(x['name']): continue
    b=AL.get(x['brand'],x['brand']); k=(x['f'],bkey(b),key(x['name']))
    groups.setdefault(k,{'b':b,'xs':[]})['xs'].append(x)
# 既有品項：同品牌＋型號代碼或名稱相近就併入
pr_src=html[html.index('const PR=['):html.index('];',html.index('const PR=['))]
exist=[dict(id=m[0],b=m[1],n=m[2],f=m[3]) for m in re.findall(r"\{id:'(\w+)',b:[\"']([^\"']+)[\"'],n:'([^']+)',f:'(\w+)'",pr_src)]
CODE=re.compile(r'(?<![A-Za-z0-9])[A-Z]{1,3}\+?\d{1,2}[A-Z]?(?![A-Za-z0-9])|\d號')
def sim(a,b):
    a=set(re.sub(r'\W','',a)); b=set(re.sub(r'\W','',b)); return len(a&b)/max(1,len(a))
merge=collections.defaultdict(list); used=set()
for e in exist:
    eb=bkey(e['b']); ec=set(CODE.findall(e['n']))
    for k,g in groups.items():
        if k[0]!=e['f'] or k[1]!=eb: continue
        nm=g['xs'][0]['name']; gc=set(CODE.findall(nm))
        pe,pg=prot(e['n']),prot(nm)
        if pe!=pg and '綜合' not in (pe,pg): continue
        sc=sim(e['n'],clean(nm))
        if ec: ok=bool(ec&gc)
        elif gc: ok=sc>=1 and eb!='royal'
        else: ok=sc>.8
        if ok:
            merge[e['id']]+= g['xs']; used.add(k)
gen=[]
for k,g in groups.items():
    if k in used: continue
    xs=g['xs']; f=k[0]; n0=min((clean(x['name']) for x in xs),key=len) or clean(xs[0]['name'])
    p=dict(id='p'+min(xs,key=lambda x:x['rank'])['id'],b=g['b'],n=n0,f=f,pr=prot(' '.join(x['name'] for x in xs)),st=stage(xs[0]['name']),src='momo',est=1,rank=min(x['rank'] for x in xs),mi=[x['id'] for x in xs])
    if re.search(r'體重|體態|低卡|胖貓',n0): p['light']=1
    if f=='dry':
        sz={}
        for x in xs: kg=x['total_kg']; sz[kg]=min(sz.get(kg,10**9),x['price'])
        p.update(kcal=3800,sizes=sorted([[kg,pr] for kg,pr in sz.items()]))
    else:
        vs={}; po={}
        for x in xs:
            g_=round(x['unit_kg']*1000); pk=x['packs']; vs[(g_,pk)]=min(vs.get((g_,pk),10**9),x['price']); po[(g_,pk)]=pouch(x['name'])
        p.update(k100=100,vs=sorted([[g_,pk,pr]+([1] if po[(g_,pk)] else []) for (g_,pk),pr in vs.items()]))
    gen.append(p)
upd={}
for eid,xs in merge.items():
    upd[eid]=[[x['total_kg'],x['price']] if x['f']=='dry' else [round(x['unit_kg']*1000),x['packs'],x['price']]+([1] if pouch(x['name']) else []) for x in xs]
block='// GEN:BEGIN 由 scripts/gen_site.py 產生（momo '+DATE+'），請勿手改\nconst GEN='+json.dumps(gen,ensure_ascii=False,separators=(',',':'))+';\nconst UPD='+json.dumps(upd,ensure_ascii=False,separators=(',',':'))+';\nconst PRICE_DATE='+json.dumps(DATE)+';\n// GEN:END'
if '// GEN:BEGIN' in html: html=re.sub(r'// GEN:BEGIN[\s\S]*?// GEN:END',lambda m:block,html)
else:
    i=html.index('const PR=['); html=html[:i]+block+'\n'+html[i:]
open(HTML,'w',encoding='utf-8').write(html)
c=collections.Counter(p['f'] for p in gen)
print('new',c,'merged existing',len(merge),'of',len(exist),'unmatched existing',[e['id'] for e in exist if e['id'] not in merge])

