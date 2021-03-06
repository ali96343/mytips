import logging

from ombott.server_adapters import ServerAdapter

try:
    from .utils.wsservers import *
except ImportError:
    wsservers_list = []

__all__ = [
    "geventWebSocketServer",
    "wsgirefThreadingServer",
    "rocketServer",
    "gevent",
] + wsservers_list

def gevent():
    # basically tihis is the same as ombotts version, but
    # since reload was added as keyword argument that's being passed to the server
    # this was passed as ssl_options to gevent's pywsgi.WSGIServer. This breaks gevent's api
    # Therefor 'reloader' is removed below in the options passed to the server.
    from gevent import pywsgi, local
    import threading
    if not isinstance(threading.local(), local.local):
        msg = "Ombott requires gevent.monkey.patch_all() (before import)"
        raise RuntimeError(msg)

    class GeventServer(ServerAdapter):
        def run(self, handler):
            if not self.quiet:
                self.log = logging.getLogger("gevent")
            options = self.options.copy()
            try:
                # keep only ssl options
                del options['reloader']
            except: pass

            server = pywsgi.WSGIServer(
                (self.host, self.port),
                handler,
                **options
            )
            server.serve_forever()

    return GeventServer


def geventWebSocketServer():
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    from geventwebsocket.logging import create_logger

    class GeventWebSocketServer(ServerAdapter):
        def run(self, handler):
            server = pywsgi.WSGIServer(
                (self.host, self.port),
                handler,
                handler_class=WebSocketHandler,
                **self.options
            )

            if not self.quiet:
                server.logger = create_logger("geventwebsocket.logging")
                server.logger.setLevel(logging.INFO)
                server.logger.addHandler(logging.StreamHandler())

            server.serve_forever()

    return GeventWebSocketServer


def wsgirefThreadingServer():
    # https://www.electricmonk.nl/log/2016/02/15/multithreaded-dev-web-server-for-the-python-bottle-web-framework/

    import socket, ssl
    from concurrent.futures import ThreadPoolExecutor  # pip install futures
    from socketserver import ThreadingMixIn
    from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server
    import threading

    class Reirector:
        # https://www.elifulkerson.com/projects/http-https-redirect.php
        def __init__(self, socket, address, host, port, logger):
            self.socket = socket
            self.host = host
            self.port = port
            self.logger = logger
            self.ip = address[0]

        def sendline(self, data):
            self.socket.send(data + b"\r\n")
    
        def fileno(self):
            self._checkClosed()
            return self.socket.fileno()
            #return self._sock.fileno()

        def run(self,):

            TARGET = f"https://{self.host}:{self.port}".encode()
            data = self.socket.recv(1024)

            if data:
                req_url = data.split(b' ', 2)
                if req_url and req_url[2].startswith( b'HTTP/1'):
                    TARGET += req_url[1]
                # send our https redirect
                self.sendline( b"HTTP/1.1 302 Encryption Required")
                self.sendline( b"Location: " + TARGET)
                self.sendline( b"Reirector: close")
                self.sendline( b"Cache-control: private")
                self.sendline( b"")
                self.sendline( b"<html><body>Encryption Required.  Please go to <a href='" + TARGET + b"'>" + TARGET + b"</a> for this service.</body></html>")
                self.sendline( b"")
            self.socket.close
            if self.logger:
               self.logger.info(f'http:// from {self.ip} to {TARGET.decode()}')

   # https://programtalk.com/python-examples/ssl.wrap_socket/?ipage=3
   # https://stackoverflow.com/questions/26554106/python-3-how-to-log-ssl-handshake-errors-from-server-side
   # https://www.google.com/search?client=firefox-b-d&q=????????????+??????????+????+????????????+????????????

    # dual mode http:// and https://
    class DualSocket:
        # https://stackoverflow.com/questions/13325642/python-magic-smart-dual-mode-ssl-socket
        # https://openvpn.net/vpn-server-resources/how-to-redirect-http-to-https/       # https://gist.github.com/sivachandran/1969859

        def __init__( self, sock, certfile, keyfile, allow_http=False, logger=None, 
                      host='localhost', port=8000):
            self.sock = sock
            self.certfile = certfile
            self.keyfile = keyfile 
            self.allow_http = allow_http 
            self.logger = logger
            self.host = host
            self.port = port
            # delegate methods as needed
            _delegate_methods = ["fileno"]
            for method in _delegate_methods:
                setattr(self, method, getattr(self.sock, method))

        def accept(self):
            (conn, addr) = self.sock.accept()
            if conn.recv(1, socket.MSG_PEEK) == b"\x16":
                return (
                    ssl.wrap_socket(
                        conn,
                        certfile=self.certfile,
                        keyfile=self.keyfile,
                        do_handshake_on_connect=False,
                        server_side=True,
                        ssl_version=ssl.PROTOCOL_SSLv23, 
                        ca_certs=None,
                    ),
                    addr,
                )
            elif self.allow_http:
                return (conn, addr)
            else:
                # https://www.geeksforgeeks.org/socket-programming-multi-threading-python/
                trash_conn = Reirector(conn, addr, self.host, self.port, self.logger)
                redir = threading.Thread(target= trash_conn.run,  )
                redir.name = 'redir_' + redir.name
                redir.start()
                redir.join()
                return (conn, addr)
    
    class WSGIRefThreadingServer(ServerAdapter):
        def run(self, app):

            if not self.quiet:
                logging.basicConfig(
                    filename="wsgiref.log",
                    format="%(threadName)s | %(message)s",
                    filemode="a",
                    encoding="utf-8",
                    level=logging.DEBUG,
                )

                self.log = logging.getLogger("WSGIRef")

            self_run = self  # used in inner classes to access options and logger

            class PoolMixIn(ThreadingMixIn):
                def process_request(self, request, client_address):
                    self.pool.submit(
                        self.process_request_thread, request, client_address
                    )

            class ThreadingWSGIServer(PoolMixIn, WSGIServer):
                daemon_threads = True
                pool = ThreadPoolExecutor(max_workers=40)

            class Server:
                def __init__(
                    self, server_address=("127.0.0.1", 8000), handler_cls=None
                ):
                    self.wsgi_app = None
                    self.listen, self.port = server_address
                    self.handler_cls = handler_cls

                def set_app(self, app):
                    self.wsgi_app = app

                def get_app(self):
                    return self.wsgi_app

                def serve_forever(self):
                    self.server = make_server(
                        self.listen,
                        self.port,
                        self.wsgi_app,
                        ThreadingWSGIServer,
                        self.handler_cls,
                    )

                    # openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
                    # ./py4web.py run apps -s wsgirefThreadingServer --watch=off --port=8000 --ssl_cert=cert.pem --ssl_key=key.pem
                    # openssl s_client -showcerts -connect 127.0.0.1:8000
                    #
                    # https://realpython.com/python-https/

                    certfile = self_run.options.get("certfile", None)

                    if certfile:
                         try:
                            self.server.socket = DualSocket(
                                sock=self.server.socket,
                                certfile=certfile,
                                keyfile=self_run.options.get("keyfile", None),
                                logger = self_run.log,
                                host = self.listen,
                                port = self.port,
                            )
                         except ssl.SSLError:
                             pass
                         except socket.error:
                             pass
                    self.server.serve_forever()

            class FixedHandler(WSGIRequestHandler):
                def address_string(self):  # Prevent reverse DNS lookups please.
                    return self.client_address[0]

                def log_request(*args, **kw):
                    if not self_run.quiet:
                        return WSGIRequestHandler.log_request(*args, **kw)

            class LogHandler(WSGIRequestHandler):

                def address_string(self):  # Prevent reverse DNS lookups please.
                    return self.client_address[0]

                def log_message(self, format, *args):
                    if not self_run.quiet:  # and ( not args[1] in ['200','304']):
                        msg = "%s - - [%s] %s" % (
                            self.client_address[0],
                            self.log_date_time_string(),
                            format % args,
                        )
                        self_run.log.info(msg)

            handler_cls = self.options.get("handler_class", LogHandler)
            # handler_cls = self.options.get("handler_class", FixedHandler)
            server_cls = Server

            if ":" in self.host:  # Fix wsgiref for IPv6 addresses.
                if getattr(server_cls, "address_family") == socket.AF_INET:

                    class server_cls(server_cls):
                        address_family = socket.AF_INET6

            srv = make_server(
                self.host,
                self.port,
                app,
                server_cls,
                handler_cls,
            )
            srv.serve_forever()

    return WSGIRefThreadingServer

def rocketServer():
    try:
        from rocket3 import Rocket3 as Rocket
    except ImportError:
        from .rocket3 import Rocket3 as Rocket
    import logging.handlers

    class RocketServer(ServerAdapter):
        def run(self, app):
            if not self.quiet:
                log = logging.getLogger("Rocket")
                log.setLevel(logging.INFO)
                log.addHandler(logging.StreamHandler())
            interface = (self.host, self.port, self.options["keyfile"], self.options["certfile"]) if self.options.get("certfile", None) else (self.host, self.port)
            server = Rocket(interface, "wsgi", dict(wsgi_app=app))
            server.start()

    return RocketServer


#import os
#from contextlib import redirect_stderr


#with redirect_stderr(open(os.devnull, "w")):
#    with make_server("", 8051, app) as httpd:
#        httpd.handle_request()
