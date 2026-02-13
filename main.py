# main.py
import sys
from PyQt6.QtWidgets import QApplication
from core.app_controller import AppController
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 初始化控制器和主窗口
    controller = AppController()
    main_win = MainWindow(controller)
    # 双向绑定
    controller.bind_ui(main_win)
    # 启动业务
    controller.start()
    # 进入事件循环
    sys.exit(app.exec())
