"""Local preview server that sends charset=utf-8, as the artifact host does.
Usage: python serve.py [port] [directory]"""
import http.server, os, sys
port = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
os.chdir(sys.argv[2] if len(sys.argv) > 2 else os.getcwd())
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        if self.path.endswith((".html", ".htm", "/")):
            self.send_header("Content-Type", "text/html; charset=utf-8")
        super().end_headers()
    def log_message(self, *a): pass
print(f"serving {os.getcwd()} on http://127.0.0.1:{port}", flush=True)
http.server.ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
