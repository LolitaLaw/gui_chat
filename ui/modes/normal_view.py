# ui/modes/normal_view.py
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QListWidget, 
                             QLineEdit, QPushButton, QLabel, QFrame, 
                             QMenu, QListWidgetItem, QInputDialog, QMessageBox,
                             QStackedWidget, QAbstractItemView, QTextEdit)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QColor
from .base_view import BaseModeView
from config.settings import THEMES, COLOR_SCHEMES
from ui.components.chat_delegate import ChatDelegate
# [新增] 引入联系人代理
from ui.components.contact_delegate import ContactDelegate

class NormalView(BaseModeView):
    # 信号定义
    message_sent = pyqtSignal(str)
    contact_selected = pyqtSignal(object)
    contact_added = pyqtSignal(str, str)
    contact_deleted = pyqtSignal(object)
    contact_modified = pyqtSignal(object, str)
    theme_toggled = pyqtSignal()

    def __init__(self, parent=None, is_dark=True):
        self.is_dark = is_dark
        self.current_theme = COLOR_SCHEMES["dark"] if is_dark else COLOR_SCHEMES["light"]
        self.send_mode = "Enter" 
        self._all_contacts_cache = []
        super().__init__(parent)

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 左侧侧边栏 ===
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(280)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # 搜索与工具栏
        search_area = QWidget()
        search_area.setFixedHeight(60)
        search_layout = QHBoxLayout(search_area)
        search_layout.setContentsMargins(10, 10, 10, 10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索")
        self.search_input.textChanged.connect(self._on_search_changed)
        
        self.add_btn = QPushButton("➕️")
        self.add_btn.setFixedSize(30, 30)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._on_add_btn_clicked)
        
        self.mode_btn = QPushButton("☀️")
        self.mode_btn.setFixedSize(30, 30)
        self.mode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mode_btn.clicked.connect(self._on_toggle_theme)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.add_btn)
        search_layout.addWidget(self.mode_btn)
        sidebar_layout.addWidget(search_area)

        # 2. 联系人列表
        self.contact_list_widget = QListWidget()
        self.contact_list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.contact_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.contact_list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.contact_list_widget.itemClicked.connect(self._on_contact_clicked)
        
        # [核心] 安装联系人绘图代理
        self.contact_delegate = ContactDelegate(self.contact_list_widget, self.current_theme)
        self.contact_list_widget.setItemDelegate(self.contact_delegate)
        # 设置行间距，让背景块之间有空隙 (如果 Delegate 画了圆角背景)
        self.contact_list_widget.setSpacing(2) 
        sidebar_layout.addWidget(self.contact_list_widget)

        main_layout.addWidget(self.sidebar)

        # === 右侧区域 ===
        self.right_stack = QStackedWidget()
        main_layout.addWidget(self.right_stack)

        # --- Page 0: 空状态(背景页) ---
        self.empty_page = QWidget()
        empty_layout = QVBoxLayout(self.empty_page)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_empty = QLabel("")
        self.lbl_empty.setFont(QFont("Microsoft YaHei UI", 14))
        self.lbl_empty.setStyleSheet("color: #888;")
        empty_layout.addWidget(self.lbl_empty)
        self.right_stack.addWidget(self.empty_page)

        # --- Page 1: 聊天界面 ---
        self.chat_page = QWidget()
        chat_layout = QVBoxLayout(self.chat_page)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # 1. 标题
        self.header_label = QLabel("")
        self.header_label.setFixedHeight(50)
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.header_label.setIndent(20)
        # 加粗标题
        font_header = QFont(THEMES["normal"]["font_main"][0], 12)
        font_header.setBold(True)
        self.header_label.setFont(font_header)
        chat_layout.addWidget(self.header_label)
        
        self.line1 = QFrame()
        self.line1.setFrameShape(QFrame.Shape.HLine)
        self.line1.setFixedHeight(1)
        chat_layout.addWidget(self.line1)

        # 2. [核心替换] 消息记录使用 QListWidget 而不是 QTextEdit
        self.history_list = QListWidget()
        self.history_list.setFrameShape(QFrame.Shape.NoFrame)
        self.history_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        # 安装绘图代理
        self.chat_delegate = ChatDelegate(self.history_list, self.current_theme)
        self.history_list.setItemDelegate(self.chat_delegate)
        
        chat_layout.addWidget(self.history_list)

        self.line2 = QFrame()
        self.line2.setFrameShape(QFrame.Shape.HLine)
        self.line2.setFixedHeight(1)
        chat_layout.addWidget(self.line2)

        # 3. 输入区容器 (圆角矩形风格)
        input_container = QWidget()
        input_container.setFixedHeight(160)
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(20, 15, 20, 15)
        
        # 输入框外层容器 (圆角边框)
        self.input_wrapper = QFrame()
        self.input_wrapper.setObjectName("InputWrapper")  # 用于QSS定位
        wrapper_layout = QVBoxLayout(self.input_wrapper)
        wrapper_layout.setContentsMargins(5, 5, 5, 5)
        wrapper_layout.setSpacing(0)

        # 输入文本框 (背景透明，融入Wrapper)
        from PyQt6.QtWidgets import QTextEdit # 确保引入
        self.msg_input = QTextEdit()
        self.msg_input.setFrameShape(QFrame.Shape.NoFrame)
        self.msg_input.setPlaceholderText("请输入消息...")
        self.msg_input.installEventFilter(self)
        wrapper_layout.addWidget(self.msg_input)

        # 底部按钮栏
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        # 发送组合键 (也设为透明或微调颜色)
        self.send_composite = QFrame()
        self.send_composite.setFixedHeight(30)
        # 注意：这里我们让 send_composite 背景透明，或者与 wrapper 一致
        self.send_composite.setStyleSheet("background-color: transparent;")
        comp_layout = QHBoxLayout(self.send_composite)
        comp_layout.setContentsMargins(0, 0, 0, 0)
        comp_layout.setSpacing(0)

        # 发送按钮
        self.btn_send = QPushButton("发送(S)")
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.clicked.connect(self._do_send)
        # 按钮样式单独设置，鼠标悬停效果
        self.btn_send.setStyleSheet(
            """
            QPushButton { border: none; padding: 0 15px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: rgba(0,0,0,0.05); }
        """
        )
        comp_layout.addWidget(self.btn_send)

        self.btn_arrow = QPushButton("▼")
        self.btn_arrow.setFixedWidth(25)
        self.btn_arrow.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_arrow.clicked.connect(self._show_send_menu)
        self.btn_arrow.setStyleSheet(
            """
            QPushButton { border: none; border-radius: 4px; }
            QPushButton:hover { background-color: rgba(0,0,0,0.05); }
        """
        )
        comp_layout.addWidget(self.btn_arrow)

        btn_bar.addWidget(self.send_composite)
        wrapper_layout.addLayout(btn_bar)

        input_layout.addWidget(self.input_wrapper)
        chat_layout.addWidget(input_container)

        self.right_stack.addWidget(self.chat_page)

        # 默认显示空状态
        self.right_stack.setCurrentIndex(0)

        self._apply_styles()

    # === 样式更新 ===
    def update_theme(self, is_dark):
        self.is_dark = is_dark
        self.current_theme = COLOR_SCHEMES["dark"] if is_dark else COLOR_SCHEMES["light"]
        # 更新两个代理的主题
        self.chat_delegate.set_theme(self.current_theme)
        self.contact_delegate.set_theme(self.current_theme) # [新增]
        
        self.history_list.viewport().update()
        self.contact_list_widget.viewport().update() # [新增]
        
        self._apply_styles()

    def _apply_styles(self):
        theme = self.current_theme

        # 全局背景
        self.setStyleSheet(f"background-color: {theme['bg_root']}; color: {theme['fg_primary']};")
        self.sidebar.setStyleSheet(f"background-color: {theme['bg_sidebar']};")
        self.header_label.setStyleSheet(f"color: {theme['fg_primary']}; font-weight: bold;")
        
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme['bg_input']}; 
                color: {theme['fg_primary']};
                border: 1px solid {theme['border']}; 
                border-radius: 4px; 
                padding: 4px;
            }}
        """)
        
        btn_style = f"""
            QPushButton {{ 
                background-color: transparent; 
                border: 1px solid {theme['border']}; 
                border-radius: 4px; 
                color: {theme['fg_primary']}; 
            }}
            QPushButton:hover {{ background-color: {theme['bg_hover']}; }}
        """
        self.add_btn.setStyleSheet(btn_style)
        self.mode_btn.setStyleSheet(btn_style)

        # [修改] 联系人列表 QSS：移除 border-left 相关的代码，只保留基础背景
        # 具体的选中背景色和竖线由 Delegate 绘制
        self.contact_list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme['bg_sidebar']};
                border: none;
                outline: none;
            }}
            /* 注意：这里不再设置 item 的 border 和 selection-background-color */
            /* 完全交给 Delegate 处理，防止样式冲突 */
        """)
        
        self.history_list.setStyleSheet(f"background-color: {theme['bg_root']}; border: none;")

        # 分割线
        self.line1.setStyleSheet(f"background-color: {theme['border']};")
        self.line2.setStyleSheet(f"background-color: {theme['border']};")
        
        self.input_wrapper.setStyleSheet(f"#InputWrapper {{ background-color: {theme['bg_input']}; border: 1px solid {theme['border']}; border-radius: 10px; }}")
        self.msg_input.setStyleSheet(f"background-color: transparent; border: none; color: {theme['fg_primary']};")
        
        self.empty_page.setStyleSheet(f"background-color: {theme['bg_root']};")
        self.lbl_empty.setStyleSheet("color: #999;")

        # 7. [关键] 滚动条美化 (智能隐藏)
        # 实现原理：
        # 默认滑块宽度 0px 或 透明 -> 隐藏
        # 悬停在滚动条区域 -> 显示圆角滑块
        scrollbar_style = f"""
            QScrollBar:vertical {{ border: none; background: transparent; width: 10px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background: {theme['scroll_handle']}; min-height: 20px; border-radius: 5px; margin: 2px; }}
            QScrollBar::handle:vertical:hover {{ background: {theme['scroll_handle_hover']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        """
        self.history_list.verticalScrollBar().setStyleSheet(scrollbar_style)
        self.contact_list_widget.verticalScrollBar().setStyleSheet(scrollbar_style)
        self.msg_input.verticalScrollBar().setStyleSheet(scrollbar_style)

    # === [优化] 气泡显示 ===
    def append_message(self, message):
        item = QListWidgetItem()
        
        # 将消息对象的数据打包存入 Item
        sender_name = "我" if message.type == "self" else (message.sender_name or "Unknown")
        item_data = {
            'type': message.type,
            'msg': message.content,
            'time': message.time,
            'name': sender_name
        }
        item.setData(Qt.ItemDataRole.UserRole, item_data)
        
        # 添加到列表
        self.history_list.addItem(item)
        
        # 滚动到底部
        self.history_list.scrollToBottom()

    def display_history(self, records, name):
        self.history_list.clear()
        for msg in records:
            self.append_message(msg)

    # ... 保持原有的逻辑方法 (_on_contact_clicked, _on_delete_contact, _do_send 等) 不变 ...
    # 为节省篇幅，请保留您之前已有的这些交互逻辑代码
    def _on_contact_clicked(self, item):
        contact_data = item.data(Qt.ItemDataRole.UserRole)
        self.header_label.setText(contact_data.name)

        # 切换到聊天页
        self.right_stack.setCurrentIndex(1)

        self.contact_selected.emit(contact_data)

    def _on_delete_contact(self, contact):
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除 {contact.name} 吗?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # 如果删除的是当前正显示的，切回空状态
            current_item = self.contact_list_widget.currentItem()
            if current_item and current_item.data(Qt.ItemDataRole.UserRole) == contact:
                self.right_stack.setCurrentIndex(0)
            self.contact_deleted.emit(contact)

    def _on_search_changed(self, text):
        text = text.lower().strip()
        self.contact_list_widget.clear()
        for contact in self._all_contacts_cache:
            if text in contact.name.lower() or text in contact.ip:
                self._add_contact_item(contact)

    def _on_add_btn_clicked(self):
        name, ok1 = QInputDialog.getText(self, "添加联系人", "请输入昵称:")
        if ok1 and name:
            ip, ok2 = QInputDialog.getText(self, "添加联系人", "请输入IP地址:")
            if ok2 and ip:
                self.contact_added.emit(name, ip)

    def _on_toggle_theme(self):
        self.theme_toggled.emit()

    def _show_context_menu(self, position):
        item = self.contact_list_widget.itemAt(position)
        if not item: return
        contact = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu()
        action_mod = QAction("修改备注", self)
        action_mod.triggered.connect(lambda: self._on_modify_contact(contact))
        action_del = QAction("删除联系人", self)
        action_del.triggered.connect(lambda: self._on_delete_contact(contact))
        menu.addAction(action_mod)
        menu.addAction(action_del)
        menu.exec(self.contact_list_widget.mapToGlobal(position))

    def _on_modify_contact(self, contact):
        new_name, ok = QInputDialog.getText(self, "修改备注", "新名称:", text=contact.name)
        if ok and new_name:
            self.contact_modified.emit(contact, new_name)

    def _show_send_menu(self):
        menu = QMenu(self)
        a1 = QAction("Enter 发送", self)
        a1.setCheckable(True)
        a1.setChecked(self.send_mode == "Enter")
        a1.triggered.connect(lambda: setattr(self, "send_mode", "Enter"))
        a2 = QAction("Ctrl+Enter 发送", self)
        a2.setCheckable(True)
        a2.setChecked(self.send_mode == "Ctrl+Enter")
        a2.triggered.connect(lambda: setattr(self, "send_mode", "Ctrl+Enter"))
        menu.addAction(a1)
        menu.addAction(a2)
        menu.exec(self.btn_arrow.mapToGlobal(self.btn_arrow.rect().bottomLeft()))

    def _do_send(self):
        text = self.msg_input.toPlainText().strip()
        if text:
            self.message_sent.emit(text)
            self.msg_input.clear()
    # 发送按键
    def eventFilter(self, obj, event):
        if obj == self.msg_input and event.type() == event.Type.KeyPress:
            key = event.key()
            is_ctrl = event.modifiers() == Qt.KeyboardModifier.ControlModifier
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if self.send_mode == "Enter":
                    if is_ctrl: self.msg_input.textCursor().insertText("\n"); return True
                    else: self._do_send(); return True
                elif self.send_mode == "Ctrl+Enter":
                    if is_ctrl: self._do_send(); return True
                    else: return False
        return super().eventFilter(obj, event)

    def update_contacts(self, contacts):
        self._all_contacts_cache = contacts
        self.contact_list_widget.clear()
        for contact in contacts:
            self._add_contact_item(contact)

    def _add_contact_item(self, contact):
        item = QListWidgetItem(contact.name)
        item.setData(Qt.ItemDataRole.UserRole, contact)
        item.setSizeHint(QSize(0, 50)) # 增加行高，更美观
        # 不再硬编码颜色，由 QSS 控制
        self.contact_list_widget.addItem(item)
