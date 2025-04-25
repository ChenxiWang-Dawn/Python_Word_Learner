import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import random
from PIL import Image, ImageTk
from utils import resize_image, pronounce_word, open_online_dictionary

class WordsManager:
    """单词管理器"""
    
    def __init__(self, root, db_path, api_key, status_bar, review_manager):
        self.root = root
        self.db_path = db_path
        self.api_key = api_key
        self.status_bar = status_bar
        self.review_manager = review_manager
        
        self.words = []
        self.current_word_index = 0
        self.current_word = None
    
    def create_words_page(self, parent):
        """创建单词页面"""
        page = ttk.Frame(parent)
        
        # 顶部控制区域
        control_frame = ttk.Frame(page)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(control_frame, text="显示模式:").pack(side=tk.LEFT, padx=5)
        self.display_mode_var = tk.StringVar(value="全部单词")
        display_modes = ["全部单词", "最近添加", "最少复习", "随机抽取"]
        mode_combo = ttk.Combobox(control_frame, textvariable=self.display_mode_var, values=display_modes, state="readonly", width=10)
        mode_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="数量:").pack(side=tk.LEFT, padx=5)
        self.display_count_var = tk.StringVar(value="20")
        count_combo = ttk.Combobox(control_frame, textvariable=self.display_count_var, values=["10", "20", "50", "100", "全部"], state="readonly", width=5)
        count_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="加载单词", command=self.load_words).pack(side=tk.LEFT, padx=20)
        
        # 单词浏览区域
        self.browse_frame = ttk.LabelFrame(page, text="单词浏览")
        self.browse_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左右分栏
        left_frame = ttk.Frame(self.browse_frame, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        right_frame = ttk.Frame(self.browse_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 左侧单词列表
        ttk.Label(left_frame, text="单词列表:").pack(anchor=tk.W, pady=(0, 5))
        
        # 创建带滚动条的列表框
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.word_listbox = tk.Listbox(list_frame)
        self.word_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.word_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.word_listbox.config(yscrollcommand=scrollbar.set)
        
        # 绑定选择事件
        self.word_listbox.bind('<<ListboxSelect>>', self.on_word_select)
        
        # 右侧单词详情
        self.detail_frame = ttk.Frame(right_frame)
        self.detail_frame.pack(fill=tk.BOTH, expand=True)
        
        # 单词标签
        self.word_label = ttk.Label(self.detail_frame, text="", font=("Arial", 20, "bold"))
        self.word_label.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # 图片区域
        self.image_frame = ttk.Frame(self.detail_frame)
        self.image_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack()
        
        # 释义区域
        ttk.Label(self.detail_frame, text="释义:", font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.translation_text = tk.Text(self.detail_frame, height=4, wrap=tk.WORD)
        self.translation_text.pack(fill=tk.X, expand=False, padx=10, pady=5)
        
        # 例句区域
        ttk.Label(self.detail_frame, text="例句:", font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.example_text = tk.Text(self.detail_frame, height=6, wrap=tk.WORD)
        self.example_text.pack(fill=tk.X, expand=False, padx=10, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(self.detail_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="发音", command=self.pronounce_current_word).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="在线查询", command=self.query_online_current_word).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="标记为已复习", command=self.mark_current_as_reviewed).pack(side=tk.LEFT, padx=5)
        
        # 导航区域
        nav_frame = ttk.Frame(self.detail_frame)
        nav_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(nav_frame, text="上一个", command=self.prev_word).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="下一个", command=self.next_word).pack(side=tk.LEFT, padx=5)
        
        self.progress_label = ttk.Label(nav_frame, text="0/0")
        self.progress_label.pack(side=tk.RIGHT, padx=5)
        
        return page
    
    def load_words(self):
        """加载单词"""
        # 获取显示模式和数量
        mode = self.display_mode_var.get()
        count_str = self.display_count_var.get()
        
        try:
            count = int(count_str) if count_str != "全部" else 9999
        except ValueError:
            count = 20
        
        # 从数据库加载单词
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 根据模式构建查询
        query = "SELECT id, word, translation, example, image_path, review_count FROM words"
        
        if mode == "最近添加":
            query += " ORDER BY added_date DESC"
        elif mode == "最少复习":
            query += " ORDER BY review_count ASC, added_date DESC"
        elif mode == "随机抽取":
            query += " ORDER BY RANDOM()"
        else:  # 全部单词
            query += " ORDER BY word"
        
        query += f" LIMIT {count}"
        
        cursor.execute(query)
        words = cursor.fetchall()
        conn.close()
        
        if not words:
            messagebox.showinfo("提示", "没有找到单词")
            return
        
        # 更新单词列表
        self.words = words
        self.current_word_index = 0
        
        # 清空列表框
        self.word_listbox.delete(0, tk.END)
        
        # 添加单词到列表框
        for word in words:
            self.word_listbox.insert(tk.END, f"{word[1]} ({word[5]})")
        
        # 选中第一个单词
        self.word_listbox.selection_set(0)
        self.on_word_select(None)
        
        # 更新状态栏
        self.status_bar.config(text=f"已加载 {len(words)} 个单词")
    
    def on_word_select(self, event):
        """当选择单词列表中的单词时"""
        selection = self.word_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_word_index = index
            self.show_word_details(index)
    
    def show_word_details(self, index):
        """显示单词详情"""
        if not self.words or index >= len(self.words):
            return
        
        # 获取单词数据
        word_data = self.words[index]
        self.current_word = word_data
        
        # 显示单词
        self.word_label.config(text=word_data[1])  # word
        
        # 显示释义
        self.translation_text.config(state=tk.NORMAL)
        self.translation_text.delete(1.0, tk.END)
        self.translation_text.insert(tk.END, word_data[2] or "")  # translation
        self.translation_text.config(state=tk.DISABLED)
        
        # 显示例句
        self.example_text.config(state=tk.NORMAL)
        self.example_text.delete(1.0, tk.END)
        self.example_text.insert(tk.END, word_data[3] or "")  # example
        self.example_text.config(state=tk.DISABLED)
        
        # 显示图片
        if word_data[4]:  # image_path
            try:
                img = Image.open(word_data[4])
                img = resize_image(img, 300, 200)
                photo = ImageTk.PhotoImage(img)
                
                self.image_label.config(image=photo)
                self.image_label.image = photo
            except Exception as e:
                self.image_label.config(image="")
                self.status_bar.config(text=f"无法加载图片: {str(e)}")
        else:
            self.image_label.config(image="")
        
        # 更新进度
        self.progress_label.config(text=f"{index + 1}/{len(self.words)}")
    
    def next_word(self):
        """下一个单词"""
        if not self.words:
            return
        
        if self.current_word_index < len(self.words) - 1:
            self.current_word_index += 1
            self.word_listbox.selection_clear(0, tk.END)
            self.word_listbox.selection_set(self.current_word_index)
            self.word_listbox.see(self.current_word_index)
            self.show_word_details(self.current_word_index)
        else:
            messagebox.showinfo("提示", "已经是最后一个单词")
    
    def prev_word(self):
        """上一个单词"""
        if not self.words:
            return
        
        if self.current_word_index > 0:
            self.current_word_index -= 1
            self.word_listbox.selection_clear(0, tk.END)
            self.word_listbox.selection_set(self.current_word_index)
            self.word_listbox.see(self.current_word_index)
            self.show_word_details(self.current_word_index)
        else:
            messagebox.showinfo("提示", "已经是第一个单词")
    
    def pronounce_current_word(self):
        """发音当前单词"""
        if not self.current_word:
            return
        
        word = self.current_word[1]
        success, message = pronounce_word(word)
        if not success:
            self.status_bar.config(text=message)
    
    def query_online_current_word(self):
        """在线查询当前单词"""
        if not self.current_word:
            return
        
        word = self.current_word[1]
        success, message = open_online_dictionary(word)
        if not success:
            self.status_bar.config(text=message)
    
    def mark_current_as_reviewed(self):
        """标记当前单词为已复习"""
        if not self.current_word:
            return
        
        word_id = self.current_word[0]
        
        # 更新数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE words SET review_count = review_count + 1, last_review_date = datetime('now') WHERE id = ?",
            (word_id,)
        )
        conn.commit()
        conn.close()
        
        # 更新显示
        self.words[self.current_word_index] = list(self.words[self.current_word_index])
        self.words[self.current_word_index][5] += 1  # 增加复习次数
        self.words[self.current_word_index] = tuple(self.words[self.current_word_index])
        
        # 更新列表显示
        self.word_listbox.delete(self.current_word_index)
        self.word_listbox.insert(self.current_word_index, 
                                f"{self.words[self.current_word_index][1]} ({self.words[self.current_word_index][5]})")
        self.word_listbox.selection_set(self.current_word_index)
        
        messagebox.showinfo("成功", f"单词 '{self.words[self.current_word_index][1]}' 已标记为已复习")