#!/usr/bin/env python3
"""Local-only dev tool: serves this site plus a simple /admin upload panel for
swapping photo-slot images and the background-music file, without needing to
hand-edit .image-slots.state.json or RokaInvite.dc.html for every change.

NOT part of the deployed site — this exists purely so photo/music swaps during
local authoring go through a small upload form instead of manual base64
splicing. Run this instead of `python3 -m http.server`:

    python3 admin_server.py [port]   # defaults to 8848

Then open http://localhost:8848/RokaInvite.dc.html as usual, and
http://localhost:8848/admin for the upload panel.
"""
import base64
import io
import json
import os
import re
import sys
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / '.image-slots.state.json'
UPLOADS_DIR = ROOT / 'uploads'
INVITE_FILE = ROOT / 'RokaInvite.dc.html'

SLOTS = ['main', '1', '2', '3', '4', '5']
MAX_DIM = 1000
WEBP_QUALITY = 90

ADMIN_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Roka Invite — Admin</title>
<style>
  body{background:#08070a;color:#f0e6cc;font-family:system-ui,sans-serif;padding:2.5rem 2rem;max-width:640px;margin:0 auto;}
  h1{font-size:1.35rem;color:#d4af37;margin:0 0 .3rem;}
  p.sub{color:#9a8456;font-size:.85rem;margin:0 0 2rem;line-height:1.5;}
  h2{margin-top:2.2rem;font-size:1rem;color:#d4af37;border-bottom:1px solid rgba(212,175,55,.2);padding-bottom:.4rem;}
  .row{display:flex;align-items:center;gap:.9rem;padding:.85rem 0;border-bottom:1px solid rgba(212,175,55,.1);}
  .row label{width:100px;flex:none;color:#c8a84e;font-size:.85rem;}
  input[type=file]{color:#f0e6cc;flex:1;font-size:.78rem;min-width:0;}
  button{background:#d4af37;color:#1a1006;border:none;padding:.5rem 1rem;border-radius:6px;cursor:pointer;font-weight:600;font-size:.82rem;flex:none;}
  button:hover{background:#e8c97a;}
  .status{font-size:.76rem;flex:none;max-width:180px;}
  .status.ok{color:#8fd48f;}
  .status.err{color:#e57373;}
</style></head>
<body>
  <h1>Roka Invite — local admin</h1>
  <p class="sub">Local-only tool, not part of the live site. Uploads write straight into <code>.image-slots.state.json</code> (photos) or <code>uploads/</code> + the invite's Audio() line (music). Reload the invite tab after uploading.</p>

  <h2>Photos</h2>
  <div id="photo-rows"></div>

  <h2>Background music</h2>
  <div class="row">
    <label>Song file</label>
    <input type="file" id="music-file" accept="audio/mpeg,audio/mp3,audio/*">
    <button onclick="uploadMusic()">Upload</button>
    <span class="status" id="music-status"></span>
  </div>

<script>
const SLOTS = [['main','Couple photo'],['1','Photo 1'],['2','Photo 2'],['3','Photo 3'],['4','Photo 4'],['5','Photo 5']];
const rows = document.getElementById('photo-rows');
SLOTS.forEach(([slot, label]) => {
  const row = document.createElement('div');
  row.className = 'row';
  row.innerHTML = '<label>' + label + '</label>' +
    '<input type="file" accept="image/png,image/jpeg,image/webp" id="file-' + slot + '">' +
    '<button>Upload</button><span class="status" id="status-' + slot + '"></span>';
  row.querySelector('button').onclick = () => uploadPhoto(slot);
  rows.appendChild(row);
});

async function uploadPhoto(slot) {
  const input = document.getElementById('file-' + slot);
  const status = document.getElementById('status-' + slot);
  if (!input.files[0]) { status.textContent = 'pick a file first'; status.className = 'status err'; return; }
  const fd = new FormData();
  fd.append('slot', slot);
  fd.append('file', input.files[0]);
  status.textContent = 'uploading…'; status.className = 'status';
  try {
    const r = await fetch('/admin/upload-photo', { method: 'POST', body: fd });
    const j = await r.json();
    if (j.ok) { status.textContent = 'done ✓ reload the invite'; status.className = 'status ok'; }
    else { status.textContent = j.error; status.className = 'status err'; }
  } catch (e) { status.textContent = String(e); status.className = 'status err'; }
}

async function uploadMusic() {
  const input = document.getElementById('music-file');
  const status = document.getElementById('music-status');
  if (!input.files[0]) { status.textContent = 'pick a file first'; status.className = 'status err'; return; }
  const fd = new FormData();
  fd.append('file', input.files[0]);
  status.textContent = 'uploading…'; status.className = 'status';
  try {
    const r = await fetch('/admin/upload-music', { method: 'POST', body: fd });
    const j = await r.json();
    if (j.ok) { status.textContent = 'done ✓ (' + j.filename + ')'; status.className = 'status ok'; }
    else { status.textContent = j.error; status.className = 'status err'; }
  } catch (e) { status.textContent = String(e); status.className = 'status err'; }
}
</script>
</body></html>
"""


def parse_multipart(body, boundary):
    """Minimal multipart/form-data parser -> {field_name: {'filename': str|None, 'data': bytes}}."""
    fields = {}
    delim = b'--' + boundary.encode()
    for part in body.split(delim):
        part = part.strip(b'\r\n')
        if not part or part == b'--':
            continue
        if b'\r\n\r\n' not in part:
            continue
        header_blob, data = part.split(b'\r\n\r\n', 1)
        data = data[:-2] if data.endswith(b'\r\n') else data
        headers = header_blob.decode('utf-8', 'replace')
        m_name = re.search(r'name="([^"]*)"', headers)
        m_file = re.search(r'filename="([^"]*)"', headers)
        if not m_name:
            continue
        fields[m_name.group(1)] = {
            'filename': m_file.group(1) if m_file else None,
            'data': data,
        }
    return fields


class AdminHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/admin', '/admin/'):
            body = ADMIN_HTML.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def do_POST(self):
        if self.path == '/admin/upload-photo':
            return self._handle_photo_upload()
        if self.path == '/admin/upload-music':
            return self._handle_music_upload()
        self.send_error(404)

    def _read_multipart(self):
        ctype = self.headers.get('Content-Type', '')
        m = re.search(r'boundary=(.+)', ctype)
        if not m:
            self._json_error(400, 'expected multipart/form-data')
            return None
        boundary = m.group(1).strip('"')
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        return parse_multipart(body, boundary)

    def _handle_photo_upload(self):
        fields = self._read_multipart()
        if fields is None:
            return
        slot = (fields.get('slot') or {}).get('data', b'').decode('utf-8', 'replace')
        file_field = fields.get('file')
        if slot not in SLOTS or not file_field or not file_field['data']:
            return self._json_error(400, 'missing slot or file')
        try:
            img = Image.open(io.BytesIO(file_field['data']))
            img = ImageOps.exif_transpose(img)
            img.thumbnail((MAX_DIM, MAX_DIM))
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')
            buf = io.BytesIO()
            img.save(buf, 'WEBP', quality=WEBP_QUALITY)
        except Exception as e:
            return self._json_error(500, 'image processing failed: ' + str(e))

        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        data_url = 'data:image/webp;base64,' + b64

        with open(STATE_FILE, encoding='utf-8') as f:
            state = json.load(f)
        state['photo-' + slot] = {'u': data_url, 's': 1, 'x': 0, 'y': 0}
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f)

        self._json_ok({'slot': slot, 'bytes': len(buf.getvalue())})

    def _handle_music_upload(self):
        fields = self._read_multipart()
        if fields is None:
            return
        file_field = fields.get('file')
        if not file_field or not file_field.get('filename'):
            return self._json_error(400, 'missing file')
        filename = os.path.basename(file_field['filename'])
        if not filename:
            return self._json_error(400, 'bad filename')

        UPLOADS_DIR.mkdir(exist_ok=True)
        dest = UPLOADS_DIR / filename
        with open(dest, 'wb') as f:
            f.write(file_field['data'])

        html_src = INVITE_FILE.read_text(encoding='utf-8')
        new_html, n = re.subn(
            r"new Audio\('\./uploads/[^']*'\)",
            "new Audio('./uploads/" + filename + "')",
            html_src,
        )
        if n:
            INVITE_FILE.write_text(new_html, encoding='utf-8')

        self._json_ok({'filename': filename, 'updated_reference': bool(n)})

    def _json_ok(self, obj):
        body = json.dumps(dict(ok=True, **obj)).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_error(self, code, msg):
        body = json.dumps({'ok': False, 'error': msg}).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # keep default stderr logging (unchanged) — override point kept for clarity
        super().log_message(fmt, *args)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8848
    os.chdir(ROOT)
    server = ThreadingHTTPServer(('', port), AdminHandler)
    print('Serving %s at http://localhost:%d  (admin panel: /admin)' % (ROOT, port))
    server.serve_forever()


if __name__ == '__main__':
    main()
