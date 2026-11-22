// ============================================================================
// ARCHIVO: js/ota.js — CotizacionesPro
// OTA local con @capgo/capacitor-updater (mismo motor verificado que TRIBALs):
//   - notifyAppReady() al arrancar (anti-rollback)
//   - push del PC: TribalFtp 'tribalOta' → pull (download + set/next)
//   - 'tribalPing' del PC → modal "comunicación viva"
//   - poller cada 8 s a /stamp.json del PC (respaldo si el evento se pierde)
//   - sello #build-tag: tap = URL manual → pull · hold 650 ms = reset()
//   - window.TRIBAL_OTA (js/ota_stamp.js) → modal "OTA aplicada" una vez
// ============================================================================
(function () {
    'use strict';
    var KEY = 'cpro_ota_url';
    var SEEN = 'cpro_ota_seen';

    function L(m) { try { console.log('[OTA] ' + m); } catch (e) {} }
    function UP() {
        return window.Capacitor && window.Capacitor.Plugins &&
            window.Capacitor.Plugins.CapacitorUpdater;
    }
    function HTTP() {
        return window.Capacitor && window.Capacitor.Plugins &&
            window.Capacitor.Plugins.CapacitorHttp;
    }
    function toast(m) {
        if (typeof window.toast === 'function') { window.toast(m); return; }
        L('toast: ' + m);
    }
    function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
    function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
    function baseOf(url) { return String(url).replace(/\/bundle\.zip.*$/, ''); }

    L('listo · UP=' + !!UP() + ' HTTP=' + !!HTTP() + ' · url=' + (lsGet(KEY) || '—'));

    var up = UP();
    if (up && up.notifyAppReady) {
        up.notifyAppReady()
            .then(function () { L('notifyAppReady OK'); })
            .catch(function (e) { L('notifyAppReady falló: ' + (e && e.message)); });
    } else L('CapacitorUpdater NO disponible — OTA muerto');

    // ---------------- pull: descarga y aplica via el plugin ----------------
    var pulling = false;
    function pull(url, version, checksum, silent) {
        var P = UP();
        if (!P || !P.download) { L('pull abortado: sin plugin'); return; }
        if (pulling) { L('pull en curso — ignorado ' + url); return; }
        pulling = true;
        L('pull → ' + url + ' · v=' + version + ' · sha=' +
            (checksum || '').slice(0, 12) + '…');
        if (!silent) toast('Descargando OTA…');
        P.download({ url: url, version: String(version || 'ota'),
                     checksum: checksum || '' })
            .then(function (bundle) {
                L('descargado id=' + bundle.id + ' — aplicando…');
                toast('Aplicando OTA…');
                return P.set({ id: bundle.id }).catch(function () {
                    L('set() falló → next() para el próximo arranque');
                    return P.next({ id: bundle.id });
                });
            }).then(function () { L('aplicado — el WebView recarga solo'); })
            .catch(function (e) {
                pulling = false;
                L('FALLO descarga/aplicar: ' + (e && e.message || e));
                toast('OTA falló: ' + (e && e.message || e));
            });
    }

    // ---------------- modales mínimos (sin dependencias de CSS) ----------------
    function overlay(titulo, html, btn) {
        var ov = document.createElement('div');
        ov.style.cssText = 'position:fixed;inset:0;z-index:2147483647;' +
            'background:rgba(10,15,30,.55);display:flex;align-items:center;' +
            'justify-content:center;padding:20px';
        var box = document.createElement('div');
        box.style.cssText = 'background:#fff;color:#1e293b;border-radius:14px;' +
            'padding:22px 24px;max-width:340px;width:100%;text-align:center;' +
            'box-shadow:0 12px 40px rgba(0,0,0,.35);font-family:system-ui,sans-serif';
        box.innerHTML = '<h3 style="margin:0 0 8px;font-size:1.05rem">' + titulo + '</h3>' +
            '<div style="font-size:.9rem;color:#475569;line-height:1.5">' + html + '</div>';
        var b = document.createElement('button');
        b.textContent = btn || 'Listo';
        b.style.cssText = 'width:100%;margin-top:14px;padding:10px;border:0;' +
            'border-radius:10px;background:#6366f1;color:#fff;font-weight:600;cursor:pointer';
        b.onclick = function () { ov.remove(); };
        box.appendChild(b); ov.appendChild(box); document.body.appendChild(ov);
    }
    function modalViva() {
        overlay('Comunicación viva',
            'La PC habla con CotizacionesPro — OTA listo.<br>' +
            new Date().toLocaleString('es-CR'));
    }

    // ---------------- push del PC: TribalFtp dispara 'tribalOta' ----------------
    var FTP = window.Capacitor && window.Capacitor.Plugins &&
        window.Capacitor.Plugins.TribalFtp;
    if (FTP && FTP.addListener) {
        FTP.addListener('tribalOta', function (e) {
            L('evento tribalOta recibido: ' + (e && e.url || '(sin url)'));
            if (e && e.url) {
                lsSet(KEY, e.url);
                pull(e.url, e.version || ('ota-' + Date.now()), e.checksum || '');
            }
        });
        FTP.addListener('tribalPing', function () {
            L('ping recibido — modal de conexión');
            modalViva();
        });
        L('listeners tribalOta/tribalPing armados');
    } else L('TribalFtp.addListener NO disponible — push muerto');

    // ---------------- poller: el sello del PC cada 8 s ----------------
    var lastPoll = '', pollFails = 0;
    function pollCheck() {
        var url = lsGet(KEY);
        if (!url || pulling) return;
        var H = HTTP();
        if (!H) return;
        var stamp = baseOf(url) + '/stamp.json';
        H.get({ url: stamp }).then(function (r) {
            var d = r && r.data;
            if (typeof d === 'string') { try { d = JSON.parse(d); } catch (x) {} }
            if (!d || !d.ts) return;
            if (d.ts !== lastPoll && d.ts !== lsGet(SEEN)) {
                L('sello nuevo del PC: ' + d.ts + ' (actual ' + lastPoll + ')');
                pull(url, d.ts, d.sha, true);   // silencioso: sin toasts
            }
            lastPoll = d.ts;
            if (pollFails) { L('poller recuperado'); pollFails = 0; }
        }).catch(function () {
            if (!(++pollFails % 10))
                L('poller sin contacto ×' + pollFails + ' (' + stamp + ')');
        });
    }
    setInterval(pollCheck, 8000);
    setTimeout(pollCheck, 2500);        // chequeo al boot: update pendiente

    // ---------------- sello de build: tap = pull · hold = reset ----------------
    function wire() {
        var t = document.getElementById('build-tag');
        if (!t || t._otaWired) return;
        t._otaWired = 1;
        t.style.cursor = 'pointer';
        t.title = 'Toca: OTA manual · Mantén: volver al paquete';
        var txt = window.TRIBAL_BUILD || '';
        if (txt) t.textContent = '· ' + txt;
        var lp = null;
        t.addEventListener('click', function () {
            if (!UP()) { L('tap sello — sin plugin'); return; }
            var url = window.prompt('URL del bundle OTA',
                lsGet(KEY) || 'http://192.168.1.100:8891/bundle.zip');
            if (url == null) return;
            url = url.trim();
            lsSet(KEY, url);
            pull(url, 'manual-' + Date.now(), '');
        });
        t.addEventListener('pointerdown', function () {
            lp = setTimeout(function () {
                lp = null;
                var P = UP();
                if (P && P.reset &&
                    window.confirm('¿Quitar el OTA y volver al paquete?')) {
                    L('reset() → paquete empaquetado');
                    P.reset();
                }
            }, 650);
        });
        ['pointerup', 'pointercancel', 'pointerleave'].forEach(function (ev) {
            t.addEventListener(ev, function () { clearTimeout(lp); lp = null; });
        });
    }
    wire();
    setTimeout(wire, 800); setTimeout(wire, 2500);

    // ---------------- modal «última OTA aplicada» ----------------
    var O = window.TRIBAL_OTA;
    L('stamp=' + (O && O.ts) + ' · seen=' + lsGet(SEEN));
    if (O && O.ts && O.ts !== lsGet(SEEN)) {
        lsSet(SEEN, O.ts);
        setTimeout(function () {
            overlay('OTA aplicada',
                (O.ts || '') + '<br>' + (O.files || 0) +
                ' archivo(s) enviados desde la PC');
        }, 600);
    }
})();
