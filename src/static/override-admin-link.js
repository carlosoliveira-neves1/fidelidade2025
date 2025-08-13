// src/static/override-admin-link.js
(() => {
  const LOG = (...a)=>console.log('[admin-link]', ...a);
  let injected = false;

  // Normaliza a role vinda em vários formatos
  function normRole(any) {
    if (!any) return '';
    if (typeof any === 'string') {
      let s = any.toUpperCase().trim();
      // ex.: "RoleEnum.ADMIN" -> "ADMIN"
      if (s.includes('.')) s = s.split('.').pop();
      return s;
    }
    if (typeof any === 'object') {
      // tenta propriedades comuns
      return normRole(any.value || any.name || any.role || any.type);
    }
    return '';
  }

  // Extrai a role tentando várias formas de resposta
  function detectRole(u) {
    if (!u) return '';
    const candidates = [
      u.role,
      u.user?.role,
      u.data?.role,
      u.currentUser?.role,
      u.profile?.role,
    ];
    for (const c of candidates) {
      const r = normRole(c);
      if (r) return r;
    }
    return '';
  }

  async function me() {
    try {
      const r = await fetch('/api/auth/me', { credentials:'include' });
      if (!r.ok) { LOG('auth/me not ok', r.status); return null; }
      const j = await r.json();
      LOG('me raw =', j);
      return j;
    } catch (e) {
      LOG('auth/me error', e);
      return null;
    }
  }

  function makeFab() {
    const btn = document.createElement('button');
    btn.id = 'fab-admin';
    btn.textContent = 'Admin';
    btn.title = 'Gerenciar usuários';
    Object.assign(btn.style, {
      position:'fixed', right:'16px', bottom:'16px', zIndex: 2147483647,
      padding:'10px 14px', borderRadius:'999px', border:'none',
      boxShadow:'0 6px 18px rgba(0,0,0,.25)', cursor:'pointer',
      background:'#2563eb', color:'#fff', fontWeight:'600', fontSize:'14px'
    });
    btn.addEventListener('click', ()=>{ location.href = '/admin-usuarios'; });
    return btn;
  }

  function injectFab() {
    if (injected) return;
    if (document.getElementById('fab-admin')) { injected = true; return; }
    document.body.appendChild(makeFab());
    injected = true;
    LOG('FAB injected');
  }

  function tryInjectSidebar() {
    const sidebar = document.querySelector(
      'aside, [data-sidebar], nav[aria-label="Sidebar"], .sidebar, .MuiDrawer-paper'
    );
    if (!sidebar) return false;
    if (sidebar.querySelector('a[href="/admin-usuarios"]')) return true;

    const a = document.createElement('a');
    a.href = '/admin-usuarios';
    a.textContent = 'Admin';
    Object.assign(a.style, {
      display:'flex', alignItems:'center', gap:'8px',
      padding:'10px 12px', margin:'6px 8px',
      borderRadius:'10px', textDecoration:'none',
      color:'inherit', background:'rgba(99,102,241,.08)'
    });
    sidebar.appendChild(a);
    LOG('Sidebar link injected');
    return true;
  }

  async function init() {
    const u = await me();
    if (!u) { LOG('no user'); return; }

    const role = detectRole(u);
    LOG('role detected =', role);

    if (role !== 'ADMIN') {
      LOG('user is not admin (or role not recognized), abort');
      return;
    }

    if (!tryInjectSidebar()) injectFab();

    // Observa mudanças do SPA e re-injeta se o botão sumir
    const obs = new MutationObserver(() => {
      if (!document.getElementById('fab-admin') &&
          !document.querySelector('a[href="/admin-usuarios"]')) {
        tryInjectSidebar() || injectFab();
      }
    });
    obs.observe(document.documentElement, { childList:true, subtree:true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
