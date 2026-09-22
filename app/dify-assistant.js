(function () {
  "use strict";

  var CHAT_URL = "https://udify.app/chat/YiRq8GHSXui6nEF9";

  function icon(name) {
    var icons = {
      wheel: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="2.4"/><path d="M3.8 10.4h5.9M14.3 10.4h5.9M10.7 14.1l-2.4 5.1M13.3 14.1l2.4 5.1"/></svg>',
      close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>',
      external: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 4h5v5M20 4l-9 9"/><path d="M18 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h6"/></svg>'
    };
    return icons[name];
  }

  function createAssistant() {
    if (document.querySelector(".ds-assistant")) return;

    var root = document.createElement("aside");
    root.className = "ds-assistant";
    root.setAttribute("aria-label", "科目一智能助手");

    var launcher = document.createElement("button");
    launcher.className = "ds-assistant__launcher";
    launcher.type = "button";
    launcher.setAttribute("aria-label", "打开科目一智能助手");
    launcher.setAttribute("aria-expanded", "false");
    launcher.innerHTML = icon("wheel") + '<span class="ds-assistant__badge" aria-hidden="true"></span>';

    var hint = document.createElement("span");
    hint.className = "ds-assistant__hint";
    hint.textContent = "有疑问？问问科目一助手";

    var panel = document.createElement("section");
    panel.className = "ds-assistant__panel";
    panel.setAttribute("aria-hidden", "true");
    panel.innerHTML =
      '<header class="ds-assistant__header">' +
        '<span class="ds-assistant__mark">' + icon("wheel") + '</span>' +
        '<span class="ds-assistant__title"><strong>科目一助手</strong><span>随时解答驾考疑问</span></span>' +
        '<span class="ds-assistant__actions">' +
          '<a class="ds-assistant__external" href="' + CHAT_URL + '" target="_blank" rel="noopener noreferrer" aria-label="在新窗口打开助手" title="在新窗口打开">' + icon("external") + '</a>' +
          '<button class="ds-assistant__icon-button" type="button" aria-label="收起助手" title="收起">' + icon("close") + '</button>' +
        '</span>' +
      '</header>' +
      '<div class="ds-assistant__body"><div class="ds-assistant__loading">助手正在接入…</div></div>';

    root.appendChild(launcher);
    root.appendChild(hint);
    root.appendChild(panel);
    document.body.appendChild(root);

    var body = panel.querySelector(".ds-assistant__body");
    var closeButton = panel.querySelector(".ds-assistant__icon-button");
    var frame = null;

    function ensureFrame() {
      if (frame) return;
      frame = document.createElement("iframe");
      frame.className = "ds-assistant__frame";
      frame.title = "科目一智能助手对话窗口";
      frame.src = CHAT_URL;
      frame.allow = "microphone; clipboard-read; clipboard-write";
      frame.addEventListener("load", function () {
        var loading = body.querySelector(".ds-assistant__loading");
        if (loading) loading.remove();
      });
      body.appendChild(frame);
    }

    function setOpen(open) {
      root.classList.toggle("ds-assistant--open", open);
      launcher.setAttribute("aria-expanded", String(open));
      launcher.setAttribute("aria-label", open ? "收起科目一智能助手" : "打开科目一智能助手");
      panel.setAttribute("aria-hidden", String(!open));
      if (open) ensureFrame();
    }

    launcher.addEventListener("click", function () {
      setOpen(!root.classList.contains("ds-assistant--open"));
    });
    closeButton.addEventListener("click", function () {
      setOpen(false);
      launcher.focus();
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && root.classList.contains("ds-assistant--open")) {
        setOpen(false);
        launcher.focus();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", createAssistant, { once: true });
  } else {
    createAssistant();
  }
})();
