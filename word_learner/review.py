import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import random
import datetime
from PIL import Image, ImageTk
from utils import resize_image, pronounce_word, open_online_dictionary

class ReviewManager:
    """复习管理器"""
    
    def __init__(self, root, db_path, api_key, status_bar):
        self.root = root
        self.db_path = db_path
        self.api_key = api_key
        self.status_bar = status_bar
        
        self.review_words = []
        self.current_word_index = 0
        self.current_word = None
        self.review_in_progress = False
    
    def create_review_page(self, parent):
        """创建复习页面"""
        page = ttk.Frame(parent)
        
        # 顶部控制区域
        control_frame = ttk.Frame(page)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(control_frame, text="复习模式:").pack(side=tk.LEFT, padx=5)
        self.review_mode_var = tk.StringVar(value="全部单词")
        review_modes = ["全部单词", "最近添加", "最少复习", "随机抽取"]
        mode_combo = ttk.Combobox(control_frame, textvariable=self.review_mode_var, values=review_modes, state="readonly", width=10)
        mode_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="数量:").pack(side=tk.LEFT, padx=5)
        self.review_count_var = tk.StringVar(value="10")
        count_combo = ttk.Combobox(control_frame, textvariable=self.review_count_var, values=["10", "20", "30", "50", "全部"], state="readonly", width=5)
        count_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="开始复习", command=self.start_review).pack(side=tk.LEFT, padx=20)
        
        # 复习区域
        self.review_frame = ttk.LabelFrame(page, text="复习")
        self.review_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 单词显示区域
        self.word_display_frame = ttk.Frame(self.review_frame)
        self.word_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 单词标签
        self.word_label = ttk.Label(self.word_display_frame, text="", font=("Arial", 24, "bold"))
        self.word_label.pack(pady=20)
        
        # 图片区域
        self.image_frame = ttk.Frame(self.word_display_frame)
        self.image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # 释义区域（初始隐藏）
        self.translation_frame = ttk.Frame(self.word_display_frame)
        
        ttk.Label(self.translation_frame, text="释义:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 0))
        self.translation_text = tk.Text(self.translation_frame, height=4, wrap=tk.WORD)
        self.translation_text.pack(fill=tk.X, expand=False, pady=5)
        
        ttk.Label(self.translation_frame, text="例句:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 0))
        self.example_text = tk.Text(self.translation_frame, height=6, wrap=tk.WORD)
        self.example_text.pack(fill=tk.X, expand=False, pady=5)
        
        # 按钮区域
        self.button_frame = ttk.Frame(self.review_frame)
        self.button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 显示释义按钮
        self.show_translation_btn = ttk.Button(self.button_frame, text="显示释义", command=self.show_translation)
        self.show_translation_btn.pack(side=tk.LEFT, padx=5)
        
        # 发音按钮
        ttk.Button(self.button_frame, text="发音", command=self.pronounce_current_word).pack(side=tk.LEFT, padx=5)
        
        # 在线查询按钮
        ttk.Button(self.button_frame, text="在线查询", command=self.query_online_current_word).pack(side=tk.LEFT, padx=5)
        
        # 记忆状态按钮
        self.memory_frame = ttk.Frame(self.button_frame)
        self.memory_frame.pack(side=tk.RIGHT)
        
        ttk.Button(self.memory_frame, text="记得", command=lambda: self.record_memory_status("recognized")).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.memory_frame, text="模糊", command=lambda: self.record_memory_status("fuzzy")).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.memory_frame, text="忘记", command=lambda: self.record_memory_status("forgotten")).pack(side=tk.LEFT, padx=5)
        
        # 导航按钮
        self.nav_frame = ttk.Frame(self.review_frame)
        self.nav_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(self.nav_frame, text="上一个", command=self.prev_word).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.nav_frame, text="下一个", command=self.next_word).pack(side=tk.LEFT, padx=5)
        
        self.progress_label = ttk.Label(self.nav_frame, text="0/0")
        self.progress_label.pack(side=tk.RIGHT, padx=5)
        
        # 初始状态
        self.reset_review_ui()
        
        return page
    
    def start_review(self):
        """开始复习"""
        # 获取复习模式和数量
        mode = self.review_mode_var.get()
        count_str = self.review_count_var.get()
        
        try:
            count = int(count_str) if count_str != "全部" else 9999
        except ValueError:
            count = 10
        
        # 从数据库加载单词
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 根据模式构建查询
        query = "SELECT id, word, translation, example, image_path FROM words"
        
        if mode == "最近添加":
            query += " ORDER BY added_date DESC"
        elif mode == "最少复习":
            query += " ORDER BY review_count ASC, added_date DESC"
        elif mode == "随机抽取":
            query += " ORDER BY RANDOM()"
        
        query += f" LIMIT {count}"
        
        cursor.execute(query)
        words = cursor.fetchall()
        conn.close()
        
        if not words:
            messagebox.showinfo("提示", "没有可复习的单词")
            return
        
        # 设置复习单词列表
        self.review_words = words
        self.current_word_index = 0
        self.review_in_progress = True
        
        # 显示第一个单词
        self.show_current_word()
        
        # 更新状态栏
        self.status_bar.config(text=f"复习开始，共 {len(words)} 个单词")
    
    def show_current_word(self):
        """显示当前复习单词"""
        if not self.review_words or self.current_word_index >= len(self.review_words):
            return
        
        # 获取当前单词数据
        word_data = self.review_words[self.current_word_index]
        self.current_word = word_data
        
        # 显示单词
        self.word_label.config(text=word_data[1])  # word
        
        # 重置释义区域
        self.translation_frame.pack_forget()
        self.translation_text.delete(1.0, tk.END)
        self.translation_text.insert(tk.END, word_data[2] or "")  # translation
        self.example_text.delete(1.0, tk.END)
        self.example_text.insert(tk.END, word_data[3] or "")  # example
        
        # 显示图片
        if word_data[4]:  # image_path
            try:
                img = Image.open(word_data[4])
                img = resize_image(img, 400, 300)
                photo = ImageTk.PhotoImage(img)
                
                self.image_label.config(image=photo)
                self.image_label.image = photo
            except Exception as e:
                self.image_label.config(image="")
                self.status_bar.config(text=f"无法加载图片: {str(e)}")
        else:
            self.image_label.config(image="")
        
        # 更新按钮状态
        self.show_translation_btn.config(state=tk.NORMAL)
        
        # 更新进度
        self.progress_label.config(text=f"{self.current_word_index + 1}/{len(self.review_words)}")
    
    def show_translation(self):
        """显示释义"""
        self.translation_frame.pack(fill=tk.BOTH, expand=True, before=self.button_frame)
        self.show_translation_btn.config(state=tk.DISABLED)
    
    def next_word(self):
        """下一个单词"""
        if not self.review_in_progress:
            return
        
        if self.current_word_index < len(self.review_words) - 1:
            self.current_word_index += 1
            self.show_current_word()
        else:
            messagebox.showinfo("提示", "已经是最后一个单词")
    
    def prev_word(self):
        """上一个单词"""
        if not self.review_in_progress:
            return
        
        if self.current_word_index > 0:
            self.current_word_index -= 1
            self.show_current_word()
        else:
            messagebox.showinfo("提示", "已经是第一个单词")
    
    def record_memory_status(self, status):
        """记录记忆状态"""
        if not self.review_in_progress or not self.current_word:
            return
        
        word_id = self.current_word[0]
        
        # 记录到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 添加复习记录
        cursor.execute(
            "INSERT INTO review_records (word_id, status) VALUES (?, ?)",
            (word_id, status)
        )
        
        # 更新单词复习次数和日期
        cursor.execute(
            "UPDATE words SET review_count = review_count + 1, last_review_date = datetime('now') WHERE id = ?",
            (word_id,)
        )
        
        # 根据记忆状态调整下次复习时间
        if status == "recognized":
            # 记得清楚，延长复习间隔
            cursor.execute(
                "UPDATE words SET review_interval = review_interval * 2, next_review_date = datetime('now', '+' || (review_interval * 2) || ' days') WHERE id = ?",
                (word_id,)
            )
        elif status == "fuzzy":
            # 记忆模糊，保持复习间隔
            cursor.execute(
                "UPDATE words SET next_review_date = datetime('now', '+' || review_interval || ' days') WHERE id = ?",
                (word_id,)
            )
        else:  # forgotten
            # 忘记了，缩短复习间隔
            cursor.execute(
                "UPDATE words SET review_interval = MAX(1, review_interval / 2), next_review_date = datetime('now', '+1 day') WHERE id = ?",
                (word_id,)
            )
        
        conn.commit()
        conn.close()
        
        # 自动进入下一个单词
        self.next_word()
    
    def pronounce_current_word(self):
        """发音当前单词"""
        if not self.review_in_progress or not self.current_word:
            return
        
        word = self.current_word[1]
        success, message = pronounce_word(word)
        if not success:
            self.status_bar.config(text=message)
    
    def query_online_current_word(self):
        """在线查询当前单词"""
        if not self.review_in_progress or not self.current_word:
            return
        
        word = self.current_word[1]
        success, message = open_online_dictionary(word)
        if not success:
            self.status_bar.config(text=message)
    
    def reset_review_ui(self):
        """重置复习界面"""
        self.word_label.config(text="点击'开始复习'按钮开始")
        self.image_label.config(image="")
        self.translation_frame.pack_forget()
        self.translation_text.delete(1.0, tk.END)
        self.example_text.delete(1.0, tk.END)
        self.progress_label.config(text="0/0")
        self.show_translation_btn.config(state=tk.DISABLED)