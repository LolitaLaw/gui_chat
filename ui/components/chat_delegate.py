# ui/components/chat_delegate.py
from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QPainter, QColor, QTextDocument, QAbstractTextDocumentLayout, QPalette

class ChatDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.theme = theme  # 接收当前主题配置

    def set_theme(self, theme):
        self.theme = theme

    def paint(self, painter, option, index):
        """核心绘制逻辑：每一行消息怎么画"""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 获取消息数据
        data = index.data(Qt.ItemDataRole.UserRole)
        if not data:
            painter.restore()
            return

        msg_type = data.get('type', 'peer')
        msg_text = data.get('msg', '')
        time_str = data.get('time', '')
        name = data.get('name', '')

        # 1. 布局配置
        is_self = (msg_type == 'self')

        # 2. 基础配置
        rect = option.rect
        max_width = int(rect.width() * 0.65) # 气泡最大宽度

        # 2. 准备文本渲染器 (用于自动换行和计算高度)
        doc = QTextDocument()
        doc.setDefaultFont(option.font)
        text_color = self.theme['fg_self'] if is_self else self.theme['fg_peer']

        # 强制左对齐，处理换行
        html_content = f"<div style='color: {text_color}; white-space: pre-wrap;'>{msg_text}</div>"
        doc.setHtml(html_content)
        doc.setTextWidth(max_width) # 限制宽度

        # 3. 计算尺寸
        content_width = doc.idealWidth()
        content_height = doc.size().height()

        padding = 12 # 气泡内边距
        bubble_w = content_width + (padding * 2)
        bubble_h = content_height + (padding * 2)

        # 名字和时间的高度
        meta_height = 20
        spacing = 5 # 元素间距

        # 5. 布局逻辑 (核心修改：时间位置)
        # Y轴：名字 -> (间距) -> 气泡
        # 如果是 Self，名字不显示或者显示在右侧？通常 Self 不显示名字，这里保留名字占位逻辑

        start_y = rect.top() + meta_height 

        if is_self:
            # === 我发送的 (右对齐) ===
            # 布局：[时间] [气泡] [头像/名]

            # A. 气泡位置 (靠右)
            bubble_x = rect.right() - bubble_w - 45 # 留出头像空间(40px)

            # B. 名字 (气泡上方靠右)
            name_rect = QRectF(rect.right() - 200, rect.top(), 190, meta_height)
            painter.setPen(QColor("#888888"))
            painter.drawText(name_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, name)

            # C. 时间 (显示在气泡**左侧** - 您的需求)
            time_width = 50
            time_x = bubble_x - time_width - spacing
            time_rect = QRectF(time_x, start_y + bubble_h - 20, time_width, 20) # 底部对齐
            painter.setPen(QColor("#999999"))
            painter.drawText(time_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom, time_str)

            # 气泡背景色
            bg_color = self.theme['bg_self']

        else:
            # === 对方发送的 (左对齐) ===
            # 布局：[头像/名] [气泡] [时间]

            # A. 气泡位置 (靠左)
            bubble_x = 10 # 左边距

            # B. 名字 (气泡上方靠左)
            name_rect = QRectF(bubble_x, rect.top(), 200, meta_height)
            painter.setPen(QColor("#999999"))
            painter.drawText(name_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name)

            # C. 时间 (显示在气泡**右侧** - 您的需求)
            time_x = bubble_x + bubble_w + spacing
            time_rect = QRectF(time_x, start_y + bubble_h - 20, 50, 20) # 底部对齐
            painter.setPen(QColor("#999999"))
            painter.drawText(time_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, time_str)

            # 气泡背景色
            bg_color = self.theme['bg_peer']

        # 6. 绘制气泡实体
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(bg_color))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing) # 抗锯齿，关键！

        bubble_rect = QRectF(bubble_x, start_y, bubble_w, bubble_h)
        painter.drawRoundedRect(bubble_rect, 10, 10) # 10px 圆角

        # 5.3 画文字内容
        painter.translate(bubble_x + padding, start_y + padding)
        # 强制设置文档颜色，覆盖 HTML
        ctx = QAbstractTextDocumentLayout.PaintContext()
        ctx.palette.setColor(QPalette.ColorRole.Text, QColor(text_color))
        doc.documentLayout().draw(painter, ctx)

        painter.restore()

    def sizeHint(self, option, index):
        """告诉列表这一行有多高"""
        data = index.data(Qt.ItemDataRole.UserRole)
        if not data:
            return QSize(0, 0)

        rect = option.rect
        max_width = int(rect.width() * 0.6)

        doc = QTextDocument()
        doc.setDefaultFont(option.font)
        doc.setHtml(f"<div>{data.get('msg', '')}</div>")
        doc.setTextWidth(max_width)

        # 总高度 = 名字高度 + 气泡内边距 + 文字高度 + 底部留白
        total_height = 20 + 20 + doc.size().height() + 10
        return QSize(int(rect.width()), int(total_height))
