<script>
/**
 * Injecta um botão "Sair" no topo e renomeia "Mega Loja" para "CASA DO CIGANO".
 * Funciona em SPA: observa mudanças no DOM e reaplica quando necessário.
 */
(function () {
  console.log("[brand-logout] v1 carregado");

  // --- helpers --------------------------------------------------------------
  function post(url, body) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: body ? JSON.stringify(body) : null,
    });
  }
  function get(url) {
    return fetch(url, { credentials: "include" });
  }

  // Renomeia "Mega Loja" no logo/side/topbar
  let brandChanged = false;
  function renameBrand(root = document) {
    if (brandChanged) return; // já fizemos
    const target = "Mega Loja";
    const replacement = "CASA DO CIGANO";

    // varre nós de texto “simples” (sem filhos) para substituir
    const all = root.querySelectorAll("*");
    for (const el of all) {
      if (!el.childNodes || el.childNodes.length !== 1) continue;
      const n = el.childNodes[0];
      if (n.nodeType === 3) {
        const txt = (el.textContent || "").trim();
        if (txt === target) {
          el.textContent = replacement;
          brandChanged = true;
          break;
        }
      }
    }

    // título da aba
    if (document.title && /mega loja/i.test(document.title)) {
      document.title = document.title.replace(/mega loja/ig, "CASA DO CIGANO");
    }
  }

  // Cria botão “Sair”
  function makeLogoutButton(label) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = label || "Sair";
    btn.style.cssText = [
      "padding:8px 12px",
      "border-radius:10px",
      "border:1px solid #334155",
      "background:#0b1220",
      "color:#e5e7eb",
      "cursor:pointer",
      "font-size:14px",
      "line-height:1",
      "display:inline-flex",
      "align-items:center",
      "gap:6px",
      "transition:opacity .15s ease",
    ].join(";");

    btn.addEventListener("mouseenter", () => (btn.style.opacity = "0.85"));
    btn.addEventListener("mouseleave", () => (btn.style.opacity = "1"));

    btn.addEventListener("click", async () => {
      try {
        await post("/api/auth/logout");
      } catch (_) {}
      location.href = "/login";
    });
    return btn;
  }

  // Injeta o botão ao lado do “Registrar Visita” (se achar),
  // senão fixa no topo direito como fallback.
  function injectLogoutButton(user) {
    if (window.__logoutInjected) return;
    const label = "Sair" + (user?.nome ? ` (${user.nome.split(" ")[0]})` : "");

    // 1) Tenta colocar ao lado do botão principal da página (ex.: "Registrar Visita")
    const anyButton = Array.from(document.querySelectorAll("button"))
      .find(b => /registrar\s+visita/i.test(b.textContent||""));
    if (anyButton && anyButton.parentElement) {
      const btn = makeLogoutButton(label);
      btn.style.marginLeft = "8px";
      anyButton.parentElement.appendChild(btn);
      window.__logoutInjected = true;
      return;
    }

    // 2) Fallback: fixa no topo direito
    const btn = makeLogoutButton(label);
    const holder = document.createElement("div");
    holder.style.cssText = [
      "position:fixed",
      "top:12px",
      "right:16px",
      "z-index:9999",
    ].join(";");
    holder.appendChild(btn);
    document.body.appendChild(holder);
    window.__logoutInjected = true;
  }

  // Aplica tudo quando logado
  function applyAll(me) {
    renameBrand(document);
    injectLogoutButton(me?.user || me);
  }

  // Primeira carga
  get("/api/auth/me")
    .then(r => (r && r.ok ? r.json() : null))
    .then(me => {
      if (!me?.authenticated) return; // não logado: não injeta
      applyAll(me);
    })
    .catch(() => {});

  // Observa mudanças no DOM (SPA) para reaplicar renomeação/se precisar
  const mo = new MutationObserver(() => {
    if (!brandChanged) renameBrand(document);
  });
  mo.observe(document.documentElement || document.body, { childList: true, subtree: true });
})();
</script>
