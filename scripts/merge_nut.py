# 把 data/ingredients/*.json 的口味成分併到網站：寫入 public/index.html 的 NUTGEN 區塊
import json,re,sys,glob
site=json.load(open(sys.argv[1]))   # node 匯出的 PR/NUT 清單
HTML='public/index.html'
recs=[r for f in sorted(glob.glob('data/ingredients/*.json')) for r in json.load(open(f,encoding='utf-8'))]
PR=site['PR']; have=set(site['NUT'])
def finds(r):
    if r.get('site_ids'): return [i for i in r['site_ids'] if any(p['id']==i for p in PR)]
    if r.get('site_id'): return [r['site_id']]
    if r.get('regex'):
        b=r['brand'].split()[0].lower()
        return [p['id'] for p in PR if p['f']==r.get('f','dry') and p['b'].split()[0].lower().startswith(b[:4]) and re.search(r['regex'],p['n'])]
    x=find(r); return (x if isinstance(x,list) else [x]) if x else []
def find(r):
    if r.get('site_id'): return r['site_id']
    b=r['brand'].split()[0].lower()
    cands=[p for p in PR if p['f']==r.get('f','dry') and p['b'].split()[0].lower().startswith(b[:4])]
    if r.get('site_code'):
        c=re.escape(r['site_code'])
        hit=[p for p in cands if re.search(r'(?<![A-Za-z0-9+])'+c+r'(?![A-Za-z0-9+])',p['n'])]
        return [h['id'] for h in hit] if hit else None
    if r.get('match'):
        hit=[p for p in cands if all(w in p['n'] for w in r['match'].split())]
        return hit[0]['id'] if hit else None
def me(ga):
    ash=ga.get('ash',7); nfe=max(0,100-ga['p']-ga['f']-ga.get('fi',0)-ga.get('m',10)-ash)
    return round(10*(3.5*ga['p']+8.5*ga['f']+3.5*nfe))
by={}
miss=[]
for r in recs:
    if r.get('status')=='unverified': continue
    if not r.get('ga') and not r.get('kcal_kg'): continue
    ids=[i for i in finds(r) if i not in have]
    if not ids: miss.append((r['brand'],r['line'])); continue
    for sid in ids: by.setdefault(sid,[]).append(r)
out=[]
for sid,rs in by.items():
    def one(r):
        st={'kitten':'growth'}.get(r.get('stage'),r.get('stage') or 'all')
        if not r.get('ga'): return {'nut':None,'set':({'k100':round(r['kcal_kg']/10,1)} if r.get('f')=='wet' else {'kcal':r['kcal_kg']})|{'ks':'o'},'flavor':r.get('flavor')}
        nut={'t':'t' if ('皇家' in r['brand'] or 'Hill' in r['brand']) else 'g','stage':st,'ga':r['ga'],'src':r['sources'][0]['url'] if r['sources'] else ''}
        if r.get('ingredients'): nut['ing']=r['ingredients']
        if r.get('ingredients') and '皇家' in r['brand']: nut['full']=1
        k=r.get('kcal_kg'); kk=k if k else me(r['ga']); ks='o' if k else 'c'
        s={'k100':round(kk/10,1),'ks':ks} if r.get('f')=='wet' else {'kcal':kk,'ks':ks}
        pr={'禽肉':'雞','魚':'魚'}.get(r.get('protein_source'),'綜合')
        s.update(pr=pr)
        if r.get('light'): s['light']=1
        return {'nut':nut,'set':s,'flavor':r.get('flavor')}
    fl=[one(r) for r in rs]
    keep=any(r.get('status')=='unverified' and sid in finds(r) for r in recs)
    out.append({'id':sid,'fl':fl,'keep':keep})
blk='// NUTGEN:BEGIN 由 scripts/merge_nut.py 產生，請勿手改\nconst NUTGEN='+json.dumps(out,ensure_ascii=False,separators=(',',':'))+';\n// NUTGEN:END'
h=open(HTML,encoding='utf-8').read()
if '// NUTGEN:BEGIN' in h: h=re.sub(r'// NUTGEN:BEGIN[\s\S]*?// NUTGEN:END',lambda m:blk,h)
else:
    a='PR.forEach(p=>{if(NUT[p.id])'
    i=h.index(a); h=h[:i]+blk+'\n'+h[i:]
open(HTML,'w',encoding='utf-8').write(h)
print('items',len(out),'flavors',sum(len(x['fl']) for x in out)); print('skipped',miss)
