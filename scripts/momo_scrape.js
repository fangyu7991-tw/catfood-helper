// 在 momo 分頁（www.momoshop.com.tw）用 Claude in Chrome 的 javascript_tool 執行。
// 依「月銷量」排序（searchType=6）抓搜尋頁，解析頁面內的 JSON-LD ItemList（name、offers.price、url 內的 i_code）。
// 背景執行，結果放在 window.__inv；window.__done = true 代表跑完。javascript_tool 回傳有長度限制，
// 讀結果時把 window.__rows 寫進 document.body 再用 get_page_text 讀出。
// 若 momo 改版抓不到，先打開一頁搜尋結果確認網址參數與 JSON-LD 結構，再調整這支程式。
(async () => {
  const JOBS = [['貓飼料', 20, 'dry'], ['貓主食罐', 15, 'wet'], ['貓餐包', 6, 'wet'], ['貓 主食 濕糧', 4, 'wet']];
  const EX = /犬|狗|零食|肉泥|副食|湯罐|點心|潔牙|貓砂|保健品|營養膏|化毛膏|玩具|碗|餵食器|試吃|即期/;
  const inv = window.__inv = {}; window.__done = false; window.__log = [];
  for (const [kw, pages, f] of JOBS) {
    let rank = 0;
    for (let p = 1; p <= pages; p++) {
      try {
        const u = '/search/' + encodeURIComponent(kw) + '?searchType=6&curPage=' + p + '&viewport=desktop&cateLevel=0&_isFuzzy=0';
        const h = await (await fetch(u, { credentials: 'include' })).text();
        const d = new DOMParser().parseFromString(h, 'text/html');
        for (const s of d.querySelectorAll('script[type="application/ld+json"]')) {
          let j; try { j = JSON.parse(s.textContent); } catch { continue; }
          const list = [].concat(j).find(x => x && x['@type'] === 'ItemList');
          if (!list) continue;
          for (const el of list.itemListElement || []) {
            const it = el.item || el; rank++;
            const id = ((it.url || '').match(/i_code=(\d+)/) || [])[1];
            const price = Math.round(+((it.offers && (it.offers.price || it.offers.lowPrice)) || 0));
            const name = (it.name || '').replace(/\([^)\d]*\)|（[^）\d]*）/g, '').replace(/\s+/g, ' ').trim().slice(0, 70);
            if (!id || !price || EX.test(name) || inv[id]) continue;
            inv[id] = [id, f, rank, price, name];
          }
        }
        window.__log.push(kw + ' p' + p + ' ok');
      } catch (e) { window.__log.push(kw + ' p' + p + ' ' + e.message); }
      await new Promise(r => setTimeout(r, 1200));
    }
  }
  window.__rows = Object.values(inv).map(r => r.join('|')).join('\n');
  window.__done = true;
})();
