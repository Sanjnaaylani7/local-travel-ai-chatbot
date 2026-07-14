/**
 * Embeddable chat widget for the Local Travel AI Chatbot.
 * Talks to the FastAPI backend: POST /api/session/, POST /api/chat/.
 */
(function () {
  "use strict";

  var API_BASE = (window.CHATBOT_API_BASE || "").replace(/\/$/, "");
  var STORAGE_KEY = "travel_chat_session_id";

  var launcher = document.getElementById("chat-launcher");
  var widget = document.getElementById("chat-widget");
  var closeBtn = document.getElementById("close-chat");
  var form = document.getElementById("chat-input");
  var input = document.getElementById("user-message");
  var messages = document.getElementById("messages");
  var typing = document.getElementById("typing-indicator");

  var sessionId = null;

  function toggle(open) {
    var show = open === undefined ? widget.classList.contains("hidden") : open;
    widget.classList.toggle("hidden", !show);
    launcher.classList.toggle("hidden", show);
    if (show) {
      input.focus();
      ensureSession();
    }
  }

  function addMessage(text, role, sources) {
    var el = document.createElement("div");
    el.className = "message " + role;
    el.textContent = text;

    if (sources && sources.length) {
      var srcWrap = document.createElement("div");
      srcWrap.className = "sources";
      var seen = {};
      sources.forEach(function (s) {
        if (!s.url || seen[s.url]) return;
        seen[s.url] = true;
        var a = document.createElement("a");
        a.href = s.url;
        a.target = "_blank";
        a.rel = "noopener";
        a.textContent = s.title || s.url;
        srcWrap.appendChild(a);
      });
      if (srcWrap.childNodes.length) el.appendChild(srcWrap);
    }

    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
  }

  function setTyping(on) {
    typing.classList.toggle("hidden", !on);
    if (on) messages.scrollTop = messages.scrollHeight;
  }

  async function ensureSession() {
    if (sessionId) return sessionId;
    var stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      sessionId = stored;
      return sessionId;
    }
    try {
      var res = await fetch(API_BASE + "/api/session/", { method: "POST" });
      var data = await res.json();
      sessionId = data.session_id;
      localStorage.setItem(STORAGE_KEY, sessionId);
    } catch (e) {
      // Session is optional; the chat endpoint will create one if needed.
    }
    return sessionId;
  }

  async function sendMessage(text) {
    addMessage(text, "user");
    setTyping(true);
    try {
      await ensureSession();
      var res = await fetch(API_BASE + "/api/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text, language: "auto" }),
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      var data = await res.json();
      if (data.session_id) {
        sessionId = data.session_id;
        localStorage.setItem(STORAGE_KEY, sessionId);
      }
      addMessage(data.response, "bot", data.sources);
    } catch (e) {
      addMessage("Sorry, something went wrong. Please try again.", "bot");
    } finally {
      setTyping(false);
    }
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var text = input.value.trim();
    if (!text) return;
    input.value = "";
    sendMessage(text);
  });

  launcher.addEventListener("click", function () { toggle(true); });
  closeBtn.addEventListener("click", function () { toggle(false); });
})();
