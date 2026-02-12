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
        self.target_addr = ("127.0.0.1", PORT)
        # self.target_name = "Loopback"
        self.target_name = None  # 初始无选中联系人

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
        self.set_app_window()

    # 强制显示任务栏图标 (Windows API)
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

            # 重新刷新窗口状态以生效
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

        # 切换模式时，同时切换图标
        self._update_app_icon(mode)

        if mode == "cmd":
            self.root.overrideredirect(False)
            self.root.title(THEMES["cmd"]["title"])
            self.root.configure(bg=THEMES["cmd"]["bg_root"])
            self.current_view = CmdView(self.root, self)
            self._log_to_cmd_view(f"{self.current_path}>", no_newline=True)

        elif mode == "normal":
            self.root.overrideredirect(False)
            self.root.title(THEMES["normal"]["title"])
            self.root.configure(bg=THEMES["normal"]["bg_root"])
            self.current_view = NormalView(self.root, self)

        elif mode == "wps":
            self.root.overrideredirect(True)
            self.root.configure(bg=THEMES["wps"]["bg_root"])
            self.current_view = WpsView(self.root, self)
            # 切换到 WPS 模式后强制刷新窗口状态
            self.root.after(10, self.set_app_window)

        self.current_view.pack(fill="both", expand=True)

    # 图标更新方法
    def _update_app_icon(self, mode):
        icon_path = ICONS.get(mode)
        # 检查文件是否存在
        if icon_path and os.path.exists(icon_path):
            try:
                # 如果是 .ico 文件 (Windows 原生图标)
                if icon_path.endswith(".ico"):
                    self.root.iconbitmap(icon_path)
                # 如果是 .png/.gif 文件
                else:
                    img = tk.PhotoImage(file=icon_path)
                    self.root.iconphoto(True, img)
            except Exception as e:
                print(f"Load icon failed: {e}")

    # ==== 主题切换 ====
    def toggle_color_scheme(self):
        self.is_dark_mode = not self.is_dark_mode
        # 重新加载当前视图以应用新主题
        self.switch_mode(self.current_mode)

    # ==== 联系人管理 ====
    def set_target(self, contact):
        self.target_addr = (contact["ip"], contact["port"])
        self.target_name = contact["name"]

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

    # 修改联系人
    def modify_contact(self):
        # 获取当前选中的联系人索引
        if not hasattr(self.current_view, "contact_list"):
            return
        try:
            idx = self.current_view.contact_list.curselection()[0]
            contact = self.displayed_contacts[idx]

            new_name = simpledialog.askstring(
                "修改备注", "输入新名称:", initialvalue=contact["name"]
            )
            if new_name:
                contact["name"] = new_name
                # 更新所有联系人列表引用 (这里简化，直接修改原列表)
                # 实际应用中建议通过 ID 查找
                for c in CONTACTS:
                    if c["id"] == contact["id"]:
                        c["name"] = new_name
                self.current_view.refresh_contacts()
        except IndexError:
            pass

    # 删除联系人
    def delete_contact(self):
        if not hasattr(self.current_view, "contact_list"):
            return
        try:
            idx = self.current_view.contact_list.curselection()[0]
            contact = self.displayed_contacts[idx]
            if messagebox.askyesno("确认", f"确定删除 {contact['name']} 吗?"):
                if self.target_name == contact["name"]:
                    self.target_name = None
                    if hasattr(self.current_view, "reset_chat_area"):
                        self.current_view.reset_chat_area()

                self.displayed_contacts.pop(idx)
                # 同步删除 CONTACTS 全局列表
                for i, c in enumerate(CONTACTS):
                    if c["id"] == contact["id"]:
                        CONTACTS.pop(i)
                        break
                self.current_view.refresh_contacts()
        except IndexError:
            pass

    # 实现联系人搜索过滤逻辑
    def filter_contacts(self, query):
        query = query.lower().strip()
        if not query:
            self.displayed_contacts = CONTACTS[:]
        else:
            self.displayed_contacts = [
                c for c in CONTACTS if query in c["name"].lower() or query in c["ip"]
            ]

        # # 如果当前是正常模式，刷新列表
        # if isinstance(self.current_view, NormalView):
        #     self.current_view.refresh_contacts()
        if hasattr(self.current_view, "refresh_contacts"):
            self.current_view.refresh_contacts()

    # --- 消息处理 ---
    def on_message_received(self, msg, ip):
        self.root.after(0, lambda: self._distribute_msg(msg, ip))

    def _distribute_msg(self, msg, ip):
        name = next((c["name"] for c in CONTACTS if c["ip"] == ip), ip)
        time_str = datetime.now().strftime("%H:%M")  # 获取当前时间
        if self.current_mode == "cmd":
            self.current_view.log(f"Reply from {ip}: {msg}", "cmd_text")
            # 消息插入后，必须重新补一个提示符，因为看起来像是终端被打断了
            if self.in_python_mode:
                self._log_to_cmd_view(">>> ", no_newline=True)
            else:
                self._log_to_cmd_view(f"{self.current_path}>", no_newline=True)

        elif self.current_mode == "normal":
            self.current_view.log(f"[{name}] [{time_str}]\n{msg}\n", "normal_peer")
        elif self.current_mode == "wps":
            self.current_view.log(f"[{name}] [{time_str}]: {msg}\n", "ai_peer")

    def handle_chat_send(self, msg, tag_self):
        if not msg:
            return
        self.network.send(msg, self.target_addr)
        time_str = datetime.now().strftime("%H:%M")  # 获取发送时间

        if self.current_mode == "normal":
            # 正常模式显示自己的时间
            self.current_view.log(f"{msg} :[{time_str}]\n", tag_self)
        else:
            self.current_view.log(f"{msg}\n", tag_self)

    # --- CMD 专属逻辑 ---
    def handle_cmd_input(self, msg):
        # 1. 移除之前的 self._log_to_cmd_view(f"{msg}\n") 回显
        # 因为现在 View 层已经直接在 Text 控件里显示用户打的字了

        # Python 模式
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
                self._log_to_cmd_view(
                    "... " if is_incomplete else ">>> ", no_newline=True
                )
            except Exception as e:
                self._log_to_cmd_view(str(e) + "\n>>> ", "cmd_err", no_newline=True)
            finally:
                sys.stdout = old_out
            return

        # Windows 命令
        if msg.lower().startswith("cd "):
            try:
                os.chdir(msg[3:].strip())
                self.current_path = os.getcwd()
            except:
                self._log_to_cmd_view("Path not found.\n", "cmd_err")
        elif msg.lower() in ["cls", "clear"]:
            self.current_view.clear()
        else:
            # 简单判断是否是系统命令
            whitelist = ["dir", "ipconfig", "ping", "ver", "whoami", "echo"]
            if msg.split()[0].lower() in whitelist:
                try:
                    res = subprocess.run(
                        msg, shell=True, capture_output=True, text=True, encoding="gbk"
                    )
                    if res.stdout:
                        self._log_to_cmd_view(res.stdout)
                    if res.stderr:
                        self._log_to_cmd_view(res.stderr, "cmd_err")
                except Exception as e:
                    self._log_to_cmd_view(str(e) + "\n", "cmd_err")
            else:
                # 不是命令，当作聊天发送
                self.network.send(msg, self.target_addr)
                # self.handle_chat_send(msg, "cmd_text")# 复用发送逻辑

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