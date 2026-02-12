# main.py
import tkinter as tk
from tkinter import simpledialog, messagebox
import sys
import os
import code
import subprocess

from settings import CONTACTS, PORT, THEMES
from network import CommManager
from components import StdoutRedirector
from views import CmdView, NormalView, WpsView

class UltimateChat:
    def __init__(self, root):
        self.root = root
        self.current_mode = None
        self.current_view = None
        self.current_path = os.getcwd()
        
        self.displayed_contacts = CONTACTS[:]
        self.target_addr = ("127.0.0.1", PORT)
        self.target_name = "Loopback"

        # Python 解释器状态
        self.in_python_mode = False
        self.python_locals = {}
        self.console = code.InteractiveConsole(self.python_locals)
        self.redirector = StdoutRedirector(self._log_to_cmd_view)

        # 启动网络
        self.network = CommManager(PORT, self.on_message_received)
        err = self.network.start()
        if err is not True:
            messagebox.showerror("Network Error", f"Port {PORT} failed: {err}")
            sys.exit(1)

        self.setup_window()
        self.switch_mode("cmd")

    def setup_window(self):
        self.root.geometry("900x600")
        self.root.bind("<F10>", lambda e: self.switch_mode("cmd"))
        self.root.bind("<F11>", lambda e: self.switch_mode("wps"))
        self.root.bind("<F12>", lambda e: self.switch_mode("normal"))
        self.root.bind("<Escape>", lambda e: self.root.iconify())

    def switch_mode(self, mode):
        self.current_mode = mode
        if self.current_view:
            self.current_view.destroy()
        
        if mode == "cmd":
            self.root.overrideredirect(False)
            self.root.title(THEMES["cmd"]["title"])
            self.root.configure(bg=THEMES["cmd"]["bg_root"])
            self.current_view = CmdView(self.root, self)
            self._log_to_cmd_view(f"{self.current_path}>")
            
        elif mode == "normal":
            self.root.overrideredirect(False)
            self.root.title(THEMES["normal"]["title"])
            self.root.configure(bg=THEMES["normal"]["bg_root"])
            self.current_view = NormalView(self.root, self)
            
        elif mode == "wps":
            self.root.overrideredirect(True)
            self.root.configure(bg=THEMES["wps"]["bg_root"])
            self.current_view = WpsView(self.root, self)
        
        self.current_view.pack(fill="both", expand=True)

    def set_target(self, contact):
        self.target_addr = (contact['ip'], contact['port'])
        self.target_name = contact['name']

    def add_new_contact(self):
        name = simpledialog.askstring("Add", "Name:")
        ip = simpledialog.askstring("Add", "IP:")
        if name and ip:
            self.displayed_contacts.append({"id": str(len(self.displayed_contacts)), "name": name, "ip": ip, "port": 9999})

    # --- 消息处理 ---
    def on_message_received(self, msg, ip):
        # 必须在主线程更新 UI
        self.root.after(0, lambda: self._distribute_msg(msg, ip))

    def _distribute_msg(self, msg, ip):
        name = next((c['name'] for c in CONTACTS if c['ip'] == ip), ip)
        
        if self.current_mode == "cmd":
            self.current_view.log(f"\nReply from {ip}: {msg}\n", "cmd_text")
            self.current_view.log(f"{self.current_path}>")
        elif self.current_mode == "normal":
            self.current_view.log(f"[{name}]\n{msg}\n", "normal_peer")
        elif self.current_mode == "wps":
            self.current_view.log(f"[{name}]: {msg}\n", "ai_peer")

    def handle_chat_send(self, msg, tag_self):
        if not msg: return
        self.network.send(msg, self.target_addr)
        self.current_view.log(f"{msg}\n", tag_self)

    # --- CMD 专属逻辑 ---
    def handle_cmd_input(self, msg):
        self._log_to_cmd_view(f"{msg}\n")
        
        # Python 模式
        if not self.in_python_mode and msg.lower() == "python":
            self.in_python_mode = True
            self._log_to_cmd_view(f"Python {sys.version.split()[0]} on win32\n>>> ")
            return

        if self.in_python_mode:
            if msg.lower() in ["exit()", "quit()"]:
                self.in_python_mode = False
                self._log_to_cmd_view(f"\n{self.current_path}>")
                return
            old_out = sys.stdout
            try:
                sys.stdout = self.redirector
                is_incomplete = self.console.push(msg)
                self._log_to_cmd_view("... " if is_incomplete else ">>> ")
            except Exception as e: self._log_to_cmd_view(str(e) + "\n", "cmd_err")
            finally: sys.stdout = old_out
            return

        # Windows 命令
        if msg.lower().startswith("cd "):
            try: os.chdir(msg[3:].strip()); self.current_path = os.getcwd()
            except: self._log_to_cmd_view("Path not found.\n", "cmd_err")
        elif msg.lower() in ["cls", "clear"]:
            self.current_view.clear()
        else:
            # 简单判断是否是系统命令
            whitelist = ['dir', 'ipconfig', 'ping', 'ver', 'whoami', 'echo']
            if msg.split()[0].lower() in whitelist:
                try:
                    res = subprocess.run(msg, shell=True, capture_output=True, text=True, encoding='gbk')
                    if res.stdout: self._log_to_cmd_view(res.stdout)
                    if res.stderr: self._log_to_cmd_view(res.stderr, "cmd_err")
                except Exception as e: self._log_to_cmd_view(str(e) + "\n", "cmd_err")
            else:
                # 不是命令，当作聊天发送
                self.network.send(msg, self.target_addr)
        
        self._log_to_cmd_view(f"{self.current_path}>")

    def _log_to_cmd_view(self, text, tag="cmd_text"):
        if isinstance(self.current_view, CmdView):
            self.current_view.log(text, tag)

    def on_close(self):
        self.network.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    try: 
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    app = UltimateChat(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()