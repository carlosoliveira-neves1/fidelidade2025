// src/static/override-cpf-search.js (v11)
console.log("override v11 carregado");

const onlyDigits = (s) => (s || "").replace(/\D/g, "");
const debounce = (fn, ms = 300) => { let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a),ms); }; };

// ------- UI: campo de busca por CPF -------
function buildCpfSearch() {
  const wrap = document.createElement("div");
  wrap.dataset.cpfSearch = "1";
  wrap.style.display = "grid";
  wrap.style.gap = "8px";
  wrap.style.marginBottom = "8px";

  const input = document.createElement("input");
  input.type = "text";
  input.placeholder = "Digite o CPF (somente números)";
  input.id = "cpfSearchInput";
  input.autocomplete = "off";
  input.style.padding = "10px";
  input.style.width = "100%";

  const label = document.createElement("label");
  label.textContent = "Cliente (buscar por CPF)";
  label.htmlFor = input.id;

  const dl = document.createElement("datalist");
  dl.id = "cpfOptions";
  input.setAttribute("list", dl.id);

  const hidden = document.createElement("input");
  hidden.type = "hidden";
  hidden.id = "clienteIdHidden";
  hidden.name = "cliente_id";

  wrap.append(label, input, dl, hidden);

  const labelToId = new Map();

  const fetchClientes = debounce(async (q) => {
    const digits = onlyDigits(q);
    if (digits.length < 3) { dl.innerHTML=""; hidden.value=""; return; }
    try {
      const r = await fetch(`/api/clientes/search?q=${encodeURIComponent(digits)}`);
      const data = await r.json();
      labelToId.clear();
      dl.innerHTML = (data||[]).map(c=>{
        const lbl = `${c.nome} - ${c.cpf}`;
        labelToId.set(lbl, String(c.id));
        return `<option value="${lbl}"></option>`;
      }).join("");
    } catch(e){ console.error("buscar clientes", e); }
  }, 300);

  input.addEventListener("input", ()=>{ fetchClientes(input.value); hidden.value=""; });
  input.addEventListener("change", ()=>{
    const id = labelToId.get(input.value);
    hidden.value = id ? String(id) : "";
  });
  input.addEventListener("blur", async ()=>{
    if (hidden.value) return;
    const digits = onlyDigits(input.value);
    if (digits.length === 11) {
      try {
        const r = await fetch(`/api/clientes/buscar-cpf/${digits}`);
        if (r.ok) {
          const c = await r.json();
          hidden.value = String(c.id);
          input.value = `${c.nome} - ${c.cpf}`;
        }
      } catch(_) {}
    }
  });

  return wrap;
}

// ------- helpers DOM -------
function findLabel(regex, root=document) {
  const nodes = root.querySelectorAll('label, [role="label"], .label, .form-label, .MuiFormLabel-root');
  for (const n of nodes) {
    const txt = (n.textContent || "").replace(/\s+/g," ").trim();
    if (regex.test(txt)) return n;
  }
  return null;
}

function findFieldContainer(el) {
  let p = el;
  for (let i=0; i<8 && p && p.tagName !== "FORM"; i++) {
    const cls = (p.classList && Array.from(p.classList)) || [];
    const hasCssHash = cls.some(c => /^css-/.test(c)); // libs css-in-js
    if (cls.includes("form-group") || cls.includes("field") || cls.includes("form-item") ||
        cls.includes("MuiFormControl-root") || hasCssHash) {
      return p;
    }
    p = p.parentElement;
  }
  return el.parentElement || el;
}

function hideOriginalClientField(modal) {
  // 1) pelo label “Cliente *”
  const lbl = findLabel(/^Cliente\s*\*/i, modal);
  if (lbl) {
    const cont = findFieldContainer(lbl);
    cont.style.display = "none";
    cont.setAttribute("aria-hidden","true");
    cont.dataset.hiddenClientBlock = "1";
    return true;
  }
  // 2) fallback: select com opções fake
  const selects = modal.querySelectorAll("select");
  for (const sel of selects) {
    const fake = Array.from(sel.options).some(o => /Maria Silva|Jo[aã]o Santos|Ana Costa/i.test(o.textContent||""));
    if (fake) {
      const cont = findFieldContainer(sel);
      cont.style.display = "none";
      cont.setAttribute("aria-hidden","true");
      cont.dataset.hiddenClientBlock = "1";
      return true;
    }
  }
  return false;
}

// seleciona 1ª opção do select original para o bundle não quebrar
function selectSafeOption(modal) {
  const selects = modal.querySelectorAll("select");
  for (const sel of selects) {
    const fake = Array.from(sel.options).some(o => /Maria Silva|Jo[aã]o Santos|Ana Costa/i.test(o.textContent||""));
    if (fake) {
      if (sel.selectedIndex <= 0 && sel.options.length > 1) {
        sel.selectedIndex = 1; // primeira real
        sel.dispatchEvent(new Event("change", { bubbles: true }));
      }
      return true;
    }
  }
  return false;
}

// inserção segura do buscador
function insertSearchBeforeValorCompra(modal, wrap) {
  try {
    const alvoLbl = findLabel(/^Valor da Compra/i, modal);
    if (alvoLbl) {
      const cont = findFieldContainer(alvoLbl);
      if (cont && cont.parentElement) {
        cont.parentElement.insertBefore(wrap, cont);
        return;
      }
    }
    const form = modal.querySelector("form");
    if (form) {
      form.insertBefore(wrap, form.firstChild);
    } else {
      // fallback seguro: coloca no próprio modal
      const host = modal.querySelector("div") || modal;
      host.appendChild(wrap);
    }
  } catch (e) {
    console.warn("insertSearchBeforeValorCompra fallback:", e);
    (modal.querySelector("div") || modal).appendChild(wrap);
  }
}

// ------- monta: só quando o modal existir -------
(function mount() {
  const style = document.createElement("style");
  style.textContent = `[data-hidden-client-block="1"]{display:none!important;}`;
  document.head.appendChild(style);

  const apply = () => {
    // só roda se existir um modal aberto
    const modal = document.querySelector('div[role="dialog"]');
    if (!modal) return;

    // seleciona algo no select original para o bundle não quebrar
    selectSafeOption(modal);

    // esconde o bloco Cliente *
    if (!modal.querySelector('[data-hidden-client-block="1"]')) {
      hideOriginalClientField(modal);
    }

    // injeta nosso buscador (se ainda não tiver)
    if (!modal.querySelector('[data-cpf-search="1"]')) {
      const wrap = buildCpfSearch();
      insertSearchBeforeValorCompra(modal, wrap);
      console.log("✅ Busca por CPF montada; campo original oculto; opção segura selecionada.");
    }
  };

  const obs = new MutationObserver(apply);
  obs.observe(document.body, { childList: true, subtree: true });
  apply();
})();

// ------- injeta cliente_id no POST /api/visitas -------
(() => {
  const origFetch = window.fetch;

  window.fetch = async (input, init = {}) => {
    const url = typeof input === "string" ? input : input.url;
    const method = (init?.method || "GET").toUpperCase();

    if (url && url.includes("/api/visitas") && method === "POST") {
      try {
        let clienteId = document.getElementById("clienteIdHidden")?.value || "";

        // se não tem, tenta resolver pelos 11 dígitos digitados
        if (!clienteId) {
          const digits = onlyDigits((document.getElementById("cpfSearchInput") || {}).value || "");
          if (digits.length === 11) {
            const r = await origFetch(`/api/clientes/buscar-cpf/${digits}`);
            if (r.ok) {
              const c = await r.json();
              clienteId = String(c.id);
              const h = document.getElementById("clienteIdHidden");
              if (h) h.value = clienteId;
            }
          }
        }

        if (clienteId) {
          let body = init.body;

          if (typeof body === "string" && body.trim().startsWith("{")) {
            try {
              const obj = JSON.parse(body);
              if (!obj.cliente_id) obj.cliente_id = Number(clienteId);
              init.body = JSON.stringify(obj);
            } catch(_) {}
          } else if (body instanceof FormData) {
            if (!body.has("cliente_id")) body.set("cliente_id", clienteId);
          } else if (body instanceof URLSearchParams) {
            if (!body.has("cliente_id")) body.set("cliente_id", clienteId);
          } else if (typeof body === "string" && body.includes("=") && !body.trim().startsWith("{")) {
            if (!/(^|&)cliente_id=/.test(body)) {
              init.body = body + `&cliente_id=${encodeURIComponent(clienteId)}`;
            }
          } else if (!body) {
            init.headers = Object.assign({}, init.headers, { "Content-Type": "application/json" });
            init.body = JSON.stringify({ cliente_id: Number(clienteId) });
            init.method = "POST";
          }
        }
      } catch (e) {
        console.warn("patch visitas: não consegui injetar cliente_id", e);
      }
    }

    return origFetch(input, init);
  };
})();
