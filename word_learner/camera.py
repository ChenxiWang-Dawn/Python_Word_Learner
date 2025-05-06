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
        self.frame = None
        self.video_label = None
        self.is_running = False  # 添加运行状态标志
        self.update_thread = None  # 添加线程引用
    
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
        self.cap = cv2.VideoCapture(0)  # 0表示默认摄像头
        
        if not self.cap.isOpened():
            messagebox.showerror("错误", "无法打开摄像头")
            self.close_camera()
            return
        
        # 设置运行标志
        self.is_running = True
        
        # 启动视频更新线程
        self.update_thread = threading.Thread(target=self.update_frame, daemon=True)
        self.update_thread.start()
    
    def update_frame(self):
        """更新视频帧"""
        while self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # 转换颜色从BGR到RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 调整大小
                height, width = frame_rgb.shape[:2]
                max_height = 600
                if height > max_height:
                    scale = max_height / height
                    width = int(width * scale)
                    height = max_height
                    frame_rgb = cv2.resize(frame_rgb, (width, height))
                
                # 转换为PIL图像
                pil_img = Image.fromarray(frame_rgb)
                
                # 调整大小以适应窗口
                width, height = 640, 480
                pil_img = pil_img.resize((width, height), Image.LANCZOS)
                
                # 转换为Tkinter可用的图像
                img_tk = ImageTk.PhotoImage(image=pil_img)
                
                # 更新标签
                try:
                    if self.video_label and self.camera_window:
                        self.video_label.config(image=img_tk)
                        self.video_label.image = img_tk
                except tk.TclError:
                    break  # 如果窗口已关闭，退出循环
            
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
        # 停止视频更新
        self.is_running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)  # 等待线程结束
        
        # 释放摄像头
        if self.cap and self.cap.isOpened():
            self.cap.release()
        
        # 关闭窗口
        if self.camera_window:
            self.camera_window.destroy()
            self.camera_window = None