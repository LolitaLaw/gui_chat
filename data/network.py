import socket
import threading

class NetworkService:
    def __init__(self, port, on_message_received):
        self.port = port
        self.callback = on_message_received
        self.running = False
        self._socket = None

    def start(self):
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.bind(("0.0.0.0", self.port))
            self.running = True
            threading.Thread(target=self._listen, daemon=True).start()
            return True
        except Exception as e:
            return str(e)

    def _listen(self):
        while self.running:
            try:
                data, addr = self._socket.recvfrom(4096)
                self.callback(data.decode('utf-8'), addr[0])
            except: pass

    def send(self, msg: str, ip: str, port: int):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(msg.encode('utf-8'), (ip, port))
        except Exception as e:
            print(f"Send Error: {e}")

    def close(self):
        self.running = False
        if self._socket: self._socket.close()