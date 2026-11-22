# OTA local TRIBALs — guía de implementación

Sistema de actualización **100 % local** (LAN, sin nube ni Tailscale) que empuja
`www/` al teléfono sin reinstalar el APK. Copiado del motor de Emprendedores:
el plugin **`@capgo/capacitor-updater`** hace todo el trabajo pesado.

```
PC                                          TELÉFONO
scripts/ota_watch.py                        TribalFtpPlugin :8765 (auto-arranque)
  vigila www/         ── cambio ──▶  POST /ota {url, checksum, version}
  sirve :8788                          → notifyListeners('tribalOta')
    /bundle.zip                          → JS: CapacitorUpdater.download(url)
    /stamp.json (ts, sha)                → .set(id) → aplica + recarga solo
                                         → modal «OTA aplicada · hora · archivos»
                                         → notifyAppReady() anti-rollback
```

## Piezas (archivos)

| Pieza | Archivo | Rol |
|---|---|---|
| Watcher + servidor | `scripts/ota_watch.py` | Vigila `www/` (excluye `builtin/` + `ota_stamp.js`), estampa `js/ota_stamp.js` ({ts, files}), zipea → SHA-256, sirve `/bundle.zip` + `/stamp.json` en :8788, y POST `{url,checksum,version}` a `http://<tel>:8765/ota`. Descubre el teléfono (barrido /24 paralelo) y lo cachea en `scripts/.ota_ip` |
| Push manual | `scripts/ota_push.py` | Igual que el watch pero un solo envío |
| Servidor simple | `scripts/ota_server.py` | Solo sirve `/bundle.zip` (pull manual por sello de build) |
| Endpoint teléfono | `TribalFtpPlugin.java` | `POST /ota` → `notifyListeners("tribalOta")` con url/checksum/version · `GET /ping` → `notifyListeners("tribalPing")` (prueba de vida) · `load()` auto-arranca el server en :8765 |
| Cliente OTA | `www/js/media/ota.js` | `notifyAppReady` al boot · listener `tribalOta` → `download()+set()` · listener `tribalPing` → modal · **poller** cada 8 s a `/stamp.json` via `CapacitorHttp` (respaldo si el evento se pierde) · sello de build: tap → pull manual, mantener → `Updater.reset()` · modal «OTA aplicada» cuando `TRIBAL_OTA.ts` cambia · todo con `S.log('[OTA] …')` |
| Sello | `www/js/ota_stamp.js` | `window.TRIBAL_OTA = {ts, files}` — lo reescribe el watcher en cada push |
| Manifest | `AndroidManifest.xml` | `android:usesCleartextTraffic="true"` — **sin esto el download muere** |

## Errores reales cometidos y su solución (lo que NO hay que hacer)

1. **OTa a mano con `setServerAssetPath` + `bridge.reload()` → `ERR_CONNECTION_REFUSED`.**
   El reload pedía la URL antes de que el server la sirviera; ni `recreate()` lo salvaba.
   **Solución: no reinventar la rueda — usar `@capgo/capacitor-updater`.**
2. **`Checksum required`** — Capgo exige SHA-256 del zip (Emprendedores lo genera
   en `herramientas/publicar.py` con `hashlib.sha256(bytes).hexdigest()`).
   El watcher cachea el bundle para que el checksum == los bytes servidos.
3. **`CLEARTEXT communication … not permitted`** — Android bloquea HTTP a la LAN.
   Solución: `usesCleartextTraffic="true"` en el manifest.
4. **ERESOLVE de npm** — `@capgo/capacitor-updater@8.x` exige Capacitor 8;
   con `@capacitor/core@6` va la rama **`@6.53.0`** + `--legacy-peer-deps`
   (porque `@capgo/capacitor-native-biometric@8.3.6` ya convive con core 6).
5. **Evento perdido con la app cerrada/background** — el push solo llega si la
   app está abierta. Solución: poller de 8 s al `/stamp.json` con
   `CapacitorHttp` (nativo, esquiva CORS **y el mixed-content** `https://localhost`
   → `http://lan` que mata `fetch()`). El `tribu_ota_url` se arma solo al
   primer `tribalOta` o por el sello de build.
6. **`org.json` `in` ya definido** — en `recvOta` el `InputStream in` choca con
   `JSONObject in` → renombrar a `jo`.
7. **Imports faltantes** — `FileOutputStream`/`InputStream` calificar
   `java.io.*` completo.
8. **Python en Windows**: `→` rompe `print` en cp1252; `bind 8090` dio
   WinError 10013 (rango reservado) → puerto **8788**.
9. **El modal se veía "a veces"** — `S.root` oculto en boot + z-index bajo:
   `document.body` + `z-index:10050` (y el ping a `2147483647` por encima de todo).

## Reglas duras aprendidas

- **El OTA actualiza SOLO `www/`** — Java/plugins nunca viajan en el bundle:
  cualquier cambio nativo = APK nuevo obligatorio.
- `builtin/` NO viaja en el zip (es estático y pesado) — el Capgo lo toma del
  paquete porque el `www` del bundle se fusiona con el del APK.
- **`notifyAppReady()` es OBLIGATORIO en cada boot** o el plugin revierte el
  bundle al empaquetado (esa es la protección anti-brick: si el nuevo `www`
  crashea, la app vuelve sola — la pantalla en blanco de antes no puede
  volver a pasar).
- El sello `build-tag` es el diagnóstico: tap → pull manual · mantener →
  `Updater.reset()` al paquete.
- Prueba de vida sin actualizar: `curl http://<tel>:8765/ping` → modal
  «Comunicación viva».

## Checklist para replicar en otra app

1. `npm i @capgo/capacitor-updater@<rama compatible con tu capacitor> --legacy-peer-deps`
2. `npx cap sync android`
3. `usesCleartextTraffic="true"` en el manifest
4. Endpoint `/ota` (JSON {url,checksum,version} → `notifyListeners`) +
   `/ping` en el server que ya tenga el teléfono (o uno mínimo)
5. `ota.js`: notifyAppReady + listener + poller + modal + reset
6. `ota_watch.py` PC: vigila `www/` → zip → SHA-256 → sirve :8788 → POST /ota
7. Instalar la APK **una última vez** y listo: cada cambio en `www/` llega solo
