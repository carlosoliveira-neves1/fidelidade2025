<!-- SALVE como: src/static/override-logout.js -->
<script>
(function () {
  const TAG = "[override-logout v3]";
  console.log(TAG, "loaded");

  async function doLogout(e) {
    if (e) e.preventDefault();
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } catch (err) {
      console.warn(TAG, "logout fetch error (seguindo para /login)", err);
    }
    location.href = "/login";
  }

  function findSidebar() {
    // tenta achar a <aside> ou um contêiner parecido do menu
    const aside = document.querySelector("aside");
    if (aside) return aside;

    // fallback: qualquer nav que contenha links do menu
    const byLinks = Array.from(document.querySelectorAll("nav"))
      .find(nv => /Dashboard|Clientes|Visitas|Campanhas|Relatórios/i.test(nv.textContent||""));
    return byLinks || null;
  }

  function insertLogoutAsMenuItem() {
    if (document.getElementById("menu-logout")) return true; // já inserido

    const sidebar = findSidebar();
    if (!sidebar) return false;

    // pega um link "modelo" para clonar estilos/classes
    const links = sidebar.querySelectorAll("a, button");
    if (!links.length) return false;

    // Prioriza o item 'Relatórios'; se não achar, usa o último link
    let model = null;
    for (const a of links) {
      const t = (a.textContent || "").trim().toLowerCase();
      if (["relatórios","relatorios","reports"].includes(t)) {
        model = a;
        break;
      }
    }
    if (!model) model = links[links.length - 1];

    const li = model.closest("li");
    const clone = (li ? li.cloneNode(true) : model.cloneNode(true));

    // Normaliza para termos um anchor clicável
    let anchor = clone.querySelector("a,button");
    if (!anchor) anchor = clone;

    // Limpa ícones específicos e texto do clone
    (anchor.querySelectorAll("svg, i")).forEach(el => el.remove());

    anchor.id = "menu-logout";
    anchor.href = "#";
    anchor.setAttribute("aria-label", "Sair");
    anchor.addEventListener("click", doLogout);

    // Atualiza rótulo
    let labelEl = anchor.querySelector("span");
    if (!labelEl) {
      labelEl = document.createElement("span");
      anchor.appendChild(labelEl);
    }
    labelEl.textContent = "Sair";

    // Adiciona um ícone simples (unicode) antes do texto, se não houver
    if (!anchor.querySelector(".logout-ico")) {
      const ico = document.createElement("span");
      ico.className = "logout-ico";
      ico.textContent = "⎋"; // ícone textual leve
      ico.style.marginRight = "8px";
      anchor.prepend(ico);
    }

    // injeta no mesmo nível do modelo
    if (li && li.parentNode) {
      li.parentNode.appendChild(clone);
    } else if (model.parentNode) {
      model.parentNode.appendChild(clone);
    } else {
      sidebar.appendChild(clone);
    }

    console.log(TAG, "logout item inserido no menu lateral");
    return true;
  }

  // OPCIONAL: botão no topo direito (se quiser esse estilo, descomente a chamada lá embaixo)
  function insertLogoutTopRight() {
    if (document.getElementById("logout-top")) return true;
    const header = document.querySelector("header") || document.body;
    const btn = document.createElement("button");
    btn.id = "logout-top";
    btn.textContent = "Sair";
    btn.onclick = doLogout;

    // tenta herdar alguma classe de botão existente
    const sampleBtn = document.querySelector("button, .btn");
    if (sampleBtn && sampleBtn.className) {
      btn.className = sampleBtn.className;
    } else {
      // fallback visual simples
      btn.style.padding = "8px 12px";
      btn.style.borderRadius = "10px";
      btn.style.border = "1px solid #d1d5db";
      btn.style.background = "#fff";
      btn.style.cursor = "pointer";
    }
    // posiciona no topo direito
    btn.style.position = "fixed";
    btn.style.top = "14px";
    btn.style.right = "18px";
    btn.style.zIndex = "9999";

    header.appendChild(btn);
    console.log(TAG, "logout botão (top-right) inserido");
    return true;
  }

  function boot() {
    // Tenta inserir no menu; se ainda não existir o DOM, re-tenta
    if (!insertLogoutAsMenuItem()) {
      const iv = setInterval(() => {
        if (insertLogoutAsMenuItem()) clearInterval(iv);
      }, 400);
      // Descomente se quiser também o botão no topo direito como redundância:
      // setTimeout(insertLogoutTopRight, 1500);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
</script>
