# components.py
# (基建层)：存放通用的 UI 组件（如智能滚动条）和工具类（如重定向器）

import tkinter as tk
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except: return "127.0.0.1"

class StdoutRedirector:
    """重定向 stdout 用于捕获 Python 解释器输出"""
    def __init__(self, callback):
        self.callback = callback
    def write(self, text):
        if text: self.callback(text)
    def flush(self): pass

class SmartScrollbar(tk.Canvas):
    """自定义美化滚动条"""
    def __init__(self, master, command=None, bg_color='#f0f0f0', thumb_color='#cdcdcd', hover_color='#a6a6a6', **kwargs):
        super().__init__(master, highlightthickness=0, bd=0, bg=bg_color, **kwargs)
        self.command = command
        self.thumb_color = thumb_color
        self.hover_color = hover_color
        self.auto_hide = True
        self.thumb = self.create_rectangle(0, 0, 0, 0, outline="", fill=self.thumb_color, tags="thumb")
        self.is_hovering = False; self.is_dragging = False; self.current_lo = 0.0; self.current_hi = 1.0
        self.bind("<Button-1>", self.on_click); self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release); self.bind("<Enter>", self.on_enter); self.bind("<Leave>", self.on_leave)
        self.itemconfig("thumb", state='hidden')
    
    def set(self, lo, hi):
        try: lo, hi = float(lo), float(hi)
        except: return
        self.current_lo = lo; self.current_hi = hi
        if lo <= 0.0 and hi >= 1.0: self.itemconfig("thumb", state='hidden'); return
        h = self.winfo_height(); w = self.winfo_width()
        self.coords("thumb", 2, lo * h, w-2, hi * h)
        if not self.auto_hide or self.is_hovering or self.is_dragging:
            self.itemconfig("thumb", state='normal', fill=self.hover_color if self.is_hovering else self.thumb_color)
        else: self.itemconfig("thumb", state='hidden')
    
    def on_click(self, e): 
        h = self.winfo_height()
        if self.current_lo * h <= e.y <= self.current_hi * h: self.is_dragging = True; self.start_y = e.y; self.start_lo = self.current_lo
        elif h > 0 and self.command: self.command("moveto", e.y/h)
    def on_drag(self, e): 
        if self.is_dragging and self.winfo_height() > 0 and self.command: 
            self.command("moveto", self.start_lo + (e.y - self.start_y)/self.winfo_height())
    def on_release(self, e): self.is_dragging = False; self.on_leave(e)
    def on_enter(self, e): self.is_hovering = True; self.itemconfig("thumb", state='normal', fill=self.hover_color)
    def on_leave(self, e): 
        self.is_hovering = False
        if not self.is_dragging: self.itemconfig("thumb", state='hidden' if self.auto_hide else 'normal', fill=self.thumb_color)