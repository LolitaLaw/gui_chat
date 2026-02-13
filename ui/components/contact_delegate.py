# ui/components/contact_delegate.py
from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QPainter, QColor, QPen


class ContactDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.theme = theme

    def set_theme(self, theme):
        self.theme = theme

    def paint(self, painter, option, index):
        if not self.theme:
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. [关键修复] 获取状态 (PyQt6 写法)
        is_selected = option.state & QStyle.StateFlag.State_Selected
        is_hover = option.state & QStyle.StateFlag.State_MouseOver

        rect = option.rect

        # 2. 绘制背景
        # 默认透明，选中或悬停时绘制背景
        bg_color = QColor("transparent")
        if is_selected:
            bg_color = QColor(self.theme["bg_select"])
        elif is_hover:
            bg_color = QColor(self.theme["bg_hover"])

        if bg_color != QColor("transparent"):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg_color)
            # 绘制圆角背景 (4px)
            painter.drawRoundedRect(rect, 4, 4)

        # 3. 绘制文字 (联系人名字)
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text:
            # 文字颜色
            text_color = QColor(self.theme["fg_primary"])
            painter.setPen(text_color)

            # 文字区域 (留出左侧边距，避免压住竖线)
            text_rect = QRectF(rect.left() + 15, rect.top(), rect.width() - 20, rect.height())
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)

        # 4. [核心] 绘制左侧圆角竖线 (仅选中时)
        if is_selected:
            # 获取强调色，默认为蓝色
            accent_color = QColor(self.theme.get("accent", "#3370ff"))
            painter.setBrush(accent_color)
            painter.setPen(Qt.PenStyle.NoPen)

            # 竖线尺寸配置
            bar_width = 4  # 宽度
            bar_height = 16  # 高度
            margin_left = 4  # 距离左边缘的距离

            # 计算居中位置
            bar_y = rect.y() + (rect.height() - bar_height) / 2
            bar_x = rect.x() + margin_left

            bar_rect = QRectF(bar_x, bar_y, bar_width, bar_height)

            # 绘制圆角矩形 (半径为宽度的一半，实现胶囊状)
            painter.drawRoundedRect(bar_rect, bar_width / 2, bar_width / 2)

        painter.restore()

    def sizeHint(self, option, index):
        # 设置行高
        return QSize(option.rect.width(), 44)