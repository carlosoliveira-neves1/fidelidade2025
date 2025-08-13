<!-- salve como: src/static/override-sidebar-brand-logout.js -->
<script>
(function () {
  const TAG = "[brand+logout v5]";
  console.log(TAG, "loaded");

  async function doLogout(e){
    if(e) e.preventDefault();
    try { await fetch("/api/auth/logout", {method:"POST"}); } catch(_){}
    location.href = "/login";
  }

  function setBrand(){
    // tenta achar o “logo/nome” na lateral
    const candidates = [
      // header dentro do aside
      'aside h1, aside header h1, aside .brand, aside [data-brand]',
      // link/logo no topo da sidebar
      'aside a[aria-label], aside a[href="/"], aside a'
    ];
    for (const sel of candidates){
      const el = document.querySelector(sel);
      if (el && (el.textContent||"").trim()) {
        el.textContent = "CASA DO CIGANO";
        return true;
      }
    }
    // fallback: título da app no topo
    const topTitle = document.querySelector('header h1, [data-app-title]');
    if (topTitle) {
      topTitle.textContent = "CASA DO CIGANO";
      return true;
    }
    return false;
  }

  function findSidebarList(){
    const aside = document.querySelector("aside");
    if (!aside) return null;
    // a lista pode ser ul/nav/div. Pegamos o container que contém os itens.
    const list =
      aside.querySelector("ul") ||
      aside.querySelector("nav") ||
      aside;
    return list;
  }

  function getMenuModel(){
    const list = findSidebarList();
    if (!list) return null;

    // pega um link de item real do menu para copiar classes
    const modelLink =
      list.querySelector("a[href], button") ||
      list.querySelector("*[role='button']");
    if (!modelLink) return null;

    // item pode estar dentro de <li>
    const wrapper = modelLink.closest("li");
    return { list, modelLink, wrapper };
  }

  function insertLogout(){
    if (document.getElementById("menu-logout")) return true;

    const model = getMenuModel();
    if (!model) return false;

    const { list, modelLink, wrapper } = model;

    // cria um novo item seguindo a estrutura do modelo
    const useLi = !!wrapper;
    const newWrapper = document.createElement(useLi ? "li" : "div");
    const a = document.createElement("a");

    a.id = "menu-logout";
    a.href = "#";
    a.addEventListener("click", doLogout);
    a.textContent = "Sair";

    // copia classes visuais do link do modelo
    if (modelLink.className) a.className = modelLink.className;
    // copia classes do wrapper (li) se existir
    if (useLi && wrapper.className) newWrapper.className = wrapper.className;

    // insere pequeno ícone textual se não houver ícones na classe
    if (!a.querySelector("svg")) {
      const ico = document.createElement("span");
      ico.textContent = "⎋";
      ico.style.marginRight = "8px";
      a.prepend(ico);
    }

    if (useLi) {
      newWrapper.appendChild(a);
      list.appendChild(newWrapper);
    } else {
      list.appendChild(a);
    }

    console.log(TAG, "Sair inserido no menu lateral");
    return true;
  }

  // OPCIONAL: botão no topo direito
  function insertTopRightLogout(){
    if (document.getElementById("logout-top")) return true;
    const header = document.querySelector("header") || document.body;
    const btn = document.createElement("button");
    btn.id = "logout-top";
    btn.textContent = "Sair";
    btn.onclick = doLogout;

    // tenta herdar classes de algum botão
    const sample = document.querySelector("header button, .btn");
    if (sample && sample.className) btn.className = sample.className;
    else {
      btn.style.padding = "8px 12px";
      btn.style.borderRadius = "10px";
      btn.style.border = "1px solid #d1d5db";
      btn.style.background = "#fff";
      btn.style.cursor = "pointer";
    }
    btn.style.position = "fixed";
    btn.style.top = "14px";
    btn.style.right = "18px";
    btn.style.zIndex = 9999;

    header.appendChild(btn);
    console.log(TAG, "Sair (top-right) inserido");
    return true;
  }

  function boot(){
    // nome/brand
    if (!setBrand()){
      const ivB = setInterval(()=>{ if (setBrand()) clearInterval(ivB); }, 400);
    }
    // sair no menu
    if (!insertLogout()){
      const iv = setInterval(()=>{ if (insertLogout()) clearInterval(iv); }, 400);
    }
    // se quiser também no topo direito, descomente:
    // setTimeout(insertTopRightLogout, 1500);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
</script>
