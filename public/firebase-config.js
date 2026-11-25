// Firebase 網頁設定（這些值會公開在網頁上，屬正常；資料安全由 firestore.rules 保護）
export const firebaseConfig = {
  apiKey: "AIzaSyAJanY6QV9mnP9TFaZIplSh96AhlZxROOY",
  authDomain: "catfood-helper.firebaseapp.com",
  projectId: "catfood-helper",
  storageBucket: "catfood-helper.firebasestorage.app",
  messagingSenderId: "791570343579",
  appId: "1:791570343579:web:490a59c99b7a81090ac83e"
};

// Apple 登入需要 Apple Developer Program（年費 US$99）並在 Firebase 開啟 Apple 供應商後，才改成 true。
export const appleEnabled = false;
