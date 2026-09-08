// Progressive enhancement only — the site works without this file.
(function () {
  // Mobile menu
  var btn = document.querySelector('.menu-btn');
  var menu = document.getElementById('mobile-menu');
  if (btn && menu) {
    btn.addEventListener('click', function () {
      var open = menu.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.style.overflow = open ? 'hidden' : '';
    });
    menu.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') { menu.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); document.body.style.overflow = ''; }
    });
  }

  // Current year
  document.querySelectorAll('.year').forEach(function (el) { el.textContent = String(new Date().getFullYear()); });

  // Open the FAQ item targeted by the URL hash (e.g. /faq/#timeline or /#faq-dpc)
  function openHashTarget() {
    var id = location.hash.replace('#', '');
    if (!id) return;
    var el = document.getElementById(id);
    if (!el) return;
    var d = el.tagName === 'DETAILS' ? el : (el.closest ? el.closest('details') : null);
    if (d) d.open = true;
  }
  openHashTarget();
  window.addEventListener('hashchange', openHashTarget);
})();
