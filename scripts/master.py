import re,json,sys,collections,statistics as st
rows=json.load(open(sys.argv[1],encoding='utf-8'))
AL={'Nutram紐頓':'Nutram 紐頓','德國Granatapet葛蕾特':'Granatapet 葛蕾特','LCB藍帶廚坊':'LCB 藍帶廚坊','義大利Schesir鮮時':'Schesir 鮮時','Fantastic98% 超越汪喵':'汪喵星球'}
for x in rows: x['brand']=AL.get(x['brand'],x['brand'])
def line(n):
    n=re.sub(r'【[^】]+】','',n)
    n=re.sub(r'官方直營|台灣公司貨|momo獨家|新客組|特惠兩箱組|網路獨家組|\d+包組|\d+入組|\d+箱|效期[^ ]*','',n)
    n=re.sub(r'\d+(\.\d+)?\s*(kg|KG|Kg|公斤|lb|LB|lbs|磅|g|G|公克|克|oz|盎司)','',n)
    n=re.sub(r'[*xX×]\s*\d+\s*(入|包|罐|EA)?|\d+\s*(入|罐|包)','',n)
    n=re.sub(r'[\s/／｜|\-()（）〔〕《》,，、+]+',' ',n).strip()
    return n[:16]
g=collections.defaultdict(list)
for x in rows:
    x['line']=line(x['name']); g[(x['f'],x['brand'],x['line'])].append(x)
master=[]
for (f,b,l),xs in g.items():
    ppk=[x['ntd_per_kg'] for x in xs if x['ntd_per_kg']]
    master.append(dict(f=f,brand=b,line=l,listings=len(xs),sizes=sorted({x['total_kg'] for x in xs if x['total_kg']}),
        best_rank=min(x['rank'] for x in xs),min_ntd_per_kg=min(ppk) if ppk else None,rx=any(x['rx'] for x in xs),ids=[x['id'] for x in xs]))
master.sort(key=lambda m:(m['f'],m['best_rank']))
json.dump(master,open(sys.argv[2],'w',encoding='utf-8'),ensure_ascii=False,indent=0)
json.dump(rows,open(sys.argv[1],'w',encoding='utf-8'),ensure_ascii=False,indent=0)
C=collections.Counter
print('master lines',C(m['f'] for m in master),'brands',{f:len({m['brand'] for m in master if m['f']==f}) for f in('dry','wet')})
for f,unit,mul in(('dry','元/kg',1),('wet','元/100g',0.1)):
    v=[x['ntd_per_kg'] for x in rows if x['f']==f and x['ntd_per_kg'] and not x['rx']]
    q=st.quantiles(v,n=4)
    print(f,unit,'P25/中位/P75',[round(a*mul) for a in q],'min',round(min(v)*mul),'max',round(max(v)*mul))
