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
        
        # 保存原始窗口大小
        self.original_window_size = None
        
        self.review_words = []
        self.current_word_index = 0
        self.current_word = None
        self.review_in_progress = False
        
        # 添加记忆状态跟踪
        self.word_memory_status = {}  # 记录每个单词的记忆状态
    
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
        
        # 创建自定义按钮样式
        self.create_memory_button_styles()
        
        # 记忆状态按钮
        self.memory_frame = ttk.Frame(self.button_frame)
        self.memory_frame.pack(side=tk.RIGHT)
        
        # 使用自定义样式的按钮
        remember_btn = ttk.Button(self.memory_frame, text="记得", 
                                 command=lambda: self.record_memory_status("recognized"),
                                 style="Remember.TButton")
        remember_btn.pack(side=tk.LEFT, padx=5)
        
        fuzzy_btn = ttk.Button(self.memory_frame, text="模糊", 
                              command=lambda: self.record_memory_status("fuzzy"),
                              style="Fuzzy.TButton")
        fuzzy_btn.pack(side=tk.LEFT, padx=5)
        
        forget_btn = ttk.Button(self.memory_frame, text="忘记", 
                               command=lambda: self.record_memory_status("forgotten"),
                               style="Forget.TButton")
        forget_btn.pack(side=tk.LEFT, padx=5)
        
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
    
    def create_memory_button_styles(self):
        """创建记忆状态按钮的自定义样式"""
        style = ttk.Style()
        
        # 记得按钮 - 绿色
        style.configure("Remember.TButton",
                       padding=(15, 8),
                       font=("SF Pro Display", 11, "bold"),
                       background="#28a745",  # 绿色
                       foreground="white",
                       borderwidth=0,
                       relief='flat',
                       focuscolor='none')
        
        style.map("Remember.TButton",
                 background=[('active', '#218838'),  # 深绿色悬停
                           ('pressed', '#1e7e34')],   # 更深绿色点击
                 foreground=[('active', 'white'),
                           ('pressed', 'white')])
        
        # 模糊按钮 - 灰色
        style.configure("Fuzzy.TButton",
                       padding=(15, 8),
                       font=("SF Pro Display", 11, "bold"),
                       background="#6c757d",  # 灰色
                       foreground="white",
                       borderwidth=0,
                       relief='flat',
                       focuscolor='none')
        
        style.map("Fuzzy.TButton",
                 background=[('active', '#5a6268'),  # 深灰色悬停
                           ('pressed', '#495057')],   # 更深灰色点击
                 foreground=[('active', 'white'),
                           ('pressed', 'white')])
        
        # 忘记按钮 - 红色
        style.configure("Forget.TButton",
                       padding=(15, 8),
                       font=("SF Pro Display", 11, "bold"),
                       background="#dc3545",  # 红色
                       foreground="white",
                       borderwidth=0,
                       relief='flat',
                       focuscolor='none')
        
        style.map("Forget.TButton",
                 background=[('active', '#c82333'),  # 深红色悬停
                           ('pressed', '#bd2130')],   # 更深红色点击
                 foreground=[('active', 'white'),
                           ('pressed', 'white')])
    
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
        
        # 重置记忆状态跟踪
        self.word_memory_status.clear()
        
        # 显示第一个单词
        self.show_current_word()
        
        # 更新状态栏
        self.status_bar.config(text=f"复习开始，共 {len(words)} 个单词")
    
    def show_current_word(self):
        """显示当前复习单词"""
        if not self.review_words or self.current_word_index >= len(self.review_words):
            return
        
        # 保存当前窗口大小（如果还没保存的话）
        if self.original_window_size is None:
            self.original_window_size = (self.root.winfo_width(), self.root.winfo_height())
        
        # 恢复原始窗口大小
        if self.original_window_size:
            width, height = self.original_window_size
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        
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
        """显示释义并自动调整窗口大小"""
        # 显示释义区域
        self.translation_frame.pack(fill=tk.X, expand=False, pady=10)
        self.show_translation_btn.config(state=tk.DISABLED)
        
        # 更新界面以获取准确的尺寸
        self.root.update_idletasks()
        
        # 计算需要的额外高度
        translation_height = self.translation_text.winfo_reqheight()
        example_height = self.example_text.winfo_reqheight()
        labels_height = 60  # 两个标签的大概高度
        padding_height = 40  # 额外的padding
        
        extra_height = translation_height + example_height + labels_height + padding_height
        
        # 获取当前窗口尺寸
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()
        
        # 计算新的窗口高度（确保不超过屏幕高度的90%）
        screen_height = self.root.winfo_screenheight()
        max_height = int(screen_height * 0.9)
        new_height = min(current_height + extra_height, max_height)
        
        # 如果需要调整窗口大小
        if new_height > current_height:
            # 获取当前窗口位置
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            
            # 调整y坐标以保持窗口居中
            height_diff = new_height - current_height
            new_y = max(0, y - height_diff // 2)
            
            # 设置新的窗口大小和位置
            self.root.geometry(f"{current_width}x{new_height}+{x}+{new_y}")
            
            # 更新状态栏提示
            self.status_bar.config(text=f"窗口已自动调整大小以显示完整内容")
    
    def next_word(self):
        """下一个单词"""
        if not self.review_in_progress:
            return
        
        if self.current_word_index < len(self.review_words) - 1:
            self.current_word_index += 1
            self.show_current_word()
        else:
            # 复习结束，根据记忆状态给出不同提示
            self.check_review_completion()
    
    def check_review_completion(self):
        """检查复习完成情况并给出相应提示"""
        if not self.word_memory_status:
            messagebox.showinfo("提示", "已经是最后一个单词")
            return
        
        # 统计各种记忆状态
        recognized_count = sum(1 for status in self.word_memory_status.values() if status == "recognized")
        fuzzy_count = sum(1 for status in self.word_memory_status.values() if status == "fuzzy")
        forgotten_count = sum(1 for status in self.word_memory_status.values() if status == "forgotten")
        total_reviewed = len(self.word_memory_status)
        
        # 根据记忆状态给出不同提示
        if fuzzy_count == 0 and forgotten_count == 0:
            # 全部记得
            messagebox.showinfo("恭喜！", f"真棒，已全部复习！\n\n📊 复习统计：\n✅ 记得清楚：{recognized_count}个\n📝 总计：{total_reviewed}个单词")
            self.status_bar.config(text=f"复习完成！全部{total_reviewed}个单词都记得很清楚！")
        else:
            # 有模糊或忘记的单词
            result = messagebox.askyesno(
                "复习完成", 
                f"再来一遍？\n\n📊 本轮复习统计：\n✅ 记得清楚：{recognized_count}个\n🤔 记忆模糊：{fuzzy_count}个\n❌ 已忘记：{forgotten_count}个\n📝 总计：{total_reviewed}个单词\n\n是否重新复习模糊和忘记的单词？"
            )
            
            if result:
                # 重新复习模糊和忘记的单词
                self.restart_difficult_words()
            else:
                self.status_bar.config(text=f"复习完成！记得{recognized_count}个，模糊{fuzzy_count}个，忘记{forgotten_count}个")
    
    def restart_difficult_words(self):
        """重新复习模糊和忘记的单词"""
        # 筛选出需要重新复习的单词
        difficult_words = []
        for word_data in self.review_words:
            word_id = word_data[0]
            if word_id in self.word_memory_status:
                status = self.word_memory_status[word_id]
                if status in ["fuzzy", "forgotten"]:
                    difficult_words.append(word_data)
        
        if difficult_words:
            # 重置复习状态
            self.review_words = difficult_words
            self.current_word_index = 0
            self.word_memory_status.clear()  # 清空之前的记录
            
            # 开始新一轮复习
            self.show_current_word()
            self.status_bar.config(text=f"开始重新复习 {len(difficult_words)} 个需要加强的单词")
        else:
            messagebox.showinfo("提示", "没有需要重新复习的单词")
    
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
        
        # 记录当前单词的记忆状态
        self.word_memory_status[word_id] = status
        
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