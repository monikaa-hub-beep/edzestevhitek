(function () {
  "use strict";
  var KEY = "et_consent", cbs = [];
  function get() { try { return JSON.parse(localStorage.getItem(KEY)); } catch (e) { return null; } }
  function fire() { var c = get(); if (c) cbs.forEach(function (f) { f(c); }); }
  function save(media, analytics) {
    try { localStorage.setItem(KEY, JSON.stringify({ necessary: true, media: !!media, analytics: !!analytics, ts: Date.now() })); } catch (e) {}
    var b = document.getElementById("cb"); if (b) b.remove();
    fire();
  }
  // Later, for analytics:  ET.onConsent(function (c) { if (c.analytics) { /* load it here */ } });
  window.ET = { consent: get, onConsent: function (f) { cbs.push(f); var c = get(); if (c) f(c); } };

  // Mobile menu
  var mb = document.getElementById("mb");
  if (mb) mb.addEventListener("click", function () {
    var open = document.getElementById("nv").classList.toggle("open");
    mb.setAttribute("aria-expanded", open);
  });

  // YouTube: nothing loads from Google until the visitor plays a video (or allowed external media)
  function loadVideo(box, autoplay) {
    if (box.querySelector("iframe")) return;
    var f = document.createElement("iframe");
    f.src = "https://www.youtube-nocookie.com/embed/" + box.dataset.id + "?rel=0" + (autoplay ? "&autoplay=1" : "");
    f.title = "YouTube-videó";
    f.loading = "lazy";
    f.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
    f.referrerPolicy = "strict-origin-when-cross-origin";
    f.allowFullscreen = true;
    box.innerHTML = ""; box.appendChild(f); box.classList.add("on");
  }
  var vids = document.querySelectorAll(".yt");
  vids.forEach(function (box) {
    box.querySelector(".yt-btn").addEventListener("click", function (e) {
      if (e.target.closest("a")) return;
      loadVideo(box, true);
    });
  });
  ET.onConsent(function (c) { if (c.media) vids.forEach(function (b) { loadVideo(b, false); }); });

  // Cookie banner
  function banner() {
    if (document.getElementById("cb")) return;
    var c = get() || {};
    var b = document.createElement("div");
    b.id = "cb"; b.setAttribute("role", "dialog"); b.setAttribute("aria-label", "Süti beállítások");
    b.innerHTML =
      '<p class="cb-t">Sütik és külső tartalmak</p>' +
      '<p>Az oldal nem használ követő vagy hirdetési sütiket. A választásodat a böngésződ tárolja. ' +
      'A cikkekbe ágyazott YouTube-videók a Google-tól töltődnek be; ezt itt engedélyezheted előre, vagy videónként, lejátszáskor. ' +
      '<a href="/adatvedelem/#sutik">Részletek</a></p>' +
      '<label class="chk"><input type="checkbox" checked disabled> <span><b>Szükséges</b> – a választásod megjegyzése</span></label>' +
      '<label class="chk"><input type="checkbox" id="cm"' + (c.media ? " checked" : "") + '> <span><b>Külső média</b> – YouTube-videók automatikus betöltése</span></label>' +
      '<div class="row"><button class="btn ghost" id="c0">Csak a szükségesek</button><button class="btn ghost" id="cs">Kiválasztottak mentése</button><button class="btn" id="c1">Mindet elfogadom</button></div>';
    document.body.appendChild(b);
    document.getElementById("c0").onclick = function () { save(false, false); };
    document.getElementById("cs").onclick = function () { save(document.getElementById("cm").checked, false); };
    document.getElementById("c1").onclick = function () { save(true, true); };
  }
  var ck = document.getElementById("ck");
  if (ck) ck.addEventListener("click", function (e) { e.preventDefault(); banner(); });
  if (!get()) banner(); else fire();

  // Contact form (only on /kapcsolat/)
  var form = document.getElementById("cf");
  if (form) {
    var st = document.getElementById("st");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var d = Object.fromEntries(new FormData(form));
      var endpoint = form.dataset.endpoint;
      if (!d.message || d.message.trim().length < 10) { st.textContent = "Kérlek, írj legalább néhány mondatot."; return; }
      if (d.email && !form.email.checkValidity()) { st.textContent = "Az e-mail-cím formátuma hibásnak tűnik."; return; }
      if (!document.getElementById("cn").checked) { st.textContent = "Az adatkezelési tájékoztató elfogadása szükséges."; return; }
      if (d._gotcha) { st.textContent = "Köszönjük, az üzenet elment!"; form.reset(); return; }
      if (endpoint.indexOf("YOUR_FORM_ID") > -1) { st.textContent = "Az űrlap még nincs bekötve (lásd README)."; return; }
      var btn = document.getElementById("sb"); btn.disabled = true; st.textContent = "Küldés…";
      fetch(endpoint, {
        method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ name: d.name, email: d.email, topic: d.topic, message: d.message, _gotcha: d._gotcha,
          _subject: "edzestevhitek.hu – új üzenet", consent: "adatkezelési tájékoztató elfogadva" })
      }).then(function (r) {
        if (!r.ok) throw 0;
        st.textContent = "Köszönjük, az üzenet elment! Hamarosan válaszolok."; form.reset();
      }).catch(function () { st.textContent = "Nem sikerült elküldeni. Kérlek, próbáld meg később."; })
        .finally(function () { btn.disabled = false; });
    });
  }
})();
