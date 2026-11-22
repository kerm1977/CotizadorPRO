# OTA watcher — vigila www/, sirve bundle.zip en :8891 y al cambiar avisa al
# telefono (POST {url,checksum} a :8890/ota); la app descarga y aplica con
# Capgo updater (el checksum SHA-256 es OBLIGATORIO) + modal con el sello.
# Uso: python scripts\ota_watch.py            (descubre el telefono)
#      python scripts\ota_watch.py 192.168.x  (IP fija, sin barrido)
import io, os, sys, time, zipfile, socket, http.client, json, threading, hashlib
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

if getattr(sys, 'frozen', False):
    ROOT = os.path.dirname(sys.executable)       # exe portátil: www/ a su lado
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WWW = os.path.join(ROOT, 'www')
SKIP = {'builtin'}
PORT_TEL = 8890                       # TribalFtpPlugin del telefono (CotizacionesPro)
PORT_SRV = 8891                       # este servidor de bundle
IPCACHE = os.path.join(ROOT, 'scripts', '.ota_ip')
LOGDIR = os.path.join(ROOT, 'logs')
LOGFILE = os.path.join(LOGDIR, 'phone.log')
BUNDLE = {'data': b'', 'sha': '', 'n': 0}   # cache: checksum == bytes servidos

def build_zip():
    buf = io.BytesIO(); n = 0
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for base, dirs, files in os.walk(WWW):
            dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith('.')]
            for f in files:
                if f.startswith('.'): continue
                p = os.path.join(base, f)
                z.write(p, os.path.relpath(p, WWW)); n += 1
    return buf.getvalue(), n

def rebuild():
    n = sum(1 for b, d, fs in os.walk(WWW) for f in fs
            if not f.startswith('.'))
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(os.path.join(WWW, 'js', 'ota_stamp.js'), 'w', encoding='utf-8') as f:
        f.write("// sello OTA generado por ota_watch.py\n"
                "window.TRIBAL_OTA = { ts: '%s', files: %d };\n" % (ts, n))
    data, n = build_zip()
    BUNDLE['data'] = data
    BUNDLE['sha'] = hashlib.sha256(data).hexdigest()
    BUNDLE['n'] = n
    BUNDLE['ts'] = ts
    return ts

def my_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80)); ip = s.getsockname()[0]; s.close()
        return ip
    except Exception:
        return '127.0.0.1'

# ---------------- servidor de bundle (el telefono hace PULL con Capgo) -------
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == '/stamp.json':         # poller de la app lee el sello
            data = json.dumps({'ts': BUNDLE['ts'], 'sha': BUNDLE['sha'],
                               'n': BUNDLE['n']}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path == '/bundle.zip':
            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.send_header('Content-Length', str(len(BUNDLE['data'])))
            self.end_headers()
            self.wfile.write(BUNDLE['data'])
            print('  servido %d KB' % (len(BUNDLE['data'])//1024), flush=True)
        else:
            self.send_response(200); self.end_headers()
            self.wfile.write(b'CotizacionesPro OTA')
    def do_POST(self):
        if self.path == '/log':                # consola remota del telefono
            try:
                n = int(self.headers.get('Content-Length') or 0)
                d = json.loads(self.rfile.read(n).decode('utf-8', 'replace'))
                lines = d.get('lines') or d.get('logs') or []
            except Exception:
                lines = []
            if lines:
                os.makedirs(LOGDIR, exist_ok=True)
                with open(LOGFILE, 'a', encoding='utf-8') as f:
                    for l in lines:
                        f.write(str(l).rstrip() + '\n')
                print('  log: %s' % str(lines[-1])[:110], flush=True)
            self.send_response(200)
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'ok')
        else:
            self.send_response(404); self.end_headers()

def alive(ip):
    try:
        s = socket.create_connection((ip, PORT_TEL), .4); s.close(); return True
    except Exception:
        return False

def discover():
    if len(sys.argv) > 1:
        return sys.argv[1]
    if os.path.exists(IPCACHE):
        try:
            ip = json.load(open(IPCACHE))['ip']
            if alive(ip): return ip
        except Exception:
            pass
    cand = []
    ip = my_ip()
    if ip != '127.0.0.1':
        pre = '.'.join(ip.split('.')[:3]) + '.'
        cand = [pre + str(i) for i in range(1, 255)]
        if ip in cand: cand.remove(ip)
    cand += ['192.168.42.129']
    found = []
    with ThreadPoolExecutor(max_workers=60) as ex:
        for c, ok in zip(cand, ex.map(alive, cand)):
            if ok: found.append(c)
    if not found: return None
    # lista los teléfonos con su devid (GET /id) — elegir cuál actualizar
    devs = []
    for ip in found:
        try:
            r = http.client.HTTPConnection(ip, PORT_TEL, timeout=3)
            r.request('GET', '/id')
            d = json.loads(r.getresponse().read().decode() or '{}')
            r.close()
            devs.append((ip, d.get('devname') or d.get('devid') or ip,
                         d.get('devid') or ip))
        except Exception:
            devs.append((ip, ip))
    if len(devs) == 1:
        json.dump({'ip': devs[0][0]}, open(IPCACHE, 'w'))
        return devs[0][0]
    print('Teléfonos CotizacionesPro encontrados:')
    for i, (ip, nm, dv) in enumerate(devs, 1):
        print('  %d. %s' % (i, nm), flush=True)
    if sys.stdin.isatty():
        pick = input('¿Cuál actualizar? [1]: ').strip() or '1'
        try:
            idx = int(pick) - 1
            if 0 <= idx < len(devs):
                ip, nm, dv = devs[idx]
                print('  → %s  (%s @ %s)' % (nm, dv, ip), flush=True)
                json.dump({'ip': ip}, open(IPCACHE, 'w'))
                return ip
        except ValueError:
            pass
    json.dump({'ip': devs[0][0]}, open(IPCACHE, 'w'))
    return devs[0][0]

def push(tel_ip, ts):
    url = 'http://%s:%d/bundle.zip' % (my_ip(), PORT_SRV)
    body = json.dumps({'url': url, 'checksum': BUNDLE['sha'],
                       'version': ts}).encode()
    c = http.client.HTTPConnection(tel_ip, PORT_TEL, timeout=15)
    c.request('POST', '/ota', body, {'Content-Type': 'application/json',
                                     'Content-Length': str(len(body))})
    r = c.getresponse(); r.read(); c.close()
    print('OTA %s -> %s  [%d]  %d archivos' % (ts, tel_ip, r.status, BUNDLE['n']),
          flush=True)

def mtimes():
    last = 0
    for base, dirs, files in os.walk(WWW):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith('.')]
        for f in files:
            if f == 'ota_stamp.js': continue
            try:
                last = max(last, os.path.getmtime(os.path.join(base, f)))
            except OSError:
                pass
    return last

if __name__ == '__main__':
    print('OTA watcher — descubriendo telefono…', flush=True)
    tel = discover()
    if not tel:
        print('telefono no encontrado; pasale la IP como argumento', flush=True)
        sys.exit(1)
    rebuild()
    threading.Thread(
        target=lambda: ThreadingHTTPServer(('0.0.0.0', PORT_SRV), H).serve_forever(),
        daemon=True).start()
    print('telefono: %s — bundle en http://%s:%d — vigilando www/…'
          % (tel, my_ip(), PORT_SRV), flush=True)
    last = mtimes()
    while True:
        time.sleep(1)
        try:
            cur = mtimes()
            if cur > last:
                time.sleep(0.7)                    # debounce de rafagas
                cur = mtimes()
                ts = rebuild()
                if alive(tel):
                    push(tel, ts)
                last = cur
        except Exception as e:
            print('watch: %s' % e, flush=True)
            time.sleep(3)
