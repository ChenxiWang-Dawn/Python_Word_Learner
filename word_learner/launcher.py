#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import traceback


def main():
    try:
        # 添加调试信息
        print("启动器开始运行...")
        print(f"Python版本: {sys.version}")
        print(f"当前工作目录: {os.getcwd()}")

        # 确保当前目录在Python路径中
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        print(f"Python路径: {sys.path[:3]}...")  # 只显示前3个路径

        # 检查是否在打包环境中
        if hasattr(sys, '_MEIPASS'):
            print(f"检测到打包环境，临时目录: {sys._MEIPASS}")
            # 确保临时目录在Python路径中
            if sys._MEIPASS not in sys.path:
                sys.path.insert(0, sys._MEIPASS)

        # 列出当前目录中的文件
        print("当前目录文件:")
        for file in os.listdir(current_dir):
            if file.endswith('.py'):
                print(f"  {file}")

        # 导入并运行主应用
        print("正在导入应用...")
        from app import WordLearnerApp
        import tkinter as tk

        print("创建主窗口...")
        root = tk.Tk()
        print("创建应用实例...")
        app = WordLearnerApp(root)
        print("启动应用...")
        root.mainloop()

    except Exception as e:
        print(f"应用启动失败: {e}")
        print(traceback.format_exc())

        # 创建错误日志
        error_log = os.path.expanduser("~/Desktop/wordlearner_error.log")
        with open(error_log, "w", encoding="utf-8") as f:
            f.write(f"Error: {str(e)}\n")
            f.write(f"Traceback:\n{traceback.format_exc()}")
            f.write(f"\nPython版本: {sys.version}\n")
            f.write(f"当前工作目录: {os.getcwd()}\n")
            f.write(f"Python路径: {sys.path}\n")
            if hasattr(sys, '_MEIPASS'):
                f.write(f"打包临时目录: {sys._MEIPASS}\n")

        # 显示错误对话框
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("应用启动失败",
                                 f"应用启动失败：\n{str(e)}\n\n错误详情已保存到桌面的 wordlearner_error.log 文件")
            root.destroy()
        except:
            print(f"Error: {e}")
            print(traceback.format_exc())


if __name__ == "__main__":
    main()