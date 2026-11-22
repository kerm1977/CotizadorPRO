#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
#  TRIBALs PC — cliente de escritorio del servidor de archivos
#  del teléfono (TribalFtpPlugin, HTTP :8765).
#
#  Funciona por CUALQUIER transporte que dé IP al teléfono:
#    · WiFi    — ambos en la misma red / hotspot del teléfono
#    · USB     — cable + "Compartir conexión por USB" (tethering)
#    · BT PAN  — Bluetooth emparejado + "Unirse a red de área
#                personal" en Windows (punto de acceso)
#
#  · Auto-descubrimiento: escanea las subredes locales + IPs de
#    tethering/PAN; conexión silenciosa configurable en ⚙.
#  · Consola interna con todos los eventos (copiar/pegar).
#  · ✖ Cancela cualquier descarga/subida en curso.
#  · Clic derecho en un archivo: descargar, renombrar, info,
#    carpeta de destino, eliminar (3 pasos).
#
#  Solo stdlib: python tribal_pc.py — sin pip.
# ============================================================

import json
import math
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

PORT = 8765
APP_TITLE = "TRIBALs · Tribu de archivos"
# el .exe congelado vive en una carpeta temporal — la config va junto al .exe
_BASE = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) \
    else os.path.dirname(os.path.abspath(__file__))
CFG_FILE = os.path.join(_BASE, "tribal_pc.json")

# Paleta tribal — la misma de la app móvil
BG      = "#17100b"   # fondo profundo
BG2     = "#201510"   # panel
BG3     = "#2e1e14"   # tarjeta / hover
BORDER  = "#4a3226"   # borde suave
FG      = "#f3e6cf"   # crema
MUTED   = "#b09472"   # texto suave
ACCENT  = "#e2602e"   # terracota
ACCENT2 = "#c94f22"   # terracota oscuro (pressed)
GOLD    = "#f0b429"   # dorado
DANGER  = "#c0392b"
DANGER2 = "#a02c20"
OKC     = "#7fbf6a"
NETC    = "#7db4ff"

KNOWN_IPS = [   # dónde suele aparecer el teléfono sin escanear la /24
    "192.168.42.129", "192.168.43.1", "192.168.44.1", "192.168.45.1",
    "192.168.137.1", "172.20.10.1", "127.0.0.1",
]

KIND_META = [
    ("audio", "♪", "♪  Música"),
    ("video", "▶", "▶  Videos"),
    ("image", "❀", "❀  Imágenes"),
    ("doc",   "✎", "✎  Documentos"),
    ("other", "◈", "◈  Otros"),
]
KIND_ICON = {k: i for k, i, _ in KIND_META}


class Cancelled(Exception):
    pass


def human_size(b):
    try:
        b = float(b)
    except (TypeError, ValueError):
        return "—"
    for u in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024 or u == "TB":
            return ("%d %s" if u == "B" else "%.1f %s") % (b, u)
        b /= 1024.0


def http_get(url, timeout=4):
    req = urllib.request.Request(url, headers={"User-Agent": "TRIBALs-PC/1.0"})
    return urllib.request.urlopen(req, timeout=timeout)


def is_tribal(data):
    return isinstance(data, dict) and (
        data.get("app") == "tribals" or isinstance(data.get("items"), list))


def probe(base, timeout=3):
    """Devuelve el catálogo si base (http://ip:8765) es un servidor tribal."""
    try:
        r = http_get(base + "/api/list", timeout=timeout)
        data = json.loads(r.read().decode("utf-8", "replace"))
        if is_tribal(data):
            return data
    except Exception:
        pass
    return None


def local_subnets():
    ips = set()
    try:
        for inf in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = inf[4][0]
            if not ip.startswith("127."):
                ips.add(ip)
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        if not ip.startswith("127."):
            ips.add(ip)
    except Exception:
        pass
    return {".".join(ip.split(".")[:3]) for ip in ips}


def discover(progress=None, extra_hosts=()):
    """Escanea subredes locales + IPs conocidas → [(base_url, data)]."""
    targets = set(extra_hosts)
    for net in local_subnets():
        targets.update("%s.%d" % (net, h) for h in range(1, 255))
    targets.update(KNOWN_IPS)
    found, done, total = [], 0, len(targets)

    def try_host(ip):
        # timeout corto: en LAN la respuesta es de milisegundos
        data = probe("http://%s:%d" % (ip, PORT), timeout=0.9)
        return ("http://%s:%d" % (ip, PORT), data) if data else None

    with ThreadPoolExecutor(max_workers=160) as ex:
        futs = {ex.submit(try_host, ip): ip for ip in targets}
        for f in as_completed(futs):
            done += 1
            if progress:
                progress(done, total)
            r = f.result()
            if r:
                found.append(r)
    return found


def load_cfg():
    try:
        with open(CFG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cfg(cfg):
    try:
        with open(CFG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ============================================================
#  Widgets propios — look tribal fino
# ============================================================
def _rrect(x1, y1, x2, y2, r, steps=6):
    """Puntos de un rectángulo redondeado para create_polygon."""
    pts = []
    corners = [(x2 - r, y1 + r, -90), (x2 - r, y2 - r, 0),
               (x1 + r, y2 - r, 90), (x1 + r, y1 + r, 180)]
    for cx, cy, a0 in corners:
        for i in range(steps + 1):
            a = math.radians(a0 + i * 90.0 / steps)
            pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
    return pts


class RButton(tk.Canvas):
    """Botón de esquinas redondeadas dibujado en canvas — estilo tribal."""
    def __init__(self, parent, text, cmd, kind="ghost", pad=(12, 5), fs=9, bold=False):
        self.cmd, self.kind = cmd, kind
        self._text, self._fs, self._bold = text, fs, bold
        colors = {
            "ghost":  (BG3,      FG,     BORDER,  "#3d2919"),
            "accent": (ACCENT,   "white", ACCENT2, GOLD),
            "danger": (DANGER,   "white", DANGER2, "#ff8a70"),
            "gold":   (GOLD,     "#241305", "#c08d16", "#ffe08a"),
        }
        self.bg, self.fg, self.press, self.hover = colors[kind]
        wfont = ("Segoe UI", fs, "bold" if bold else "normal")
        probe_lbl = tk.Label(parent, text=text, font=wfont)
        w = probe_lbl.winfo_reqwidth() + pad[0] * 2
        h = probe_lbl.winfo_reqheight() + pad[1] * 2
        probe_lbl.destroy()
        tk.Canvas.__init__(self, parent, width=w, height=h, bg=parent["bg"],
                           highlightthickness=0, cursor="hand2", bd=0)
        self.cw, self.ch = w, h   # NUNCA self._w: es el nombre Tcl del widget
        self._draw(self.bg)
        self.bind("<Enter>", lambda e: self._draw(self.hover))
        self.bind("<Leave>", lambda e: self._draw(self.bg))
        self.bind("<Button-1>", lambda e: self._draw(self.press))
        self.bind("<ButtonRelease-1>", self._fire)

    def _draw(self, color):
        self.delete("all")
        r = min(9, (self.ch - 2) // 2)
        self.create_polygon(_rrect(1, 1, self.cw - 1, self.ch - 1, r),
                            smooth=True, fill=color, outline="")
        self.create_text(self.cw / 2, self.ch / 2, text=self._text,
                         fill=self.fg, font=("Segoe UI", self._fs,
                                             "bold" if self._bold else "normal"))

    def _fire(self, e):
        self._draw(self.hover)
        if 0 <= e.x <= self.cw and 0 <= e.y <= self.ch and self.cmd:
            self.cmd()


# ---------- confirmación en 3 pasos (como la app) ----------
class Confirm3(tk.Toplevel):
    TEXTS = ["¿Eliminarlo?", "¿De verdad?", "Última llamada"]

    def __init__(self, parent, name, count=1):
        super().__init__(parent)
        self.result = False
        self.step = 0
        self.title("Eliminar")
        self.configure(bg=BG2)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        what = name if count == 1 else "%d archivos" % count
        tk.Label(self, text="◈", font=("Segoe UI", 22), fg=GOLD, bg=BG2).pack(pady=(14, 2))
        self.lbl = tk.Label(self, text="%s\n«%s»" % (self.TEXTS[0], what),
                            fg=FG, bg=BG2, font=("Segoe UI", 10), justify="center",
                            wraplength=330)
        self.lbl.pack(padx=24, pady=6)
        row = tk.Frame(self, bg=BG2)
        row.pack(pady=(8, 16))
        RButton(row, "Cancelar", self._cancel).pack(side="left", padx=6)
        self.yes = RButton(row, "Continuar (1/3)", self._next, kind="danger")
        self.yes.pack(side="left", padx=6)
        self.bind("<Escape>", lambda e: self._cancel())
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.wait_window(self)

    def _next(self):
        self.step += 1
        if self.step >= 3:
            self.result = True
            self.destroy()
            return
        self.lbl.config(text=self.TEXTS[self.step] + "\nLa eliminación es en el teléfono.")
        self.yes._text = "Continuar (%d/3)" % (self.step + 1)
        self.yes._draw(DANGER)

    def _cancel(self):
        self.result = False
        self.destroy()


# ============================================================
#  Aplicación
# ============================================================
class TribalPC(tk.Tk):
    def __init__(self):
        super().__init__()
        self.cfg = load_cfg()
        self.title(APP_TITLE)
        self.configure(bg=BG)
        self.geometry("920x660")
        self.minsize(700, 480)
        self.base_url = self.cfg.get("last_url") or ""
        self.server_name = ""
        self.dev_id = ""
        self.items = []
        self.row_item = {}
        self._connected = False
        self._scanning = False
        self._xfer_cancel = threading.Event()
        self._xfer_running = False
        self._console_on = True
        self._style()
        self._build()
        self.log("inf", "═══ TRIBALs PC iniciado — escucho el puerto %d en cualquier red", PORT)
        self.after(300, self._auto_connect)
        self.after(30000, self._watchdog)

    # ---------- estilo ----------
    def _style(self):
        st = ttk.Style(self)
        try:
            st.theme_use("clam")
        except Exception:
            pass
        st.configure("Treeview", background=BG2, fieldbackground=BG2,
                     foreground=FG, rowheight=32, borderwidth=0,
                     font=("Segoe UI", 9))
        st.configure("Treeview.Heading", background=BG3, foreground=GOLD,
                     relief="flat", font=("Segoe UI", 9, "bold"), padding=(6, 4))
        st.map("Treeview", background=[("selected", "#503019")],
               foreground=[("selected", "#ffe8c8")])
        st.configure("TCombobox", fieldbackground=BG3, background=BG3,
                     foreground=FG, arrowcolor=GOLD, padding=4)
        st.configure("TProgressbar", background=GOLD, troughcolor=BG3,
                     borderwidth=0, thickness=7)
        st.configure("Vertical.TScrollbar", background=BG3, troughcolor=BG2,
                     borderwidth=0, arrowcolor=FG)

    # ---------- consola interna ----------
    def log(self, lv, fmt, *args):
        msg = fmt % args if args else fmt
        ts = time.strftime("%H:%M:%S")
        line = "%s  %-4s  %s" % (ts, lv.upper(), msg)
        if not hasattr(self, "txt_log"):
            return
        self.txt_log.config(state="normal")
        self.txt_log.insert("end", line + "\n", lv)
        self.txt_log.config(state="disabled")
        if not self._console_paused():
            self.txt_log.see("end")
        self.lbl_log_n.config(text="%s líneas" %
                              int(float(self.txt_log.index("end-1c").split(".")[0])))

    def _console_paused(self):
        return getattr(self, "_log_hold", False)

    def toggle_console(self):
        self._console_on = not self._console_on
        if self._console_on:
            self.logf.pack(fill="x", padx=12, pady=(0, 8))
            self.btn_console._text = "⌨ Consola ▾"
        else:
            self.logf.pack_forget()
            self.btn_console._text = "⌨ Consola ▸"
        self.btn_console._draw(self.btn_console.bg)

    def copy_log(self):
        txt = self.txt_log.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(txt)
        self.set_status("⧉ Consola copiada — pégala donde quieras", OKC)

    def clear_log(self):
        self.txt_log.config(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.config(state="disabled")
        self.log("inf", "consola limpiada")

    # ---------- UI ----------
    def _build(self):
        # cabecera
        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=14, pady=(12, 6))
        tk.Label(head, text="✹", font=("Segoe UI", 26), fg=GOLD, bg=BG).pack(side="left")
        t = tk.Frame(head, bg=BG)
        t.pack(side="left", padx=10)
        tk.Label(t, text="TRIBALs", font=("Segoe UI", 16, "bold"),
                 fg=FG, bg=BG).pack(anchor="w")
        self.lbl_srv = tk.Label(t, text="Tribu de archivos · PC",
                                font=("Segoe UI", 9), fg=MUTED, bg=BG)
        self.lbl_srv.pack(anchor="w")
        self.lbl_state = tk.Label(head, text="○ sin conexión",
                                  font=("Segoe UI", 9), fg=MUTED, bg=BG)
        self.lbl_state.pack(side="right")
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x", padx=14)

        # fila de conexión
        conn = tk.Frame(self, bg=BG)
        conn.pack(fill="x", padx=14, pady=(10, 6))
        tk.Label(conn, text="Servidor", fg=MUTED, bg=BG,
                 font=("Segoe UI", 9)).pack(side="left")
        self.cmb_hosts = ttk.Combobox(conn, width=30)
        self.cmb_hosts.pack(side="left", padx=8)
        if self.base_url:
            self.cmb_hosts.set(self.base_url)
        self.cmb_hosts.bind("<Return>", lambda e: self.connect_manual())
        RButton(conn, "🔍 Buscar tribu", self.discover).pack(side="left", padx=3)
        RButton(conn, "⚡ Conectar", self.connect_manual, kind="accent").pack(side="left", padx=3)
        self.btn_console = RButton(conn, "⌨ Consola ▾", self.toggle_console)
        self.btn_console.pack(side="left", padx=3)
        RButton(conn, "⚙", self.show_settings).pack(side="left", padx=3)
        RButton(conn, "?", self.show_help).pack(side="left", padx=3)
        self.lbl_via = tk.Label(conn, text="", fg=MUTED, bg=BG, font=("Segoe UI", 8))
        self.lbl_via.pack(side="right")

        # fila de acciones
        acts = tk.Frame(self, bg=BG)
        acts.pack(fill="x", padx=14, pady=(0, 8))
        RButton(acts, "⬆ Subir archivos", self.upload_files, kind="accent").pack(side="left", padx=(0, 4))
        RButton(acts, "📁 Subir carpeta", self.upload_folder).pack(side="left", padx=4)
        RButton(acts, "⬇ Descargar", self.download_sel).pack(side="left", padx=4)
        RButton(acts, "⬇⬇ Todo", self.download_all).pack(side="left", padx=4)
        RButton(acts, "✎ Renombrar", self.rename_sel).pack(side="left", padx=4)
        RButton(acts, "🗑 Eliminar", self.delete_sel, kind="danger").pack(side="left", padx=4)
        RButton(acts, "⟳", self.refresh).pack(side="right", padx=4)
        RButton(acts, "📂 Destino…", self.pick_dest).pack(side="right", padx=4)

        # lista
        wrap = tk.Frame(self, bg=BG)
        wrap.pack(fill="both", expand=True, padx=14, pady=(0, 6))
        self.tree = ttk.Treeview(wrap, columns=("size",), selectmode="extended")
        self.tree.heading("#0", text="Nombre")
        self.tree.heading("size", text="Tamaño")
        self.tree.column("#0", anchor="w")
        self.tree.column("size", width=95, anchor="e")
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.tag_configure("sec", foreground=GOLD,
                                font=("Segoe UI", 9, "bold"), background="#1c1109")
        self.tree.tag_configure("ro", foreground=MUTED)
        self.tree.tag_configure("odd", background="#1e1410")
        self.tree.bind("<Double-1>", lambda e: self.download_sel())
        self.tree.bind("<Delete>", lambda e: self.delete_sel())
        self.tree.bind("<F2>", lambda e: self.rename_sel())
        self.tree.bind("<Button-3>", self._context_menu)

        # progreso + ✖ cancelar
        prow = tk.Frame(self, bg=BG)
        prow.pack(fill="x", padx=14, pady=(0, 2))
        self.prog = ttk.Progressbar(prow, mode="determinate")
        self.prog.pack(side="left", fill="x", expand=True)
        self.btn_cancel = RButton(prow, "✖", self.cancel_xfer, kind="danger",
                                  pad=(10, 3))
        # solo visible durante una transferencia
        self.lbl_prog = tk.Label(self, text="", fg=MUTED, bg=BG,
                                 font=("Segoe UI", 8))
        self.lbl_prog.pack(anchor="w", padx=16)

        # consola
        self.logf = tk.Frame(self, bg=BG2)
        lf_head = tk.Frame(self.logf, bg=BG2)
        lf_head.pack(fill="x")
        tk.Label(lf_head, text="⌨ Consola", fg=GOLD, bg=BG2,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=10, pady=3)
        self.lbl_log_n = tk.Label(lf_head, text="", fg=MUTED, bg=BG2,
                                  font=("Segoe UI", 8))
        self.lbl_log_n.pack(side="left", padx=8)
        RButton(lf_head, "⧉ Copiar", self.copy_log, pad=(8, 2), fs=8).pack(side="right", padx=4, pady=2)
        RButton(lf_head, "🗑", self.clear_log, pad=(8, 2), fs=8).pack(side="right", padx=2, pady=2)
        self._holdbtn = RButton(lf_head, "⏸", self._toggle_hold, pad=(8, 2), fs=8)
        self._holdbtn.pack(side="right", padx=2, pady=2)
        tframe = tk.Frame(self.logf, bg=BG2)
        tframe.pack(fill="x", padx=8, pady=(0, 8))
        self.txt_log = tk.Text(tframe, height=7, bg="#120b07", fg="#e8dcc4",
                               font=("Consolas", 8), relief="flat", bd=6,
                               state="disabled", wrap="word")
        lsb = ttk.Scrollbar(tframe, orient="vertical", command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=lsb.set)
        lsb.pack(side="right", fill="y")
        self.txt_log.pack(side="left", fill="x", expand=True)
        for tag, col in (("err", "#ff7a66"), ("wrn", GOLD), ("net", NETC),
                         ("ok", OKC), ("inf", "#9fe8a8"), ("ui", "#d9a7ff")):
            self.txt_log.tag_configure(tag, foreground=col)
        self.logf.pack(fill="x", padx=14, pady=(0, 8))

        # barra de estado
        st = tk.Frame(self, bg=BG2)
        st.pack(fill="x")
        self.lbl_status = tk.Label(st, text="Listo — toca 🔍 Buscar tribu o escribe la IP",
                                   fg=MUTED, bg=BG2, font=("Segoe UI", 8), anchor="w")
        self.lbl_status.pack(side="left", padx=10, pady=4)

    def _toggle_hold(self):
        self._log_hold = not getattr(self, "_log_hold", False)
        self._holdbtn._text = "▶" if self._log_hold else "⏸"
        self._holdbtn._draw(self._holdbtn.bg)

    # ---------- utilidades ----------
    def set_status(self, msg, color=MUTED):
        self.lbl_status.config(text=msg, fg=color)

    def set_prog(self, txt, pct=None):
        self.lbl_prog.config(text=txt)
        if pct is not None:
            self.prog["value"] = pct
        self.update_idletasks()

    def bg(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def _selected_items(self):
        return [self.row_item[iid] for iid in self.tree.selection()
                if iid in self.row_item]

    def _xfer_begin(self):
        self._xfer_running = True
        self._xfer_cancel.clear()
        self.btn_cancel.pack(side="right", padx=6)

    def _xfer_end(self):
        self._xfer_running = False
        self.btn_cancel.pack_forget()
        self.after(10, lambda: self.set_prog("", 0))

    def cancel_xfer(self):
        self._xfer_cancel.set()
        self.log("wrn", "cancelación pedida por el usuario")

    # ---------- conexión ----------
    def auto_on(self):
        return self.cfg.get("auto_connect") is not False

    def _auto_connect(self):
        if self.auto_on():
            self.discover(silent=True)
        elif self.base_url:
            self.set_status("Reconectando a %s…" % self.base_url)
            self.bg(lambda: self._try_connect(self.base_url))
        else:
            self.set_status("Auto-conexión apagada — 🔍 Buscar tribu o escribe la IP")

    def _watchdog(self):
        try:
            if not self._connected and self.auto_on() and not self._scanning:
                self.discover(silent=True)
        finally:
            self.after(30000, self._watchdog)

    def connect_manual(self):
        url = self.cmb_hosts.get().strip().split("  —  ")[0].strip()
        if not url:
            return self.discover()
        if not url.startswith("http"):
            url = "http://" + url
        if ":" not in url.split("//", 1)[1]:
            url += ":%d" % PORT
        url = url.rstrip("/")
        self.set_status("Conectando a %s…" % url)
        self.log("inf", "conectando a %s …", url)
        self.bg(lambda: self._try_connect(url))

    def _try_connect(self, url):
        data = probe(url)
        if not data:
            def fail():
                self._connected = False
                self.set_status("✖ %s no respondió — ¿servidor encendido en la app?" % url,
                                DANGER)
                self.log("err", "%s no respondió", url)
                if self.auto_on():
                    self.discover(silent=True)
            self.after(0, fail)
            return
        self.base_url = url
        self.cfg["last_url"] = url
        save_cfg(self.cfg)
        self.after(0, lambda: self._connected_ok(data))

    def _connected_ok(self, data):
        self._connected = True
        self.server_name = data.get("name") or "Mi tribu"
        self.dev_id = data.get("id") or ""
        if self.dev_id:
            devs = self.cfg.setdefault("devices", {})
            devs[self.dev_id] = {"name": self.server_name, "url": self.base_url}
            self.cfg["last_dev"] = self.dev_id
            save_cfg(self.cfg)
        short = (" · " + self.dev_id.replace("tribal-", "")[:8]) if self.dev_id else ""
        self.lbl_srv.config(text="%s · tribu de archivos" % self.server_name)
        self.lbl_state.config(text="● conectado — %s%s" % (self.base_url, short), fg=OKC)
        n = len(data.get("items") or [])
        self.set_status("✔ Conectado a «%s» — %d archivos" % (self.server_name, n), OKC)
        self.log("ok", "conectado a «%s» (%s) — %d archivos%s",
                 self.server_name, self.base_url, n,
                 (" · id " + self.dev_id) if self.dev_id else " · apk sin id")
        self._paint_items(data.get("items") or [])

    def _lost(self):
        self._connected = False
        self.lbl_state.config(text="○ sin conexión", fg=MUTED)

    def discover(self, silent=False):
        if self._scanning:
            return
        self._scanning = True
        if not silent:
            self.set_status("Escaneando la red (WiFi · USB · Bluetooth PAN)…", GOLD)
            self.set_prog("Buscando quién responde en el puerto %d…" % PORT, 0)
        self.log("inf", "escaneando la red…%s", "" if not silent else " (silencioso)")
        extra = []
        for src in (self.cmb_hosts.get().split("  —  ")[0], self.cfg.get("last_url") or ""):
            h = src.split("//")[-1].split(":")[0].split("/")[0].strip()
            if h and h.count(".") == 3:
                extra.append(h)

        def run():
            prog = None if silent else (
                lambda d, t: self.after(0, lambda d=d, t=t: self.set_prog(
                    "Escaneando… %d/%d" % (d, t), d * 100.0 / t)))
            found = discover(progress=prog, extra_hosts=extra)
            self.after(0, lambda: self._discover_done(found, silent))
        self.bg(run)

    def _discover_done(self, found, silent=False):
        self._scanning = False
        self.set_prog("", 0)
        if not found:
            if not silent:
                self.set_status("No apareció ninguna tribu — ¿servidor encendido en ⋮→Servidor de archivos?",
                                DANGER)
            self.log("wrn", "ninguna tribu respondió en la red")
            return
        urls = ["%s  —  %s" % (u, (d.get("name") or "tribu")) for u, d in found]
        self.cmb_hosts["values"] = urls
        self.log("ok", "%d tribu(s) hallada(s): %s", len(found),
                 ", ".join(u.split("//")[1] for u, _ in found))

        if not self.auto_on():
            self.cmb_hosts.set(urls[0])
            self.set_status("%d tribu(s) en la red — elige y pulsa ⚡ Conectar" % len(found), GOLD)
            return

        want = self.cfg.get("last_dev")
        pick = None
        if want:
            pick = next(((u, d) for u, d in found if d.get("id") == want), None)
        if not pick:
            pick = found[0]
        if not silent or not self._connected:
            if len(found) > 1:
                self.set_status("%d tribus — conectando a «%s» (elige otra arriba si quieres)"
                                % (len(found), pick[1].get("name") or "tribu"), GOLD)
            self._try_connect(pick[0])

    # ---------- catálogo ----------
    def _paint_items(self, items):
        self.items = items
        self.row_item.clear()
        for iid in self.tree.get_children(""):
            self.tree.delete(iid)
        for kind, icon, title in KIND_META:
            rows = [it for it in items
                    if (it.get("k") or "other") == kind
                    or (kind == "other" and it.get("k") not in KIND_ICON)]
            if not rows:
                continue
            sec = self.tree.insert("", "end", text=title + "   (%d)" % len(rows),
                                   values=("",), open=True, tags=("sec",))
            for i, it in enumerate(rows):
                name = it.get("n") or "?"
                ro = it.get("ro")
                txt = "%s  %s%s" % (icon, name, "   🔒" if ro else "")
                tags = ["ro"] if ro else ([] if i % 2 == 0 else ["odd"])
                iid = self.tree.insert(sec, "end", text=txt,
                                       values=(human_size(it.get("s")),), tags=tags)
                self.row_item[iid] = it
        if not items:
            self.tree.insert("", "end", text="La tribu está vacía — sube el primer archivo.",
                             values=("",), tags=("sec",))

    def refresh(self):
        if not self.base_url:
            return self.discover()
        self.set_status("Actualizando catálogo…")

        def run():
            data = probe(self.base_url)
            if data:
                self.after(0, lambda: self._connected_ok(data))
            else:
                self.after(0, lambda: (self._lost(),
                                       self.log("err", "el teléfono dejó de responder"),
                                       self.set_status("✖ Sin respuesta del teléfono", DANGER)))
        self.bg(run)

    # ---------- clic derecho ----------
    def _context_menu(self, e):
        iid = self.tree.identify_row(e.y)
        it = self.row_item.get(iid)
        if not it:
            return
        self.tree.selection_set(iid)
        m = tk.Menu(self, tearoff=0, bg=BG2, fg=FG, relief="flat", bd=1,
                    activebackground=ACCENT, activeforeground="white",
                    font=("Segoe UI", 9))
        ro = bool(it.get("ro"))
        m.add_command(label="⬇  Descargar", command=self.download_sel)
        m.add_command(label="✎  Renombrar", command=self.rename_sel,
                      state="disabled" if ro else "normal")
        m.add_command(label="ℹ  Información", command=lambda: self.show_info(it))
        m.add_command(label="📂  Carpeta de destino",
                      command=lambda: self.open_dest(it))
        m.add_separator()
        m.add_command(label="🗑  Eliminar", command=self.delete_sel,
                      state="disabled" if ro else "normal")
        m.tk_popup(e.x_root, e.y_root)

    def show_info(self, it):
        d = tk.Toplevel(self)
        d.title("Información — TRIBALs")
        d.configure(bg=BG2)
        d.resizable(False, False)
        d.transient(self)
        tk.Label(d, text="ℹ  %s" % (it.get("n") or "?"), fg=GOLD, bg=BG2,
                 font=("Segoe UI", 11, "bold"), wraplength=360,
                 justify="left").pack(padx=20, pady=(16, 8), anchor="w")
        rows = [
            ("Tipo", it.get("k") or "archivo"),
            ("Tamaño", human_size(it.get("s"))),
            ("ID", it.get("i") or "—"),
            ("Ruta en el teléfono", it.get("p") or "—"),
            ("Origen", "Incluido con la app (solo lectura)" if it.get("ro") else "De la tribu"),
            ("Servidor", "%s — %s" % (self.server_name or "?", self.base_url or "?")),
        ]
        for k, v in rows:
            f = tk.Frame(d, bg=BG2)
            f.pack(fill="x", padx=20)
            tk.Label(f, text=k, fg=MUTED, bg=BG2, width=20, anchor="w",
                     font=("Segoe UI", 8)).pack(side="left")
            tk.Label(f, text=str(v), fg=FG, bg=BG2, anchor="w",
                     font=("Segoe UI", 9), wraplength=280,
                     justify="left").pack(side="left", pady=1)
        RButton(d, "Cerrar", d.destroy).pack(pady=(12, 16))

    def open_dest(self, it=None):
        dest = self._dest()
        path = os.path.join(dest, (it.get("n") or "")) if it else None
        try:
            if path and os.path.isfile(path):
                subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
                self.log("inf", "explorador abierto en %s", path)
            else:
                os.startfile(os.path.normpath(dest))
                self.log("inf", "carpeta de descargas abierta: %s", dest)
        except Exception as e:
            self.set_status("✖ %s" % e, DANGER)

    # ---------- transferencias ----------
    def pick_dest(self):
        d = filedialog.askdirectory(title="Carpeta de descarga")
        if d:
            self.cfg["dest"] = d
            save_cfg(self.cfg)
            self.set_status("Descargas → %s" % d, OKC)
            self.log("inf", "destino de descargas: %s", d)

    def _dest(self):
        d = self.cfg.get("dest")
        if not d:
            d = os.path.join(os.path.expanduser("~"), "Downloads", "TRIBALs")
        os.makedirs(d, exist_ok=True)
        return d

    def _dl_one(self, it, dest_dir):
        p = urllib.parse.quote(it.get("p") or "")
        n = urllib.parse.quote(it.get("n") or "archivo")
        url = "%s/dl?p=%s&n=%s" % (self.base_url, p, n)
        fname = (it.get("n") or "archivo").replace("/", "_").replace("\\", "_")
        os.makedirs(dest_dir, exist_ok=True)
        path = os.path.join(dest_dir, fname)
        try:
            with http_get(url, timeout=10) as r, open(path, "wb") as f:
                total = int(r.headers.get("Content-Length") or 0)
                got = 0
                cancel = getattr(self, "_xfer_cancel", None)
                while True:
                    if cancel and cancel.is_set():
                        raise Cancelled()
                    chunk = r.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    got += len(chunk)
                    if total:
                        self.after(0, lambda g=got, t=total, fn=fname:
                                   self.set_prog("⬇ %s — %s / %s" %
                                                 (fn, human_size(g), human_size(t)),
                                                 g * 100.0 / t))
        except Cancelled:
            try:
                os.remove(path)
            except Exception:
                pass
            raise
        return path

    def download_sel(self):
        sel = [it for it in self._selected_items() if it.get("p")]
        if not sel:
            return self.set_status("Selecciona archivos en la lista", MUTED)
        self._download_many(sel)

    def download_all(self):
        sel = [it for it in self.items if it.get("p")]
        if not sel:
            return self.set_status("La tribu está vacía", MUTED)
        if not messagebox.askyesno(APP_TITLE, "¿Descargar los %d archivos?" % len(sel)):
            return
        self._download_many(sel)

    def _download_many(self, items):
        if self._xfer_running:
            return self.set_status("Ya hay una transferencia en curso — ✖ la cancela", MUTED)
        dest = self._dest()
        self.set_status("Descargando %d archivo(s) → %s" % (len(items), dest), GOLD)
        self.log("inf", "descargando %d archivo(s) → %s", len(items), dest)
        self._xfer_begin()

        def run():
            ok = canc = 0
            try:
                for it in items:
                    if self._xfer_cancel.is_set():
                        raise Cancelled()
                    try:
                        self._dl_one(it, dest)
                        ok += 1
                        self.after(0, lambda it=it: self.log("ok", "⬇ %s", it.get("n")))
                    except Cancelled:
                        raise
                    except Exception as e:
                        fail = str(e)
                        self.after(0, lambda it=it, fail=fail: (
                            self.log("err", "⬇ %s falló: %s", it.get("n"), fail),
                            self.set_status("✖ %s: %s" % (it.get("n"), fail), DANGER)))
            except Cancelled:
                canc = 1
            def fin():
                self._xfer_end()
                if canc:
                    self.set_status("✖ Descarga cancelada — %d archivo(s) guardados" % ok, GOLD)
                    self.log("wrn", "descarga cancelada — %d guardados", ok)
                else:
                    self.set_status("✔ %d/%d descargados en %s" % (ok, len(items), dest), OKC)
                    self.log("ok", "descarga completa: %d/%d", ok, len(items))
            self.after(0, fin)
        self.bg(run)

    def upload_files(self):
        fs = filedialog.askopenfilenames(title="Archivos para la tribu")
        if fs:
            self._upload_many(list(fs))

    def upload_folder(self):
        d = filedialog.askdirectory(title="Carpeta completa para la tribu")
        if not d:
            return
        fs = []
        for root, _, names in os.walk(d):
            fs.extend(os.path.join(root, n) for n in names)
        if fs:
            self._upload_many(fs)

    def _upload_many(self, paths):
        if not self.base_url:
            return self.set_status("Conéctate a una tribu primero", DANGER)
        if self._xfer_running:
            return self.set_status("Ya hay una transferencia en curso — ✖ la cancela", MUTED)
        self.set_status("Subiendo %d archivo(s)…" % len(paths), GOLD)
        self.log("inf", "subiendo %d archivo(s) a %s", len(paths), self.base_url)
        self._xfer_begin()

        def run():
            ok = canc = 0
            try:
                for i, path in enumerate(paths, 1):
                    if self._xfer_cancel.is_set():
                        raise Cancelled()
                    name = os.path.basename(path)
                    try:
                        with open(path, "rb") as f:
                            body = f.read()
                        url = "%s/up?n=%s" % (self.base_url, urllib.parse.quote(name))
                        req = urllib.request.Request(
                            url, data=body, method="POST",
                            headers={"Content-Type": "application/octet-stream",
                                     "Content-Length": str(len(body))})
                        urllib.request.urlopen(req, timeout=120).read()
                        ok += 1
                        self.after(0, lambda i=i, n=len(paths), nm=name:
                                   (self.log("ok", "⬆ %d/%d «%s»", i, n, nm),
                                    self.set_prog("⬆ %d/%d — «%s»" % (i, n, nm),
                                                  i * 100.0 / n)))
                    except Cancelled:
                        raise
                    except Exception as e:
                        fail = str(e)
                        self.after(0, lambda nm=name, fail=fail: (
                            self.log("err", "⬆ %s falló: %s", nm, fail),
                            self.set_status("✖ %s: %s" % (nm, fail), DANGER)))
            except Cancelled:
                canc = 1
            def fin():
                self._xfer_end()
                if canc:
                    self.set_status("✖ Subida cancelada — %d enviados" % ok, GOLD)
                    self.log("wrn", "subida cancelada — %d enviados", ok)
                else:
                    self.set_status("✔ %d/%d recibidos por la tribu" % (ok, len(paths)), OKC)
                    self.log("ok", "subida completa: %d/%d", ok, len(paths))
            self.after(0, fin)
            self.after(3000, self.refresh)   # la app tarda en indexar la bandeja
        self.bg(run)

    # ---------- renombrar / eliminar ----------
    def rename_sel(self):
        sel = self._selected_items()
        if len(sel) != 1:
            return self.set_status("Selecciona UN solo archivo para renombrar", MUTED)
        it = sel[0]
        if it.get("ro"):
            return self.set_status("Los archivos incluidos no se renombran", MUTED)
        new = simpledialog.askstring(APP_TITLE, "Nuevo nombre:",
                                     initialvalue=it.get("n"), parent=self)
        if not new or new.strip() == it.get("n"):
            return
        url = "%s/ren?i=%s&n=%s" % (self.base_url, urllib.parse.quote(it.get("i") or ""),
                                    urllib.parse.quote(new.strip()))
        self.log("inf", "renombrando «%s» → «%s»", it.get("n"), new.strip())
        self.bg(lambda: self._simple_call(url, "✎ Renombrado en el teléfono"))

    def delete_sel(self):
        sel = [it for it in self._selected_items() if not it.get("ro")]
        if not sel:
            return self.set_status("Nada eliminable seleccionado (los 🔒 incluidos no se borran)",
                                   MUTED)
        name = sel[0].get("n") if len(sel) == 1 else ""
        dlg = Confirm3(self, name, len(sel))
        if not dlg.result:
            return self.set_status("Eliminación cancelada", MUTED)
        ids = [it.get("i") for it in sel if it.get("i")]
        self.log("wrn", "eliminando %d archivo(s) del teléfono…", len(ids))

        def run():
            ok = 0
            for i in ids:
                try:
                    http_get("%s/del?i=%s" % (self.base_url, urllib.parse.quote(i)),
                             timeout=8).read()
                    ok += 1
                except Exception:
                    pass
            self.after(0, lambda: (
                self.set_status("🗑 %d/%d eliminados del teléfono" % (ok, len(ids)), OKC),
                self.log("ok", "eliminados %d/%d", ok, len(ids))))
            self.after(1400, self.refresh)
        self.bg(run)

    def _simple_call(self, url, okmsg):
        try:
            http_get(url, timeout=8).read()
            self.after(0, lambda: (self.set_status(okmsg, OKC),
                                   self.log("ok", okmsg)))
            self.after(900, self.refresh)
        except Exception as e:
            self.after(0, lambda: (self.set_status("✖ %s" % e, DANGER),
                                   self.log("err", "falló: %s", e)))

    # ---------- ajustes ----------
    def show_settings(self):
        d = tk.Toplevel(self)
        d.title("Ajustes — TRIBALs PC")
        d.configure(bg=BG2)
        d.resizable(False, False)
        d.transient(self)
        d.grab_set()
        tk.Label(d, text="⚙ Ajustes", fg=GOLD, bg=BG2,
                 font=("Segoe UI", 12, "bold")).pack(padx=20, pady=(14, 4), anchor="w")

        var_auto = tk.BooleanVar(value=self.auto_on())
        tk.Checkbutton(
            d, text="Conectar automáticamente (silencioso)",
            variable=var_auto, fg=FG, bg=BG2, selectcolor=BG3,
            activebackground=BG2, activeforeground=FG,
            font=("Segoe UI", 9), anchor="w", justify="left",
            wraplength=340).pack(padx=20, pady=4, anchor="w")
        tk.Label(d,
                 text="Activo: al abrir, el PC encuentra cualquier teléfono\n"
                      "con TRIBALs en la misma red y se conecta solo, sin\n"
                      "preguntar — igual si la conexión se cae, reengancha.\n"
                      "Apagado: eliges la tribu y pulsas ⚡ Conectar.",
                 fg=MUTED, bg=BG2, font=("Segoe UI", 8), justify="left"
                 ).pack(padx=20, anchor="w")

        devs = self.cfg.get("devices") or {}
        if devs:
            tk.Label(d, text="Dispositivos conocidos:", fg=MUTED, bg=BG2,
                     font=("Segoe UI", 8, "bold")).pack(padx=20, pady=(10, 2), anchor="w")
            for did, inf in devs.items():
                tk.Label(d, text="  · %s  (%s)" % (inf.get("name", "?"),
                                                  did.replace("tribal-", "")[:12]),
                         fg=MUTED, bg=BG2, font=("Segoe UI", 8)).pack(padx=20, anchor="w")

        def save():
            self.cfg["auto_connect"] = bool(var_auto.get())
            save_cfg(self.cfg)
            self.set_status("Auto-conexión %s" %
                            ("ACTIVADA — el PC engancha solo" if var_auto.get()
                             else "desactivada — conexión manual"),
                            OKC if var_auto.get() else MUTED)
            self.log("inf", "auto-conexión %s",
                     "activada" if var_auto.get() else "desactivada")
            if var_auto.get() and not self._connected:
                self.discover(silent=True)
            d.destroy()
        RButton(d, "Guardar", save, kind="accent").pack(pady=(10, 16))

    # ---------- ayuda ----------
    def show_help(self):
        txt = (
            "CÓMO CONECTAR EL PC A LA TRIBU\n"
            "══════════════════════════════════\n\n"
            "En el teléfono: ⋮ → «Servidor de archivos» → Encender.\n"
            "Aquí: toca 🔍 Buscar tribu — el escaneo encuentra el\n"
            "teléfono en cualquiera de estas vías:\n\n"
            "📶 WIFI\n"
            "  Ambos en la misma red (o el PC conectado al hotspot\n"
            "  WiFi del teléfono). Es la vía normal en casa/oficina.\n\n"
            "🔌 CABLE USB\n"
            "  Conecta el cable → en el teléfono: Ajustes → Red →\n"
            "  «Compartir conexión / Zona Wi-Fi» → activa\n"
            "  «Anclaje a red por USB». Windows verá una red nueva\n"
            "  y el buscador lo encuentra solo (192.168.42.129).\n"
            "  No gasta datos: es un cable directo.\n\n"
            "🔵 BLUETOOTH\n"
            "  1) Empareja el PC con el teléfono (Bluetooth de Windows).\n"
            "  2) En el teléfono activa «Anclaje a red por Bluetooth».\n"
            "  3) En Windows: Dispositivos Bluetooth → clic derecho\n"
            "     en el teléfono → «Unirse a red de área personal» →\n"
            "     Punto de acceso. El buscador lo encuentra en la\n"
            "     red PAN (192.168.44.x y similares).\n\n"
            "CLIC DERECHO en un archivo: descargar, renombrar,\n"
            "información, carpeta de destino, eliminar.\n"
            "✖ junto a la barra de progreso cancela la transferencia.\n\n"
            "Si el escaneo no lo encuentra, escribe la IP que muestra\n"
            "la app (http://192.168.x.x:8765) en el campo y pulsa\n"
            "⚡ Conectar.\n"
        )
        messagebox.showinfo(APP_TITLE + " — conexión", txt)


def main():
    app = TribalPC()
    app.mainloop()


if __name__ == "__main__":
    main()
