# 貓糧預算小幫手：網站版上線步驟

這個資料夾是可以直接上線的網站：前端放在 `public/`，登入用 Firebase Authentication，Home kit 存在 Cloud Firestore，網站放在 Firebase Hosting。用量小的時候都在免費方案（Spark）內。

不登入也能用，資料只存在那台裝置。登入後會存到帳號，換手機或電腦都看得到。第一次登入時，會把那台裝置上已經填的資料一起存進帳號。

---

## 一、建立 Firebase 專案（約 10 分鐘，用瀏覽器操作）

1. 打開 https://console.firebase.google.com ，用你的 Google 帳號登入，按「建立專案」。名稱可以填 `catfood-helper`，Google Analytics 可以先不開。
2. 進入專案後，在首頁按 `</>`（網頁）圖示「新增應用程式」，暱稱隨意，**不用**勾選 Firebase Hosting（之後用指令設定）。
3. 畫面會出現一段 `const firebaseConfig = { ... }`。把大括號裡的值，逐一貼到 `public/firebase-config.js` 對應的欄位。
4. 左側選單 **Authentication** →「開始使用」→「登入方式」分頁 → 選 **Google** → 啟用 → 填支援電子郵件 → 儲存。
5. 左側選單 **Firestore Database** →「建立資料庫」→ 位置選 `asia-east1（台灣）` → 選「以正式版模式啟動」→ 建立。

## 二、上線（約 10 分鐘，需要電腦的終端機）

1. 安裝 Node.js（https://nodejs.org ，選 LTS 版）。
2. 打開終端機，執行：
   ```
   npm install -g firebase-tools
   firebase login
   ```
3. 切到這個資料夾（有 `firebase.json` 的那層），執行：
   ```
   firebase use --add
   ```
   選剛建立的專案，別名填 `default`。
4. 部署網站和資料庫規則：
   ```
   firebase deploy
   ```
5. 完成後終端機會顯示網址，例如 `https://catfood-helper.web.app`。打開、按右上角「登入」測試。

之後改了內容，只要再執行一次 `firebase deploy`。

### 在自己電腦先測試（選用）
```
firebase emulators:start --only hosting
```
打開 http://localhost:5000 。`localhost` 預設就在 Firebase 的授權網域裡，可以直接測 Google 登入。

---

## 三、加上 Apple 登入（選用）

Apple 登入需要 **Apple Developer Program**（年費 US$99）。上線前可以先只開 Google。

1. 在 Apple Developer 後台建立 **Services ID**，啟用 Sign in with Apple；Return URL 填 `https://<你的專案ID>.firebaseapp.com/__/auth/handler`。
2. 建立一把 **Key**（勾選 Sign in with Apple），下載 `.p8` 檔，記下 Key ID 和 Team ID。
3. Firebase 主控台 → Authentication → 登入方式 → **Apple** → 啟用，填入 Services ID、Team ID、Key ID 和 `.p8` 的內容。
4. 把 `public/firebase-config.js` 最下面的 `appleEnabled` 改成 `true`，重新 `firebase deploy`。

## 四、綁自己的網域（選用）

Firebase 主控台 → Hosting →「新增自訂網域」，照指示到網域商加 DNS 記錄。綁好後，到 Authentication → 設定 →「已授權網域」把新網域加進去，否則登入視窗會被擋。

---

## 資料怎麼存、安全嗎

- `users/{uid}`：主要資料（貓咪資料、我的品項、口味標記、預算、推薦快照）。
- `users/{uid}/cats/{貓咪ID}`：每隻貓的照片（大頭照、BCS 俯視與側面照）。分開存是因為 Firestore 單一文件上限 1 MiB。
- `firestore.rules` 規定**每個人只能讀寫自己的資料**，別人拿到網址也看不到你的 Home kit。
- `firebase-config.js` 裡的 apiKey 不是密碼，放在網頁上是正常的；資料安全靠上面的規則保護。

## 和 claude.ai 版本的差異

- **「用 AI 判讀照片」在網站版不會出現。** 那個功能用的是 claude.ai 內建的 Claude 呼叫；網站版要另外接 AI API（需要後端和 API 金鑰），手動 BCS 問卷照常可用。
- 其他功能（預算推薦、Home kit、我的品項、飼料資料庫、營養分析）都相同。

## 上線前建議再補

- **隱私權政策頁**：公開讓陌生人註冊、或要開 Apple 登入時，最好有一頁說明收集哪些資料（帳號名稱、email、貓咪資料與照片）和怎麼刪除。
- **刪除帳號功能**：目前可以登出，還沒有「刪除我的資料」按鈕。
- **範例資料**：沒填過資料的新訪客，看到的是範例貓（島灰、麻糬、阿福）。正式對外前可以改成空白，或加上「這是範例」的標示。
