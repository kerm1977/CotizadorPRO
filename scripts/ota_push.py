# OTA push — estampa, comprime www/ y lo ENVIA al teléfono por su servidor
# FTP (TribalFtpPlugin puerto 8890): el APK lo aplica y recarga solo.
# Uso:  python scripts\ota_push.py <ip-del-telefono>
#       python scripts\ota_push.py            (prueba IPs comunes)
import io, os, sys, time, zipfile, socket, http.client

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WWW = os.path.join(ROOT, 'www')
SKIP = {'builtin'}
PORT = 8890
CANDIDATES = ['192.168.100.', '192.168.42.129', '192.168.43.',
              '192.168.44.', '192.168.45.', '172.20.10.']

def build_zip():
    buf = io.BytesIO()
    n = 0
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for base, dirs, files in os.walk(WWW):
            dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith('.')]
            for f in files:
                if f.startswith('.'):
                    continue
                p = os.path.join(base, f)
                z.write(p, os.path.relpath(p, WWW)); n += 1
    return buf.getvalue(), n

def stamp(n):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    p = os.path.join(WWW, 'js', 'ota_stamp.js')
    with open(p, 'w', encoding='utf-8') as f:
        f.write("// sello OTA generado por ota_push.py\n"
                "window.TRIBAL_OTA = { ts: '%s', files: %d };\n" % (ts, n))
    return ts

def find_phone():
    cands = []
    if len(sys.argv) > 1:
        return sys.argv[1]
    # barrido corto por las /24 típicas (WiFi, USB tethering, hotspot)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80)); my = s.getsockname()[0]; s.close()
        pre = '.'.join(my.split('.')[:3]) + '.'
        cands = [pre + str(i) for i in range(1, 255)]
        cands.remove(my)
    except Exception:
        pass
    cands += CANDIDATES
    for ip in cands:
        if ip.endswith('.'):
            for i in range(1, 255):
                try:
                    s = socket.create_connection((ip + str(i), PORT), .2)
                    s.close(); return ip + str(i)
                except Exception:
                    pass
        else:
            try:
                s = socket.create_connection((ip, PORT), .3)
                s.close(); return ip
            except Exception:
                pass
    return None

if __name__ == '__main__':
    ip = find_phone()
    if not ip:
        print('telefono no encontrado — pasale su IP: python scripts\\ota_push.py 192.168.x.x')
        sys.exit(1)
    data, n = build_zip()
    ts = stamp(n)                          # estampa antes de zipear
    data, n = build_zip()                  # re-zip ya con el sello nuevo
    c = http.client.HTTPConnection(ip, PORT, timeout=30)
    c.request('POST', '/ota', data,
              {'Content-Type': 'application/zip',
               'Content-Length': str(len(data))})
    r = c.getresponse(); r.read()
    print('OTA %s -> %s:%d  [%d]  %d archivos, %d KB'
          % (ts, ip, PORT, r.status, n, len(data) // 1024))
