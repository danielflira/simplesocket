from simplesocket import SimpleSocket, SocketDisconnected

class CharClient(SimpleSocket):
    def __init__(self, *args, **kwargs):
        self.create_client(*args, **kwargs)

    def handle_recv(self, client):
        char = str(client.recv(1), "utf8")
        if len(char) == 0:
            raise SocketDisconnected()
        print(char, end="", flush=True)

def main():
    try:
        client = CharClient("localhost", 1234)
        client.forever()
    except SocketDisconnected:
        pass
    except KeyboardInterrupt:
        client.close()

if __name__ == "__main__":
    main()
