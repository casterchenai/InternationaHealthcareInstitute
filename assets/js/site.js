// Minimal progressive enhancement — no dependencies.
(function () {
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }
  var y = document.getElementById('year');
  if (y) y.textContent = String(new Date().getFullYear());

  // Open the FAQ item targeted by the URL hash (e.g. faq/#timeline)
  function openHashTarget() {
    var id = location.hash.replace('#', '');
    if (!id) return;
    var el = document.getElementById(id);
    if (!el) return;
    var d = el.closest ? el.closest('details') : null;
    if (d) d.open = true;
  }
  openHashTarget();
  window.addEventListener('hashchange', openHashTarget);
})();
