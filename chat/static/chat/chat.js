// ============================================
// chat.js
// AIプログラミングチューター用フロントJS
// ============================================

// =======================
// セッションID管理
// =======================
if (!localStorage.getItem("session_id")) {
  localStorage.setItem("session_id", "session_" + Date.now());
}
const sessionId = localStorage.getItem("session_id");

// =======================
// CodeMirror 初期化
// =======================
const codeMirror = CodeMirror.fromTextArea(document.getElementById("code"), {
  mode: "python",
  theme: "default",
  lineNumbers: true,
  indentUnit: 4,
  autoCloseBrackets: true,
  viewportMargin: Infinity
});

// =======================
// ページロード時に履歴を取得して表示
// =======================

/*
window.addEventListener("load", async () => {
  const chatBox = document.getElementById("chat-box");
  try {
    const res = await fetch("/api/history/");
    const data = await res.json();

    data.history.forEach(msg => {
      const wrapper = document.createElement("div");
      wrapper.classList.add("message", msg.role === "user" ? "user-message" : "ai-message");
      wrapper.innerHTML = `<div class="bubble ${msg.role === "user" ? "user-bubble" : "ai-bubble"}">
        ${marked.parse(msg.content)}
      </div>`;
      chatBox.appendChild(wrapper);
    });

    chatBox.scrollTop = chatBox.scrollHeight;
  } catch (err) {
    console.error("履歴の取得に失敗:", err);
  }
});
*/

// =======================
// 新しい会話開始ボタン
// =======================
const newSessionBtn = document.getElementById("new-session");
if (newSessionBtn) {
  newSessionBtn.addEventListener("click", () => {
    localStorage.setItem("session_id", "session_" + Date.now());
    location.reload();
  });
}

// =======================
// 送信ボタン処理
// =======================
document.getElementById("send-btn").addEventListener("click", async () => {
  const problem = document.getElementById("problem").value.trim();
  const question = document.getElementById("question").value.trim();
  const code = codeMirror.getValue();
  const skillLevel = document.getElementById("skill-level").value;


  if (!problem && !question && !code) return;

  const chatBox = document.getElementById("chat-box");

  // 🧑‍💻 ユーザーの吹き出し表示
  const userBubble = `
    <div class="bubble user-bubble">
      👤 <strong>質問:</strong> ${marked.parse(question)}
      ${problem ? `<br><strong>問題文:</strong><br>${marked.parse(problem)}` : ""}
      ${code ? `<br><strong>コード:</strong><br>${marked.parse("```python\n" + code + "\n```")}` : ""}
    </div>`;
  const userWrapper = document.createElement("div");
  userWrapper.classList.add("message", "user-message");
  userWrapper.innerHTML = userBubble;
  chatBox.appendChild(userWrapper);
  chatBox.scrollTop = chatBox.scrollHeight;

  // 🎯 AIに送信
  try {
    const res = await fetch("/api/chat/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        problem,
        question,
        code,
        session_id: sessionId,
        skill_level: skillLevel
      })
    });

    const data = await res.json();
    const aiReply = data.reply || data.error || "エラーが発生しました。";

    // 🤖 AIの吹き出し表示
    const aiWrapper = document.createElement("div");
    aiWrapper.classList.add("message", "ai-message");
    aiWrapper.innerHTML = `<div class="bubble ai-bubble">${marked.parse(aiReply)}</div>`;
    chatBox.appendChild(aiWrapper);

    // コードブロックをハイライト
    chatBox.querySelectorAll("pre code").forEach((el) => {
      hljs.highlightElement(el);
    });

    chatBox.scrollTop = chatBox.scrollHeight;

    // 入力欄リセット
    document.getElementById("question").value = "";
    codeMirror.setValue("");
  } catch (err) {
    console.error("送信エラー:", err);
  }
});
// =======================
// 会話入力専用の処理
// =======================
  document.getElementById("chat-input").addEventListener("keypress", async (e) => {
    if (e.key !== "Enter") return;

    const message = e.target.value.trim();
    if (!message) return;

    const chatBox = document.getElementById("chat-box");

    // ユーザー吹き出し表示
    const userWrapper = document.createElement("div");
    userWrapper.classList.add("message", "user-message");
    userWrapper.innerHTML = `<div class="bubble user-bubble">👤 ${marked.parse(message)}</div>`;
    chatBox.appendChild(userWrapper);
    chatBox.scrollTop = chatBox.scrollHeight;

    // AI に送信
    try {
        const res = await fetch("/api/chat/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                problem: "",       // 問題文は更新しない
                question: message, // 会話内容を question に渡す
                code: "",          // コードは更新しない
                session_id: sessionId,
                skill_level: skillLevel
            })
        });

        const data = await res.json();
        const aiReply = data.reply || data.error || "エラーが発生しました。";

        // AI 吹き出し表示
        const aiWrapper = document.createElement("div");
        aiWrapper.classList.add("message", "ai-message");
        aiWrapper.innerHTML = `<div class="bubble ai-bubble">🤖 ${marked.parse(aiReply)}</div>`;
        chatBox.appendChild(aiWrapper);
        chatBox.scrollTop = chatBox.scrollHeight;

        e.target.value = ""; // 入力欄リセット
    } catch (err) {
        console.error("送信エラー:", err);
    }
});

// =======================
// 履歴削除の処理
// =======================
document.getElementById("delete-history").addEventListener("click", async () => {
    if (!confirm("この会話の履歴を削除しますか？")) return;

    try {
        const res = await fetch("/api/delete_history/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId })
        });
        const data = await res.json();

        if (data.deleted) {
            alert("履歴を削除しました。");
            // チャット表示をクリア
            const chatBox = document.getElementById("chat-box");
            chatBox.innerHTML = "";
        } else {
            alert("削除できる履歴がありませんでした。");
        }
    } catch (err) {
        console.error(err);
        alert("履歴削除に失敗しました。");
    }
});
