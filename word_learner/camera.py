import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import time

class CameraCapture:
    """摄像头捕获类"""
    
    def __init__(self, parent):
        self.parent = parent
        self.camera_window = None
        self.cap = None
        self.is_running = False
        self.frame = None
    
    def open_camera(self):
        """打开摄像头窗口"""
        # 创建新窗口
        self.camera_window = tk.Toplevel(self.parent)
        self.camera_window.title("拍照")
        self.camera_window.geometry("800x600")
        self.camera_window.protocol("WM_DELETE_WINDOW", self.close_camera)
        
        # 创建视频显示标签
        self.video_label = ttk.Label(self.camera_window)
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建按钮
        btn_frame = ttk.Frame(self.camera_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.capture_btn = ttk.Button(btn_frame, text="拍照", command=self.capture)
        self.capture_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="取消", command=self.close_camera).pack(side=tk.RIGHT, padx=5)
        
        # 打开摄像头
        self.is_running = True
        self.cap = cv2.VideoCapture(0)  # 0表示默认摄像头
        
        if not self.cap.isOpened():
            messagebox.showerror("错误", "无法打开摄像头")
            self.close_camera()
            return
        
        # 开始视频流
        threading.Thread(target=self.update_frame, daemon=True).start()
    
    def update_frame(self):
        """更新视频帧"""
        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                # 转换颜色从BGR到RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 转换为PIL图像
                pil_img = Image.fromarray(frame_rgb)
                
                # 调整大小以适应窗口
                width, height = 640, 480
                pil_img = pil_img.resize((width, height), Image.LANCZOS)
                
                # 转换为Tkinter可用的图像
                img_tk = ImageTk.PhotoImage(image=pil_img)
                
                # 更新标签
                self.video_label.config(image=img_tk)
                self.video_label.image = img_tk  # 保持引用以防止垃圾回收
            
            # 短暂休眠以减少CPU使用
            time.sleep(0.03)
    
    def capture(self):
        """拍照"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # 转换颜色从BGR到RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 保存为PIL图像
                self.frame = Image.fromarray(frame_rgb)
                
                # 关闭摄像头窗口
                self.close_camera()
    
    def close_camera(self):
        """关闭摄像头"""
        self.is_running = False
        
        # 释放摄像头
        if self.cap and self.cap.isOpened():
            self.cap.release()
        
        # 关闭窗口
        if self.camera_window:
            self.camera_window.destroy()
            self.camera_window = None