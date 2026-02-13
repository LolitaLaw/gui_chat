# core/cmd_processor.py
import sys
import os
import code
import subprocess


class StdoutCatcher:
    def __init__(self, callback):
        self.callback = callback

    def write(self, text):
        self.callback(text)

    def flush(self):
        pass


class CmdProcessor:
    def __init__(self, output_callback):
        self.output_callback = output_callback
        self.current_path = os.getcwd()
        self.in_python_mode = False
        self.py_locals = {}
        self.console = code.InteractiveConsole(self.py_locals)
        self.redirector = StdoutCatcher(self._on_py_stdout)

    def _on_py_stdout(self, text):
        self.output_callback(text, "info")

    def process(self, cmd: str) -> bool:
        """
        处理命令。
        返回 True 表示命令已被处理（是系统命令或Python命令）。
        返回 False 表示不是命令，应该被当作聊天消息发送。
        """
        cmd = cmd.strip()
        if not cmd:
            self.output_callback(f"{self.current_path}>", "info")
            return True

        # 1. Python 模式
        if not self.in_python_mode and cmd.lower() == "python":
            self.in_python_mode = True
            self.output_callback(f"Python {sys.version.split()[0]} on win32\n>>> ", "info")
            return True

        if self.in_python_mode:
            if cmd.lower() in ["exit()", "quit()"]:
                self.in_python_mode = False
                self.output_callback(f"\n{self.current_path}>", "info")
                return True

            old_stdout = sys.stdout
            sys.stdout = self.redirector
            try:
                more = self.console.push(cmd)
                sys.stdout = old_stdout
                self.output_callback("... " if more else ">>> ", "info")
            except Exception as e:
                sys.stdout = old_stdout
                self.output_callback(f"{e}\n>>> ", "error")
            return True

        # 2. 内部命令处理
        lower_cmd = cmd.lower()
        if lower_cmd.startswith("cd "):
            try:
                os.chdir(cmd[3:].strip())
                self.current_path = os.getcwd()
            except Exception as e:
                self.output_callback(f"{e}\n", "error")
            self.output_callback(f"{self.current_path}>", "info")
            return True
        elif lower_cmd in ["cls", "clear"]:
            self.output_callback("", "clear")
            self.output_callback(f"{self.current_path}>", "info")
            return True

        # 3. 系统命令白名单 (防止聊天内容 "Hello" 报错)
        # 只有这些命令才会被当做系统指令执行，其他的都视为聊天
        whitelist = ["dir", "ipconfig", "ping", "ver", "whoami", "echo", "netstat", "tasklist"]
        is_system_cmd = False
        if lower_cmd.split()[0] in whitelist:
            is_system_cmd = True

        if is_system_cmd:
            try:
                # 隐藏窗口执行，避免弹出黑框
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="gbk", startupinfo=startupinfo)
                if res.stdout:
                    self.output_callback(res.stdout, "info")
                if res.stderr:
                    self.output_callback(res.stderr, "error")
            except Exception as e:
                self.output_callback(str(e) + "\n", "error")

            self.output_callback(f"{self.current_path}>", "info")
            return True

        # 如果不是 Python 也是系统命令，返回 False，交给 Controller 发送聊天
        return False
