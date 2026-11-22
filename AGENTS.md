# CotizacionesPro — reglas del proyecto (APP DE COTIZACIONES)

App Android standalone de cotizaciones (~5.9 MB), Capacitor 6 + plugins
Java propios, JS vanilla ES5-style en `www/`. Distribuible por WhatsApp.
**El usuario pregunta por "cotizaciones" → este es el proyecto.**

## OTA LOCAL — SECCIÓN BLINDADA (orden expresa del usuario)

- **PUERTOS FIJOS — PROHIBIDO cambiar sin preguntar**: `:8890` =
  TribalFtpPlugin DENTRO del teléfono (recibe el aviso POST /ota y sirve
  /ping); `:8891` = servidor de bundle EN LA PC (`ota_server.py`,
  sirve `/bundle.zip` + `/stamp.json` al teléfono por WiFi).
- **PROHIBIDO modificar** `scripts/ota_watch.py`, `scripts/ota_push.py`,
  `scripts/ota_server.py`, `www/js/ota_stamp.js`, `www/js/ota.js` ni la
  config Capgo sin autorización — "jamás permitir que se desconecte el
  OTA por equivocaciones de puertos".
- Flujo: watcher detecta cambio en `www/` → estampa `TRIBAL_OTA.ts`
  (hora local) → zippea → SHA-256 → sirve en :8891 → POST a
  `http://<IP-PC>:8890/ota` → el APK descarga, checksum y aplica con
  `@capgo/capacitor-updater@6.53.0` + `notifyAppReady`.
- El OTA **solo actualiza `www/`** — cambios en Java/manifest/plugins
  exigen recompilar APK (`scripts/build.bat`) y pasar el APK al usuario.
- Teléfono y PC deben estar en el **mismo WiFi**; la URL del bundle es
  `http://<IP-de-la-PC>:8891/bundle.zip` (verificar IP con `ipconfig`).
- Log del teléfono: `[OTA]` en consola — `Version successfully loaded`
  confirma que llegó. `On-premise app detected` de Capgo cloud es
  NORMAL (es OTA local, no error).
- Verificación rápida: `curl http://<IP>:8891/ping` debe dar 200 y
  `bundle.zip` ~390 KB.

## Estructura y límites

- `www/index.html` (~207 ln) · `www/js/app.js` (~208) ·
  `www/js/exports.js` (~33) · `www/css/app.css` (~285) ·
  `www/js/ota.js`, `www/js/ota_stamp.js`, `www/js/buildstamp.js`.
- **REGLA: ningún archivo >300 líneas** (objetivo ~250). Verificar con
  `wc -l` tras cada edición.
- **SIN CDNs** — todo asset es local (Bootstrap CSS/JS en `www/`).
- Sintaxis: `node --check www/js/app.js` (y exports.js si se toca)
  **ANTES de cada push OTA** — un `;` faltante ya tumbó la app entera
  una vez (se vio como "perdí mis datos"; los datos NO se borran,
  localStorage/IndexedDB sobreviven).

## Convenciones aprendidas (NO romper)

- **NUNCA `window.prompt()/alert()/confirm()`** — no funcionan en el
  WebView de Capacitor. Usar modales propios (`#mCf` para nombres de
  campo, `#mDel` para confirmación).
- **Bootstrap `.d-flex` lleva `display:flex!important`** — un
  `style.display='none'` inline NO lo gana; usar la clase `d-none`.
- Todo borrado pasa por `askDel()` → modal `#mDel` con **doble
  confirmación** (Eliminar → "¿Seguro? Confirmar").
- Helpers: `$`, `$$`, `esc()`. Persistencia: `localStorage` claves
  `cpro_*` (`cpro_info`, `cpro_logo`, `cpro_logo_src`, `cpro_theme`,
  `cpro_cfields`, `cpro_xfields`) + IndexedDB cotizaciones/clientes.
- **Folio**: `XXX-YYMMDD-0001` (3 letras del nombre empresa + fecha
  compacta + correlativo persistente desde 0001; solo consume número
  al GUARDAR, no en borrador).
- **Campos personalizados**: perfil empresa → `cf_<slug>` en `cpro_info`
  (selector `#ifadd`); cliente en cotización → `x_<slug>` en `cx`
  (botón `#cfnew` bajo Dirección, inputs en `#cfcli` entre Dirección y
  Tipo de cliente). Nombres se guardan en `cpro_cfields`/`cpro_xfields`.
- **Moneda**: ₡ CRC / $ USD — el símbolo del precio sigue a `#cur`.
- **Impuesto**: switch `#taxtog`; apagado = no se calcula NI aparece
  (subtotal y total sí). Toggle con clase `d-none`, nunca inline.
- **Tipo de cliente**: solo Persona/Empresa; Empresa muestra
  nombre/contacto/teléfono empresa (`#empcli`). "Tipo de pago":
  Crédito/Contado viaja en `cx`.
- **Perfil**: read-only por defecto; lápiz `#pedit` activa edición;
  "Guardar info"/"Aplicar logo" vuelven a read-only. Avatar header
  `.avbtn` con halo arcoíris animado + empresa debajo del título
  centrado (`#hdco`).
- **Documento** (`qbody` preview + `drawQ` canvas): logo centrado
  arriba → nombre empresa → contacto → horario/SINPE/Tarjetas →
  Cliente | Cotización+fecha → tabla → totales. OJO: `.qh` es
  `display:block` (NO flex — flex los ponía lado a lado).
- **Export PNG/JPG/PDF**: lienzo 760px ancho, **alto mínimo 1351px
  (9:16 vertical)** — crece con ítems (9:18, 9:20…); totales anclados
  abajo cuando sobra espacio.
- Botón agregar ítems: solo el largo `#add` (brillo+parpadeo+
  "Agregar más servicios/productos" dinámico); selector `#itpo` a
  ancho completo. Labels "Moneda/Tipo de ítem/Concepto" centrados.
- Selector "+ Campo" de cliente (`#cfadd`) está OCULTO a propósito.
- UI: español, glassmorphism pastel, labels claros, inputs tipo pill.

## Verificación antes de avisar "listo"

1. `node --check` en cada JS tocado.
2. `wc -l` — ningún archivo >300.
3. Esperar ~9 s y confirmar `TRIBAL_OTA.ts` nuevo en
   `www/js/ota_stamp.js` (el watcher estampa solo).
4. Decir "OTA enviada (<ts>)" — el teléfono la aplica solo si está en
   el mismo WiFi; si el usuario dice "no llega", revisar `ipconfig`
   (la IP puede cambiar) y el log `[OTA]` del teléfono.

---

# TRIBALs — reglas del proyecto (legado del repo original)

## Cliente de escritorio (TRIBALs PC)

- `desktop/tribal_pc.py` — app Python+tkinter (solo stdlib, sin pip);
  lanzador `desktop/TRIBALs-PC.bat`. Config en `desktop/tribal_pc.json`.
- Habla la API HTTP del `TribalFtpPlugin` (puerto 8765): `GET /api/list`,
  `GET /dl?p=&n=`, `POST /up?n=` (binario crudo), `GET /del?i=`, `GET /ren?i=&n=`.
- Descubrimiento: escanea las /24 de todos los adaptadores locales +
  IPs conocidas de tethering/PAN (`192.168.42.129` USB, `192.168.43-45.x`
  hotspot/BT-PAN, `172.20.10.1`). El mismo socket sirve por WiFi, USB
  (anclaje RNDIS) y Bluetooth PAN — es solo TCP en cualquier caso.
- Prueba sin teléfono: `desktop/test_mock.py` levanta un mock del API
  en `127.0.0.1:8765` y valida discover/list/dl/up/ren/del.
- Borrado en el PC usa el propio `Confirm3` de 3 pasos (la app del
  teléfono ejecuta el `MS.remove` real al recibir `/del`).

## Preview del player (REGLA FIJA — NUNCA CAMBIAR)

- El servidor de preview es **http://localhost:8787** sirviendo `www/`.
- La vista del player es **`http://localhost:8787/media.html`**.
- **NUNCA** abrir un puerto nuevo ni apuntar la preview a otro puerto,
  a la raíz `/` ni a `index.html`. Siempre `/media.html` en `:8787`.
- Si el servidor no responde, levantar `python -m http.server 8787`
  (o el equivalente) en `www/` — el puerto es siempre 8787.

## Build

- APK: `scripts\build.bat` → `apks\app-debug.apk`
- Sintaxis JS: `node --check <archivo>` (los módulos son ES5-compatible)
- `build.bat` regenera `www/js/buildstamp.js` (`window.TRIBAL_BUILD`,
  en **hora de Costa Rica** `America/Costa_Rica`) antes del sync — el
  sello se muestra al pie del menú ⋮
  (`#build-tag` en `viewmenu.js`) para verificar qué build corre el teléfono.
- **OTA local (BLINDADO Y VERIFICADO EN VIVO — 2026-11-03):
  funcionando perfecto (ping ×2, pull, checksum, aplicar, modal).
  PROHIBIDO modificar `scripts/ota_watch.py`, `scripts/ota_push.py`,
  `scripts/ota_server.py`, `www/js/ota_stamp.js`, `www/js/media/ota.js`,
  el `/ota`+`/ping`+`/id` de TribalFtpPlugin ni la config Capgo sin
  PREGUNTARLE AL USUARIO primero — está blindado por orden expresa.**
  el APK ya NO sirve siempre el `www/` empaquetado. El plugin
  `@capgo/capacitor-updater@6.53.0` (rama compatible con Capacitor 6,
  instalado con `--legacy-peer-deps`) descarga el bundle nuevo y conmuta
  la carpeta del WebView con anti-rollback (`notifyAppReady` en `ota.js`).
  - `scripts/ota_watch.py` vigila `www/` (sin `builtin/`): estampa
    `js/ota_stamp.js`, zipea, SHA-256, sirve `/bundle.zip` + `/stamp.json`
    en :8788 y POST `{url,checksum,version}` a `http://<tel>:8765/ota`.
  - `TribalFtpPlugin` auto-arranca su server en `load()` (`:8765`):
    `POST /ota` → `notifyListeners('tribalOta')` · `GET /ping` →
    `tribalPing` (prueba de vida, modal por encima de todo).
  - `ota.js`: listener `tribalOta` → `download()+set()` · poller 8 s a
    `/stamp.json` via `CapacitorHttp` (respaldo si el evento se pierde) ·
    sello `#build-tag`: tap → pull manual, mantener → `Updater.reset()` ·
    modal «OTA aplicada» por `TRIBAL_OTA.ts` · logs `[OTA]` a la consola.
  - `usesCleartextTraffic="true"` en el manifest — SIN esto el download
    muere en "CLEARTEXT not permitted".
  - **El OTA solo actualiza `www/`** — Java/plugins exigen APK nuevo.
  - Guía completa de errores y réplica en `OTA-LOCAL.md`.

- **Ojo con el archivo `nul`**: un `> nul` mal redirigido desde bash crea
  un archivo literal `www/nul`; `cap sync` lo copia a `assets/public/nul`
  y Gradle falla en `mergeDebugAssets` ("nul: Función incorrecta").
  Solución: `rm -f www/nul android/app/src/main/assets/public/nul`.
- El teléfono corre SOLO lo empaquetado: cualquier cambio en `www/` o
  Java exige `scripts\build.bat` + reinstalar el APK. Verificar con el
  sello del pie del menú ⋮.

## Swipe de la cuadrícula → carrusel de la barra (NUEVO)

- `render.js` `barStep()`: swipe horizontal sobre `#grid`/`S.grid` recorre
  los `.tribal-tab` visibles de `#media-tabs` en el ORDEN del DOM (=
  `tribu_bar_order` → `tabfavs.js`). Fijar una app en la barra la mete en
  el carrusel automáticamente; quitarla la saca — sin tocar nada más.
- Reemplazó el swipe que cambiaba de página (`S.page±1`); la paginación
  sigue por los botones `pager-prev/next`.
- `.click()` en el siguiente ícono: filtros (`tab-*`) cambian de vista,
  proxies (`.tribal-fav`) abren su herramienta (Divisas, Tabla mágica…).
  Posición actual = el tab con `.active`; si ninguno, parte de bar[0].
- Transición: `.swipe-in-next`/`.swipe-in-prev` en `#grid` (media-extras
  `@keyframes tr-swipe-*` .3 s, entra deslizándose desde el lado).
- Mismas reglas sagradas: un dedo, |dx|>55, dominancia ×1.4, `touchend`
  con otro dedo apoyado anula.

## Tabla mágica — ELIMINADA POR ORDEN EXPLÍCITA (2026-11-03)

El usuario pidió quitar TODA la lógica: borrados mtable.js,
mtable2.js, mtable3.js, mtableev.js; botón vm-mtable, scripts en
media.html, entrada en tabfavs.js, voz en voiceparse.js, las 149
reglas .mt-* en media-extras.css y los bindBack() de retorno en
fx.js/notepad.js (las funciones huérfanas quedan inertes).
Los swipes Divisas⇄tabla y Notas⇄tabla ya NO existen.

## Hoja del lector (readerswipe.js) — invariantes, NO ROMPER

- Misma hoja orgánica (`makeLeaf`/`poseLeaf`/`settleLeaf`) para PDF,
  EPUB, TXT/notas y Office, por dedo y por botón.
- EPUB: `snapIframes` clona el iframe con `srcdoc` (epub.js usa
  `sandbox="allow-same-origin"`, el documento es accesible) y
  `copyScroll` copia el scroll de TODOS los contenedores (epub.js pagina
  moviendo `.epub-container.scrollLeft`) — sin eso la hoja enseña siempre
  el inicio del capítulo.
- Al decidir girar se llama `reveal(L)`: se quita la copia de abajo y se
  muestra la página REAL, cuyo contenido nuevo se pinta debajo; el paso
  corre AL SOLTAR (no tras la animación) y `pg._trSkipFlip` evita que
  `flip()` re-anime (doble giro fantasma = "la misma hoja").
- `flip()` (botones) también hace `reveal(L)` → transición idéntica.
- Segundo dedo durante el arrastre → la hoja se ASIENTA (nunca queda a
  medio giro); `makeLeaf` borra cualquier `.tr-leaf`/`.tr-under` huérfano.
- ↺ `#tr-home` (izquierda del fab, espejo de la lupa `.tr-finds`) llama
  `ui.goFirst` — cada lector lo define antes de `wireNav`; si falta, el
  botón se quita.

## Lector: long-press, marcador y pellizco

- **Long-press YA NO pone marcador.** `readerbm.js` solo expone
  `ui.bmPut()`; el marcador se pone con el botón 🔖 (`data-a="bm"`) de
  la burbuja `.tr-selpop` (readerfx.js `bindSel`).
- **EPUB** (normal e inmersivo): long-press ~650 ms quieto → `pickWord`
  (readerepub.js) selecciona la palabra bajo el dedo
  (`caretRangeFromPoint`), saca su CFI y abre la burbuja vía
  `selApi.showSel`. **TXT**: la selección nativa abre la burbuja.
  **PDF modo página y Office**: el long-press no hace nada.
- **Pellizco** (`readerpinch.js`, enganchado en `wireNav`): escala en
  vivo SOLO el contenido (`#tr-canvas`/`#tr-text`/`.tr-ozoom`, nunca la
  hoja de papel), con origen en el punto entre los dedos, y al soltar
  llama `ui.onPinch(r, focus, done)` (PDF/Office) o aplica
  `meta.info.fontSize` 40–400 % (TXT y PDF modo texto). Office:
  `ui.onPinch` con envoltura `.tr-ozoom` (`zoom` 0.15–8) y foco por scroll.
  Página más ancha que la pantalla (scroll): el dedo pasea y la hoja solo
  gira desde el borde (readerswipe).
### EPUB: letra por el librito — SECCIÓN BLINDADA (aprobada)

**PROHIBIDO modificar** salvo orden explícita del usuario.

- **EPUB NO tiene pellizco**: `ui.noPinch = true` en readerepub.js (justo
  tras `R.shell`) y readerpinch.js lo respeta en su `touchstart`; el
  iframe del EPUB NO lleva `TribalReaderPinch.bindDoc`.
- En EPUB el tamaño de letra se cambia con **long-press ~1.5 s en el
  librito `#tr-fab`** (modo limpio) → panel `.tr-fabpanel`, slider
  `data-fp="font"` 40–400 % (reader.js) → `meta.info.fontSize` →
  `rend.themes.fontSize`. También A−/A+ (readerfx.js `bump`, 40–400 %).
- El EPUB funciona distinto al PDF a propósito: NO igualarlos.

### Hoja orgánica (readerswipe.js `poseLeaf`)

- La hoja se siente tomada por el borde: `L.g` = dónde se agarró
  (−1 esquina de arriba … +1 de abajo, calculado al nacer la hoja con el
  offset del iframe si es EPUB); esa esquina se adelanta y levanta.
- `L.dy` = el dedo sube/baja (satura a ¼ de la altura de la página): la
  hoja se DOBLA con `skewY` únicamente (`rotateY` + `skewY`, máximo a
  mitad del giro por `sin(p·π)`): el LOMO (borde izquierdo) queda pegado
  al libro — NO usar rotateZ/rotateX, despegaban el borde y perdía
  naturalidad. Al asentarse `L.dy = 0` (se relaja).
- Sensibilidad del arrastre: `poseLeaf` corre UNA vez por cuadro
  (`L.raf` = requestAnimationFrame con `L.pp` pendiente; `settleLeaf`
  lo cancela) — NUNCA recalcular clip-path/gradientes en cada touchmove.
  Nada de `filter: drop-shadow` en la punta (mata los fps): la sombra
  del pliegue es `.tr-leaf-csh`, un degradado estático recortado.
  Giro completo a 0.8 del ancho de página.
- La dominancia horizontal ×1.4 solo decide si NACE la hoja; ya tomada,
  el movimiento vertical dobla. El giro final sigue exigiendo |dx| > 55 y
  dominancia ×1.4 al soltar (regla sagrada intacta).
- `.tr-leaf-gloss` dentro de la cara frontal: banda de luz/sombra que
  corre del borde libre al lomo y se inclina con el doblez.
- **La punta** (esquina inferior derecha, solo hoja "siguiente"):
  `.tr-leaf-csh` (sombra del pliegue, degradado) + `.tr-leaf-curl > <i>`
  (lengüeta del dorso con borde CURVO y punta redondeada: `clip-path:
  path("M0 0 Lc 0 Q .42c .30c .20c .58c Q .05c .82c 0 c Z")` — nunca un
  triángulo recto, se ve falso); la cara frontal recorta la esquina con
  polygon recto (la curva la da la lengüeta). Tamaño `c = min(W,H)·0.2·k`,
  `k = sin(min(1,1.8p)·π/2)·(1−0.35p)·(0.65 + 0.35·max(0,g) + 0.15·max(0,dy))`
  → se levanta enseguida al tirar y se recoge al final. `curlTr(L,t)`
  sincroniza su transición con la de la hoja (sin transición al arrastrar).
- Botones/flechas (`flip`): `L.g = 0.55` (esquina de abajo) y dos tiempos:
  se jala la punta (p 0→0.12 en .18 s) y luego gira completa (.5 s).
- Origen de giro: SIEMPRE `left center` (CSS `.tr-leaf`) — la hoja de
  "anterior" vuelve desde −180°; no cambiar el origen por dirección.

### Zoom del PDF — SECCIÓN BLINDADA (aprobada: "movimiento perfecto")

**PROHIBIDO modificar** este comportamiento salvo orden explícita del
usuario — ni umbrales, ni inercia, ni la cámara, ni volver al scroll.

- **Zoom del PDF = CÁMARA LIBRE** (readerpdf.js `place`/`keepFocus`):
  `ii.pdfZoom` 15–800 %; el canvas va `position:absolute` centrado en la
  hoja (`overflow:hidden`, SIN scroll — el scroll era lo que lo "pegaba"
  arriba) y se mueve con `translate(tx,ty)`; límite suave = siempre ≥25 %
  de pantalla con documento. Pellizco con foco: la vista previa se SUMA
  al `translate` base (readerpinch `base`) y al terminar el render
  (canvas temporal + swap, sin hoja en blanco) el punto entre los dedos
  queda bajo ellos. Ampliado (`pg._trPan`): un dedo pasea con inercia y
  readerswipe NO pasa hoja (se pasa con botones/flechas). Hoja nueva →
  arranca desde arriba (`toTop`).
- Valores exactos (no tocar): vista previa del pellizco `r` 0.15–8,
  umbral de aplicar |r−1| ≥ 0.06; inercia: velocidad suavizada
  `v*0.6 + inst*0.4`, frenado `×0.93` por frame, corte < 0.02 px/ms, sin
  flick si el dedo estuvo quieto > 80 ms antes de soltar; límite suave
  `(tamaño + pantalla)/2 − 25 % pantalla`; canvas a `devicePixelRatio`
  ≤ 2 con tope 8192 px por lado y 16 M px totales; render con `renderTok`
  (solo el último render se muestra). A−/A+ en modo página copia
  `fontSize` → `pdfZoom`.
- Archivos: `readerpdf.js` (`place`, `keepFocus`, `pend`, IIFE del
  paseo con inercia, `ui.onPinch`), `readerpinch.js` (foco + `base`),
  `readerswipe.js` (guard `pg._trPan`).
- **PDF inmersivo**: en `.tr-immersive` la hoja encaja ancho Y alto
  (`.tr-pdfpage` sin padding) y se re-encaja con `tr:imm`/`resize`;
  canvas renderizado a `devicePixelRatio` (máx. 2) para nitidez.

## RSS: gestión de canales (rss.js)

- **Buscar por tema**: `#rss-findq`+`#rss-find` → `dirSearch` consulta el
  directorio público `cloud.feedly.com/v3/search/feeds?query=&count=20&
  locale=es_ES` por `fetchText` (TribalRss nativo en el teléfono — sin
  CORS; en navegador depende de que Feedly sirva CORS). Resultados en
  `#rss-findres`: `.rss-res` con `data-u` (feedId sin el prefijo
  `feed/`) + `.rss-resadd` (+ / ✓ disabled si ya está) y `#rss-findall`.
  Todo lo agregado cae en «Mis feeds» (`tribu_rss_custom_v1`, `c:'mios'`).
- **Editar** (lápiz `.rss-srced`): rellena el form `#rss-newname/
  #rss-newurl`, pone `editing={u,mine}` y «Guardar»+`#rss-editcancel`.
  Catálogo → override `tribu_rss_edit_v1[urlOriginal]={n,u}` (la entrada
  conserva `c`/`p` y gana `_o`=url original); propio → `updCustom` en
  sitio. `moveCache` migra el offline si cambia la URL.
- **Quitar** (`.rss-srcdel`, cualquier canal): propio → `delCustom`;
  catálogo → URL original a `tribu_rss_hidden_v1` (`removeFeed`).
  `#rss-unhide` limpia ocultos. `allFeeds()` = catálogo −hidden +edits
  concat customs — TODO el módulo consume allFeeds, nunca FEEDS directo.
- **⚠ canal que falla**: `tribu_rss_fail_v1` url→1 (`markFail` en
  loadFeed sin caché y en updateAll; `markOk` al éxito). `#rss-cleanfail`
  quita de una vez todos los marcados. El ⚠ aparece en `.rss-srcm` (y en
  `renderSourcesMark`).
- El estado `editing` se reinicia en cada `viewSources()`.

## Identidad y contenido empaquetado

- La app se llama **TRIBALs** (`application-label` del APK), paquete `com.altair.app`.
- `index.html` redirige a `media.html` — el arranque del APK es el player.
- Música semilla: `C:\Users\MINIOS\Music\musica de la tribu` → se copia a
  `www/builtin/` (+ `builtin/manifest.json`). `js/media/seed.js` la registra
  como colección "musica de la tribu" en el primer arranque (flag
  `tribu_builtin_seed_v1`). Los metas llevan `builtin: 'builtin/<archivo>'`
  y se reproducen directo del asset — nunca copiar el blob al store.
- Tras cambiar el contenido de la carpeta: regenerar `manifest.json` y
  subir la versión del flag en seed.js para re-sembrar.

## Barra de accesos personalizable — SECCIÓN BLINDADA

`www/js/media/tabfavs.js` + su CSS en `media-extras.css` + markup en
`media.html` (orden `tribu_bar_order`, Todo siempre primero, píldora
fija al reordenar). **PROHIBIDO modificar esta sección** salvo orden
explícita del usuario — ni refactor, ni "mejoras", ni tocarla al añadir
entradas nuevas al menú de opciones. Las nuevas herramientas se integran
solo agregando su botón al menú ⋮ y un módulo aparte.

### Explorador «Todo» (`foldview.js`) — pedido por el usuario

- En «Todo» sin búsqueda (`viewMode 'items'` + `filter 'all'` + `!S.query`)
  `S.render()` delega a `S.renderExplorer()`: **solo carpetas**, ningún
  archivo suelto en la vista. Con búsqueda activa o en otras pestañas el
  render sigue igual.
- **Raíces de sistema** (acordeones `.tr-acc`, abiertos persistidos en
  `tribu_fold_acc`): Música, Notas de audio (`grab` = kind audio +
  `info.vn`/`Mi grabación`), Videos, Imágenes, Documentos, Archivos.
  Favoritos es fila especial arriba (`data-open-fav`).
- Dentro de cada raíz: **subcarpetas de usuario** (colecciones reales
  con `[data-fren]`/`[data-fdel]` — editables) y **subcarpetas de
  sistema por formato** (`fmtOf`: docs agrupan Word/Excel/PowerPoint/
  PDF/EPUB/TXT/Libros; el resto por extensión en mayúsculas) — solo se
  pintan si tienen archivos, NO se editan ni se borran.
- **Expansión EN LÍNEA** (`S.foldSub` → `tribu_fold_sub`): tocar una
  subcarpeta (`data-fold-sub="c:id"` usuario · `"f:kind:bucket"`
  sistema) la expande bajo ella misma con sus archivos como filas
  `.tribal-row tr-acc-file` (mismo markup de la vista de lista →
  play/⋮/long-press/selección funcionan por delegación) — la carpeta
  madre nunca se pierde de vista. La flecha › (`tr-acc-open`) abre la
  vista de página completa (`data-open-folder`/`data-open-fmt` →
  viewMode 'col'). Espaciado uniforme 10 px en `.tr-acc` y
  `.tr-acc-body` (sangría + guía lateral) — pedido explícito.
- **Migaja de ruta** (`S.crumbTrail` en foldview): dentro de una
  carpeta el crumb muestra «Todo › raíz › subcarpeta» (o
  «Colecciones › …» si se abrió desde ahí) — `.tr-crumb-seg`
  `data-cseg` toca para volver: `todo` → explorador, `acc:<k>` →
  explorador con esa raíz abierta, `cols` → vista Colecciones.
  El listener vive en `#media-crumb` (foldview attach).
- **El tipo también gobierna lo que se MUESTRA**: `TribalFoldView.
  memberOf(colId, m, items, cols?)` = miembro real (`m.cols`) Y
  compatible con el tipo de la carpeta (`accepts`). Se usa en el
  filtro `viewMode 'col'` (render.js), en el conteo `fileCount`, en
  la expansión inline y en las tarjetas-carpeta — así los datos
  viejos con miembros incompatibles (un video guardado en una
  carpeta de música antes de la regla) quedan invisibles en todas
  partes sin destruir la membresía.
- **Auto-vaciado de carpetas** (colassign.js): al desmarcar una
  colección, si los seleccionados son sus ÚLTIMOS miembros,
  `S.confirm` pregunta «quedará vacía y se eliminará — ¿proseguir?»;
  al aceptar, `setInCollections(false)` + `deleteCollection`. Si se
  estaba DENTRO (`viewMode 'col'`, `activeCol`), vuelve a la vista
  de origen. `MediaStore.pruneTypes()` corre al arranque (foldview
  register) y limpia membresías incompatibles viejas.
- **«Descargas» NO EXISTE como carpeta** (decisión del usuario):
  `origins.js` ya no la crea ni agrupa (los audios de Download caen
  en «Música» genérico + su formato); el arranque de foldview borra
  cualquier colección `org_dl`/`descargas?`/`downloads?` y
  `collections.js`/`multisel.js` bloquean crearla o renombrar a ese
  nombre. `meta.dl` sigue vivo solo para dlplay/bitácora.
- **Nota de voz = identificador indeleble `info.vn`** (el grabador lo
  estampa con `updateInfo(id,{vn:1})`; fallback nombre «Mi grabación»).
  Su raíz efectiva es `grab` (`rootOf`/`effectiveType`), así:
  `colAccepts`/`accepts` comparan por raíz — un VN JAMÁS entra en una
  carpeta de música ni forzado (rechazo con mensaje «va en Notas de
  audio › MP3») y un audio normal jamás entra en notas de audio.
  `matchFmt` lo excluye de `fmt:audio:*` → nunca aparece en Música›MP3.
- Una colección cuelga de la raíz `typeOf(c)` = `c.type` declarado o el
  tipo dominante de su contenido. `openNewCol(mode,col,type)` y
  `createCollection(name,type)` tipan las nuevas; las creadas desde
  multiselección heredan el dominante de lo seleccionado.
- **Tipado estricto** (media-store.js `effectiveType`/`colAccepts`):
  `setInCollections`/`toggleInCollection` rechazan archivos que no son
  del tipo de la carpeta; `setInCollections` devuelve cuántos saltó
  (los toasts avisan «N no eran de ese tipo»). Carpeta vacía sin tipo:
  acepta todo y luego hereda el dominante.
- Subcarpetas de formato se abren como colección virtual
  `S.activeCol='fmt:kind:bucket'` — `filtered()` y `collectionName()`
  las resuelven vía `TribalFoldView.matchFmt`/`fmtName`.
- El handler `[data-open-folder]` de render.js ignora toques en
  `[data-fren]/[data-fdel]` y respeta `S._lpBlock`; el long-press de
  carpeta (solo usuario, no sistema) vive en foldview.

### Administrador de comprimidos (`zip.js`/`zipui.js`) — PÁGINA COMPLETA

- Reconstruido de cero: `zipui.js` es `.arc-page` dentro de
  `.tribal-overlay.tribal-p2p-ov.arc-ov` (mismo molde flexbox del
  Directorio: cabecera ← Volver + `.arc-tabs` + `.arc-body` con
  `.arc-list` scrolleable y `.arc-form` abajo). Los estilos `.zp-*`
  fueron ELIMINADOS — todo es `.arc-*` (media-vnotes.css).
- **Buscador en vivo** en ambas pestañas (`#arc-q`/`#arc-q2` +
  `matchQ`): cada tecla refiltra — coincide por nombre, extensión/
  formato, palabra de tipo (audio/imagen/pdf…) y números, sin
  acentos (`norm` NFD); ✖ `.arc-qx` limpia. En Comprimir convive
  con el filtro de tipo y conserva los checks (`sel`).
- **Pestaña Comprimir**: filtro por tipo (`kindOf`), checks
  `.arc-row`, nombre + formato ZIP|TAR|TAR.GZ (contraseña solo en
  ZIP — el campo se oculta fuera de ZIP), `.arc-go`. El comprimido
  cae en «mis comprimidos» (raíz Archivos).
- **Pestaña Descomprimir**: `.arc-up` + `<input type=file>` sube
  comprimidos del teléfono a la tribu (`store.add`); `.arc-xlist`
  lista los de la tribu (`isArchive`); cada fila extrae → cada
  entrada se `store.add` + colección «nombre (extraído)» (la regla
  de tipos reparte lo incompatible). Campo contraseña para cifrados.
- `TribalZip` (motor, zip.js): `build` ZIP (DEFLATE+ZipCrypto),
  `buildTar`+`gzip` (TAR/TAR.GZ), `extract` → zip vía JSZip ·
  tar/tgz propio · **RAR/7z/tar.bz2/xz/ISO/CAB vía libarchive.js WASM**
  (`js/vendor/libarchive/` — `main.js` ESM `import()` dinámico,
  worker `worker-bundle.js`, WASM en `wasm-gen/` RELATIVO al worker —
  no mover). `isArchive` = regex de extensiones.
- RAR y 7z son SOLO LECTURA (no hay escritor libre — RAR propietario);
  la UI lo avisa en el hint de Comprimir.
- Entradas: ⋮ herramientas (`vm-zip`), ⋮ de archivo `menu-unz`
  (solo si `isArchive`) → `TribalZipUI.openExtract(m,deps)`, y
  «Comprimir» en el menú de selección múltiple (`msa-zip` →
  `TribalZipUI.open(deps, ids)` preselecciona).

### Espacio Tribal + P2P — RETIRADO (backup en `backup/`)

El usuario ordenó eliminar la nebulosa y TODO lo peer-to-peer para
aligerar la app en teléfonos lentos (A33 y menores). Quitado del APK:

- `space.js` `spacenet.js` `spacesim.js` `spacenear.js` `spaceme.js`
  `spacecam.js` `spacefx.js` `spacelink.js` + `TribalSpacePlugin.java`
  + `cinerc.js` («buscar mando» por la nebulosa) + `scan.js` (escáner).
- `chatp2p.js` `chatcall.js` `chatp2p.json` (sala MQTT + videollamada
  WebRTC), su intent-filter `tribals://` en el Manifest y el handler
  `tribalInvite` de `MainActivity`.
- UI: `vm-space`, `vm-scan`, `vm-newcol`, `tab-cols` (pestaña
  Colecciones), filas «Espacio Tribal» de Ajustes, tarjeta Colecciones
  de Estadísticas, `#col-new-card`, comandos de voz scan/colección.
- CSS: bloque `.space-*`/`.sl-*` de media-extras y `.rtc-*`/`.p2p-*`
  de btchat.
- TODO respaldado: `backup/nebula/` (js + plugin java + css),
  `backup/p2p/` (js + json + css), `backup/scan/`, `backup/cinerc/`.

### Wi-Fi / Hotspot / FTP / Control remoto — RETIRADO (backup en `backup/net/`)

El usuario ordenó dejar SOLO Bluetooth (chat + gestor) + Chromecast;
después pidió eliminar TAMBIÉN el control remoto/mando Bluetooth.
Quitado del APK:

- `btwifi.js` (gestor Wi-Fi/hotspot/Wi-Fi Direct + «Redes creadas por
  ti» `tribu_nets_v1`), `ftpserver.js` (servidor de archivos :8765),
  `TribalFtpPlugin.java`, `TribalWfdPlugin.java`, `btremote.js`
  (mando remoto + trackpad) → `backup/net/`.
- UI: `vm-ftp`, `ms-ftp`, `menu-ftp`, `btc-wf` («Chat Wi-Fi»),
  `vm-remote`, `btc-rc`, `btm-rc`/`data-act="rc"`, `cine-rc`,
  tiles `btm-wifi`/`btm-hs` del gestor BT, filas `wifiDevice`/redes
  Wi-Fi, comandos de voz wifi/ftp/remoto.
- `btchatnet.js`: `send()` = solo `BT.send` (RFCOMM); `connect()` =
  solo `BT.connect`. Sin `wifi*`/`hotspot*`/`chatConnect`/`chatSend`/
  `minimize`. Mensajes `rc` e invitaciones `winvite/waccept/wdecline`
  se descartan en silencio (ya nadie los ejecuta ni los envía).
- `TribalBtPlugin.load()`: ya NO arranca `startWifiUdpServer()`
  (discovery UDP :47777) ni `startChatServer()` (:47779) — sin
  oyentes perpetuos. Los métodos `wifi*`/`hotspot*`/`chat*`/`minimize`
  quedan DORMIDOS en el plugin (cero coste si nadie los llama) —
  no usarlos.
- Eliminado `viewmenu` → `TribalRemote.initListener(S)`: este teléfono
  ya NO ejecuta comandos remotos entrantes (ambas direcciones mueren).
- **TRIBALs PC (`desktop/tribal_pc.py`) queda sin servidor** — la API
  :8765 era el plugin FTP. Resucitar el plugin = copiar de
  `backup/net/` + registrarlo en `MainActivity`.

Lo que SIGUE de esa era (todavía vigente):

- **`scanio.js` + `TribalScanPlugin`** se quedan: `media-meta.js` los
  usa para «abrir la carpeta» (`TribalScanIO.openLocation`) de los
  archivos referenciados (`m.ref`). El escáner-como-página murió, el
  plugin nativo no.
- **Permisos al boot**: `btchatnet.js` llama `ensurePerms()` ~3 s tras
  cargar (Ubicación + BT de una). Ya concedidos → sin diálogo.
- **`WebChromeClient` de `MainActivity`** (`setupWebChromeClient` →
  `request.grant(...)`) se queda: el grabador de notas de voz
  (`vnotes.js`, `btchatvoice.js`) pide `getUserMedia({audio})` al
  WebView y sin el grant muere en silencio.
- **Identidad tribal**: `tribu_btname`/`tribu_tid` (`btchatnet`) —
  siembra con el modelo real del UA y renombra el adaptador BT a
  `TRL·<modelo>` (`TribalBtPlugin.tagAdapter`). El chat la usa.
- **Redes creadas persisten** (`tribu_nets_v1`, btwifi.js): sección
  «Redes creadas por ti» en la pestaña Hotspot con SSID+clave reales.
- **`/call` del `TribalFtpPlugin`** queda como vestigio sin llamantes
  (lo invocaba la nebulosa); el resto del servidor :8765 (FTP/remoto)
  sigue igual y es el canal de TRIBALs PC (`desktop/`).
- **Anclaje USB `192.168.42.x`** sigue siendo la vía cableada hacia el
  servidor :8765 (misma verdad: ninguna app puede activar «Compartir
  por USB», es toggle del sistema).

### Modo Cine — ELIMINADO (oct 2026)

- Eliminados `cine.js`/`cinecat.js`/`cinemus.js`/`cinepic.js`/`cineart.js`
  + `media-cine.css` + `#view-cine` + `TS.reg('cine')` — todo respaldado
  en `backup/cine/` por si se resucita.
- El look de TRIBALs Video vive ahora EN LA REPISA: en `render.js`
  (`shelfView`) los items `kind==='video'` llevan `.tr-shelf-cov.tr-movie`
  con `.tr-movie-grad` + `.tr-movie-t` + `.tr-movie-play`
  (gradiente + título + ▶) — el cargador `data-videothumb` inserta el
  fotograma sin pisar el overlay (usa `insertBefore`).
- Chromecast quedó directo en el player: `#vf-cast` (stage de video),
  `#iv-cast` (visor de imagen), `data-v="cast"` en el vinilo
  (`cb.sono` = S — pasado desde `S.openVinyl`) y `menu-cast` del menú
  contextual por archivo.
- **Cast** (`TribalCast` — Chromecast/Fire Stick/TV/DLNA ya existente):
  `#vf-cast` dentro de `.vf-stage` (player.js — se muestra ~4.5 s al sonar
  o al tocar el video; al usarlo sale del fullscreen para que el modal
  z-90 se vea) · `#cm-cast` en el header de cinemus (transmite la pista
  que suena o la 1ª) · `.cp-cast` en el visor de cinepic (cierra el visor
  primero — su z-9800 taparía el modal). Todos llaman
  `TribalCast.open(m, S)` = RemotePlayback → Presentation → Cast nativo.
  - **Modo TV** (`tvroom.js`, opción del diálogo) — DOS vías en cadena:
    1. `tvcast.js` + `TribalCastNativePlugin` (Cast SDK real,
       `play-services-cast-framework:21.5.0`, provider
       `TribalCastOptions` = receptor por defecto CC1AD845): levanta
       `TribalFtpPlugin` :8765, descubre Chromecasts por MediaRouter,
       `route.select()` abre sesión y `RemoteMediaClient.load(MediaInfo)`
       apunta a `http://ip:8765/s?p=tribu_media/…` (`?a=` absoluta para
       `ref`, `?p=builtin/…` para semilla). El Chromecast descarga y
       reproduce ÉL — fullscreen + buffer nativos (estilo Netflix);
       el teléfono muestra `.tvroom-rv` (picker de TVs → mando
       ⏮±10 s⏭, play/pausa, progreso poll `status()` 1 s, ✕ fantasma).
       Endpoint `/s` sirve Range/206 + mime — el receptor los EXIGE
       para seek. `RemotePlayback`/`Presentation` del WebView NO existen
       en Android — por eso el cast es 100 % plugin nativo.
    2. **Espejo limpio** (fallback + imágenes): `body.tvroom` oculta TODO
       el chrome (vf-x/cast/restore, títulos, controles nativos del
       video vía `removeAttribute('controls')`) y `.vf-stage`/`#image-viewer`
       van a `position:fixed inset:0` 100 vw×100 vh — la TV duplicada ve
       solo el media. Audio → sala `.tvroom-au` (carátula + progreso).
    Salida: ✕ fantasma `.tvroom-x` (3 s tras tocar) o Atrás
    (`fullscreenchange` → `close()` restaura controles, para el :8765
    si hubo cast real). Indicador `.tvroom-buf` en waiting/stalled.
- **Control remoto** (`TribalRemote` — ELIMINADO): `#cine-rc` quitado;
  `btremote.js` respaldado en `backup/net/`.
  TribalRemote ya controla este player (toggle/prev/next/vol/seek —
  `execLocal` usa `S.stepAudio` sobre `S.queue`, que el cine reasigna =
  funciona con la cola de cinemus).
- **«Buscar mando» fue RETIRADO** con la nebulosa (`cinerc.js` borrado —
  su UI de enlace era el Espacio). `TribalRemote` sigue activo desde el
  menú/chat y vincula por sí mismo (escaneo + `N.connect` propios).
- **TRIBALs Music** (`cinemus.js`): lista plana — SOLO música
  (`kind==='audio'` sin `isVN` — notas de voz/grabaciones excluidas);
  sin carpetas ni notas. **TRIBALs Pictures** (`cinepic.js`): solo
  JPG/JPEG/PNG (`isPic` — ni GIF ni otros formatos) y los thumbnails
  (`cineart.js imgThumb`) son 320 px JPEG q.62, más livianos.

### Directorio (`appdir.js`) — pedido por el usuario

- El ⋮ solo muestra `#vm-dir` (Directorio) y `#vm-batt` (Ajustes) +
  Ordenar/build-tag: `#view-menu > button:not(#vm-dir):not(#vm-batt)
  {display:none}` — los demás botones SIGUEN en el DOM (los proxies de
  la barra y los listeners de viewmenu los necesitan vivos).
- `window.TribalBar` (exportado al final de tabfavs.js): `list()`,
  `inBar(id)`, `toggle(id)`, `move(id,dir)`, `render()`, `max` — es el
  MISMO motor `tribu_bar_order`; el pin del directorio y el del ⋮ son
  la misma llave. Nunca duplicar lógica de pines.
- `ACTIONS` creció con `vm-dedup`, `vm-logs`, `vm-batt`, `vm-dir` (los 4
  pinnables como cualquier acceso).
- `appdir.js`: overlay `.dir-ov` con `.dir-body` — todos los ACTIONS en
  orden alfabético (`titleOf`: para vm-* el texto del botón del ⋮, para
  tab:* el título del catálogo), separador `.dir-letter` por inicial,
  fila `.dir-open` (re-dispara `.click()` del botón original, igual que
  los proxies) + `.dir-pin` (toggle de barra; `tab-all` con candado).

### Tamaños FIJOS de los botones (no tocar NUNCA)

- PC y móvil: círculos de **46×46 px**, `border-radius: 50%`.
- Móvil (≤640px): `flex: 0 0 46px`, `justify-content: space-evenly`,
  ícono `1.05rem`. **Sin `aspect-ratio` ni `flex-basis` porcentual** —
  eso fue lo que los hizo ovalar y luego gigantizar.
- Ícono en PC: `1.15rem`.

## Íconos dentro de círculos (play, ⋮, kind) — SAGRADO, NO TOCAR

`bootstrap-icons.css` pone `vertical-align: -.125em` en `::before` →
el glifo queda bajo dentro de círculos (visible sobre todo en Firefox).
NUNCA usar `display:inline-block`/`block` en el `<i>` de un botón
circular. La regla blindada (media-extras.css) es:

```css
.btn-circular i {
    display: inline-flex;
    align-items: center; justify-content: center;
    line-height: 1;
}
.btn-circular i::before { vertical-align: initial; }
```

El `<i>` flex convierte el `::before` en flex item y el centrado es
exacto en PC/móvil/Firefox. El triángulo `bi-play-fill` además lleva
`transform: translate(1px,0)` porque su glifo está ópticamente a la
izquierda.

### Medidas FIJAS de los círculos de fila (sagradas)

- `.tr-row-play`: **30×30 px**, `border-radius: 50%`, borde
  `1px var(--tb-border)`, fondo `rgba(0,0,0,.35)`, ícono `0.95rem`;
  `.playing` → borde `--tb-gold` + halo dorado.
- `.tr-row-kind`: 30px de ancho, ícono `1rem` en `--tb-muted`.
- `.tr-row-menu`: **30×30 px** circular transparente, ícono `1rem`.
- Todos con el `<i>` en `inline-flex` centrado (regla de arriba).
- **PROHIBIDO** cambiar tamaños, centrado, colores o la corrección
  óptica del play salvo orden explícita del usuario.

## Mapa de blur de modales — REGLA DE ESTILO GLOBAL

**Todos los modales de la app usan el mismo patrón**: backdrop fijo a
pantalla completa (`position:fixed; inset:0`), fondo semitransparente,
`backdrop-filter: blur(Npx)` + `-webkit-backdrop-filter`, y la tarjeta
centrada horizontal y vertical (flex `align-items:center` +
`justify-content:center`, o `translate(-50%,-50%)`).

### Cómo obedecer "revierte el blur en X"

Cuando el usuario pida **quitar el blur de una sección**, ir a la fila de
ese selector en la tabla y **quitar las líneas `backdrop-filter` y
`-webkit-backdrop-filter`** de ESE selector solamente (dejar el
`background` semitransparente intacto). Si pide quitarlo de TODO,
quitarlo de todas las filas "modal con blur" de la tabla.

| Sección (lo que dice el usuario) | Selector (backdrop) | Archivo CSS | Blur |
|---|---|---|---|
| "libros", "lector", "diálogos del libro" (nota / compartir / convertir) | `.tr-notedlg` | `css/media-extras.css` | 10px |
| "orden", "orden de secciones" | `.sec-bd` | `css/media-extras.css` | 9px |
| "menús", "menú ⋮", "menú del reproductor", "menú de tarjeta" | `.tribal-menu-bd` | `css/media.css` | 9px |
| "diálogos", "confirmaciones", "modales" (genérico: confirm, colecciones, batch, zip, dl-formato, conv-audio) | `.tribal-overlay` | `css/media.css` | 6px |
| "bloc de notas", "notas" | `.np-modal-bd` | `css/media-notepad.css` | 8px |
| "estadísticas", "archivos guardados" | `.stats-fov` | `css/media-extras.css` | 12px |
| "píldora de acciones", "menú flotante" | `#fav-pop` | `css/media-extras.css` | 10px |

### NO son backdrops de modal — no tocar si piden "quitar blur de modales"

- **Páginas completas** (ocupan toda la pantalla con fondo opaco; un blur
  detrás sería invisible): `.tribal-reader-ov` (lector), `.tribal-p2p-ov`,
  `.np-overlay` (bloc), `.vn-overlay` (notas de voz), `.zp-overlay` (zip),
  `.tribal-btchat-ov` (chat BT — tiene `backdrop-filter:none` explícito),
  `.tribal-dl` (descargas), `.tribal-fx` (divisas), `.stats-page`.
- **Blur de vidrio** (es el estilo del elemento flotante, no un fondo de
  modal): `.tribal-fab`, `.tribal-fab-wrap.open`, `.tr-fab`, `.tr-finds`,
  `.tr-finds-nav`, `.tr-edge`, `.tf-bar`, `.np-selmenu`, `.tr-selpop`.
  Si el usuario dice "quita el blur de los botones del lector" se refiere
  a ESTOS, no a los backdrops de la tabla.

## Subsistemas blindados recientes (no regresar)

- **Secciones por tipo** — `sections.js` agrupa (Todo/orden del usuario,
  Música + "Mis grabaciones", búsqueda); `render.js` pinta un stream
  separador+items; separadores `.tribal-kind-sep` con hr centrados.
- **Colapso de secciones** — tap en el título de sección colapsa su
  grupo; long-press (~550ms) en `#sec-order` colapsa/expande TODO.
  Estado en `tribu_sec_collapsed`. Sin botones extra en el separador.
- **Orden de secciones CONTEXTUAL** — botón `#sec-order` junto a
  `#view-switch` abre un MODAL centrado con fondo blur (`.sec-bd` +
  `.sec-panel`, flechas ▲▼). El contenido depende de la vista activa:
  · **Todo** (`filter=all`) → secciones grandes, clave `tribu_sec_order`
    (default image,audio,video,doc,other; 'grab' va pegado tras 'audio').
  · **Libros y notas** (`filter=doc`) → Favoritos/EPUB/PDF/TXT/Notas/
    Libros, clave `tribu_sec_order_doc` (lee `S.secOrderDoc` en
    `sections.js` en vez del ORD fijo).
  · **Música** (`filter=audio`) → grupos vivos del render actual
    (col:/org:/mus — tribu, colecciones, orígenes), clave
    `tribu_sec_order_audio`; `applyAudio` superpone ese orden y los
    grupos nuevos van al final en su orden natural.
  · Otras vistas (videos, imágenes, búsqueda, colecciones) → el modal
    dice "Esta vista no tiene secciones que ordenar".
  `render.js` guarda `S._lastSecs` con los grupos vivos de cada render.
  OJO: `.sec-bd` lleva `display:flex` — SIN `[hidden]` guard
  (`display` le gana a `hidden`) queda tapando la app entera.
- **Buscador inteligente** — `smartsearch.js` (`S.buildMatcher`):
  nombre/metadatos/tipo/ext/colección/duración/tamaño; soporta
  `3:45`, `>1:00`, `<90s`, `>10mb`, `tipo:x ext:y col:z`.
- **Grabador de notas persistente** — `vnotes.js` + `vnotesav.js` +
  `vndraft.js`: autoguardado en IndexedDB (ranuras `__vn_*`) +
  localStorage `tribu_vn_draft`; auto-pausa al ocultar la app;
  restaurar = seguir/guardar/eliminar (triple confirmación); retomar
  fusiona por decode+paste→wav (NUNCA concatenar blobs webm crudos —
  cada sesión trae su propio header y se corrompe).
- **Comandos de voz** — plugin nativo `TribalVoice` (SpeechRecognizer
  es-ES, parciales; eventos voiceResult/voicePartial/voiceError) +
  `voicecmd.js`: parsea frases y dispara los MISMOS handlers de
  botones/tabs (nada paralelo). Entrada ÚNICA: ⋮ → Ajustes →
  «Comandos de voz» (`#batt-voice`). El activador de voz de la «B»
  del logo fue RETIRADO a pedido del usuario — no reactivarlo.
  En navegador no hay plugin → toast "solo en la app instalada".
- **La «B» del logo = encabezado compacto — SECCIÓN BLINDADA**
  (aprobada por el usuario: «hasta ahí llegamos muy bien»).
  PROHIBIDO modificar salvo orden explícita.
  `headctl.js`: clic en `.tribal-title .tr-b` (NO la `.tr-b` del
  vinilo) alterna `.tr-compact` en `#tribal-root`. Persiste en
  localStorage `tribu_head_compact`. Pensado para pantallas chicas;
  igual en PC. En compacto **TRIBALs queda 100% centrado** (la caja
  título+crédito `flex:1` + `text-align:center` — NO `margin:auto`, que
  centra la caja pero el ancho lo marca la línea del crédito y el
  título quedaba corrido — y el sol `absolute` a la derecha).
- **Colapso SUAVE (pedido posterior, mismo sistema)**: los ocultos NO
  usan `display:none` sino pliegue animado — `.tribal-sub`,
  `.tribal-tabs`, `.tribal-viewswitch` llevan `max-height` holgado +
  `overflow:hidden` + transición (a 0 con `opacity`/`visibility:hidden`
  + `pointer-events:none` en `.tr-compact`); el sol transiciona
  width/height 64→34 px; y el título viaja izquierda⇄centro con FLIP
  en `apply()` (rect antes/después + transform inverso + la transición
  `transform` de `.tribal-header-inner > div`; `apply(on,true)` salta
  sin animar al restaurar el estado guardado). El crédito
  `.tribal-credit` se REUBICA en el DOM junto al título (y vuelve
  antes de `.tribal-search` al expandir).
  En compacto el sol (`#sun-btchat`) QUEDA visible pero mucho más chico
  (`.tr-compact .tribal-sun` 34 px) — hubo un relevo `#tr-btchat`
  (círculo BT azul) que el usuario pidió ELIMINAR: no reintroducirlo.
  **El sol abre el CHAT BLUETOOTH** (btchatbadge `hookSun` → `openChat()`
  → clic en `vm-btchat`, o `TribalBtChat.open` de respaldo). La insignia
  de mensajes sin leer `.fab-btbadge` sigue sobre el sol y también abre
  el chat (stopPropagation).
- **Ajustes de batería** — plugin `TribalBatt` (status/ask/openList),
  menú ⋮ → "Ajustes de la aplicación" `#vm-batt`, diálogo `#batt-overlay`.
- **Media Session / pantalla de bloqueo** — `mediasession.js` exporta
  `window.TribalMS` (set/state/pos/clear); `player.js` lo llama en
  play/pause/timeupdate/loadedmetadata/close. ⏮⏭ del sistema pasan por
  `stepAudio` (mismo cerrojo). La carátula se convierte a data URL ≤384px
  (blob: no lo lee el SO fuera del proceso). Es sesión WebView: si el SO
  mata el proceso de la app, la notificación muere — no hay servicio
  nativo en foreground.
- **Slider de volumen del vinilo con relleno de nivel** — SAGRADO:
  `.tribal-vinyl-volrange` muestra el nivel real — izquierda del thumb
  = degradado tribal (terracota→dorado), derecha = gris apagado.
  `paintVol()` en `media-vinyl.js` repinta el gradiente con tope duro
  en el % actual (WebKit); Firefox usa `::-moz-range-progress` nativo.
  Se llama en el `input` directo, en el gesto vertical del lado
  derecho y al abrir el fullscreen. NO cambiar colores, thumb, ni el
  mecanismo de repintado salvo orden explícita del usuario.
- **Cerrojo anti-fantasma del cambio de pista** — `player.js`/`media-vinyl.js`:
  `stepAudio` ignora saltos <400 ms (doble disparo); el evento `ended`
  solo avanza si `currentTime ≥ duration − 1.5` (ended espurio del WebView
  a media canción se reanuda, nunca salta); el swipe del vinilo exige dedo
  primario + flick <700 ms con |dx|>55 y dominancia ×1.4 — `pointercancel`
  y el segundo dedo/palma JAMÁS cambian de pista. La MISMA regla aplica a
  TODAS las superficies de arrastre (`swipenav.js` visores, `readerswipe.js`
  pasar hoja, swipe de página de la cuadrícula en `render.js`): un
  `touchend` con otro dedo aún apoyado (`e.touches.length !== 0`) anula el
  gesto — nunca cambia de elemento/página/hoja. No relajar estos filtros.
- **Selector de archivos nativo** — El botón de subir (`fabdir.js`), el
  chat Bluetooth (`btchat.js`) y el slideshow (`media-slidecfg.js`) usan
  directamente el selector nativo de Android/sistema (`<input type="file">`).
  Los motores y trackers de torrent se extrajeron a
  `torrents-motores-y-trackers.txt` y el subsistema P2P fue retirado
  (la sala MQTT/chatp2p.js también — ver «Espacio Tribal + P2P —
  RETIRADO»).
- **Flechas de pasar hoja del lector — SAGRADO, NO TOCAR** — `.tr-edge-l`
  y `.tr-edge-r` en `reader.js` + `media-extras.css`: solo existen en modo
  lectura limpio (`.tr-clean`, cuando las barras se auto-ocultan a los 5 s).
  Pegadas a los bordes (`left:0`/`right:0`), a la altura del fab
  (`bottom: calc(30px + env(safe-area-inset-bottom, 0px))`), 40×68 px,
  vidrio oscuro `rgba(6,4,2,.52)` + blur 10px + ícono ámbar `#ffb347` —
  el MISMO look del fab herramientas. Comparten su ciclo de atenuación:
  clase `.tr-fab-dim` → `opacity:.13` tras 30 s sin tocar, siguen
  respondiendo. Hacen `nav(±1)` con `stopPropagation` para no despertar
  el chrome; el swipe del dedo sigue enganchado al overlay entero. En
  `.tr-clean` el `.tribal-reader-body` reserva `padding-bottom` para que
  el texto NUNCA quede bajo los botones (ni su blur los tape).
  PROHIBIDO mover, retocar look ni romper el dim compartido salvo orden
  explícita del usuario.
- **Long-press del fab herramientas** — mantener ~1.5 s sobre `#tr-fab`
  en modo limpio abre `.tr-fabpanel`: sliders de tamaño de letra
  (`meta.info.fontSize`, 50–250%), brillo (`meta.info.dim` → `#tr-dimlay`)
  y volumen de la música de lectura (`TribalReaderMusic.setVol`).
- **Marcas del lector — invariante de offsets, NO ROMPER** — las marcas
  `{s,e,c,n}` son offsets absolutos del TEXTO crudo; `renderMarked` las
  pinta y `pgnums` convierte `── Página N ──` en la píldora `.tr-pgnum`
  cuyo texto visible (`· N ·`) es MÁS CORTO que el marcador. Por eso la
  píldora lleva `data-t` con el marcador original y `selOffsets`
  REINTEGRA la diferencia de longitud (folio antes del inicio → ajusta
  `s`; folio dentro de la selección → ajusta `e` con `intersectsNode`).
  PROHIBIDO cambiar el contenido visual de `.tr-pgnum` sin conservar
  `data-t` ni alterar esa compensación: si el DOM difiere del texto, las
  marcas se guardan corridas y "se pierde el color". Paginación TXT con
  folios = cortes reales en cada `── Página N ──` (no por tamaño de
  letra); sin folios = ~1400 caracteres. El ⊘ limpia marcas tocadas por
  la selección (unmarkSel) — funciona igual.

## Estado al 2026-11-03 — dónde quedó el proyecto

- **OTA local en producción**: push → descarga con checksum → aplicar →
  recarga → modal. Poller cada 8 s + chequeo al boot (~2.5 s): si la
  actualización llegó con la app cerrada, se descarga EN SILENCIO al
  reabrir (sin toasts — solo el modal avisa). `reset()` vuelve al paquete.
- **Identidad del teléfono**: `devname='tribals-<uuid5>'` +
  `devid='<modelo>-<uuid5>'` persistentes (SharedPreferences `tribu_dev`)
  en `FTP.info()`/`/id`. Visible: ⋮ → fila 📱 arriba con HR (tap → modelo
  · IP · devid), Ajustes → «Identidad del teléfono», bajo el lema.
- **⋮ Opciones = modal centrado** (`#view-menu` position:fixed,
  left/top 50% + translate(-50%,-50%), 80vw, max-height 82vh, scroll)
  con TODAS las herramientas (`vm-dir` oculto — el ⋮ ES el directorio).
- **Ajustes**: secciones «Identidad», «Llevar TRIBALs a otra PC»
  (compartir zip portátil + URL `/dl?p=tribu_inbox/TRIBALs-PC.zip`),
  «Segundo plano», «Comandos de voz», «Permisos».
- **Lema**: `Hecho con ♥ por la tribu de los libres` bajo el título
  (corazón rojo con pulso `trHeart`); subtítulo del fuego fuera.
- **builtin via FTP stream**: `getURL` sirve `builtin:` por
  `http://127.0.0.1:8765/s?p=` en APK — bajo bundle OTA el `builtin/` del
  paquete no está en el directorio servido (no viaja en el zip).
- **Portátil PC**: `Desktop\TRIBALs-PC\` — TRIBALs-PC.exe + OTA-watch.exe
  + www/ (sin builtin) + codigo/ (fuentes, OTA-LOCAL.md, AGENTS.md) +
  LEEME.txt. Zip subido al teléfono (`tribu_inbox/TRIBALs-PC.zip`).
- **Tabla mágica eliminada** (2026-11-03): ver sección arriba.
- GitHub: `git@github.com:kerm1977/altair2.git` rama `main` — último
  commit blindado `49aeb0f` + estado posterior pendiente.
