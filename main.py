# main.py
import tkinter as tk
from tkinter import simpledialog, messagebox
import sys
import os
import code
import subprocess
from datetime import datetime

from settings import CONTACTS, PORT, THEMES, ICONS
from network import CommManager
from components import StdoutRedirector
from views import CmdView, NormalView, WpsView
import ctypes
from ctypes import windll


class UltimateChat:
    def __init__(self, root):
        self.root = root
        self.current_mode = None
        self.current_view = None
        self.is_dark_mode = True  # 默认为深色模式
        self.current_path = os.getcwd()

        self.displayed_contacts = CONTACTS[:]
        self.target_addr = None  # 初始不连接任何人
        self.target_name = None  # 初始无选中联系人
        self.target_ip = None  # 新增：用于索引聊天记录

        # === 核心：聊天记录存储 ===
        # 结构: { '192.168.1.20': [ {'type': 'self'/'peer', 'msg': '...', 'time': '...'}, ... ] }
        self.chat_history = {}

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
        # self.switch_mode("normal")
        self.switch_mode("cmd")
        self.set_app_window()

    def set_app_window(self):
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080

        try:
            hwnd = windll.user32.GetParent(self.root.winfo_id())
            style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = style & ~WS_EX_TOOLWINDOW
            style = style | WS_EX_APPWINDOW
            windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            self.root.wm_withdraw()
            self.root.after(10, lambda: self.root.wm_deiconify())
        except Exception as e:
            print(f"Force Taskbar Icon Failed: {e}")

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

        self._update_app_icon(mode)

        if mode == "cmd":
            self.root.overrideredirect(False)
            self.root.title(THEMES["cmd"]["title"])
            self.root.configure(bg=THEMES["cmd"]["bg_root"])
            self.current_view = CmdView(self.root, self)
            # self._log_to_cmd_view(f"{self.current_path}>", no_newline=True)
            if self.in_python_mode:
                self._log_to_cmd_view(">>> ", no_newline=True)
            else:
                self._log_to_cmd_view(f"{self.current_path}>", no_newline=True)

        elif mode == "normal":
            self.root.overrideredirect(False)
            self.root.title(THEMES["normal"]["title"])
            self.root.configure(bg=THEMES["normal"]["bg_root"])
            # 传递 is_dark_mode 给 NormalView
            self.current_view = NormalView(self.root, self, self.is_dark_mode)

        elif mode == "wps":
            self.root.overrideredirect(True)

            # [关键修复] 获取正确的 WPS 主题配置
            scheme_key = "dark" if self.is_dark_mode else "light"
            wps_bg = THEMES["wps"][scheme_key]["bg_root"]

            self.root.configure(bg=wps_bg)

            # 传递 is_dark_mode 给 WpsView
            self.current_view = WpsView(self.root, self, self.is_dark_mode)
            self.root.after(10, self.set_app_window)

        self.current_view.pack(fill="both", expand=True)
        # 切换模式后，立即加载当前选中联系人的历史记录
        self.load_history_to_view()

    def _update_app_icon(self, mode):
        icon_path = ICONS.get(mode)
        if icon_path and os.path.exists(icon_path):
            try:
                if icon_path.endswith(".ico"):
                    self.root.iconbitmap(icon_path)
                else:
                    img = tk.PhotoImage(file=icon_path)
                    self.root.iconphoto(True, img)
            except Exception as e:
                print(f"Load icon failed: {e}")

    def toggle_color_scheme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.switch_mode(self.current_mode)

    # ================= 联系人管理 =================
    def set_target(self, contact):
        self.target_addr = (contact["ip"], contact["port"])
        self.target_name = contact["name"]
        self.target_ip = contact["ip"]
        # 切换联系人时，加载该人的历史记录
        self.load_history_to_view()

    def load_history_to_view(self):
        # 将内存中的聊天记录渲染到当前视图
        # 如果没有选中联系人，且在 Normal 模式，显示空状态
        if not self.target_ip:
            if hasattr(self.current_view, "toggle_empty_state"):
                self.current_view.toggle_empty_state(is_empty=True)
            return

        # 获取记录
        records = self.chat_history.get(self.target_ip, [])

        # 通知视图层渲染
        if hasattr(self.current_view, "render_history"):
            self.current_view.render_history(records, self.target_name)

    def add_new_contact(self):
        name = simpledialog.askstring("Add", "Name:")
        ip = simpledialog.askstring("Add", "IP:")
        if name and ip:
            self.displayed_contacts.append(
                {
                    "id": str(len(self.displayed_contacts)),
                    "name": name,
                    "ip": ip,
                    "port": 9999,
                }
            )

    def modify_contact(self):
        if not hasattr(self.current_view, "contact_list"):
            return
        try:
            idx = self.current_view.contact_list.curselection()[0]
            contact = self.displayed_contacts[idx]

            new_name = simpledialog.askstring("修改备注", "输入新名称:", initialvalue=contact["name"])
            if new_name:
                contact["name"] = new_name
                for c in CONTACTS:
                    if c["id"] == contact["id"]:
                        c["name"] = new_name
                self.current_view.refresh_contacts()
        except IndexError:
            pass

    def delete_contact(self):
        if not hasattr(self.current_view, "contact_list"):
            return
        try:
            idx = self.current_view.contact_list.curselection()[0]
            contact = self.displayed_contacts[idx]
            if messagebox.askyesno("确认", f"确定删除 {contact['name']} 吗?"):
                if self.target_name == contact["name"]:
                    self.target_name = None
                    self.target_ip = None
                    self.target_addr = None
                    if hasattr(self.current_view, "reset_chat_area"):
                        self.current_view.reset_chat_area()
                    self.load_history_to_view()

                self.displayed_contacts.pop(idx)
                for i, c in enumerate(CONTACTS):
                    if c["id"] == contact["id"]:
                        CONTACTS.pop(i)
                        break
                self.current_view.refresh_contacts()
        except IndexError:
            pass

    def filter_contacts(self, query):
        query = query.lower().strip()
        if not query:
            self.displayed_contacts = CONTACTS[:]
        else:
            self.displayed_contacts = [c for c in CONTACTS if query in c["name"].lower() or query in c["ip"]]

        if hasattr(self.current_view, "refresh_contacts"):
            self.current_view.refresh_contacts()

    def on_message_received(self, msg, ip):
        self.root.after(0, lambda: self._distribute_msg(msg, ip))

    def _process_received_msg(self, msg, ip):
        # 1. 存入历史记录
        if ip not in self.chat_history:
            self.chat_history[ip] = []

        time_str = datetime.now().strftime("%H:%M")
        record = {"type": "peer", "msg": msg, "time": time_str}
        self.chat_history[ip].append(record)

        # 2. 如果当前正在看这个人（或者是CMD模式），更新UI
        if self.current_mode == "cmd" or self.target_ip == ip:
            if hasattr(self.current_view, "append_msg"):
                # 查找发送者名字
                sender_name = next((c["name"] for c in CONTACTS if c["ip"] == ip), ip)
                self.current_view.append_msg(record, sender_name)

    def _distribute_msg(self, msg, ip):
        name = next((c["name"] for c in CONTACTS if c["ip"] == ip), ip)
        time_str = datetime.now().strftime("%H:%M")

        if self.current_mode == "cmd":
            self.current_view.log(f"Reply from {ip}: {msg}", "cmd_text")
            if self.in_python_mode:
                self._log_to_cmd_view(">>> ", no_newline=True)
            else:
                self._log_to_cmd_view(f"{self.current_path}>", no_newline=True)

        elif self.current_mode == "normal":
            self.current_view.log(f"[{name}] [{time_str}]\n{msg}\n", "normal_peer")
        elif self.current_mode == "wps":
            self.current_view.log(f"[{name}] [{time_str}]: {msg}\n", "ai_peer")

    def handle_chat_send(self, msg, tag_self):
        if not msg or not self.target_addr:
            return
        self.network.send(msg, self.target_addr)  # 先发后存，确保网络异常时不丢记录
        # 存入历史记录
        target_ip = self.target_addr[0]
        if target_ip not in self.chat_history:
            self.chat_history[target_ip] = []
        time_str = datetime.now().strftime("%H:%M")
        record = {"type": "self", "msg": msg, "time": time_str}
        self.chat_history[target_ip].append(record)

        # 更新 UI
        if hasattr(self.current_view, "append_msg"):
            self.current_view.append_msg(record, "我")
        """
        if self.current_mode == "normal":
            self.current_view.log(f"{msg} :[{time_str}]\n", tag_self)
        else:
            self.current_view.log(f"{msg}\n", tag_self)
        """

    def handle_cmd_input(self, msg):
        if not self.in_python_mode and msg.lower() == "python":
            self.in_python_mode = True
            self._log_to_cmd_view(f"Python {sys.version.split()[0]} on win32\n")
            self._log_to_cmd_view(">>> ", no_newline=True)
            return

        if self.in_python_mode:
            if msg.lower() in ["exit()", "quit()"]:
                self.in_python_mode = False
                self._log_to_cmd_view(f"\n{self.current_path}>", no_newline=True)
                return
            old_out = sys.stdout
            try:
                sys.stdout = self.redirector
                is_incomplete = self.console.push(msg)
                self._log_to_cmd_view("... " if is_incomplete else ">>> ", no_newline=True)
            except Exception as e:
                self._log_to_cmd_view(str(e) + "\n>>> ", "cmd_err", no_newline=True)
            finally:
                sys.stdout = old_out
            return

        if msg.lower().startswith("cd "):
            try:
                os.chdir(msg[3:].strip())
                self.current_path = os.getcwd()
            except:
                self._log_to_cmd_view("Path not found.\n", "cmd_err")
        elif msg.lower() in ["cls", "clear"]:
            self.current_view.clear()
        else:
            whitelist = ["dir", "ipconfig", "ping", "ver", "whoami", "echo"]
            if msg.split()[0].lower() in whitelist:
                try:
                    res = subprocess.run(msg, shell=True, capture_output=True, text=True, encoding="gbk")
                    if res.stdout:
                        self._log_to_cmd_view(res.stdout)
                    if res.stderr:
                        self._log_to_cmd_view(res.stderr, "cmd_err")
                except Exception as e:
                    self._log_to_cmd_view(str(e) + "\n", "cmd_err")
            else:
                self.network.send(msg, self.target_addr)

        self._log_to_cmd_view(f"{self.current_path}>", no_newline=True)

    def _log_to_cmd_view(self, text, tag="cmd_text", no_newline=False):
        if isinstance(self.current_view, CmdView):
            self.current_view.log(text, tag, no_newline)

    def on_close(self):
        self.network.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = UltimateChat(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
