/**
 * Interacțiunile paginii, într-un singur script mic, fără React: merge și când pagina e deschisă direct
 * de pe disc (file://), unde Next nu se poate hidrata. Fără JS, pagina rămâne completă: textul aprins,
 * harta din „How it works” în starea finală, butoanele vizibile.
 *
 * 1. [data-scroll-words]: cuvintele se aprind pe măsură ce derulezi.
 * 2. [data-scrolly]: pasul din mijlocul ecranului scrie data-step pe secțiune (CSS-ul schimbă harta).
 * 3. [data-hold-root]: „Hold to approve” (ține apăsat 1,2 s), „Skip”, „Undo”. Nu trimite nimic.
 */
const ENHANCE = `(function () {
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var all = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

  var paras = all("[data-scroll-words]").map(function (p) { return { el: p, words: all("[data-w]", p) }; });
  if (!reduce && paras.length) {
    var raf = 0;
    var update = function () {
      raf = 0;
      var vh = window.innerHeight, start = vh * 0.82, end = vh * 0.35;
      paras.forEach(function (it) {
        var r = it.el.getBoundingClientRect();
        var p = Math.min(1, Math.max(0, (start - r.top) / (r.height + start - end)));
        var lit = p * it.words.length;
        for (var i = 0; i < it.words.length; i++) it.words[i].style.opacity = String(Math.min(1, Math.max(0.2, lit - i + 0.2)));
      });
    };
    var onScroll = function () { if (!raf) raf = requestAnimationFrame(update); };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
  }

  if ("IntersectionObserver" in window) {
    all("[data-scrolly]").forEach(function (root) {
      var steps = all("[data-scrolly-step]", root);
      if (!steps.length) return;
      root.setAttribute("data-js", "1");
      root.setAttribute("data-step", "0");
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { if (e.isIntersecting) root.setAttribute("data-step", e.target.getAttribute("data-scrolly-step")); });
      }, { rootMargin: "-50% 0px -49% 0px" });
      steps.forEach(function (s) { io.observe(s); });
    });
  }

  all("[data-hold-root]").forEach(function (root) {
    var btn = root.querySelector("[data-hold]"), skip = root.querySelector("[data-skip]"), controls = root.querySelector("[data-controls]");
    var status = root.querySelector("[data-status]"), text = root.querySelector("[data-status-text]"), icon = root.querySelector("[data-status-icon]"), undo = root.querySelector("[data-undo]");
    if (!btn || !status) return;
    var t = null;
    var finish = function (kind) {
      controls.hidden = true; status.hidden = false;
      text.textContent = kind === "approved" ? "Approved. Logged as a human decision." : "Skipped. The case stays in the queue.";
      icon.textContent = kind === "approved" ? "\\u2713" : "\\u2013";
      icon.setAttribute("data-kind", kind);
      undo.focus();
    };
    var start = function () { if (t) return; btn.setAttribute("data-holding", ""); t = setTimeout(function () { t = null; btn.removeAttribute("data-holding"); finish("approved"); }, 1200); };
    var stop = function () { if (t) { clearTimeout(t); t = null; } btn.removeAttribute("data-holding"); };
    btn.addEventListener("pointerdown", function (e) { try { btn.setPointerCapture(e.pointerId); } catch (_) {} start(); });
    btn.addEventListener("pointerup", stop);
    btn.addEventListener("pointercancel", stop);
    btn.addEventListener("keydown", function (e) { if ((e.key === " " || e.key === "Enter") && !e.repeat) { e.preventDefault(); start(); } });
    btn.addEventListener("keyup", function (e) { if (e.key === " " || e.key === "Enter") stop(); });
    btn.addEventListener("contextmenu", function (e) { e.preventDefault(); });
    skip.addEventListener("click", function () { finish("skipped"); });
    undo.addEventListener("click", function () { status.hidden = true; controls.hidden = false; btn.focus(); });
  });
})();`;

export function Enhance() {
  return <script dangerouslySetInnerHTML={{ __html: ENHANCE }} />;
}
