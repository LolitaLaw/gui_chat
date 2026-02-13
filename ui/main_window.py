import ctypes
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QApplication
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QIcon

from config.settings import THEMES, ICONS

# 导入各个拆解后的视图模块
from ui.modes.cmd_view import CmdView
from ui.modes.normal_view import NormalView
from ui.modes.wps_view import WpsView


class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        # 记录当前状态
        self.current_mode = None
        self.views = {}  # 视图缓存：{"cmd": widget, ...}

        # 1. 初始化 UI 栈 (使用 QStackedWidget 实现页面无缝切换)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # 2. 基础窗口设置
        self.resize(900, 600)
        self._center_window()

        # 拖拽相关变量 (用于无边框模式)
        self._drag_pos = QPoint()

    def set_mode_view(self, mode_name):
        """
        切换显示模式
        由 Controller 调用
        """
        self.current_mode = mode_name

        # 1. 懒加载视图 (第一次切换到该模式时才创建)
        if mode_name not in self.views:
            view = self._create_view(mode_name)
            if view:
                self.views[mode_name] = view
                self.stack.addWidget(view)

        # 2. 切换显示的页面
        if mode_name in self.views:
            current_view = self.views[mode_name]
            self.stack.setCurrentWidget(current_view)

            # 触发视图的 on_show 生命周期 (如果有定义)
            if hasattr(current_view, "on_show"):
                current_view.on_show()

        # 3. 更新窗口外观 (标题、图标、边框)
        self._update_window_style(mode_name)

    @property
    def current_view(self):
        """获取当前正在显示的视图对象，供 Controller 使用"""
        return self.views.get(self.current_mode)

    def _create_view(self, mode_name):
        """工厂方法：创建对应模式的视图"""
        if mode_name == "cmd":
            return CmdView(self)
        elif mode_name == "normal":
            # 可以在这里读取配置决定是否深色模式
            return NormalView(self, is_dark=True)
        elif mode_name == "wps":
            return WpsView()
        return None

    def _update_window_style(self, mode):
        """根据模式调整窗口的标题、图标和边框特性"""
        theme = THEMES.get(mode, {})

        # 设置标题
        self.setWindowTitle(theme.get("title", "UltimateChat"))

        # 设置图标
        icon_path = ICONS.get(mode)
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
            # 强制刷新 Windows 任务栏图标 (AppID)
            try:
                myappid = f"mycompany.ultimatechat.{mode}"
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except:
                pass

        # 设置边框特性 (WPS 模式通常无边框)
        if mode == "wps":
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        else:
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint, False)

        # 注意：更改 WindowFlag 后必须调用 show() 才能生效
        self.show()

    def _center_window(self):
        """窗口居中"""
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # ==========================
    # 事件处理 (Global Events)
    # ==========================

    def keyPressEvent(self, event):
        """全局快捷键拦截"""
        key = event.key()

        if key == Qt.Key.Key_F10:
            self.controller.switch_mode("cmd")
        elif key == Qt.Key.Key_F11:
            self.controller.switch_mode("wps")
        elif key == Qt.Key.Key_F12:
            self.controller.switch_mode("normal")
        elif key == Qt.Key.Key_Escape:
            # 最小化
            self.showMinimized()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """处理无边框模式下的窗口拖动 (按下)"""
        # 只有在无边框模式 (WPS) 下才允许点击背景拖动
        if self.windowFlags() & Qt.WindowType.FramelessWindowHint:
            if event.button() == Qt.MouseButton.LeftButton:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """处理无边框模式下的窗口拖动 (移动)"""
        if self.windowFlags() & Qt.WindowType.FramelessWindowHint:
            if event.buttons() & Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()
        super().mouseMoveEvent(event)
