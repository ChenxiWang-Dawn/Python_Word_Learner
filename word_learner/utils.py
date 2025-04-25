import tkinter as tk
from tkinter import ttk, messagebox
import os
import webbrowser
from PIL import Image

def resize_image(img, max_width, max_height):
    """调整图片大小"""
    width, height = img.size
    
    # 计算缩放比例
    if width > max_width or height > max_height:
        ratio = min(max_width / width, max_height / height)
        width = int(width * ratio)
        height = int(height * ratio)
        img = img.resize((width, height), Image.LANCZOS)
    
    return img

def pronounce_word(word):
    """发音单词"""
    if not word:
        return False, "没有单词可发音"
    
    try:
        import platform
        system = platform.system()
        
        if system == "Darwin":  # macOS
            os.system(f"say {word}")
            return True, "发音成功"
        elif system == "Windows":
            try:
                import win32com.client
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Speak(word)
                return True, "发音成功"
            except ImportError:
                return False, "Windows系统需要安装pywin32库"
        else:
            return False, "当前系统不支持文本转语音"
    except Exception as e:
        return False, f"发音失败: {str(e)}"

def open_online_dictionary(word):
    """在线查询单词"""
    if not word:
        return False, "没有单词可查询"
    
    try:
        # 使用剑桥词典
        url = f"https://dictionary.cambridge.org/dictionary/english-chinese-simplified/{word}"
        webbrowser.open(url)
        return True, "已打开在线词典"
    except Exception as e:
        return False, f"打开在线词典失败: {str(e)}"

def ensure_dir_exists(directory):
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def create_styled_button(parent, text, command, side=tk.LEFT, padx=5):
    """创建统一样式的按钮"""
    btn = ttk.Button(parent, text=text, command=command)
    btn.pack(side=side, padx=padx)
    return btn

def create_scrollable_frame(parent):
    """创建可滚动的框架"""
    canvas = tk.Canvas(parent)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    return canvas, scrollable_frame