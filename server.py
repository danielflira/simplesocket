import socket
import select
import sys

class ClientDisconnected(Exception):
    pass

class Server:
    def __init__(self, address, port, backlog=1, timeout=0.1):
        self.timeout = timeout

        try:
            server = socket.create_server(
                    (address, port,), 
                    backlog=backlog, 
                    reuse_port=True)
        except AttributeError:
            server = socket.socket(
                    socket.AF_INET, 
                    socket.SOCK_STREAM)
            server.setsockopt(
                    socket.SOL_SOCKET, 
                    socket.SO_REUSEADDR, 
                    1)
            server.bind((address, port,))
            server.listen(backlog)

        server.settimeout(0)
        server.setblocking(0)

        self.server = server
        self.clients = [server]
        self.buffers = {}

        self.handle_init(server)

    def handle_init(self, server):
        pass

    def accept(self, server):
        client, address = server.accept()
        client.setblocking(0)
        client.settimeout(0)
        self.clients.append(client)

        self.handle_accept(client)

    def handle_accept(self, client):
        pass

    def handle_recv(self, client):
        raise NotImplementedError()

    def close(self, client):
        self.handle_close(client)

        try:
            self.clients.remove(client)
        except ValueError:
            pass

        if client in self.buffers:
            del(self.buffers[client])

        client.shutdown(socket.SHUT_RDWR)
        client.close()

    def handle_close(self, client):
        pass

    def send(self, client):
        buffers = self.buffers[client]
        try:
            sended = client.send(buffers[0])
            if sended == 0:
                raise ClientDisconnected()
            elif sended == len(buffers[0]):
                buffers.pop(0)
            else:
                buffers[0] = buffers[0][sended:]

            if len(self.buffers[client]) == 0:
                del(self.buffers[client])

            self.handle_send(client)
        except IndexError:
            del(self.buffers[client])
    
    def handle_send(self, client):
        pass

    def step(self):
        read, write, error = select.select(
                self.clients, 
                self.clients, 
                self.clients, 
                self.timeout)

        ignore = []

        for r in read:
            if r == self.server:
                self.accept(r)
            else:
                try:
                    self.handle_recv(r)
                except ClientDisconnected:
                    self.close(r)
                    ignore.append(r)

        for w in write:
            if not w in ignore:
                if w in self.buffers:
                    try:
                        self.send(w)
                    except ClientDisconnected:
                        self.close(w)
                        ignore.append(w)

        for e in error:
            if not e in ignore:
                self.close(e)

        self.handle_step(self.clients)

    def handle_step(self, clients):
        pass

    def forever(self):
        while True:
            self.step()

    def enqueue_send(self, client, data):
        try:
            self.buffers[client].append(data)
        except KeyError:
            self.buffers[client] = [data]

    def stop(self):
        self.handle_stop(self.clients)

        try:
            del(self.buffers[self.server])
        except KeyError:
            pass

        while len(self.buffers) > 0:
            read, write, error = select.select(
                    self.clients, 
                    self.clients, 
                    self.clients, 
                    self.timeout)

            for w in write:
                if w in self.buffers:
                    try:
                        self.send(w)
                    except ClientDisconnected:
                        self.close(w)
                        ignore.append(w)

        self.close(self.server)

    def handle_stop(self, clients):
        pass


class CharServer(Server):
    def handle_recv(self, client):
        char = client.recv(1)
        if len(char) == 0:
            raise ClientDisconnected()
        self.enqueue_send(client, char)

    def handle_accept(self, client):
        self.enqueue_send(client, '123testando'.encode("utf8"))

    def handle_stop(self, clients):
        for client in clients:
            if client != self.server:
                self.enqueue_send(client, "adeus amiguinho".encode("utf8"))

def main():
    try:
        server = CharServer("localhost", 1234)
        server.forever()
    except KeyboardInterrupt:
        server.stop()

main()
