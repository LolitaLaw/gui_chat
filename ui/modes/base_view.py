# ui/modes/base_view.py
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal


class BaseModeView(QWidget):
    """
    所有模式视图的基类。
    定义了通用的信号和接口，确保 Controller 可以统一调用。
    """

    # 通用信号：视图层只负责发射信号，不直接调用 Controller 的逻辑方法
    action_triggered = pyqtSignal(str, object)  # (action_type, data)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化 UI，子类必须实现此方法
        self.init_ui()

    def init_ui(self):
        """子类必须重写此方法以构建界面"""
        raise NotImplementedError("Subclasses must implement init_ui()")

    def on_show(self):
        """当视图被切换为当前显示时触发"""
        pass

    def on_hide(self):
        """当视图被隐藏时触发"""
        pass

    def update_theme(self, theme_config):
        """接收主题配置字典，更新界面样式"""
        pass

    def handle_message(self, message_data):
        """
        处理接收到的消息
        :param message_data: 数据层传来的 Message 对象或字典
        """
        pass
