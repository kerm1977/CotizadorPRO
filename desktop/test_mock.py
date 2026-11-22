#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Servidor mock de la API TribalFtp para probar tribal_pc.py sin teléfono."""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote

STORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_mock_store")
os.makedirs(STORE, exist_ok=True)

ITEMS = [
    {"i": "m1", "n": "Cancion tribal.mp3", "s": 3145728, "k": "audio", "p": "tribu_media/m1.mp3"},
    {"i": "m2", "n": "Video del campamento.mp4", "s": 52428800, "k": "video", "p": "tribu_media/m2.mp4"},
    {"i": "m3", "n": "Foto portada.png", "s": 204800, "k": "image", "p": "tribu_media/m3.png"},
    {"i": "m4", "n": "Libro de prueba.epub", "s": 1048576, "k": "doc", "p": "tribu_media/m4.epub"},
    {"i": "m5", "n": "Semilla incluida.mp3", "s": 409600, "k": "audio", "p": "builtin/semilla.mp3", "ro": 1},
]
for it in ITEMS:                      # archivos falsos en el store
    fp = os.path.join(STORE, it["i"])
    if not os.path.exists(fp):
        with open(fp, "wb") as f:
            f.write(b"TRIBAL-MOCK:" + it["n"].encode("utf-8") + b":" + bytes(it["s"] if it["s"] < 10**6 else 10**5))


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, data, mime="application/json", code=200, name=None):
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        if name:
            self.send_header("Content-Disposition", 'attachment; filename="%s"' % name)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path == "/api/list":
            self._send(json.dumps({"app": "tribals", "v": 1, "id": "tribal-mock001",
                                   "name": "Mock tribu", "items": ITEMS}).encode())
        elif u.path == "/dl":
            p = unquote(q.get("p", ""))
            it = next((x for x in ITEMS if x["p"] == p), None)
            if it:
                fp = os.path.join(STORE, it["i"])
                self._send(open(fp, "rb").read(), "application/octet-stream", name=it["n"])
            else:
                self._send(b"404", "text/plain", 404)
        elif u.path == "/del":
            ITEMS[:] = [x for x in ITEMS if x["i"] != q.get("i")]
            self._send(b'{"ok":true}')
        elif u.path == "/ren":
            it = next((x for x in ITEMS if x["i"] == q.get("i")), None)
            if it:
                it["n"] = unquote(q.get("n", it["n"]))
            self._send(b'{"ok":true}')
        else:
            self._send(b"no encontrado", "text/plain", 404)

    def do_POST(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path == "/up":
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n)
            name = unquote(q.get("n", "archivo"))
            ITEMS.append({"i": "up%d" % len(ITEMS), "n": name, "s": len(body),
                          "k": "other", "p": "tribu_inbox/" + name})
            self._send(('{"ok":true,"name":"%s"}' % name).encode())
        else:
            self._send(b"404", "text/plain", 404)


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", 8765), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    # --- probar el cliente ---
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tribal_pc as pc

    print("1) discover() debe hallar 127.0.0.1…")
    found = pc.discover(extra_hosts=["127.0.0.1"])
    assert found, "no se encontró el mock"
    base = found[0][0]
    print("   OK:", found)

    print("2) catálogo…")
    data = pc.probe(base)
    assert data["name"] == "Mock tribu" and len(data["items"]) == 5
    print("   OK: %d items" % len(data["items"]))

    print("3) descarga…")
    class Fake:  # fake app para usar _dl_one sin Tk
        base_url = base
        @staticmethod
        def after(ms, fn=None):
            if fn:
                fn()
        @staticmethod
        def set_prog(t, p=None):
            pass
    dest = os.path.join(STORE, "dl")
    os.makedirs(dest, exist_ok=True)
    path = pc.TribalPC._dl_one(Fake, ITEMS[0], dest)
    assert os.path.getsize(path) > 0
    print("   OK: %s (%d bytes)" % (path, os.path.getsize(path)))

    print("4) subida…")
    tmp = os.path.join(STORE, "subida.txt")
    with open(tmp, "wb") as f:
        f.write(b"hola tribu" * 100)
    body = open(tmp, "rb").read()
    req = pc.urllib.request.Request(
        base + "/up?n=subida.txt", data=body, method="POST",
        headers={"Content-Length": str(len(body))})
    pc.urllib.request.urlopen(req, timeout=10).read()
    assert any(x["n"] == "subida.txt" for x in pc.probe(base)["items"])
    print("   OK: subida indexada")

    print("5) ren + del…")
    pc.http_get(base + "/ren?i=m4&n=Renombrado.epub").read()
    assert pc.probe(base)["items"][3]["n"] == "Renombrado.epub"
    pc.http_get(base + "/del?i=m5").read()
    assert len(pc.probe(base)["items"]) == 5  # m5 fuera, +subida = 5
    print("   OK")

    srv.shutdown()
    print("\n[OK] TODAS LAS PRUEBAS PASARON")


if __name__ == "__main__":
    main()
