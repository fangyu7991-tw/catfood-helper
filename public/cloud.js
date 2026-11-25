// 帳號登入與雲端存檔（Firebase Authentication + Cloud Firestore）
// 資料結構：
//   users/{uid}              主要狀態（貓咪資料不含照片、我的品項、口味標記、預算、推薦快照）
//   users/{uid}/cats/{catId} 每隻貓的照片（大頭照、BCS 俯視與側面照），分開存以免超過單一文件 1 MiB 上限
import { firebaseConfig, appleEnabled } from './firebase-config.js';

const V = '10.12.2';
const $ = id => document.getElementById(id);
const acct = $('acct'), modal = $('loginM'), err = $('loginErr');

const Cloud = window.Cloud = { user: null, queue() {} };

if (!firebaseConfig.apiKey) {
  console.info('[cloud] firebase-config.js 尚未設定，以訪客模式運作（資料只存在這台裝置）');
} else {
  start().catch(e => { console.error('[cloud] 無法載入 Firebase', e); });
}

async function start() {
  const [{ initializeApp }, A, F] = await Promise.all([
    import(`https://www.gstatic.com/firebasejs/${V}/firebase-app.js`),
    import(`https://www.gstatic.com/firebasejs/${V}/firebase-auth.js`),
    import(`https://www.gstatic.com/firebasejs/${V}/firebase-firestore.js`),
  ]);
  const app = initializeApp(firebaseConfig);
  const auth = A.getAuth(app), db = F.getFirestore(app);
  auth.languageCode = 'zh-TW';

  acct.hidden = false;
  if (appleEnabled) modal.querySelector('[data-sso="apple"]').hidden = false;

  // ---- 登入／登出 ----
  const open = () => { err.textContent = ''; modal.hidden = false; modal.querySelector('.sso').focus(); };
  const close = () => { modal.hidden = true; };
  modal.addEventListener('click', e => {
    if (e.target === modal || e.target.closest('[data-close]')) close();
    const b = e.target.closest('[data-sso]'); if (!b) return;
    const provider = b.dataset.sso === 'apple'
      ? Object.assign(new A.OAuthProvider('apple.com'), {}) : new A.GoogleAuthProvider();
    if (b.dataset.sso === 'apple') { provider.addScope('email'); provider.addScope('name'); }
    else provider.setCustomParameters({ prompt: 'select_account' });
    err.textContent = '';
    A.signInWithPopup(auth, provider).then(close).catch(e => {
      if (e.code === 'auth/popup-blocked' || e.code === 'auth/operation-not-supported-in-this-environment') return A.signInWithRedirect(auth, provider);
      if (e.code === 'auth/popup-closed-by-user' || e.code === 'auth/cancelled-popup-request') return;
      err.textContent = '登入沒有成功，請再試一次（' + (e.code || e.message) + '）';
    });
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !modal.hidden) close(); });
  A.getRedirectResult(auth).catch(e => { err.textContent = '登入沒有成功（' + e.code + '）'; });

  let status = '';
  const paint = () => {
    const u = Cloud.user;
    if (!u) { acct.innerHTML = `<button type="button" class="btn sm" id="loginBtn">登入</button>`; $('loginBtn').onclick = open; return; }
    const name = u.displayName || u.email || '已登入';
    const pic = u.photoURL ? `<img src="${u.photoURL}" alt="" referrerpolicy="no-referrer">` : `<span class="ini">${name.slice(0, 1)}</span>`;
    acct.innerHTML = `<span class="who">${pic}<span><span class="nm"></span><br><span class="st">${status}</span></span></span><button type="button" class="btn ghost sm" id="logoutBtn">登出</button>`;
    acct.querySelector('.nm').textContent = name;
    $('logoutBtn').onclick = async () => { await flush(); await A.signOut(auth); };
  };

  // ---- 存檔 ----
  const userRef = () => F.doc(db, 'users', Cloud.user.uid);
  const catRef = id => F.doc(db, 'users', Cloud.user.uid, 'cats', id);
  let timer = null, sentPics = {}, knownCats = new Set();
  const setStatus = t => { status = t; const el = acct.querySelector('.st'); if (el) el.textContent = t; };

  async function flush() {
    if (!timer || !Cloud.user) return; clearTimeout(timer); timer = null;
    const S = window.App.get();
    const main = JSON.parse(JSON.stringify({ ...S, cats: S.cats.map(({ photo, pics, aiBusy, ...c }) => c) }));
    try {
      setStatus('儲存中…');
      const jobs = [F.setDoc(userRef(), { state: main, v: 1, updatedAt: F.serverTimestamp() })];
      for (const c of S.cats) {
        const pics = { photo: c.photo || null, top: (c.pics || {}).top || null, side: (c.pics || {}).side || null };
        const sig = JSON.stringify(pics).length + ':' + (pics.photo || '').slice(-40) + (pics.top || '').slice(-40) + (pics.side || '').slice(-40);
        if (sentPics[c.id] !== sig) { jobs.push(F.setDoc(catRef(c.id), pics)); sentPics[c.id] = sig; }
      }
      const now = new Set(S.cats.map(c => c.id));
      for (const id of knownCats) if (!now.has(id)) { jobs.push(F.deleteDoc(catRef(id))); delete sentPics[id]; }
      knownCats = now;
      await Promise.all(jobs);
      setStatus('已存到帳號');
    } catch (e) { console.error(e); setStatus('存檔失敗，稍後會再試'); Cloud.queue(); }
  }
  Cloud.queue = () => { if (!Cloud.user) return; setStatus('有變更，準備儲存…'); clearTimeout(timer); timer = setTimeout(flush, 1200); };
  window.addEventListener('pagehide', () => { flush(); });
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') flush(); });

  // ---- 讀檔 ----
  A.onAuthStateChanged(auth, async u => {
    if (!u) {
      Cloud.user = null; sentPics = {}; knownCats = new Set(); status = '';
      window.App.guest(); paint(); return;
    }
    Cloud.user = u; setStatus('讀取中…'); paint();
    try {
      const snap = await F.getDoc(userRef());
      if (snap.exists()) {
        const S = snap.data().state;
        const pics = await F.getDocs(F.collection(db, 'users', u.uid, 'cats'));
        const P = {}; pics.forEach(d => { P[d.id] = d.data(); });
        S.cats = (S.cats || []).map(c => { const p = P[c.id] || {}; const o = { ...c }; if (p.photo) o.photo = p.photo; if (p.top || p.side) o.pics = { top: p.top || undefined, side: p.side || undefined }; return o; });
        knownCats = new Set(Object.keys(P));
        for (const c of S.cats) { const p = P[c.id] || {}; const pp = { photo: p.photo || null, top: p.top || null, side: p.side || null }; sentPics[c.id] = JSON.stringify(pp).length + ':' + (pp.photo || '').slice(-40) + (pp.top || '').slice(-40) + (pp.side || '').slice(-40); }
        window.App.set(S); setStatus('已同步');
      } else {
        // 第一次登入：把這台裝置上目前的資料存進帳號
        setStatus('第一次登入，正在建立你的 Home kit…');
        timer = 1; await flush();
        setStatus('已把這台裝置的資料存到帳號');
      }
    } catch (e) { console.error(e); setStatus('讀取失敗，請重新整理頁面'); }
    paint();
  });
}
