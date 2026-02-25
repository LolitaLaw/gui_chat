# ui/modes/wps_view.py
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QFrame,
    QLabel,
    QHBoxLayout,
    QTabWidget,
    QSplitter,
    QLineEdit,
    QPushButton,
    QListWidget,
    QAbstractItemView,
)
from PyQt6.QtGui import QFont, QColor, QAction, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from .base_view import BaseModeView
from config.settings import THEMES, COLOR_SCHEMES

# 复用之前写好的绘图代理，保持聊天体验一致
from ui.components.chat_delegate import ChatDelegate
from PyQt6.QtWidgets import QListWidgetItem


class WpsView(BaseModeView):
    # 信号定义
    message_sent = pyqtSignal(str)
    window_minimized = pyqtSignal()
    window_closed = pyqtSignal()
    window_dragged = pyqtSignal(object)  # 传递鼠标事件给 MainWindow 处理拖拽

    def __init__(
        self, parent=None, is_dark=False
    ):  # WPS 默认通常是浅色或特定的蓝色主题
        super().__init__(parent)
        self.is_dark = is_dark
        self.current_theme = THEMES["wps"]["light"]  # 默认使用 WPS 亮色主题
        self.chat_delegate = None

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 1. 自定义标题栏 (因为是无边框窗口) ===
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(30)
        # 支持拖拽
        self.title_bar.mousePressEvent = self._on_title_bar_press
        self.title_bar.mouseMoveEvent = self._on_title_bar_move

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 0, 0)
        title_layout.setSpacing(10)

        # 标题栏图标和文字
        self.lbl_icon = QLabel("W")  # 模拟 WPS 图标
        self.lbl_icon.setStyleSheet(
            "background-color: white; color: #2b579a; font-weight: bold; padding: 2px 5px; border-radius: 2px;"
        )

        self.lbl_title = QLabel("新建 DOCX 文档.docx - WPS Office")
        self.lbl_title.setStyleSheet(
            "color: white; font-family: 'Microsoft YaHei UI'; font-size: 12px;"
        )

        title_layout.addWidget(self.lbl_icon)
        title_layout.addWidget(self.lbl_title)
        title_layout.addStretch()

        # 窗口控制按钮
        btn_style = """
            QPushButton { background: transparent; color: white; border: none; font-weight: bold; font-family: Webdings; }
            QPushButton:hover { background-color: rgba(255,255,255,0.2); }
        """
        btn_close_style = """
            QPushButton { background: transparent; color: white; border: none; font-weight: bold; font-family: Webdings; }
            QPushButton:hover { background-color: #e81123; }
        """

        self.btn_min = QPushButton("0")  # Webdings 字体 '0' 是最小化
        self.btn_min.setFixedSize(45, 30)
        self.btn_min.setStyleSheet(btn_style)
        self.btn_min.clicked.connect(lambda: self.window_minimized.emit())

        self.btn_max = QPushButton(
            "1"
        )  # Webdings '1' 是最大化 (这里仅做视觉，不做实际最大化逻辑)
        self.btn_max.setFixedSize(45, 30)
        self.btn_max.setStyleSheet(btn_style)

        self.btn_close = QPushButton("r")  # Webdings 'r' 是关闭
        self.btn_close.setFixedSize(45, 30)
        self.btn_close.setStyleSheet(btn_close_style)
        self.btn_close.clicked.connect(lambda: self.window_closed.emit())

        title_layout.addWidget(self.btn_min)
        title_layout.addWidget(self.btn_max)
        title_layout.addWidget(self.btn_close)

        main_layout.addWidget(self.title_bar)

        # === 2. Ribbon 功能区 (视觉装饰) ===
        self.ribbon = QTabWidget()
        self.ribbon.setFixedHeight(90)
        self.ribbon.setStyleSheet(
            """
            QTabWidget::pane { border: none; background: #f3f3f3; border-bottom: 1px solid #dcdcdc; }
            QTabBar::tab { background: transparent; padding: 6px 15px; color: #444; font-size: 11px; }
            QTabBar::tab:selected { background: #f3f3f3; border-bottom: 2px solid #2b579a; color: #2b579a; font-weight: bold; }
            QTabBar::tab:hover { background: rgba(0,0,0,0.05); }
        """
        )

        tabs = ["开始", "插入", "页面布局", "引用", "审阅", "视图", "章节", "云服务"]
        for tab in tabs:
            page = QWidget()
            if tab == "开始":
                self._setup_ribbon_home(page)
            self.ribbon.addTab(page, tab)

        main_layout.addWidget(self.ribbon)

        # === 3. 主体内容 (文档 + 聊天侧边栏) ===
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # A. 文档编辑区 (伪装区)
        self.doc_area = QWidget()
        self.doc_area.setStyleSheet("background-color: #f0f0f0;")  # 灰色底
        doc_layout = QVBoxLayout(self.doc_area)
        doc_layout.setContentsMargins(20, 20, 20, 0)

        # 白纸
        self.paper = QTextEdit()
        self.paper.setStyleSheet(
            "background-color: white; color: black; border: 1px solid #ccc; padding: 40px;"
        )
        self.paper.setFont(QFont("Times New Roman", 12))
        self.paper.setHtml(
            """
        <h2 style='text-align: center;'>标题</h2>
        <p><b>1.</b></p>
        <p></p>
        <p><b>2.</b></p>
        <ul>
            <li>list</li>
            <li>list</li>
            <li>list</li>
        </ul>
        <p><b>3.</b></p>
        <p></p>
        <p></p>
        """
        )

        # 底部状态栏模拟
        status_bar = QLabel(" 页面 1/5  字数: 342  中文(中国)               100% - +")
        status_bar.setFixedHeight(24)
        status_bar.setStyleSheet(
            "background: #f3f3f3; color: #666; font-size: 10px; border-top: 1px solid #ddd;"
        )

        doc_layout.addWidget(self.paper)
        doc_layout.addWidget(status_bar)

        # B. 侧边栏 (AI 助手 / 真实聊天区)
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(320)
        self.sidebar.setStyleSheet(
            "background-color: #fcfcfc; border-left: 1px solid #e0e0e0;"
        )
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # 侧边栏标题
        ai_header = QWidget()
        ai_header.setFixedHeight(40)
        ai_header.setStyleSheet("background: white; border-bottom: 1px solid #eee;")
        ah_layout = QHBoxLayout(ai_header)
        ah_layout.setContentsMargins(10, 0, 10, 0)

        lbl_ai = QLabel("✨ WPS AI 助手")
        lbl_ai.setStyleSheet(
            "font-weight: bold; color: #3370ff; font-family: 'Microsoft YaHei UI';"
        )
        ah_layout.addWidget(lbl_ai)
        ah_layout.addStretch()

        # 聊天列表 (复用 ChatDelegate)
        self.chat_list = QListWidget()
        self.chat_list.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_list.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        self.chat_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.chat_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.chat_list.setStyleSheet("background: transparent;")

        # 配置代理 (强制使用浅色主题配置，符合 WPS 风格)
        light_theme_cfg = COLOR_SCHEMES["light"]
        self.chat_delegate = ChatDelegate(self.chat_list, light_theme_cfg)
        self.chat_list.setItemDelegate(self.chat_delegate)

        # 输入区
        input_box = QWidget()
        input_box.setFixedHeight(120)
        input_box.setStyleSheet("background: white; border-top: 1px solid #eee;")
        ib_layout = QVBoxLayout(input_box)
        ib_layout.setContentsMargins(10, 10, 10, 10)

        self.ai_input = QTextEdit()
        self.ai_input.setPlaceholderText("向 AI 提问或输入指令...")
        self.ai_input.setFrameShape(QFrame.Shape.NoFrame)
        self.ai_input.setStyleSheet("background: transparent;")
        self.ai_input.installEventFilter(self)  # 监听回车

        # 发送按钮
        btn_send = QPushButton("发送")
        btn_send.setFixedSize(60, 26)
        btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_send.clicked.connect(self._do_send)
        btn_send.setStyleSheet(
            """
            QPushButton { background-color: #3370ff; color: white; border-radius: 4px; border: none; }
            QPushButton:hover { background-color: #295ecc; }
        """
        )

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_send)

        ib_layout.addWidget(self.ai_input)
        ib_layout.addLayout(btn_layout)

        sidebar_layout.addWidget(ai_header)
        sidebar_layout.addWidget(self.chat_list)
        sidebar_layout.addWidget(input_box)

        # 组装
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.doc_area)
        splitter.addWidget(self.sidebar)
        splitter.setStretchFactor(0, 1)  # 文档区占据主要空间
        splitter.setCollapsible(1, True)  # 侧边栏可折叠

        main_layout.addWidget(splitter)
        main_layout.addWidget(status_bar)  # 状态栏放在最底部

        self._apply_theme()

    def _apply_theme(self):
        # 应用 WPS 特有的蓝色头部
        self.title_bar.setStyleSheet("background-color: #2b579a;")

    def _setup_ribbon_home(self, parent):
        """模拟 Ribbon 开始菜单的按钮"""
        layout = QHBoxLayout(parent)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setSpacing(5)

        # 简单模拟一些功能组
        groups = [
            ["粘贴", "复制", "格式刷"],
            ["宋体", "12", "B", "I", "U"],
            ["左对齐", "居中", "右对齐"],
            ["行距", "缩进"],
        ]

        for i, group in enumerate(groups):
            # 每个组加个分割线
            if i > 0:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.VLine)
                line.setFixedHeight(40)
                line.setStyleSheet("color: #ddd;")
                layout.addWidget(line)

            for text in group:
                btn = QPushButton(text)
                btn.setFixedSize(40 if len(text) < 3 else 60, 40)
                btn.setStyleSheet(
                    """
                    QPushButton { border: none; color: #555; border-radius: 3px; }
                    QPushButton:hover { background-color: #e6f1ff; color: #2b579a; }
                """
                )
                layout.addWidget(btn)

    # === 事件处理 ===
    def _on_title_bar_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 发送拖拽信号，参数是 globalPos
            self.window_dragged.emit(event.globalPosition().toPoint())

    def _on_title_bar_move(self, event):
        # 移动逻辑通常由 MainWindow 处理，这里只需确保信号被 MainWindow 捕获
        # 但由于 Qt 事件冒泡机制，我们在 MainWindow 中重写 mousePress/Move 更直接。
        # 这里保留空方法或 pass 即可，主要逻辑在 MainWindow。
        pass

    def _do_send(self):
        text = self.ai_input.toPlainText().strip()
        if text:
            self.message_sent.emit(text)
            self.ai_input.clear()

    def eventFilter(self, obj, event):
        if obj == self.ai_input and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                    self.ai_input.textCursor().insertText("\n")
                else:
                    self._do_send()
                return True
        return super().eventFilter(obj, event)

    # === 外部接口 ===
    def append_message(self, message):
        item = QListWidgetItem()
        sender_name = (
            "我" if message.type == "self" else (message.sender_name or "Unknown")
        )
        item_data = {
            "type": message.type,
            "msg": message.content,
            "time": message.time,
            "name": sender_name,
        }
        item.setData(Qt.ItemDataRole.UserRole, item_data)
        self.chat_list.addItem(item)
        self.chat_list.scrollToBottom()

    def display_history(self, records, name):
        self.chat_list.clear()
        for msg in records:
            self.append_message(msg)
