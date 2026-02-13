# network.py
# (模型层/网络层)：封装 UDP 通信逻辑
# 只管发和收，不管界面怎么显示
import socket
import threading


class CommManager:
    def __init__(self, port, on_message_received):
        self.port = port
        self.on_message_received = on_message_received  # 回调函数
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = False

    def start(self):
        try:
            self.sock.bind(("0.0.0.0", self.port))
            self.running = True
            threading.Thread(target=self._receive_loop, daemon=True).start()
            return True
        except Exception as e:
            return str(e)

    def _receive_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                msg = data.decode("utf-8")
                # 通过回调通知主程序，将 data 和 sender_ip 传出去
                if self.on_message_received:
                    self.on_message_received(msg, addr[0])
            except:
                break

    def send(self, msg, target_addr):
        try:
            self.sock.sendto(msg.encode("utf-8"), target_addr)
        except Exception as e:
            print(f"Send Error: {e}")

    def close(self):
        self.running = False
        self.sock.close()
