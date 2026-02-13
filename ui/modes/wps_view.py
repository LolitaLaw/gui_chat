# ui/modes/wps_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QFrame, QLabel, QHBoxLayout, QTabWidget, QSplitter, QLineEdit, QPushButton
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from .base_view import BaseModeView
from config.settings import THEMES


class WpsView(BaseModeView):
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 获取样式配置 (防止 KeyError)
        wps_theme = THEMES["wps"]
        # 默认使用 dark 配色的一项，或者根据 self.controller 传入的状态决定
        style_cfg = wps_theme.get("dark", {"bg_header": "#2b579a"})

        # 1. 顶部标题栏
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet(f"background-color: {style_cfg['bg_header']};")
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 0, 0)

        lbl_title = QLabel(wps_theme.get("title", "WPS"))
        lbl_title.setStyleSheet("color: white; font-family: 'Microsoft YaHei UI';")
        title_layout.addWidget(lbl_title)
        title_layout.addStretch()

        main_layout.addWidget(self.title_bar)

        # 2. Ribbon 功能区
        self.ribbon = QTabWidget()
        self.ribbon.setFixedHeight(100)
        self.ribbon.setStyleSheet(
            """
            QTabWidget::pane { border: none; background: #f3f3f3; }
            QTabBar::tab { padding: 5px 15px; color: #444; }
            QTabBar::tab:selected { background: white; border-bottom: 2px solid #3370ff; }
        """
        )

        tabs = ["开始", "插入", "页面布局", "引用", "审阅", "视图"]
        for tab in tabs:
            page = QWidget()
            if tab == "开始":
                self._setup_home_toolbar(page)
            self.ribbon.addTab(page, tab)

        main_layout.addWidget(self.ribbon)

        # 3. 主体内容 (文档 + 聊天侧边栏)
        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧文档编辑器
        self.doc_editor = QTextEdit()
        self.doc_editor.setStyleSheet("background-color: white; color: black; padding: 40px; border: none;")
        self.doc_editor.setFont(QFont("Times New Roman", 12))
        self.doc_editor.setHtml("<p>二、系统参数定义</p><p>1. 质量浓度范围: Range: 0 to 1000 ug/m3</p>")

        # 右侧 AI 助手
        self.ai_sidebar = QWidget()
        self.ai_sidebar.setFixedWidth(300)
        self.ai_sidebar.setStyleSheet("background-color: #f5f5f5; border-left: 1px solid #ddd;")
        ai_layout = QVBoxLayout(self.ai_sidebar)
        ai_layout.setContentsMargins(0, 0, 0, 0)

        ai_header = QLabel("✨ WPS AI 助手")
        ai_header.setStyleSheet("font-weight: bold; color: #3370ff; padding: 10px; background: white;")
        ai_layout.addWidget(ai_header)

        self.ai_chat = QTextEdit()
        self.ai_chat.setReadOnly(True)
        self.ai_chat.setFrameShape(QFrame.Shape.NoFrame)
        ai_layout.addWidget(self.ai_chat)

        # 底部输入
        input_box = QWidget()
        input_box.setFixedHeight(50)
        ib_layout = QHBoxLayout(input_box)
        ib_layout.setContentsMargins(5, 5, 5, 5)

        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Ask AI...")
        self.ai_input.setStyleSheet("border: 1px solid #ddd; border-radius: 4px; padding: 5px;")
        ib_layout.addWidget(self.ai_input)

        ai_layout.addWidget(input_box)

        content_splitter.addWidget(self.doc_editor)
        content_splitter.addWidget(self.ai_sidebar)
        content_splitter.setStretchFactor(0, 1)

        main_layout.addWidget(content_splitter)

    def _setup_home_toolbar(self, parent):
        layout = QHBoxLayout(parent)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        for text in ["B", "I", "U", "A", "左对齐", "居中"]:
            btn = QPushButton(text)
            btn.setFixedSize(40, 30)
            btn.setStyleSheet("border: 1px solid transparent; border-radius: 3px;")
            layout.addWidget(btn)
