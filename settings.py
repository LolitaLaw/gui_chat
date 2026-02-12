# settings.py
# 存放所有静态数据（颜色、字体、联系人列表）。
# 改皮肤、改人名只动这里。
import os

# === 基础配置 ===
PORT = 9999
DEFAULT_TARGET_IP = "127.0.0.1"

# === 图标配置 ===
# 请确保这些图片文件存在于项目根目录下
ICONS = {
    "cmd": "terminal.png",  # 对应 CMD 模式
    "normal": "wechat.png",  # 对应 正常 模式
    "wps": "word.png",  # 对应 WPS 模式
}

# === 联系人数据 ===
CONTACTS = [
    {"id": "loopback", "name": "loop", "ip": "127.0.0.1", "port": 9999},
    {"id": "office", "name": "name1", "ip": "192.168.1.20", "port": 9999},
    {"id": "home", "name": "name2", "ip": "192.168.10.3", "port": 9999},
]

# === 皮肤主题配置 ===
# 定义两套配色方案
COLOR_SCHEMES = {
    "dark": {
        "bg_root": "#191919",
        "bg_sidebar": "#2e2e2e",
        "bg_input": "#191919",
        "fg_primary": "white",
        "bg_select": "#4c4c4c",
        "fg_peer": "white",
        "bg_peer": "#191919",
        "fg_self": "#98e165",
        "bg_self": "#191919",
        "border": "#333",
    },
    "light": {
        "bg_root": "#f5f5f5",
        "bg_sidebar": "#e7e7e7",
        "bg_input": "#ffffff",
        "fg_primary": "black",
        "bg_select": "#cce8ff",
        "fg_peer": "black",
        "bg_peer": "#ffffff",
        "fg_self": "black",
        "bg_self": "#95ec69",
        "border": "#dcdcdc",
    },
}
THEMES = {
    "cmd": {
        "bg_root": "#0c0c0c",
        "fg_primary": "#cccccc",
        "fg_error": "#ff3333",
        "font_main": ("Consolas", 11),
        "title": "Administrator: Windows PowerShell",
    },
    "normal": {
        "bg_root": "#191919",
        "bg_sidebar": "#2e2e2e",
        "fg_primary": "white",
        "font_main": ("Microsoft YaHei UI", 10),
        "title": "wx",
    },
    "wps": {
        # "bg_selected": "#cce8ff",  # 按钮选中背景
        "font_doc": ("Times New Roman", 12),
        "font_ui": ("Microsoft YaHei UI", 9),
        "title": "新建 DOCX 文档.docx - WPS Office",
        # WPS 的深浅配色
        "dark": {
            "bg_root": "#333333",
            "bg_header": "#333333",
            "bg_ribbon": "#444444",
            "bg_paper": "#2b2b2b",
            "fg_text": "#dcdcdc",
            "fg_ui": "#dcdcdc",
            "bg_hover": "#555",
        },
        "light": {
            "bg_root": "#f0f0f0",
            "bg_header": "#3370ff",
            "bg_ribbon": "#f3f3f3",
            "bg_paper": "white",
            "fg_text": "black",
            "fg_ui": "#444",
            "bg_hover": "#e6f1ff",
        },
    },
}
