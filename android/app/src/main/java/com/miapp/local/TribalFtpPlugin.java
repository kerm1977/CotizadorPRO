package com.miapp.local;

import android.content.Context;
import android.net.wifi.WifiManager;
import android.os.PowerManager;
import com.getcapacitor.*;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;

/** TribalFtp — mini servidor HTTP LAN (estilo FTP web tribal).
 *  GET / → interfaz tribal (assets public/ftp/) · /ftp/x → su css/js
 *  GET /api/list → catálogo JSON (setCatalog) · /dl?p=&n= → descarga
 *  POST /up?n= → sube a files/tribu_inbox → evento tribalInbox
 *  GET /del?i= → avisa al JS para eliminar (3 pasos desde la web) */
@CapacitorPlugin(name = "TribalFtp")
public class TribalFtpPlugin extends Plugin {
    private static final int PORT = 8890;
    private ServerSocket srv;
    private ExecutorService pool;
    private volatile String catalog = "[]";
    private PowerManager.WakeLock wl;
    private WifiManager.WifiLock wfLock;

    // mantiene la radio y el proceso despiertos mientras el server corre:
    // sin esto el teléfono dormido deja de contestar aunque diga «activo»
    private void acquireLocks() {
        try {
            PowerManager pm = (PowerManager)
                getContext().getSystemService(Context.POWER_SERVICE);
            if (pm != null && (wl == null || !wl.isHeld())) {
                wl = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "tribals:ftp");
                wl.setReferenceCounted(false);
                wl.acquire();
            }
            WifiManager wm = (WifiManager) getContext().getApplicationContext()
                .getSystemService(Context.WIFI_SERVICE);
            if (wm != null && (wfLock == null || !wfLock.isHeld())) {
                wfLock = wm.createWifiLock(
                    WifiManager.WIFI_MODE_FULL_LOW_LATENCY, "tribals:ftp");
                wfLock.setReferenceCounted(false);
                wfLock.acquire();
            }
        } catch (Exception ignored) {}
    }
    private void releaseLocks() {
        try { if (wl != null && wl.isHeld()) wl.release(); } catch (Exception ignored) {}
        try { if (wfLock != null && wfLock.isHeld()) wfLock.release(); } catch (Exception ignored) {}
    }

    // arranque automático: el teléfono siempre es alcanzable en :8890 para
    // el OTA push y la app de PC, sin que la JS tenga que pedir 'start'
    @Override
    public void load() {
        try {
            if (srv == null || srv.isClosed()) {
                srv = new ServerSocket();
                srv.setReuseAddress(true);
                srv.bind(new InetSocketAddress(PORT));
                pool = Executors.newCachedThreadPool();
                pool.execute(this::acceptLoop);
            }
            acquireLocks();
        } catch (Exception ignored) {}
    }

    @PluginMethod public void start(PluginCall c) {
        try {
            if (srv == null || srv.isClosed()) {
                srv = new ServerSocket();
                srv.setReuseAddress(true);
                srv.bind(new InetSocketAddress(PORT));
                pool = Executors.newCachedThreadPool();
                pool.execute(this::acceptLoop);
            }
            acquireLocks();
            c.resolve(info());
        } catch (Exception e) { c.reject("ftp start: " + e.getMessage()); }
    }

    @PluginMethod public void stop(PluginCall c) {
        try { if (srv != null) srv.close(); } catch (Exception ignored) {}
        srv = null;
        if (pool != null) pool.shutdownNow();
        releaseLocks();
        c.resolve(info());
    }

    @PluginMethod public void status(PluginCall c) { c.resolve(info()); }

    @PluginMethod public void setCatalog(PluginCall c) {
        String j = c.getString("json");
        if (j != null) catalog = j;
        c.resolve();
    }

    // 0 = hotspot del teléfono · 1 = wifi/eth/usb/bt-pan · 2 = otra LAN ·
    // -1 = inútil para compartir (datos móviles, VPNs, túneles)
    private int rankIf(NetworkInterface ni, InetAddress a) {
        try { if (!ni.isUp() || ni.isLoopback()) return -1; } catch (Exception e) { return -1; }
        if (a.isLoopbackAddress() || !(a instanceof Inet4Address)) return -1;
        String n = ni.getName().toLowerCase();
        if (n.matches("rmnet.*|ccmni.*|pdp.*|ppp.*|tun.*|ipsec.*|ip_vti.*|dummy.*"))
            return -1;
        if (n.matches(".*ap.*|swlan.*|wlan1.*")) return 0;
        if (n.matches("wlan.*|eth.*|rndis.*|usb.*|bt-pan.*|p2p.*")) return 1;
        return a.isSiteLocalAddress() ? 2 : 3;
    }

    private JSObject info() {
        JSObject r = new JSObject();
        r.put("running", srv != null && !srv.isClosed());
        // solo IPs alcanzables desde la LAN, ordenadas: hotspot → wifi/eth → resto
        List<String[]> cands = new ArrayList<>();
        try {
            for (NetworkInterface ni : Collections.list(NetworkInterface.getNetworkInterfaces())) {
                for (InetAddress a : Collections.list(ni.getInetAddresses())) {
                    int rk = rankIf(ni, a);
                    if (rk < 0) continue;
                    cands.add(new String[]{
                        "http://" + a.getHostAddress() + ":" + PORT,
                        String.valueOf(rk)});
                }
            }
        } catch (Exception ignored) {}
        Collections.sort(cands, new Comparator<String[]>() {
            public int compare(String[] x, String[] y) {
                return Integer.compare(Integer.parseInt(x[1]), Integer.parseInt(y[1]));
            }
        });
        JSArray urls = new JSArray();
        String first = "http://127.0.0.1:" + PORT;
        for (String[] c2 : cands) {
            if (first.contains("127.0.0.1")) first = c2[0];
            JSObject j = new JSObject(); j.put("u", c2[0]);
            j.put("hot", Integer.parseInt(c2[1]) == 0); urls.put(j);
        }
        String host = "";
        try {   // solo el modelo (SM-A037M → sm-a037m) — nunca el nombre personal
            host = android.os.Build.MODEL;
            host = host.replaceAll("[^A-Za-z0-9-]", "-").replaceAll("-+", "-")
                       .replaceAll("^-|-$", "").toLowerCase();
        } catch (Exception ignored) {}
        // identificador único por teléfono: modelo + uuid corto persistente
        String did = getContext().getSharedPreferences("tribu_dev", 0)
            .getString("id", null);
        if (did == null) {
            did = java.util.UUID.randomUUID().toString().substring(0, 5);
            getContext().getSharedPreferences("tribu_dev", 0)
                .edit().putString("id", did).apply();
        }
        r.put("url", first); r.put("urls", urls);
        r.put("host", host.isEmpty() ? null : "http://" + host + ":" + PORT);
        r.put("model", host);                          // sm-a376b
        r.put("id", did);                              // a4f2c (persistente)
        r.put("devid", (host.isEmpty() ? "tribu" : host) + "-" + did);
        r.put("devname", "tribals-" + did);            // tribals-a4f2c
        return r;
    }

    private void acceptLoop() {
        try {
            while (srv != null && !srv.isClosed()) {
                final Socket s = srv.accept();
                pool.execute(new Runnable() { public void run() { handle(s); } });
            }
        } catch (Exception ignored) {} }

    private void handle(Socket s) {
        try {
            s.setSoTimeout(30000);
            InputStream in = s.getInputStream();
            OutputStream out = s.getOutputStream();
            ByteArrayOutputStream headBuf = new ByteArrayOutputStream();
            int b, nl = 0;                                    // cabeceras hasta línea vacía
            while ((b = in.read()) != -1) {
                headBuf.write(b);
                if (b == '\n') { if (++nl >= 2) break; }
                else if (b != '\r') nl = 0;
            }
            String[] hs = headBuf.toString("UTF-8").split("\n");
            if (hs.length == 0) { s.close(); return; }
            String[] req = hs[0].trim().split(" ");
            if (req.length < 2) { s.close(); return; }
            int q = req[1].indexOf('?');
            String path = URLDecoder.decode(q < 0 ? req[1] : req[1].substring(0, q), "UTF-8");
            Map<String, String> qs = new HashMap<>();
            if (q >= 0) for (String kv : req[1].substring(q + 1).split("&")) {
                int e = kv.indexOf('=');
                if (e > 0) qs.put(kv.substring(0, e), URLDecoder.decode(kv.substring(e + 1), "UTF-8"));
            }
            long bodyLen = 0;
            Map<String, String> hdr = new HashMap<>();
            for (int i = 1; i < hs.length; i++) {
                String h = hs[i].trim().toLowerCase();
                int ci = h.indexOf(':'); if (ci > 0) hdr.put(h.substring(0, ci), h.substring(ci + 1).trim());
                if (h.startsWith("content-length:")) bodyLen = Long.parseLong(h.substring(15).trim());
            }
            if (path.equals("/")) sendAsset(out, "public/ftp/index.html", "text/html; charset=utf-8");
            else if (path.startsWith("/ftp/")) sendAsset(out, "public" + path, mimeOf(path));
            else if (path.equals("/api/list")) sendBytes(out, catalog.getBytes("UTF-8"), "application/json; charset=utf-8", 200);
            else if (path.equals("/call")) callEvent(out, s, qs);
            else if (path.equals("/dl")) sendFile(out, qs.get("p"), qs.get("n"));
            else if (path.equals("/up")) recvUpload(in, out, qs.get("n"), bodyLen);
            else if (path.equals("/ota")) recvOta(in, out, bodyLen);
            else if (path.equals("/ping")) fireJs(out, "tribalPing", "1", null);
            else if (path.equals("/id")) sendBytes(out,
                info().toString().getBytes("UTF-8"), "application/json", 200);
            else if (path.equals("/del")) fireJs(out, "ftpDel", qs.get("i"), null);
            else if (path.equals("/ren")) fireJs(out, "ftpRen", qs.get("i"), qs.get("n"));
            else if (path.equals("/s")) streamMedia(out, qs, hdr);
            else sendBytes(out, "no encontrado".getBytes("UTF-8"), "text/plain; charset=utf-8", 404);
            s.close();
        } catch (Exception e) { try { s.close(); } catch (Exception ignored) {} }
    }

    // POST /ota — el PC (scripts/ota_watch.py) manda {"url":"http://pc:8891/
    // bundle.zip"}; solo avisa a JS, que descarga y aplica via el plugin
    // @capgo/capacitor-updater (motor probado — nada de path a mano)
    private void recvOta(InputStream in, OutputStream out, long len)
            throws Exception {
        byte[] body = new byte[(int) len]; int off = 0;
        while (off < body.length) {
            int n = in.read(body, off, body.length - off);
            if (n < 0) break; off += n;
        }
        org.json.JSONObject jo = new org.json.JSONObject(
            new String(body, "UTF-8"));
        JSObject j = new JSObject();
        j.put("url", jo.optString("url", ""));
        j.put("checksum", jo.optString("checksum", ""));  // Capgo lo exige
        j.put("version", jo.optString("version", "ota"));
        notifyListeners("tribalOta", j);
        sendBytes(out, "{\"ok\":true}".getBytes("UTF-8"),
            "application/json", 200);
    }

    private String mimeOf(String p) {
        if (p == null) return "application/octet-stream";
        if (p.endsWith(".css")) return "text/css; charset=utf-8";
        if (p.endsWith(".js")) return "application/javascript; charset=utf-8";
        String l = p.toLowerCase();
        if (l.endsWith(".mp4") || l.endsWith(".m4v")) return "video/mp4";
        if (l.endsWith(".webm")) return "video/webm";
        if (l.endsWith(".mkv") || l.endsWith(".webm")) return "video/x-matroska";
        if (l.endsWith(".mp3")) return "audio/mpeg";
        if (l.endsWith(".m4a") || l.endsWith(".aac")) return "audio/mp4";
        if (l.endsWith(".ogg") || l.endsWith(".opus")) return "audio/ogg";
        if (l.endsWith(".wav")) return "audio/wav";
        if (l.endsWith(".flac")) return "audio/flac";
        if (l.endsWith(".jpg") || l.endsWith(".jpeg")) return "image/jpeg";
        if (l.endsWith(".png")) return "image/png";
        if (l.endsWith(".webp")) return "image/webp";
        return "application/octet-stream";
    }

    // GET /s?p=tribu_media/x.mp4 | /s?p=builtin/x | /s?a=/absoluto → stream
    // para el Chromecast: mime correcto, sin Content-Disposition y con Range
    // (obligatorio — el receptor de Google Cast hace peticiones 206 para seek)
    private void streamMedia(OutputStream out, Map<String, String> qs, Map<String, String> hdr) {
        InputStream in = null;
        try {
            String p = qs.get("p"), a = qs.get("a"), fpath;
            long len;
            if (p != null && !p.contains("..")) {
                fpath = p;
                if (p.startsWith("builtin/")) { in = getContext().getAssets().open("public/" + p); len = in.available(); }
                else if (p.startsWith("tribu_media/") || p.startsWith("tribu_inbox/")) {
                    File f = new File(getContext().getFilesDir(), p);
                    if (!f.isFile()) throw new FileNotFoundException();
                    len = f.length(); in = new FileInputStream(f);
                } else throw new FileNotFoundException();
            } else if (a != null && !a.contains("..")) {
                File f = new File(a); if (!f.isFile()) throw new FileNotFoundException();
                fpath = a; len = f.length(); in = new FileInputStream(f);
            } else throw new FileNotFoundException();
            String mime = mimeOf(fpath), range = hdr.get("range");
            if (range != null && range.startsWith("bytes=")) {
                String[] rb = range.substring(6).split("-");
                long start = rb[0].isEmpty() ? 0 : Long.parseLong(rb[0]);
                long end = rb.length > 1 && !rb[1].isEmpty() ? Long.parseLong(rb[1]) : len - 1;
                if (end > len - 1) end = len - 1;
                long skipped = 0;
                while (skipped < start) skipped += in.skip(start - skipped);
                String h = "HTTP/1.1 206 Partial Content\r\nContent-Type: " + mime +
                    "\r\nContent-Length: " + (end - start + 1) +
                    "\r\nContent-Range: bytes " + start + "-" + end + "/" + len +
                    "\r\nAccept-Ranges: bytes\r\nAccess-Control-Allow-Origin: *" +
                    "\r\nConnection: close\r\n\r\n";
                out.write(h.getBytes("UTF-8"));
                pump(in, out, end - start + 1);
            } else {
                String h = "HTTP/1.1 200 OK\r\nContent-Type: " + mime +
                    "\r\nContent-Length: " + len + "\r\nAccept-Ranges: bytes" +
                    "\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n";
                out.write(h.getBytes("UTF-8"));
                pump(in, out, -1);
            }
            in.close(); in = null;
        } catch (Exception e) {
            try { if (in != null) in.close(); } catch (Exception ignored) {}
            fail(out, 404);
        }
    }

    private void sendHead(OutputStream out, int code, String mime, long len, String name) throws IOException {
        String h = "HTTP/1.1 " + code + (code == 200 ? " OK" : " ERR") +
            "\r\nContent-Type: " + mime +
            (len >= 0 ? "\r\nContent-Length: " + len : "") +
            (name != null ? "\r\nContent-Disposition: attachment; filename=\"" + name.replace("\"", "_") + "\"" : "") +
            "\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n";
        out.write(h.getBytes("UTF-8"));
    }

    private void sendBytes(OutputStream out, byte[] d, String mime, int code) throws IOException {
        sendHead(out, code, mime, d.length, null); out.write(d); out.flush();
    }

    private void sendAsset(OutputStream out, String ap, String mime) {
        try {
            InputStream in = getContext().getAssets().open(ap);
            sendHead(out, 200, mime, in.available(), null);
            pump(in, out, -1); in.close();
        } catch (Exception e) { fail(out, 404); }
    }

    // p: 'builtin/…' = asset | 'tribu_media/…' / 'tribu_inbox/…' = files dir
    private void sendFile(OutputStream out, String p, String name) {
        try {
            if (p == null || p.contains("..")) throw new FileNotFoundException();
            InputStream in; long len;
            if (p.startsWith("builtin/")) { in = getContext().getAssets().open("public/" + p); len = in.available(); }
            else if (p.startsWith("tribu_media/") || p.startsWith("tribu_inbox/")) {
                File f = new File(getContext().getFilesDir(), p);
                if (!f.isFile()) throw new FileNotFoundException();
                len = f.length(); in = new FileInputStream(f);
            } else throw new FileNotFoundException();
            sendHead(out, 200, "application/octet-stream", len, name != null ? name : new File(p).getName());
            pump(in, out, -1); in.close();
        } catch (Exception e) { fail(out, 404); }
    }

    private void recvUpload(InputStream in, OutputStream out, String name, long len) {
        File target = null; FileOutputStream fos = null;
        try {
            String safe = (name == null || name.isEmpty() ? "archivo" : name).replaceAll("[^\\w.\\-() áéíóúñÁÉÍÓÚÑ]", "_");
            File dir = new File(getContext().getFilesDir(), "tribu_inbox"); dir.mkdirs();
            target = new File(dir, safe);
            fos = new FileOutputStream(target);
            pump(in, fos, len); fos.close(); fos = null;
            getBridge().triggerWindowJSEvent("tribalInbox");   // inbox.js lo indexa en la tribu
            sendBytes(out, ("{\"ok\":true,\"name\":\"" + safe + "\"}").getBytes("UTF-8"), "application/json", 200);
        } catch (Exception e) {
            // subida cortada (teléfono dormido, red caída): el parcial NO se
            // queda en la bandeja — nunca se importa un archivo truncado
            if (fos != null) { try { fos.close(); } catch (Exception ignored) {} }
            if (target != null) { try { target.delete(); } catch (Exception ignored) {} }
            fail(out, 500);
        }
    }

    // la app (JS) borra/renombra índice+archivo vía MediaStore — aquí solo avisamos
    private void fireJs(OutputStream out, String ev, String id, String name) {
        JSObject j = new JSObject(); j.put("id", id == null ? "" : id);
        if (name != null) j.put("name", name);
        notifyListeners(ev, j);
        try { sendBytes(out, "{\"ok\":true}".getBytes("UTF-8"), "application/json", 200); } catch (Exception ignored) {}
    }

    // ping tribal: /call?n=&i= → solicitud de vínculo · /call?acc=1|0&n= → respuesta.
    // En ambos casos se avisa a JS (tribalCall) con la IP remota real del socket
    // y se responde 200 = la tribu está viva y la llamada fue entregada.
    private void callEvent(OutputStream out, Socket s, Map<String, String> qs) {
        JSObject j = new JSObject();
        j.put("ip", s.getInetAddress() == null ? "" : s.getInetAddress().getHostAddress());
        j.put("n", qs.get("n")); j.put("i", qs.get("i"));
        if (qs.get("acc") != null) j.put("acc", qs.get("acc"));
        getBridge().triggerWindowJSEvent("tribalCall", j.toString());
        try { sendBytes(out, "{\"ok\":true}".getBytes("UTF-8"), "application/json", 200); }
        catch (Exception ignored) {}
    }

    private void fail(OutputStream out, int code) {
        try { sendBytes(out, ("error " + code).getBytes("UTF-8"), "text/plain", code); } catch (Exception ignored) {}
    }

    private void pump(InputStream in, OutputStream out, long max) throws IOException {
        byte[] buf = new byte[65536]; long left = max; int r;
        while ((r = in.read(buf, 0, max < 0 ? buf.length : (int) Math.min(buf.length, left))) != -1) {
            out.write(buf, 0, r);
            if (max >= 0 && (left -= r) <= 0) break;
        }
        out.flush();
    }
}
