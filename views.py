# views.py
import tkinter as tk
from tkinter import simpledialog, colorchooser, font, ttk
from settings import THEMES, COLOR_SCHEMES
from components import SmartScrollbar, WindowsTitleBarFix


# === CMD 视图 ===
class CmdView(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master, bg=THEMES["cmd"]["bg_root"])
        self.controller = controller

        # 尝试应用 Win11 深色标题栏
        self.master.update_idletasks()
        WindowsTitleBarFix.apply_dark_title_bar(self.master)

        # 输出区
        self.text_area = tk.Text(
            self,
            bg=THEMES["cmd"]["bg_root"],
            fg=THEMES["cmd"]["fg_primary"],
            font=THEMES["cmd"]["font_main"],
            wrap="word",
            bd=0,
            insertbackground="white",
        )
        self.text_area.pack(side="top", fill="both", expand=True)
        self.text_area.tag_config("cmd_text", foreground=THEMES["cmd"]["fg_primary"])
        self.text_area.tag_config("cmd_err", foreground=THEMES["cmd"]["fg_error"])

        # 窄滚动条
        sb = SmartScrollbar(
            self,
            command=self.text_area.yview,
            bg_color=THEMES["cmd"]["bg_root"],
            thumb_color="#333",
            hover_color="#555",
            width=10,
        )
        sb.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")
        self.text_area.config(yscrollcommand=sb.set)

        # 绑定事件
        self.text_area.bind("<Return>", self._on_return)
        self.text_area.bind("<Button-1>", lambda e: self.text_area.focus_set())
        self.input_mark = "1.0"

    def _on_return(self, event):
        user_input = self.text_area.get(self.input_mark, "end-1c").strip()
        self.text_area.insert("end", "\n")
        self.text_area.see("end")
        self.controller.handle_cmd_input(user_input)
        return "break"

    def log(self, text, tag="cmd_text", no_newline=False):
        self.text_area.config(state="normal")
        self.text_area.insert("end", text + ("" if no_newline else "\n"), tag)
        self.text_area.see("end")
        self.input_mark = self.text_area.index("end-1c")

    def prompt(self, text):
        self.text_area.config(state="normal")
        self.text_area.insert("end", text, "cmd_text")
        self.text_area.see("end")
        self.input_mark = self.text_area.index("end-1c")

    def clear(self):
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", tk.END)
        self.input_mark = "1.0"

    # CMD 模式通常不需要重置聊天区，但为了兼容性可以留空
    def reset_chat_area(self):
        self.clear()


# === Normal 视图 ===
class NormalView(tk.Frame):
    def __init__(self, master, controller, is_dark=True):
        self.colors = COLOR_SCHEMES["dark"] if is_dark else COLOR_SCHEMES["light"]
        super().__init__(master, bg=self.colors["bg_root"])
        self.controller = controller

        self.master.update_idletasks()
        if is_dark:
            WindowsTitleBarFix.apply_dark_title_bar(self.master)
        else:
            WindowsTitleBarFix.apply_light_title_bar(self.master)

        paned = tk.PanedWindow(
            self, orient="horizontal", bg=self.colors["bg_sidebar"], sashwidth=1
        )
        paned.pack(fill="both", expand=True)

        # --- 左侧联系人 ---
        sidebar = tk.Frame(paned, width=220, bg=self.colors["bg_sidebar"])
        paned.add(sidebar)

        # 搜索框区域
        search_frm = tk.Frame(
            sidebar, bg="#262626" if is_dark else "#e0e0e0", height=40
        )
        search_frm.pack(fill="x", padx=10, pady=10)

        self.search_var = tk.StringVar()
        self.search_var.trace(
            "w", lambda *a: self.controller.filter_contacts(self.search_var.get())
        )

        tk.Entry(
            search_frm,
            textvariable=self.search_var,
            bg=self.colors["bg_input"],
            fg=self.colors["fg_primary"],
            bd=0,
        ).pack(side="left", fill="x", expand=True, ipady=3, padx=5)

        tk.Button(
            search_frm,
            text="+",
            bg=search_frm["bg"],
            fg=self.colors["fg_primary"],
            bd=0,
            width=2,
            command=self._add_contact,
        ).pack(side="right")

        mode_btn_txt = "☼" if is_dark else "☾"
        tk.Button(
            search_frm,
            text=mode_btn_txt,
            bg=search_frm["bg"],
            fg=self.colors["fg_primary"],
            bd=0,
            width=2,
            command=self.controller.toggle_color_scheme,
        ).pack(side="right")

        # 联系人列表
        self.contact_list = tk.Listbox(
            sidebar,
            bg=self.colors["bg_sidebar"],
            fg=self.colors["fg_primary"],
            bd=0,
            font=THEMES["normal"]["font_main"],
            selectbackground=self.colors["bg_select"],
            selectforeground=self.colors["fg_primary"],
        )
        self.contact_list.pack(fill="both", expand=True)
        self.contact_list.bind("<<ListboxSelect>>", self._on_contact_select)

        self.contact_list.bind("<Button-3>", self._show_context_menu)
        self.context_menu = tk.Menu(self, tearoff=0, bg="white", fg="black")
        self.context_menu.add_command(label="修改备注", command=self._menu_modify)
        self.context_menu.add_command(label="删除联系人", command=self._menu_delete)

        self.refresh_contacts()

        # --- 右侧聊天 ---
        self.main_chat = tk.Frame(paned, bg=self.colors["bg_root"])
        paned.add(self.main_chat)

        # 头部
        self.header_label = tk.Label(
            self.main_chat,
            text=self.controller.target_name or "未选择",
            bg=self.colors["bg_root"],
            fg=self.colors["fg_primary"],
            font=("微软雅黑", 12, "bold"),
            anchor="w",
            padx=15,
            pady=10,
        )
        self.header_label.pack(fill="x")
        tk.Frame(self.main_chat, height=1, bg=self.colors["border"]).pack(fill="x")

        # 聊天记录区
        self.text_area = tk.Text(
            self.main_chat,
            bg=self.colors["bg_root"],
            fg=self.colors["fg_primary"],
            font=THEMES["normal"]["font_main"],
            wrap="word",
            bd=0,
            padx=10,
            pady=10,
        )
        self.text_area.pack(fill="both", expand=True)

        self.text_area.tag_config(
            "normal_self",
            foreground=self.colors["fg_self"],
            background=self.colors["bg_self"],
            justify="right",
            rmargin=10,
        )
        self.text_area.tag_config(
            "normal_peer",
            foreground=self.colors["fg_peer"],
            background=self.colors["bg_peer"],
            justify="left",
            lmargin1=10,
        )
        self.text_area.tag_config("time_tag", foreground="#888", font=("微软雅黑", 8))

        sb = SmartScrollbar(
            self.main_chat,
            command=self.text_area.yview,
            bg_color=self.colors["bg_root"],
        )
        sb.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")
        self.text_area.config(yscrollcommand=sb.set)

        # 输入区
        input_frm = tk.Frame(self.main_chat, height=120, bg=self.colors["bg_root"])
        input_frm.pack(fill="x", side="bottom")
        tk.Frame(input_frm, height=1, bg=self.colors["border"]).pack(fill="x")

        self.input_area = tk.Text(
            input_frm,
            height=5,
            bg=self.colors["bg_input"],
            fg=self.colors["fg_primary"],
            font=THEMES["normal"]["font_main"],
            bd=0,
            insertbackground=self.colors["fg_primary"],
            padx=10,
            pady=5,
        )
        self.input_area.pack(fill="both", expand=True)
        self.input_area.bind("<Return>", self._on_return)

    def reset_chat_area(self):
        self.header_label.config(text="未选择联系人")
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", tk.END)
        self.text_area.config(state="disabled")
        self.controller.target_addr = None

    def refresh_contacts(self):
        self.contact_list.delete(0, tk.END)
        for c in self.controller.displayed_contacts:
            self.contact_list.insert(tk.END, f" {c['name']}")

    def _on_contact_select(self, event):
        sel = self.contact_list.curselection()
        if not sel:
            return
        try:
            c = self.controller.displayed_contacts[sel[0]]
            self.controller.set_target(c)
            self.header_label.config(text=c["name"])
        except IndexError:
            pass

    def _show_context_menu(self, event):
        idx = self.contact_list.nearest(event.y)
        self.contact_list.selection_clear(0, tk.END)
        self.contact_list.selection_set(idx)
        self.contact_list.activate(idx)
        self._on_contact_select(None)
        self.context_menu.post(event.x_root, event.y_root)

    def _menu_modify(self):
        self.controller.modify_contact()
        self.refresh_contacts()

    def _menu_delete(self):
        self.controller.delete_contact()
        self.refresh_contacts()

    def _add_contact(self):
        self.controller.add_new_contact()
        self.refresh_contacts()

    def _on_return(self, event):
        if event.state & 0x0004:
            return
        msg = self.input_area.get("1.0", "end-1c").strip()
        self.input_area.delete("1.0", tk.END)
        self.controller.handle_chat_send(msg, "normal_self")
        return "break"

    def log(self, text, tag="normal_peer", no_newline=False):
        self.text_area.config(state="normal")
        self.text_area.insert(tk.END, text + ("" if no_newline else "\n"), tag)
        self.text_area.see(tk.END)
        self.text_area.config(state="disabled")


# === WPS 视图 ===
class WpsView(tk.Frame):
    def __init__(self, master, controller, is_dark=False):
        scheme = THEMES["wps"]["dark"] if is_dark else THEMES["wps"]["light"]
        super().__init__(master, bg=scheme["bg_root"])
        self.controller = controller
        self._drag_data = {"x": 0, "y": 0}
        self.scheme = scheme

        self._build_title_bar(scheme)

        # Ribbon 功能区
        self.ribbon_container = tk.Frame(self, bg=scheme["bg_ribbon"], height=120)
        self.ribbon_container.pack(fill="x", side="top")
        self.ribbon_container.pack_propagate(False)

        self.tabs_frame = tk.Frame(
            self.ribbon_container, bg=scheme["bg_ribbon"], height=30
        )
        self.tabs_frame.pack(fill="x", side="top")

        self.tools_panel = tk.Frame(self.ribbon_container, bg=scheme["bg_ribbon"])
        self.tools_panel.pack(fill="both", expand=True, padx=10, pady=5)

        self.menu_tabs = [
            "开始",
            "插入",
            "页面布局",
            "引用",
            "审阅",
            "视图",
            "章节",
            "会员专享",
        ]
        self.current_tab_lbls = {}
        self._init_menu_tabs(scheme)
        self._switch_tab("开始")

        main_paned = tk.PanedWindow(
            self, orient="horizontal", bg=scheme["bg_root"], sashwidth=4
        )
        main_paned.pack(fill="both", expand=True)

        doc_container = tk.Frame(main_paned, bg=scheme["bg_root"])
        main_paned.add(doc_container)
        paper = tk.Frame(doc_container, bg=scheme["bg_paper"], padx=40, pady=40)
        paper.pack(fill="both", expand=True, padx=20, pady=10)

        self.doc_editor = tk.Text(
            paper,
            bg=scheme["bg_paper"],
            fg=scheme["fg_text"],
            font=THEMES["wps"]["font_doc"],
            wrap="word",
            bd=0,
            undo=True,
            insertbackground=scheme["fg_text"],
        )
        self.doc_editor.pack(fill="both", expand=True)
        self._init_doc_tags()
        self.doc_editor.insert(
            "1.0",
            "二、系统参数定义\n\n1. 质量浓度范围:\n   Range: 0 to 1000 ug/m3\n\n(在此处继续编写文档...)\n",
        )

        self._build_sidebar(main_paned, scheme)

    def _build_title_bar(self, style):
        title_bar = tk.Frame(self, bg=style["bg_header"], height=35)
        title_bar.pack(fill="x", side="top")
        title_bar.pack_propagate(False)
        title_bar.bind("<Button-1>", self.start_move)
        title_bar.bind("<B1-Motion>", self.do_move)

        tk.Label(
            title_bar,
            text=" W ",
            bg=style["bg_header"],
            fg="white",
            font=("Arial", 12, "bold"),
        ).pack(side="left", padx=10)

        # [修复] 这里的 title 从全局 THEMES 读取，而不是 style (因为 style 是子字典 dark/light)
        tk.Label(
            title_bar,
            text=THEMES["wps"]["title"],
            bg=style["bg_header"],
            fg="white",
            font=THEMES["wps"]["font_ui"],
        ).pack(side="left")

        btn_close = tk.Label(
            title_bar,
            text=" × ",
            bg=style["bg_header"],
            fg="white",
            font=("Arial", 14),
            width=3,
        )
        btn_close.pack(side="right")
        btn_close.bind("<Button-1>", lambda e: self.master.destroy())

        btn_min = tk.Label(
            title_bar,
            text=" — ",
            bg=style["bg_header"],
            fg="white",
            font=("Arial", 14),
            width=3,
        )
        btn_min.pack(side="right")
        btn_min.bind("<Button-1>", lambda e: self.master.iconify())

    def _build_sidebar(self, parent, style):
        sidebar = tk.Frame(parent, width=300, bg=style["bg_paper"])
        parent.add(sidebar)
        tk.Label(
            sidebar,
            text="✨ WPS AI 助手",
            font=("微软雅黑", 10, "bold"),
            bg=style["bg_paper"],
            fg=style["bg_header"],
            pady=10,
        ).pack(fill="x")

        self.chat_log = tk.Text(
            sidebar,
            bg=style["bg_paper"],
            fg=style["fg_ui"],
            font=THEMES["wps"]["font_ui"],
            state="disabled",
            bd=0,
            wrap="word",
        )
        self.chat_log.pack(side="top", fill="both", expand=True, padx=5)

        self.chat_log.tag_config(
            "ai_me",
            foreground="#333",
            background="#e1ecff",
            justify="right",
            lmargin1=20,
            rmargin=5,
        )
        self.chat_log.tag_config(
            "ai_peer",
            foreground=style["fg_ui"],
            background=style["bg_root"],
            justify="left",
            rmargin=20,
            lmargin1=5,
        )
        self.chat_log.tag_config(
            "time_tag", foreground="#999", font=("Arial", 8), justify="center"
        )

        input_frm = tk.Frame(sidebar, bg=style["bg_root"], height=40)
        input_frm.pack(side="bottom", fill="x", padx=10, pady=10)
        tk.Label(input_frm, text="Ask:", bg=style["bg_root"], fg="#aaa").pack(
            side="left"
        )
        self.input = tk.Entry(
            input_frm,
            bg=style["bg_root"],
            fg=style["fg_ui"],
            bd=0,
            font=THEMES["wps"]["font_ui"],
            insertbackground=style["fg_text"],
        )
        self.input.pack(side="left", fill="x", expand=True, padx=5)
        self.input.bind("<Return>", self._on_return)

    # [新增] 重置聊天区方法
    def reset_chat_area(self):
        self.chat_log.config(state="normal")
        self.chat_log.delete("1.0", tk.END)
        self.chat_log.config(state="disabled")
        self.controller.target_addr = None

    def _init_menu_tabs(self, style):
        for tab in self.menu_tabs:
            lbl = tk.Label(
                self.tabs_frame,
                text=tab,
                bg=style["bg_ribbon"],
                fg=style["fg_ui"],
                font=("微软雅黑", 9),
                padx=12,
                pady=5,
            )
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda e, t=tab: self._switch_tab(t))
            lbl.bind("<Enter>", lambda e, l=lbl: l.config(bg=style["bg_hover"]))
            lbl.bind("<Leave>", lambda e, l=lbl, t=tab: self._reset_tab_style(l, t))
            self.current_tab_lbls[tab] = lbl

    def _reset_tab_style(self, lbl, tab):
        if tab == self.active_tab:
            lbl.config(bg=self.scheme["bg_paper"])
        else:
            lbl.config(bg=self.scheme["bg_ribbon"])

    def _switch_tab(self, tab_name):
        self.active_tab = tab_name
        for name, lbl in self.current_tab_lbls.items():
            if name == tab_name:
                lbl.config(
                    bg=self.scheme["bg_paper"],
                    fg=self.scheme["bg_header"],
                    font=("微软雅黑", 9, "bold"),
                )
            else:
                lbl.config(
                    bg=self.scheme["bg_ribbon"],
                    fg=self.scheme["fg_ui"],
                    font=("微软雅黑", 9),
                )

        for widget in self.tools_panel.winfo_children():
            widget.destroy()

        if tab_name == "开始":
            self._render_home_toolbar()
        else:
            self._render_placeholder_toolbar(tab_name)

    def _render_home_toolbar(self):
        style = self.scheme

        def create_tool_btn(
            parent, text, cmd, width=3, fg=style["fg_ui"], font_spec=("Times", 9)
        ):
            btn = tk.Button(
                parent,
                text=text,
                font=font_spec,
                bg=style["bg_ribbon"],
                bd=0,
                fg=fg,
                command=cmd,
                width=width,
            )
            btn.pack(side="left", padx=1, pady=2)
            btn.bind("<Enter>", lambda e: btn.config(bg=style["bg_hover"]))
            btn.bind("<Leave>", lambda e: btn.config(bg=style["bg_ribbon"]))
            return btn

        f_font = tk.Frame(self.tools_panel, bg=style["bg_ribbon"])
        f_font.pack(side="left", padx=5)

        f_font_top = tk.Frame(f_font, bg=style["bg_ribbon"])
        f_font_top.pack(side="top", fill="x")
        font_families = sorted(font.families())
        self.cb_font = ttk.Combobox(
            f_font_top, values=font_families, width=12, state="readonly"
        )
        self.cb_font.set("Times New Roman")
        self.cb_font.pack(side="left", padx=2)
        self.cb_font.bind("<<ComboboxSelected>>", lambda e: self._apply_font_family())

        self.cb_size = ttk.Combobox(
            f_font_top, values=[8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 36, 48], width=3
        )
        self.cb_size.set(12)
        self.cb_size.pack(side="left", padx=2)
        self.cb_size.bind("<<ComboboxSelected>>", lambda e: self._apply_font_size())

        f_font_bot = tk.Frame(f_font, bg=style["bg_ribbon"])
        f_font_bot.pack(side="top", fill="x", pady=2)
        create_tool_btn(
            f_font_bot,
            "B",
            lambda: self._toggle_tag("bold"),
            font_spec=("Times", 9, "bold"),
        )
        create_tool_btn(
            f_font_bot,
            "I",
            lambda: self._toggle_tag("italic"),
            font_spec=("Times", 9, "italic"),
        )
        create_tool_btn(
            f_font_bot,
            "U",
            lambda: self._toggle_tag("underline"),
            font_spec=("Times", 9, "underline"),
        )
        create_tool_btn(
            f_font_bot,
            "abc",
            lambda: self._toggle_tag("overstrike"),
            font_spec=("Times", 9, "overstrike"),
        )

        create_tool_btn(
            f_font_bot,
            "A",
            self._choose_fg_color,
            fg="red",
            font_spec=("Times", 9, "bold"),
        )
        create_tool_btn(f_font_bot, "🖊️", self._choose_bg_color, fg="orange")

        ttk.Separator(self.tools_panel, orient="vertical").pack(
            side="left", fill="y", padx=5
        )

        f_para = tk.Frame(self.tools_panel, bg=style["bg_ribbon"])
        f_para.pack(side="left", padx=5)
        f_para_top = tk.Frame(f_para, bg=style["bg_ribbon"])
        f_para_top.pack(side="top", fill="x")
        create_tool_btn(f_para_top, "•-", lambda: self._insert_bullet("• "))
        create_tool_btn(f_para_top, "1.-", lambda: self._insert_bullet("1. "))
        create_tool_btn(f_para_top, "←", lambda: self._change_indent(-20))
        create_tool_btn(f_para_top, "→", lambda: self._change_indent(20))

        f_para_bot = tk.Frame(f_para, bg=style["bg_ribbon"])
        f_para_bot.pack(side="top", fill="x", pady=2)
        create_tool_btn(f_para_bot, "≡", lambda: self._set_align("left"))
        create_tool_btn(f_para_bot, "≍", lambda: self._set_align("center"))
        create_tool_btn(f_para_bot, "≣", lambda: self._set_align("right"))

    def _render_placeholder_toolbar(self, name):
        tk.Label(
            self.tools_panel,
            text=f"【{name}】功能模块待加载... (预留接口)",
            bg=self.scheme["bg_ribbon"],
            fg="#888",
        ).pack(expand=True)

    def _init_doc_tags(self):
        self.doc_editor.tag_config("bold", font=("Times New Roman", 12, "bold"))
        self.doc_editor.tag_config("italic", font=("Times New Roman", 12, "italic"))
        self.doc_editor.tag_config("underline", underline=True)
        self.doc_editor.tag_config("overstrike", overstrike=True)
        self.doc_editor.tag_config("align_left", justify="left")
        self.doc_editor.tag_config("align_center", justify="center")
        self.doc_editor.tag_config("align_right", justify="right")

    def _toggle_tag(self, tag_name):
        try:
            if tag_name in self.doc_editor.tag_names("sel.first"):
                self.doc_editor.tag_remove(tag_name, "sel.first", "sel.last")
            else:
                self.doc_editor.tag_add(tag_name, "sel.first", "sel.last")
        except tk.TclError:
            pass

    def _apply_font_family(self):
        f_family = self.cb_font.get()
        tag_name = f"font_{f_family}"
        self.doc_editor.tag_config(tag_name, font=(f_family, int(self.cb_size.get())))
        try:
            self.doc_editor.tag_add(tag_name, "sel.first", "sel.last")
        except:
            pass

    def _apply_font_size(self):
        try:
            size = int(self.cb_size.get())
            tag_name = f"size_{size}"
            self.doc_editor.tag_config(tag_name, font=(self.cb_font.get(), size))
            self.doc_editor.tag_add(tag_name, "sel.first", "sel.last")
        except:
            pass

    def _choose_fg_color(self):
        color = colorchooser.askcolor(title="选择字体颜色")[1]
        if color:
            tag_name = f"fg_{color}"
            self.doc_editor.tag_config(tag_name, foreground=color)
            try:
                self.doc_editor.tag_add(tag_name, "sel.first", "sel.last")
            except:
                pass

    def _choose_bg_color(self):
        color = colorchooser.askcolor(title="选择底纹颜色")[1]
        if color:
            tag_name = f"bg_{color}"
            self.doc_editor.tag_config(tag_name, background=color)
            try:
                self.doc_editor.tag_add(tag_name, "sel.first", "sel.last")
            except:
                pass

    def _set_align(self, align):
        try:
            self.doc_editor.tag_remove("align_left", "sel.first", "sel.last")
            self.doc_editor.tag_remove("align_center", "sel.first", "sel.last")
            self.doc_editor.tag_remove("align_right", "sel.first", "sel.last")
            self.doc_editor.tag_add(f"align_{align}", "sel.first", "sel.last")
        except:
            pass

    def _change_indent(self, delta):
        try:
            self.doc_editor.tag_config("indent_1", lmargin1=40, lmargin2=40)
            if delta > 0:
                self.doc_editor.tag_add("indent_1", "sel.first", "sel.last")
            else:
                self.doc_editor.tag_remove("indent_1", "sel.first", "sel.last")
        except:
            pass

    def _insert_bullet(self, symbol):
        self.doc_editor.insert("insert", f"\n{symbol}")

    def start_move(self, event):
        self._drag_data = {"x": event.x, "y": event.y}

    def do_move(self, event):
        x = self.master.winfo_x() + (event.x - self._drag_data["x"])
        y = self.master.winfo_y() + (event.y - self._drag_data["y"])
        self.master.geometry(f"+{x}+{y}")

    def _on_return(self, event):
        msg = self.input.get().strip()
        self.input.delete(0, tk.END)
        self.controller.handle_chat_send(msg, "ai_me")

    def log(self, text, tag="ai_peer", no_newline=False):
        self.chat_log.config(state="normal")
        self.chat_log.insert(tk.END, text + ("" if no_newline else "\n"), tag)
        self.chat_log.see(tk.END)
        self.chat_log.config(state="disabled")
