<!-- salve como: src/static/override-lojas-filter.js -->
<script>
(function(){
  const TAG = "[lojas-filter v4]";
  console.log(TAG, "loaded");

  // Mapa Enum -> texto exibido no front
  const HUMAN_BY_ENUM = {
    "JABAQUARA": "Mega Loja Jabaquara",
    "INDIANOPOLIS": "Indianópolis",
    "MASCOTE": "Mascote",
    "TATUAPE": "Tatuapé",
    "PRAIA_GRANDE": "Praia Grande",
    "OSASCO": "Osasco",
  };
  const ALL_HUMAN = Object.values(HUMAN_BY_ENUM);

  let allowedEnums = null;   // null => sem restrição (admin)
  let allowedHuman = null;

  async function fetchAllowed(){
    try{
      const r = await fetch("/api/auth/me");
      const j = await r.json();
      const user = j && j.user;
      const perms = (user && user.permissoes && user.permissoes.lojas) || {};
      const enums = Object.entries(perms)
        .filter(([_, v]) => v && (v.create || v.view || v.edit))
        .map(([k, _]) => k);

      if (enums.length > 0) {
        allowedEnums = enums;
        allowedHuman = new Set(enums.map(e => HUMAN_BY_ENUM[e]).filter(Boolean));
      } else {
        // sem configuração => admin (não limita) ou atendente sem lojas (libera tudo para não travar)
        allowedEnums = null;
        allowedHuman = null;
      }
      console.log(TAG, "allowedEnums=", allowedEnums);
    } catch(e){
      console.warn(TAG, "me fetch fail", e);
    }
  }

  function filterNativeSelects(){
    if (!allowedHuman) return; // sem restrição
    document.querySelectorAll("select").forEach(sel=>{
      // olhamos se o select contém algumas das lojas conhecidas
      const hasKnown = Array.from(sel.options).some(o => ALL_HUMAN.includes((o.text||"").trim()));
      if (!hasKnown) return;

      Array.from(sel.options).forEach(o=>{
        const label = (o.text||"").trim();
        if (ALL_HUMAN.includes(label)){
          const allow = allowedHuman.has(label);
          o.disabled = !allow;
          o.hidden = !allow;
          if (!allow && o.selected) o.selected = false;
        }
      });

      // se restou só uma loja, já seleciona
      const allowedOpts = Array.from(sel.options).filter(o => !o.disabled && !o.hidden && ALL_HUMAN.includes((o.text||"").trim()));
      if (allowedOpts.length === 1) sel.value = allowedOpts[0].value;
    });
  }

  function filterCustomLists(root=document){
    if (!allowedHuman) return; // sem restrição
    // tenta esconder itens de listas customizadas (li / role="option" / .dropdown-item)
    const nodes = root.querySelectorAll("li, [role='option'], .dropdown-item, .option");
    nodes.forEach(n=>{
      const t = (n.textContent||"").trim();
      if (ALL_HUMAN.includes(t)){
        n.style.display = allowedHuman.has(t) ? "" : "none";
      }
    });
  }

  function observeDropdowns(){
    const mo = new MutationObserver(muts=>{
      muts.forEach(m=>{
        filterCustomLists(m.target || document);
      });
    });
    mo.observe(document.body, {childList:true, subtree:true});
  }

  async function boot(){
    await fetchAllowed();
    filterNativeSelects();
    filterCustomLists();
    observeDropdowns();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
</script>
