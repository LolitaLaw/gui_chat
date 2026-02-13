# settings.py
# 存放所有静态数据（颜色、字体、联系人列表）。
# 改皮肤、改人名只动这里。
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === 基础配置 ===
PORT = 9999
DEFAULT_TARGET_IP = "127.0.0.1"

# === 图标配置 ===
# 请确保这些图片文件存在于项目根目录下
ICONS = {
    "cmd": os.path.join(BASE_DIR, "terminal.png"),  # 对应 CMD 模式
    "normal": os.path.join(BASE_DIR, "wechat.png"),  # 对应 正常 模式
    "wps": os.path.join(BASE_DIR, "word.png"),  # 对应 WPS 模式
}

# === 联系人数据 ===
CONTACTS = [
    {"id": "loopback", "name": "loop", "ip": "127.0.0.1", "port": 9999},
    {"id": "office", "name": "name1", "ip": "192.168.1.20", "port": 9999},
    {"id": "home", "name": "name2", "ip": "192.168.10.3", "port": 9999},
]

# === 皮肤主题配置 ===
COLOR_SCHEMES = {
    "dark": {
        "bg_root": "#1e1e1e",
        "bg_sidebar": "#2d2d2d",
        "bg_input": "#3c3c3c",
        "fg_primary": "#cccccc",
        "border": "#333333",
        "bg_hover": "#3a3d41",
        "bg_select": "#3a3d41",  # 深色模式选中背景
        "accent": "#3370ff",     # 蓝色竖线颜色
        "bg_self": "#98e165", 
        "fg_self": "#000000",
        "bg_peer": "#2d2d2d",
        "fg_peer": "#ffffff",
        # 滚动条
        "scroll_bg": "transparent",
        "scroll_handle": "#555555",
        "scroll_handle_hover": "#777777",
    },
    "light": {
        "bg_root": "#f5f5f5",
        "bg_sidebar": "#e7e7e7",
        "bg_input": "#ffffff",
        "fg_primary": "#000000",
        "border": "#d6d6d6",
        "bg_hover": "#dcdcdc",
        "bg_select": "#e6f3ff",  # [优化] 极淡蓝色，保证黑色文字清晰
        "accent": "#1890ff",     # [新增] 亮蓝色竖线
        "bg_self": "#95ec69",    
        "fg_self": "#000000",
        "bg_peer": "#ffffff",    
        "fg_peer": "#000000",
        "scroll_handle": "#c1c1c1",
        "scroll_handle_hover": "#a8a8a8"
    }
}


THEMES = {
    "cmd": {
        "bg_root": "#0c0c0c", "fg_primary": "#cccccc", "fg_error": "#ff3333",
        "font_main": ("Consolas", 11), "title": "Administrator: Windows PowerShell"
    },
    "normal": {"title": "WX", "font_main": ("Microsoft YaHei UI", 10), "font_msg": ("Microsoft YaHei UI", 11)},  # 消息内容稍微大一点
    "wps": {
        "title": "新建DOCX文档.docx - WPS Office",
        "dark": {"bg_header": "#2b579a", "bg_ribbon": "#f3f3f3"},
        "light": {"bg_header": "#2b579a", "bg_ribbon": "#f3f3f3"},
    },
}
