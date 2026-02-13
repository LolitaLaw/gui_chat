# ui/components/scrollbar.py
from PyQt6.QtWidgets import QScrollBar
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QEvent
from PyQt6.QtGui import QPainter, QColor, QBrush


class OverlayScrollBar(QScrollBar):
    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Vertical, parent)
        self.setFixedWidth(12)
        # 设置透明背景，不占用布局空间（悬浮）或者融入背景
        self.setStyleSheet(
            """
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #888;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """
        )

        # 自动隐藏逻辑
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(200)
        self.hide()  # 默认隐藏

    def enterEvent(self, event):
        self.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        # 离开时不立即隐藏，而是等一小会儿，或者交给父容器控制
        # 这里简单处理：如果不在拖动中，可以考虑隐藏
        # 但通常更稳健的做法是让父容器的 enter/leave 来控制它的显隐
        super().leaveEvent(event)

    # 实际项目中，通常通过 installEventFilter 到 TextEdit 上来控制显隐
    # 下面是一个辅助函数，用于绑定到 TextEdit
    @staticmethod
    def install_on(text_edit):
        sb = OverlayScrollBar(text_edit)
        # 将原滚动条替换为隐藏的系统滚动条，用自定义的覆盖在上面
        # 或者简单点：直接美化原生的 verticalScrollBar
        # PyQt QSS 已经足够强大，下面直接在 NormalView 里用 QSS 实现“鼠标悬停显示”的效果更简单稳定。
        pass


# 修正：为了实现“不滑动不显示”的最佳效果，单纯用 QSS 的伪状态 hover 结合 width 是最轻量的。
# 我们将在 NormalView 中直接应用高级 QSS。
