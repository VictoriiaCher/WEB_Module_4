import pathlib
import json
import socket
import urllib.parse
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from threading import Thread

BASE_DIR = pathlib.Path()

UDP_IP = '127.0.0.1'
UDP_PORT = 5000
SERV_PORT = 3000


class HTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.send_html("index.html")
            case "/message.html":
                self.send_html("message.html")
            case _:
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html("error.html", 404)

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header(
            "Content-type", "text/html"
        )
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self, filename ):
        self.send_response(200)
        mime_type, *rest = mimetypes.guess_type(
            filename
        )
        if mime_type:
            self.send_header("Content-type", mime_type)
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())

    def do_POST(self):
        body = self.rfile.read(
            int(self.headers["Content-Length"])
        )

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server = UDP_IP, UDP_PORT
        server_socket.sendto(body, server)
        server_socket.close()

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()


def run_http(server=HTTPServer, handler=HTTPHandler):
    address = ('',SERV_PORT)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def run_server():
    socket_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_server.bind((UDP_IP, UDP_PORT))
    try:
        while True:
            data, address = socket_server.recvfrom(1024)
            save_data(data)
    except KeyboardInterrupt:
        socket_server.close()
    finally:
        socket_server.close()


def save_data(data: bytes):
    data = urllib.parse.unquote_plus(data.decode())
    payload = {
        key: value for key, value in [el.split("=") for el in data.split("&")]
        }
    data_dict = {str(datetime.now()): payload}

    with open('storage/data.json', 'a', encoding='utf-8') as fd:
        json.dump(data_dict, fd, ensure_ascii=False)


if __name__ == "__main__":
    http_server = Thread(target=run_http)
    echo_server = Thread(target=run_server)

    http_server.start()
    echo_server.start()
