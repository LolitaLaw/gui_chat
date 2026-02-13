# ui/modes/cmd_view.py
from PyQt6.QtWidgets import QVBoxLayout, QTextEdit
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QTextCursor
from .base_view import BaseModeView
from config.settings import THEMES  # 假设您保留了原有的配置结构

class CmdView(BaseModeView):
    # 定义特定信号：输入命令
    command_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 记录最后一次光标位置，防止用户删除提示符
        self.last_prompt_pos = 0

    def init_ui(self):
        # 布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 终端文本框
        self.console = QTextEdit()
        self.console.setFrameStyle(0) # 无边框
        
        # 应用样式
        cmd_theme = THEMES["cmd"]
        self.console.setStyleSheet(f"""
            QTextEdit {{
                background-color: {cmd_theme['bg_root']};
                color: {cmd_theme['fg_primary']};
                border: none;
                padding: 5px;
            }}
        """)
        font = QFont(cmd_theme['font_main'][0], cmd_theme['font_main'][1])
        self.console.setFont(font)
        
        layout.addWidget(self.console)

        # 安装事件过滤器以拦截按键
        self.console.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.console and event.type() == event.Type.KeyPress:
            # 拦截回车键
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._handle_enter()
                return True # 阻止默认换行
            
            # 拦截退格键（防止删除提示符）
            if event.key() == Qt.Key.Key_Backspace:
                cursor = self.console.textCursor()
                if cursor.position() <= self.last_prompt_pos:
                    return True
        
        return super().eventFilter(obj, event)

    def _handle_enter(self):
        # 获取用户输入的命令
        full_text = self.console.toPlainText()
        command = full_text[self.last_prompt_pos:].strip()
        
        # 移动光标到末尾并换行
        self.console.moveCursor(QTextCursor.MoveOperation.End)
        self.console.insertPlainText("\n")
        
        # 发射信号给 Controller
        if command:
            self.command_submitted.emit(command)
        else:
            # 如果是空命令，直接打印新提示符（此处简单模拟，实际应由Controller回调）
            pass

    def append_text(self, text, tag="info"):
        """供 Controller 调用以输出日志"""
        self.console.moveCursor(QTextCursor.MoveOperation.End)
        
        # 简单的颜色处理
        theme = THEMES["cmd"]
        color = theme['fg_primary']
        if tag == "error": color = theme['fg_error']
        
        # 设置文本颜色
        cursor = self.console.textCursor()
        format = cursor.charFormat()
        format.setForeground(QColor(color))
        cursor.setCharFormat(format)
        
        cursor.insertText(text)
        self.console.setTextCursor(cursor)
        self.console.ensureCursorVisible()
        
        # 更新提示符位置标记
        self.last_prompt_pos = self.console.textCursor().position()

    def clear_screen(self):
        self.console.clear()
        self.last_prompt_pos = 0