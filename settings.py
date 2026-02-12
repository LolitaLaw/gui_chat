# settings.py
# 存放所有静态数据（颜色、字体、联系人列表）。
# 改皮肤、改人名只动这里。
import os

# === 基础配置 ===
PORT = 9999
DEFAULT_TARGET_IP = "127.0.0.1"

# === 联系人数据 ===
CONTACTS = [
    {"id": "loopback", "name": "loop", "ip": "127.0.0.1", "port": 9999},
    {"id": "office", "name": "name1", "ip": "192.168.1.20", "port": 9999},
    {"id": "home", "name": "name2", "ip": "192.168.10.3", "port": 9999},
]

# === 皮肤主题配置 ===
THEMES = {
    "cmd": {
        "bg_root": "#0c0c0c",
        "fg_primary": "#cccccc",
        "fg_error": "#ff3333",
        "font_main": ("Consolas", 11),
        "title": "Administrator: Windows PowerShell"
    },
    "normal": {
        "bg_root": "#191919",
        "bg_sidebar": "#2e2e2e",
        "fg_primary": "white",
        "font_main": ("Microsoft YaHei UI", 10),
        "title": "wx"
    },
    "wps": {
        "bg_root": "#f0f0f0",
        "bg_header": "#3370ff",
        "font_doc": ("Times New Roman", 12),
        "font_ui": ("Microsoft YaHei UI", 9),
        "title": "新建 DOCX 文档.docx - WPS Office"
    }
}