# core/app_controller.py
from PyQt6.QtCore import QObject, pyqtSlot, QTimer, Qt
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
        self.is_dark_mode = True

        # [核心修复1] 记录上一个聊天对象，防止盲发和多余提示
        self._last_cmd_target = None

        # [核心修复：绝杀重复绑定的集合]
        # 记录哪些视图已经绑定过信号，绑定过的绝对不再绑第二次！
        self._bound_views = set()

    def bind_ui(self, main_window):
        self.ui = main_window

    def start(self):
        if self.network.start() is True:
            # self.switch_mode("normal")  # 默认进 Normal 看效果
            self.switch_mode("cmd") 
        else:
            print("Error: Port occupied.")

    def switch_mode(self, mode_name):
        # 【核心防御机制】如果当前已经是该模式，直接拦截！防止狂按快捷键产生Bug
        if self.ui and self.ui.current_mode == mode_name:
            return

        self.ui.set_mode_view(mode_name)
        self.current_view = self.ui.current_view

        if mode_name == "cmd":
            self._bind_cmd_view()
        elif mode_name == "normal":
            self._bind_normal_view()
        elif mode_name == "wps":
            self._bind_wps_view()

        def debug_print_size():
            if self.current_view and self.ui:
                view_w = self.current_view.width()
                view_h = self.current_view.height()
                win_w = self.ui.width()
                win_h = self.ui.height()
                print(
                    f"[Debug] 模式 '{mode_name}' 加载完毕 | 内部界面大小: {view_w} x {view_h} | 外层窗口大小: {win_w} x {win_h}"
                )

        QTimer.singleShot(100, debug_print_size)
        # QTimer.singleShot(100, lambda: print(f"[Debug] 已切换至 {mode_name} 模式，当前窗口大小: {self.ui.width()} x {self.ui.height()}"))
    # ==========================================
    # 模式绑定与数据同步
    # ==========================================

    def _bind_cmd_view(self):
        try:
            v = self.current_view
            # [修复点] 如果这个视图没有被绑定过，才进行绑定
            if v not in self._bound_views:
                v.command_submitted.connect(self._handle_cmd_input)
                self._bound_views.add(v)

            # 获取当前终端内已有的所有文本
            current_text = v.console.toPlainText()
            prompt = f"{self.cmd_processor.current_path}>"

            # [修复点] 判断聊天目标是否发生了改变
            if self.target_contact != self._last_cmd_target:
                self._last_cmd_target = self.target_contact

                # 为了排版美观，如果当前终端最后没有换行符，补一个换行
                prefix = "\n" if current_text and not current_text.endswith("\n") else ""

                if self.target_contact:
                    v.append_text(f"{prefix}[System] Chat Target: {self.target_contact.name} ({self.target_contact.ip})\n{prompt}", "info")
                    # v.append_text(f"\n[System] Current Chat Target: {self.target_contact.name} ({self.target_contact.ip}:{self.target_contact.port})\n{self.cmd_processor.current_path}>", "info")
                else:
                    v.append_text(f"{prefix}[System] No Chat Target Selected. Select in Normal Mode.\n{prompt}", "error")

            # 优化点 2: 目标没变，但如果终端是空的（比如程序刚启动，或者用户输入了 cls 清屏）
            elif not current_text.strip():
                # 只有屏幕是空的时候才打印初始提示符，解决切来切去满屏提示符的 Bug
                v.append_text(prompt, "info")

        except Exception as e: 
            print(f"Bind CMD Error: {e}")

    def _bind_normal_view(self):
        try:
            v = self.current_view
            # 使用 _bound_views 防重复绑定
            if v not in self._bound_views:
                v.contact_selected.connect(self._on_contact_selected)
                v.message_sent.connect(self._on_normal_msg_sent)
                v.contact_added.connect(self._on_contact_added)
                v.contact_deleted.connect(self._on_contact_deleted)
                v.contact_modified.connect(self._on_contact_modified)
                v.theme_toggled.connect(self.toggle_color_scheme)
                v.contact_unselected.connect(self._on_contact_unselected)# 监听取消选中信号
                self._bound_views.add(v)

            # 初始化状态
            v.update_contacts(self.store.contacts)
            v.update_theme(self.is_dark_mode)

            # [同步优化 2] 切回 Normal 时，强制从底层 Store 重新拉取历史记录
            # 这样在 CMD 里发送/接收的消息就会变成漂亮的圆角气泡显示出来
            if self.target_contact:
                history = self.store.get_history(self.target_contact.ip)
                v.display_history(history, self.target_contact.name)
        except Exception as e:
            print(f"Bind Normal Error: {e}")

    def _bind_wps_view(self):
        try:
            v = self.current_view
            if v not in self._bound_views:
                v.message_sent.connect(self._on_wps_msg_sent)
                v.window_minimized.connect(self.ui.showMinimized)
                v.window_closed.connect(self.ui.close)
                self._bound_views.add(v)

            if self.target_contact:
                history = self.store.get_history(self.target_contact.ip)
                v.display_history(history, self.target_contact.name)
            # else:
            #     # WPS 模式如果没有目标，默认选第一个或者显示空
            #     # 这里为了体验，如果没有选中人，默认选中第一个
            #     if self.store.contacts:
            #         self.target_contact = self.store.contacts[0]
            #         history = self.store.get_history(self.target_contact.ip)
            #         v.display_history(history, self.target_contact.name)
        except Exception as e:
            print(f"Bind WPS Error: {e}")

    @pyqtSlot(str)
    def _on_wps_msg_sent(self, content):
        """WPS 模式下的发送逻辑"""
        # 复用 Normal 模式的发送逻辑，或者单独处理
        if not self.target_contact: return

        # 发送并存储
        msg = self._send_to_network(content, self.target_contact.ip, self.target_contact.port)

        # 更新界面
        self.current_view.append_message(msg)

        # Loop 回发模拟
        if self.target_contact.id == 'loopback' or self.target_contact.name.lower() == 'loopback':
            QTimer.singleShot(500, lambda: self._handle_incoming(f"AI Response: {content}", self.target_contact.ip))

    # --- 其他绑定保持不变 ---
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
            print(f"Bind CMD Error: {e}")

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
            self._last_cmd_target = None
            if hasattr(self.current_view, "header_label"):
                self.current_view.header_label.setText("未选择联系人") # 待注释
        self.current_view.update_contacts(self.store.contacts)

    @pyqtSlot()
    def _on_contact_unselected(self):
        """处理正常模式下点击返回 / 双击联系人的逻辑"""
        self.target_contact = None
        self._last_cmd_target = None
        # 如果视图还有头部的 label，清空它备用
        if hasattr(self.current_view, "header_label"):
            self.current_view.header_label.setText("")

    @pyqtSlot(object, str)
    def _on_contact_modified(self, contact, new_name):
        contact.name = new_name
        self.current_view.update_contacts(self.store.contacts)
        if self.target_contact == contact:
            if hasattr(self.current_view, 'header_label'):
                self.current_view.header_label.setText(new_name)

    # [功能] 切换主题的逻辑
    def toggle_color_scheme(self):
        self.is_dark_mode = not self.is_dark_mode
        if hasattr(self.current_view, 'update_theme'):
            self.current_view.update_theme(self.is_dark_mode)
        # 也可以通知 MainWindow 更新标题栏颜色（如果需要）

    # ==========================================
    # 网络与消息逻辑
    # ==========================================

    def _send_to_network(self, content, ip, port):
        self.network.send(content, ip, port)
        # 统一由 Store 接管数据存储，确保无论在哪个视图发消息，数据都一致
        return self.store.add_message(ip, content, "self")

    @pyqtSlot(object)
    def _on_contact_selected(self, contact):
        self.target_contact = contact
        history = self.store.get_history(contact.ip)
        if hasattr(self.current_view, 'display_history'):
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

    @pyqtSlot(str)
    def _on_wps_msg_sent(self, content):
        if not self.target_contact: return
        msg = self._send_to_network(content, self.target_contact.ip, self.target_contact.port)
        self.current_view.append_message(msg)

        if self.target_contact.id == 'loopback' or self.target_contact.name.lower() == 'loopback':
            QTimer.singleShot(500, lambda: self._handle_incoming(f"AI Response: {content}", self.target_contact.ip))

    def _on_network_message(self, content, ip):
        QTimer.singleShot(0, lambda: self._handle_incoming(content, ip))

    def _handle_incoming(self, content, ip):
        # 收到消息，直接入库
        msg = self.store.add_message(ip, content, "peer")

        # [同步优化 3] 查找发信人姓名，让 CMD 模式不再只显示冷冰冰的 IP
        contact = self.store.get_contact_by_ip(ip)
        sender_name = contact.name if contact else "Unknown"

        if self.ui.current_mode in ["normal", "wps"]:
            if self.target_contact and self.target_contact.ip == ip:
                self.current_view.append_message(msg)
        elif self.ui.current_mode == "cmd":
            # 在终端直接打印日志
            self.current_view.append_text(f"\n[Recv from {sender_name} ({ip})]: {content}\n{self.cmd_processor.current_path}>", "info")

    def _handle_cmd_input(self, cmd):
        handled = self.cmd_processor.process(cmd)

        # 如果不是系统命令，当作聊天消息发送
        if not handled:
            if self.target_contact:
                self._send_to_network(cmd, self.target_contact.ip, self.target_contact.port)
                # CMD 回显
                self.current_view.append_text(f"[Sent to {self.target_contact.name}]: {cmd}\n{self.cmd_processor.current_path}>", "info")

                if self.target_contact.id == 'loopback' or self.target_contact.name.lower() == 'loopback':
                    QTimer.singleShot(500, lambda: self._handle_incoming(f"Echo: {cmd}", self.target_contact.ip))
            else:
                self.current_view.append_text(f"'{cmd}' is not recognized.\n{self.cmd_processor.current_path}>", "error")

    def _on_cmd_output(self, text, tag):
        if self.ui.current_mode == "cmd" and self.current_view:
            if tag == "clear":
                self.current_view.clear_screen()
            else:
                self.current_view.append_text(text, tag)
