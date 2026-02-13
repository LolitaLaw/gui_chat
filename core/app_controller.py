# core/app_controller.py
from PyQt6.QtCore import QObject, pyqtSlot, QTimer
from config.settings import CONTACTS, PORT
from data.store import DataStore, Contact
from data.network import NetworkService
from .cmd_processor import CmdProcessor
import uuid


class AppController(QObject):
    def __init__(self):
        super().__init__()
        self.store = DataStore()
        self.store.load_contacts(CONTACTS)
        self.cmd_processor = CmdProcessor(self._on_cmd_output)
        self.network = NetworkService(PORT, self._on_network_message)

        self.ui = None
        self.current_view = None
        self.target_contact = None
        self.is_dark_mode = True  # [功能] 记录主题状态

    def bind_ui(self, main_window):
        self.ui = main_window

    def start(self):
        if self.network.start() is True:
            self.switch_mode("normal")  # 默认进 Normal 看效果
        else:
            print("Error: Port occupied.")

    def switch_mode(self, mode_name):
        self.ui.set_mode_view(mode_name)
        self.current_view = self.ui.current_view

        if mode_name == "cmd":
            self._bind_cmd_view()
        elif mode_name == "normal":
            self._bind_normal_view()
        elif mode_name == "wps":
            self._bind_wps_view()

    # --- 绑定 Normal 视图 ---
    def _bind_normal_view(self):
        try:
            v = self.current_view
            # 1. 断开可能存在的旧连接 (防止重复绑定)
            disconnect_list = [
                v.contact_selected,
                v.message_sent,
                v.contact_added,
                v.contact_deleted,
                v.contact_modified,
                v.theme_toggled,  # 加入新信号
            ]
            for signal in disconnect_list:
                try:
                    signal.disconnect()
                except:
                    pass

            # 连接新信号
            v.contact_selected.connect(self._on_contact_selected)   # 连接选中联系人信号
            v.message_sent.connect(self._on_normal_msg_sent)        # 连接发送消息信号
            v.contact_added.connect(self._on_contact_added)         # 连接联系人添加信号
            v.contact_deleted.connect(self._on_contact_deleted)     # 连接联系人删除信号
            v.contact_modified.connect(self._on_contact_modified)   # 连接联系人修改信号
            v.theme_toggled.connect(self.toggle_color_scheme)       # 连接主题切换信号
            # 初始化状态
            v.update_contacts(self.store.contacts)
            v.update_theme(self.is_dark_mode)  # [功能] 应用当前主题

            if self.target_contact:
                history = self.store.get_history(self.target_contact.ip)
                v.display_history(history, self.target_contact.name)
        except Exception as e:
            print(f"Bind Normal Error: {e}")

    # --- 业务逻辑槽函数 ---

    @pyqtSlot(str, str)
    def _on_contact_added(self, name, ip):
        # 创建新联系人并存入
        new_c = Contact(id=str(uuid.uuid4()), name=name, ip=ip, port=9999)
        self.store.contacts.append(new_c)
        # 刷新界面
        self.current_view.update_contacts(self.store.contacts)

    @pyqtSlot(object)
    def _on_contact_deleted(self, contact):
        if contact in self.store.contacts:
            self.store.contacts.remove(contact)
        # 如果删的是当前聊天的人，清空
        if self.target_contact == contact:
            self.target_contact = None
            # 注意：NormalView现在用stack切换，这里不需要手动清空label，切到page0即可
            pass 
        self.current_view.update_contacts(self.store.contacts)

    @pyqtSlot(object, str)
    def _on_contact_modified(self, contact, new_name):
        contact.name = new_name
        self.current_view.update_contacts(self.store.contacts)
        if self.target_contact == contact:
            self.current_view.header_label.setText(new_name)

    # [功能] 切换主题的逻辑
    def toggle_color_scheme(self):
        self.is_dark_mode = not self.is_dark_mode
        # 通知当前视图更新
        if hasattr(self.current_view, "update_theme"):
            self.current_view.update_theme(self.is_dark_mode)
        # 也可以通知 MainWindow 更新标题栏颜色（如果需要）

    # --- 发送/接收逻辑 (保持之前的修复) ---
    def _send_to_network(self, content, ip, port):
        self.network.send(content, ip, port)
        return self.store.add_message(ip, content, "self")

    @pyqtSlot(object)
    def _on_contact_selected(self, contact):
        self.target_contact = contact
        history = self.store.get_history(contact.ip)
        self.current_view.display_history(history, contact.name)

    @pyqtSlot(str)
    def _on_normal_msg_sent(self, content):
        if not self.target_contact: return
        msg = self._send_to_network(content, self.target_contact.ip, self.target_contact.port)
        self.current_view.append_message(msg)
        
        # [新增] Loop 回发功能
        # 如果是 loopback，模拟延迟自动回复
        if self.target_contact.id == 'loopback' or self.target_contact.name.lower() == 'loopback':
            QTimer.singleShot(500, lambda: self._handle_incoming(f"Echo: {content}", self.target_contact.ip))

    def _on_network_message(self, content, ip):
        QTimer.singleShot(0, lambda: self._handle_incoming(content, ip))

    def _handle_incoming(self, content, ip):
        msg = self.store.add_message(ip, content, "peer")
        if self.ui.current_mode == "normal":
            if self.target_contact and self.target_contact.ip == ip:
                self.current_view.append_message(msg)
        elif self.ui.current_mode == "cmd":
            self.current_view.append_text(f"\n[Recv from {ip}]: {content}\n{self.cmd_processor.current_path}>", "info")

    def _bind_cmd_view(self):
        try:
            self.current_view.command_submitted.connect(self._handle_cmd_input)
            self.current_view.append_text(f"{self.cmd_processor.current_path}>", "info")
        except: pass
    
    def _bind_wps_view(self): pass

    def _handle_cmd_input(self, cmd):
        handled = self.cmd_processor.process(cmd)
        if not handled:
            if self.target_contact:
                self._send_to_network(cmd, self.target_contact.ip, self.target_contact.port)
                self.current_view.append_text(f"[Sent to {self.target_contact.name}]: {cmd}\n{self.cmd_processor.current_path}>", "info")
            else:
                self.current_view.append_text(f"'{cmd}' is not recognized.\n{self.cmd_processor.current_path}>", "error")

    def _on_cmd_output(self, text, tag):
        if self.ui.current_mode == "cmd" and self.current_view:
            if tag == "clear": self.current_view.clear_screen()
            else: self.current_view.append_text(text, tag)