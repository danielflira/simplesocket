import socket
import select
import sys

class SocketDisconnected(Exception):
    pass

class Socket:
    def __init__(self, *args, **kwargs):
        if "wrap_socket" in kwargs:
            self.socket = kwargs["wrap_socket"]
        else:
            self.socket = socket.socket(*args, **kwargs)

    def __getattr__(self, attr):
        return getattr(self.socket, attr)

class SimpleSocket:
    def create_server(self, address, port, backlog=1, timeout=0.1):
        self.timeout = timeout

        try:
            server = Socket(wrap_socket=socket.create_server(
                    (address, port,), 
                    backlog=backlog, 
                    reuse_port=True))
        except AttributeError:
            server = Socket(
                    socket.AF_INET, 
                    socket.SOCK_STREAM)
            server.setsockopt(
                    socket.SOL_SOCKET, 
                    socket.SO_REUSEADDR, 
                    1)
            server.bind((address, port,))
            server.listen(backlog)

        server.settimeout(timeout)
        server.setblocking(0)
        server.address = (address, port,)
        server.data = []

        self.server = server
        self.clients = [server]

        self.handle_init(server)

    def create_client(self, address, port, timeout=0.1):
        self.timeout = timeout
      
        try:
            client = Socket(wrap_socket=socket.create_connection(
                    (address, port)))
        except AttributeError:
            client = Socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((address, port))
        
        client.settimeout(timeout)
        client.setblocking(0)
        client.address = (address, port,)
        client.data = []

        self.server = None
        self.clients = [client]

        self.handle_init(client)

    def handle_init(self, client_or_server):
        pass

    def accept(self, server):
        client, address = server.accept()
        client = Socket(wrap_socket=client)
        client.setblocking(0)
        client.settimeout(0)

        client.address = address
        client.data = []

        self.clients.append(client)

        self.handle_accept(client)

    def handle_accept(self, client):
        pass

    def handle_recv(self, client):
        raise NotImplementedError()

    def close(self, client=None):
        # if has one client and not server is a client socket
        if self.server == None and len(self.clients) == 1:
            client = self.clients[0]

        self.handle_close(client)

        try:
            self.clients.remove(client)
        except ValueError:
            pass

        try:
            client.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        client.close()

    def handle_close(self, client):
        pass

    def send(self, client):
        sended = client.send(client.data[0])

        if sended == 0:
            raise SocketDisconnected()
        elif sended < len(client.data[0]):
            client.data[0] = client.data[0][sended:]
        else:
            client.data.pop(0)

        self.handle_send(client)
    
    def handle_send(self, client):
        pass

    def step(self):
        write = [i for i in self.clients if len(i.data) > 0]

        read, write, error = select.select(
                self.clients, 
                write, 
                self.clients, 
                self.timeout)

        for r in read:
            if r == self.server:
                self.accept(r)
            else:
                try:
                    self.handle_recv(r)
                except SocketDisconnected:
                    self.close(r)
                    return

        for w in write:
            try:
                self.send(w)
            except SocketDisconnected:
                self.close(w)
                return

        for e in error:
            self.close(e)
            return

        self.handle_step(self.clients)

    def handle_step(self, clients):
        pass

    def forever(self):
        while (self.server != None 
                or (self.server == None and len(self.clients) == 1)):
            self.step()

    def stop(self):
        self.handle_stop(self.clients)

        write = [i for i in self.clients if len(i.data) > 0]

        while len(write) > 0:
            read, write, error = select.select(
                    self.clients, 
                    write, 
                    self.clients, 
                    self.timeout)

            for w in write:
                try:
                    self.send(w)
                except SocketDisconnected:
                    self.close(w)

            write = [i for i in self.clients if len(i.data) > 0]

        self.close(self.server)

    def handle_stop(self, clients):
        pass
