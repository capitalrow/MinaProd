/* Minimal hash router: #/library, #/live, #/upload, #/settings */
(function(){
  const routes = {
    '': 'view-welcome',
    '#/library': 'view-library',
    '#/live': 'view-live',
    '#/upload': 'view-upload',
    '#/settings': 'view-settings'
  };
  function show(id){
    document.querySelectorAll('[data-view]').forEach(n=>n.hidden=true);
    const el = document.getElementById(id);
    if (el) el.hidden = false;
    // active nav
    document.querySelectorAll('[data-nav]').forEach(a=>{
      a.classList.toggle('active', a.getAttribute('href') === location.hash);
    });
  }
  function resolve(){
    const hash = location.hash || '';
    const id = routes[hash] || routes[''];
    show(id);
  }
  window.addEventListener('hashchange', resolve);
  window.addEventListener('DOMContentLoaded', resolve);
})();


// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
