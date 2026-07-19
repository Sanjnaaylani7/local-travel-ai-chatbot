/**
 * Embeddable chat widget for the Local Travel AI Chatbot.
 * Talks to the FastAPI backend: POST /api/session/, POST /api/chat/.
 * Implements the spec (§8.1): welcome message, suggested questions, typing
 * indicator, retry state, disclaimer, and human escalation (WhatsApp/email).
 */
(function () {
  "use strict";

  var API_BASE = (window.CHATBOT_API_BASE || "").replace(/\/$/, "");
  var CFG = window.CHATBOT_CONFIG || {};
  var STORAGE_KEY = "travel_chat_session_id";

  var launcher = document.getElementById("chat-launcher");
  var widget = document.getElementById("chat-widget");
  var closeBtn = document.getElementById("close-chat");
  var form = document.getElementById("chat-input");
  var input = document.getElementById("user-message");
  var messages = document.getElementById("messages");
  var suggestions = document.getElementById("suggestions");
  var typing = document.getElementById("typing-indicator");

  var sessionId = null;
  var started = false;
  var lastUserMessage = null;

  function toggle(open) {
    var show = open === undefined ? widget.classList.contains("hidden") : open;
    widget.classList.toggle("hidden", !show);
    launcher.classList.toggle("hidden", show);
    if (show) {
      input.focus();
      ensureSession();
      if (!started) {
        started = true;
        showWelcome();
      }
    }
  }

  function scrollDown() {
    messages.scrollTop = messages.scrollHeight;
  }

  function showWelcome() {
    if (CFG.welcome) addMessage(CFG.welcome, "bot");
    renderSuggestions(CFG.suggestions || []);
  }

  function renderSuggestions(list) {
    suggestions.innerHTML = "";
    list.forEach(function (q) {
      var chip = document.createElement("button");
      chip.className = "suggestion";
      chip.type = "button";
      chip.textContent = q;
      chip.addEventListener("click", function () {
        suggestions.innerHTML = "";
        sendMessage(q);
      });
      suggestions.appendChild(chip);
    });
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
        a.textContent = s.title && s.title !== "No Title" ? s.title : "Source";
        srcWrap.appendChild(a);
      });
      if (srcWrap.childNodes.length) el.appendChild(srcWrap);
    }

    messages.appendChild(el);
    scrollDown();
    return el;
  }

  function addEscalation(container) {
    var wrap = document.createElement("div");
    wrap.className = "escalation";
    if (CFG.whatsapp) {
      var wa = document.createElement("a");
      wa.href = "https://wa.me/" + CFG.whatsapp;
      wa.target = "_blank";
      wa.rel = "noopener";
      wa.className = "escalate-btn whatsapp";
      wa.textContent = "Chat on WhatsApp";
      wrap.appendChild(wa);
    }
    if (CFG.contactEmail) {
      var mail = document.createElement("a");
      mail.href = "mailto:" + CFG.contactEmail;
      mail.className = "escalate-btn email";
      mail.textContent = "Email our team";
      wrap.appendChild(mail);
    }
    (container || messages).appendChild(wrap);
    scrollDown();
  }

  function addRetry(text) {
    var el = addMessage(text, "bot");
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "retry-btn";
    btn.textContent = "Retry";
    btn.addEventListener("click", function () {
      el.remove();
      if (lastUserMessage) sendMessage(lastUserMessage, true);
    });
    el.appendChild(btn);
    scrollDown();
  }

  function setTyping(on) {
    typing.classList.toggle("hidden", !on);
    if (on) scrollDown();
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

  async function sendMessage(text, isRetry) {
    lastUserMessage = text;
    if (!isRetry) addMessage(text, "user");
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
      // Escalate to a human when the answer isn't grounded in the knowledge base.
      if (data.grounded === false) addEscalation();
    } catch (e) {
      addRetry("Sorry, I couldn't reach the assistant. Please try again.");
    } finally {
      setTyping(false);
    }
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var text = input.value.trim();
    if (!text) return;
    input.value = "";
    suggestions.innerHTML = "";
    sendMessage(text);
  });

  launcher.addEventListener("click", function () { toggle(true); });
  closeBtn.addEventListener("click", function () { toggle(false); });
})();
