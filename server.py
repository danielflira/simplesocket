from simplesocket import SimpleSocket, SocketDisconnected

class CharServer(SimpleSocket):
    def __init__(self, *args, **kwargs):
        self.create_server(*args, **kwargs)

    def handle_recv(self, client):
        char = client.recv(1)
        if len(char) == 0:
            raise SocketDisconnected()
        client.data.append(char)

    def handle_accept(self, client):
        client.data.append("123 testando".encode("utf8"))

    def handle_stop(self, clients):
        for client in clients:
            if client != self.server:
                client.data.append("adeus amiguinho".encode("utf8"))

def main():
    try:
        server = CharServer("localhost", 1234)
        server.forever()
    except KeyboardInterrupt:
        server.stop()

if __name__ == "__main__":
    main()
