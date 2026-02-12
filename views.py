# views.py
# (视图层)：存放 CMD、Normal、WPS 三大界面的具体布局代码。
# 这是代码量最大的部分，独立出来非常便于管理

import tkinter as tk
from tkinter import simpledialog
from settings import THEMES
from components import SmartScrollbar

# === CMD 视图 ===
class CmdView(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master, bg=THEMES["cmd"]["bg_root"])
        self.controller = controller
        
        # 输出区
        self.text_area = tk.Text(self, bg=THEMES["cmd"]["bg_root"], fg=THEMES["cmd"]["fg_primary"], 
                               font=THEMES["cmd"]["font_main"], wrap="word", bd=0)
        self.text_area.pack(side="top", fill="both", expand=True)
        self.text_area.tag_config("cmd_text", foreground=THEMES["cmd"]["fg_primary"])
        self.text_area.tag_config("cmd_err", foreground=THEMES["cmd"]["fg_error"])
        
        sb = SmartScrollbar(self, command=self.text_area.yview, bg_color=THEMES["cmd"]["bg_root"], thumb_color="#333", hover_color="#555")
        sb.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")
        self.text_area.config(yscrollcommand=sb.set)
        
        # 输入区
        self.input_area = tk.Text(self, height=1, bg=THEMES["cmd"]["bg_root"], fg="white", 
                                font=THEMES["cmd"]["font_main"], bd=0, insertbackground="white")
        self.input_area.pack(side="bottom", fill="x")
        self.input_area.bind("<Return>", self._on_return)

    def _on_return(self, event):
        if event.state & 0x0004: return
        msg = self.input_area.get("1.0", "end-1c").strip()
        self.input_area.delete("1.0", tk.END)
        self.controller.handle_cmd_input(msg)
        return "break"

    def log(self, text, tag="cmd_text"):
        self.text_area.config(state="normal")
        self.text_area.insert(tk.END, text, tag)
        self.text_area.see(tk.END)
        self.text_area.config(state="disabled")

    def clear(self):
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", tk.END)
        self.text_area.config(state="disabled")

# === Normal 视图 ===
class NormalView(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master, bg=THEMES["normal"]["bg_root"])
        self.controller = controller
        style = THEMES["normal"]
        
        paned = tk.PanedWindow(self, orient="horizontal", bg=style["bg_sidebar"], sashwidth=2)
        paned.pack(fill="both", expand=True)
        
        # 左侧联系人
        sidebar = tk.Frame(paned, width=220, bg=style["bg_sidebar"])
        paned.add(sidebar)
        
        search_frm = tk.Frame(sidebar, bg="#262626", height=30)
        search_frm.pack(fill="x", padx=10, pady=10)
        tk.Label(search_frm, text="🔍", bg="#262626", fg="gray").pack(side="left", padx=5)
        tk.Entry(search_frm, bg="#262626", fg="white", bd=0).pack(side="left", fill="x", expand=True)
        tk.Button(search_frm, text="+", bg="#262626", fg="white", bd=0, width=2, command=self._add_contact).pack(side="right")
        
        self.contact_list = tk.Listbox(sidebar, bg=style["bg_sidebar"], fg="#ddd", bd=0, font=style["font_main"], selectbackground="#4c4c4c")
        self.contact_list.pack(fill="both", expand=True)
        self.contact_list.bind("<<ListboxSelect>>", self._on_contact_select)
        self.refresh_contacts()
        
        # 右侧聊天
        main_chat = tk.Frame(paned, bg=style["bg_root"])
        paned.add(main_chat)
        
        self.header_label = tk.Label(main_chat, text=self.controller.target_name, bg=style["bg_root"], fg="white", font=("微软雅黑", 12, "bold"), anchor="w", padx=15, pady=10)
        self.header_label.pack(fill="x")
        tk.Frame(main_chat, height=1, bg="#333").pack(fill="x")
        
        self.text_area = tk.Text(main_chat, bg=style["bg_root"], fg="white", font=style["font_main"], wrap="word", bd=0, padx=10, pady=10)
        self.text_area.pack(fill="both", expand=True)
        self.text_area.tag_config("normal_self", foreground="#98e165", justify="right", rmargin=10)
        self.text_area.tag_config("normal_peer", foreground="white", justify="left", lmargin1=10)
        
        sb = SmartScrollbar(main_chat, command=self.text_area.yview, bg_color=style["bg_root"])
        sb.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")
        self.text_area.config(yscrollcommand=sb.set)
        
        # 输入区
        input_frm = tk.Frame(main_chat, height=120, bg=style["bg_root"])
        input_frm.pack(fill="x", side="bottom")
        tk.Frame(input_frm, height=1, bg="#333").pack(fill="x")
        self.input_area = tk.Text(input_frm, height=5, bg=style["bg_root"], fg="white", font=style["font_main"], bd=0, insertbackground="white", padx=10, pady=5)
        self.input_area.pack(fill="both", expand=True)
        self.input_area.bind("<Return>", self._on_return)

    def refresh_contacts(self):
        self.contact_list.delete(0, tk.END)
        for c in self.controller.displayed_contacts: self.contact_list.insert(tk.END, f" {c['name']}")

    def _on_contact_select(self, event):
        idx = self.contact_list.curselection()
        if idx:
            c = self.controller.displayed_contacts[idx[0]]
            self.controller.set_target(c)
            self.header_label.config(text=c['name'])

    def _add_contact(self):
        self.controller.add_new_contact()
        self.refresh_contacts()

    def _on_return(self, event):
        if event.state & 0x0004: return
        msg = self.input_area.get("1.0", "end-1c").strip()
        self.input_area.delete("1.0", tk.END)
        self.controller.handle_chat_send(msg, "normal_self")
        return "break"

    def log(self, text, tag="normal_peer"):
        self.text_area.config(state="normal")
        self.text_area.insert(tk.END, text, tag)
        self.text_area.see(tk.END)
        self.text_area.config(state="disabled")

# === WPS 视图 ===
class WpsView(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master, bg=THEMES["wps"]["bg_root"])
        self.controller = controller
        self._drag_data = {"x": 0, "y": 0}
        style = THEMES["wps"]
        
        # 3.1 蓝色标题栏
        title_bar = tk.Frame(self, bg=style["bg_header"], height=35)
        title_bar.pack(fill="x", side="top")
        title_bar.pack_propagate(False)
        title_bar.bind("<Button-1>", self.start_move)
        title_bar.bind("<B1-Motion>", self.do_move)
        
        tk.Label(title_bar, text=" W ", bg=style["bg_header"], fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        tk.Label(title_bar, text=style["title"], bg=style["bg_header"], fg="white", font=style["font_ui"]).pack(side="left")
        
        btn_close = tk.Label(title_bar, text=" × ", bg=style["bg_header"], fg="white", font=("Arial", 14), width=3)
        btn_close.pack(side="right")
        btn_close.bind("<Button-1>", lambda e: self.master.destroy())

        # 3.2 功能区
        ribbon = tk.Frame(self, bg="#f3f3f3", height=90)
        ribbon.pack(fill="x", side="top")
        ribbon.pack_propagate(False)
        
        menu_row = tk.Frame(ribbon, bg="#f3f3f3")
        menu_row.pack(fill="x", pady=2)
        tk.Label(menu_row, text="开始", bg="white", fg=style["bg_header"], font=("微软雅黑", 9, "bold"), padx=10).pack(side="left", padx=5)
        for m in ["插入", "页面布局", "引用", "审阅", "视图", "章节"]:
            tk.Label(menu_row, text=m, bg="#f3f3f3", fg="#444", font=("微软雅黑", 9), padx=8).pack(side="left")
            
        tool_row = tk.Frame(ribbon, bg="#f3f3f3")
        tool_row.pack(fill="x", padx=10, pady=5)
        tk.Button(tool_row, text=" B ", font=("Times", 9, "bold"), bg="#e1e1e1", bd=0, command=self._toggle_bold).pack(side="left", padx=2)
        tk.Button(tool_row, text=" A ", fg="red", font=("Times", 9, "bold"), bg="#e1e1e1", bd=0, command=self._set_red).pack(side="left", padx=2)

        # 3.3 主体
        main_paned = tk.PanedWindow(self, orient="horizontal", bg="#f0f0f0", sashwidth=4)
        main_paned.pack(fill="both", expand=True)
        
        # 文档
        doc_container = tk.Frame(main_paned, bg="#f0f0f0")
        main_paned.add(doc_container)
        paper = tk.Frame(doc_container, bg="white", padx=40, pady=40)
        paper.pack(fill="both", expand=True, padx=20, pady=10)
        self.doc_editor = tk.Text(paper, bg="white", fg="black", font=style["font_doc"], wrap="word", bd=0, undo=True)
        self.doc_editor.pack(fill="both", expand=True)
        self.doc_editor.insert("1.0", "二、系统参数定义\n\n1. 质量浓度范围:\n   Range: 0 to 1000 ug/m3\n\n(在此处继续编写文档...)\n")
        self.doc_editor.tag_config("bold", font=("Times New Roman", 12, "bold"))
        self.doc_editor.tag_config("red", foreground="red")
        
        # AI 侧边栏
        sidebar = tk.Frame(main_paned, width=300, bg="white")
        main_paned.add(sidebar)
        tk.Label(sidebar, text="✨ WPS AI 助手", font=("微软雅黑", 10, "bold"), bg="white", fg=style["bg_header"], pady=10).pack(fill="x")
        
        self.chat_log = tk.Text(sidebar, bg="white", fg="#333", font=style["font_ui"], state="disabled", bd=0, wrap="word")
        self.chat_log.pack(side="top", fill="both", expand=True, padx=5)
        self.chat_log.tag_config("ai_me", foreground="#333", background="#e1ecff", justify="right", lmargin1=20, rmargin=5)
        self.chat_log.tag_config("ai_peer", foreground="#333", background="#f5f5f5", justify="left", rmargin=20, lmargin1=5)
        
        input_frm = tk.Frame(sidebar, bg="#f5f5f5", height=40)
        input_frm.pack(side="bottom", fill="x", padx=10, pady=10)
        tk.Label(input_frm, text="Ask:", bg="#f5f5f5", fg="#aaa").pack(side="left")
        self.input = tk.Entry(input_frm, bg="#f5f5f5", bd=0, font=style["font_ui"])
        self.input.pack(side="left", fill="x", expand=True, padx=5)
        self.input.bind("<Return>", self._on_return)

    def _toggle_bold(self):
        try: 
            if "bold" in self.doc_editor.tag_names("sel.first"): self.doc_editor.tag_remove("bold", "sel.first", "sel.last")
            else: self.doc_editor.tag_add("bold", "sel.first", "sel.last")
        except: pass
    
    def _set_red(self):
        try: self.doc_editor.tag_add("red", "sel.first", "sel.last")
        except: pass

    def start_move(self, event): self._drag_data = {"x": event.x, "y": event.y}
    def do_move(self, event):
        x = self.master.winfo_x() + (event.x - self._drag_data["x"])
        y = self.master.winfo_y() + (event.y - self._drag_data["y"])
        self.master.geometry(f"+{x}+{y}")

    def _on_return(self, event):
        msg = self.input.get().strip()
        self.input.delete(0, tk.END)
        self.controller.handle_chat_send(msg, "ai_me")

    def log(self, text, tag="ai_peer"):
        self.chat_log.config(state="normal")
        self.chat_log.insert(tk.END, text, tag)
        self.chat_log.see(tk.END)
        self.chat_log.config(state="disabled")