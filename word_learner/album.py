import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import datetime
from PIL import Image, ImageTk
from utils import resize_image


class AlbumManager:
    """相册管理器"""

    def __init__(self, root, db_path, status_bar):
        self.root = root
        self.db_path = db_path
        self.status_bar = status_bar
        self.current_image = None
        self.images = []
        self.sort_order = "DESC"  # 默认降序排列

        # 初始化数据库
        self.init_database()

    def init_database(self):
        """初始化相册数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建相册表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS album (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT UNIQUE,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            has_words BOOLEAN DEFAULT 0
        )
        ''')

        conn.commit()
        conn.close()

    def create_album_page(self, content_frame):
        """创建相册页面"""
        page = ttk.Frame(content_frame)

        # 顶部工具栏
        toolbar = ttk.Frame(page)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        # 排序按钮
        self.sort_btn = ttk.Button(toolbar, text="时间 ↓", command=self.toggle_sort_order)
        self.sort_btn.pack(side=tk.RIGHT, padx=5)

        # 创建滚动区域
        self.canvas = tk.Canvas(page)
        scrollbar = ttk.Scrollbar(page, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 加载相册图片
        self.load_album_images()

        return page

    def toggle_sort_order(self):
        """切换排序顺序"""
        if self.sort_order == "DESC":
            self.sort_order = "ASC"
            self.sort_btn.config(text="时间 ↑")
        else:
            self.sort_order = "DESC"
            self.sort_btn.config(text="时间 ↓")

        # 重新加载图片
        self.load_album_images()

    def load_album_images(self):
        """加载相册中的图片"""
        # 清空现有内容
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # 从数据库获取图片
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT image_path, added_date FROM album WHERE has_words = 1 ORDER BY added_date {self.sort_order}"
        )
        images = cursor.fetchall()
        conn.close()

        if not images:
            # 如果没有图片，显示提示
            ttk.Label(
                self.scrollable_frame,
                text="相册中还没有图片\n拍照并添加单词后，图片会自动保存到相册",
                font=("Arial", 12),
                justify=tk.CENTER
            ).pack(pady=50)
            return

        # 保存图片引用，防止被垃圾回收
        self.images = []

        # 创建网格布局
        row, col = 0, 0
        max_cols = 3  # 每行最多显示3张图片

        for img_path, added_date in images:
            if not os.path.exists(img_path):
                continue

            try:
                # 创建图片框架
                img_frame = ttk.Frame(self.scrollable_frame, width=200, height=200)
                img_frame.grid(row=row, column=col, padx=10, pady=10)
                img_frame.pack_propagate(False)  # 防止框架大小被内容改变

                # 加载并调整图片大小
                img = Image.open(img_path)
                img = self.resize_image(img, 180, 150)
                photo = ImageTk.PhotoImage(img)
                self.images.append(photo)  # 保存引用

                # 创建图片标签
                img_label = ttk.Label(img_frame, image=photo)
                img_label.pack(pady=(5, 0))

                # 添加日期标签
                date_obj = datetime.datetime.strptime(added_date, "%Y-%m-%d %H:%M:%S")
                date_str = date_obj.strftime("%Y/%m/%d %H:%M")
                ttk.Label(img_frame, text=date_str, font=("Arial", 9)).pack()

                # 绑定点击事件
                img_label.bind("<Button-1>", lambda e, path=img_path: self.show_image_detail(path))

                # 更新行列位置
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

            except Exception as e:
                print(f"加载图片出错: {str(e)}")

        self.status_bar.config(text=f"相册中共有 {len(images)} 张图片")

    def resize_image(self, img, max_width, max_height):
        """调整图片大小"""
        width, height = img.size

        # 计算缩放比例
        if width > max_width or height > max_height:
            ratio = min(max_width / width, max_height / height)
            width = int(width * ratio)
            height = int(height * ratio)
            img = img.resize((width, height), Image.LANCZOS)

        return img

    def show_image_detail(self, image_path):
        """显示图片详情"""
        # 创建详情对话框
        detail_window = tk.Toplevel(self.root)
        detail_window.title("图片详情")
        detail_window.transient(self.root)
        detail_window.grab_set()
        
        # 获取屏幕尺寸
        screen_width = detail_window.winfo_screenwidth()
        screen_height = detail_window.winfo_screenheight()
        
        # 先设置一个初始大小
        initial_width = min(1000, int(screen_width * 0.8))
        initial_height = min(700, int(screen_height * 0.8))
        detail_window.geometry(f"{initial_width}x{initial_height}")
        
        # 顶部工具栏
        toolbar = ttk.Frame(detail_window)
        toolbar.pack(fill=tk.X, padx=10, pady=10)
        
        # 返回按钮
        back_btn = ttk.Button(toolbar, text="← 返回", command=detail_window.destroy)
        back_btn.pack(side=tk.LEFT, padx=5)
        
        # 删除按钮
        delete_btn = ttk.Button(
            toolbar,
            text="删除",
            command=lambda: self.delete_image(image_path, detail_window)
        )
        delete_btn.pack(side=tk.RIGHT, padx=5)
        
        # 创建主滚动区域
        main_canvas = tk.Canvas(detail_window)
        main_scrollbar = ttk.Scrollbar(detail_window, orient="vertical", command=main_canvas.yview)
        scrollable_main_frame = ttk.Frame(main_canvas)
        
        scrollable_main_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_main_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        # 添加鼠标滚轮支持
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            main_canvas.unbind_all("<MouseWheel>")
        
        main_canvas.bind('<Enter>', _bind_to_mousewheel)
        main_canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        try:
            # 图片区域
            img_frame = ttk.Frame(scrollable_main_frame)
            img_frame.pack(fill=tk.X, padx=10, pady=10)
            
            # 加载图片
            img = Image.open(image_path)
            # 根据窗口大小动态调整图片大小
            max_img_width = initial_width - 100
            max_img_height = int(initial_height * 0.4)  # 图片占窗口高度的40%
            img = self.resize_image(img, max_img_width, max_img_height)
            photo = ImageTk.PhotoImage(img)
            
            # 保存引用
            self.current_image = photo
            
            # 显示图片
            img_label = ttk.Label(img_frame, image=photo)
            img_label.pack(pady=10)
            
            # 获取图片信息
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取添加日期
            cursor.execute("SELECT added_date FROM album WHERE image_path = ?", (image_path,))
            result = cursor.fetchone()
            if result:
                added_date = result[0]
            else:
                added_date = "未知"
            
            # 获取关联的单词
            cursor.execute("""
                SELECT word, translation FROM words 
                WHERE image_path = ?
                ORDER BY word
            """, (image_path,))
            words = cursor.fetchall()
            
            conn.close()
            
            # 显示图片信息
            info_frame = ttk.Frame(scrollable_main_frame)
            info_frame.pack(fill=tk.X, padx=20, pady=10)
            
            if added_date != "未知":
                date_obj = datetime.datetime.strptime(added_date, "%Y-%m-%d %H:%M:%S")
                date_str = date_obj.strftime("%Y年%m月%d日 %H:%M")
            else:
                date_str = "未知"
            
            ttk.Label(info_frame, text=f"添加时间: {date_str}", font=("Arial", 10)).pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"关联单词数: {len(words)}", font=("Arial", 10)).pack(anchor=tk.W)
            
            # 显示关联的单词
            if words:
                words_frame = ttk.LabelFrame(scrollable_main_frame, text="关联的单词")
                words_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
                
                # 创建单词列表
                columns = ("word", "translation")
                word_tree = ttk.Treeview(words_frame, columns=columns, show="headings")
                
                word_tree.heading("word", text="单词")
                word_tree.heading("translation", text="释义")
                
                word_tree.column("word", width=150)
                word_tree.column("translation", width=450)
                
                for word, translation in words:
                    word_tree.insert("", tk.END, values=(word, translation))
                
                word_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # 添加滚动条
                word_scrollbar = ttk.Scrollbar(words_frame, orient=tk.VERTICAL, command=word_tree.yview)
                word_scrollbar.place(relx=1, rely=0, relheight=1, anchor=tk.NE)
                word_tree.configure(yscrollcommand=word_scrollbar.set)
                
                # 根据单词数量动态调整窗口高度
                word_count = len(words)
                if word_count > 10:  # 如果单词较多，增加窗口高度
                    new_height = min(int(screen_height * 0.9), initial_height + (word_count - 10) * 25)
                    detail_window.geometry(f"{initial_width}x{new_height}")
            
            # 布局主滚动区域
            main_canvas.pack(side="left", fill="both", expand=True)
            main_scrollbar.pack(side="right", fill="y")
            
            # 更新窗口以计算实际需要的大小
            detail_window.update_idletasks()
            
            # 获取内容的实际大小
            required_width = scrollable_main_frame.winfo_reqwidth() + 50
            required_height = scrollable_main_frame.winfo_reqheight() + 100  # 加上工具栏高度
            
            # 限制最大尺寸不超过屏幕的90%
            max_width = int(screen_width * 0.9)
            max_height = int(screen_height * 0.9)
            
            final_width = min(max(required_width, 800), max_width)  # 最小800，最大屏幕90%
            final_height = min(max(required_height, 600), max_height)  # 最小600，最大屏幕90%
            
            # 设置最终窗口大小并居中
            x = (screen_width - final_width) // 2
            y = (screen_height - final_height) // 2
            detail_window.geometry(f"{final_width}x{final_height}+{x}+{y}")
            
            # 设置最小尺寸
            detail_window.minsize(600, 400)
            
            # 允许窗口调整大小
            detail_window.resizable(True, True)
            
        except Exception as e:
            # 如果出错，显示错误信息
            error_frame = ttk.Frame(scrollable_main_frame)
            error_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            ttk.Label(error_frame, text=f"无法加载图片: {str(e)}", font=("Arial", 12)).pack(pady=50)
            
            # 布局主滚动区域
            main_canvas.pack(side="left", fill="both", expand=True)
            main_scrollbar.pack(side="right", fill="y")

    def delete_image(self, image_path, detail_window=None):
        """从相册中删除图片"""
        if not messagebox.askyesno("确认删除", "确定要删除这张图片吗？\n这将同时删除所有关联的单词记录。"):
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 删除相册记录
            cursor.execute("DELETE FROM album WHERE image_path = ?", (image_path,))

            # 获取关联的单词ID
            cursor.execute("SELECT id FROM words WHERE image_path = ?", (image_path,))
            word_ids = [row[0] for row in cursor.fetchall()]

            # 删除复习记录
            for word_id in word_ids:
                cursor.execute("DELETE FROM review_records WHERE word_id = ?", (word_id,))

            # 删除单词记录
            cursor.execute("DELETE FROM words WHERE image_path = ?", (image_path,))

            conn.commit()
            conn.close()

            # 关闭详情窗口
            if detail_window:
                detail_window.destroy()

            # 重新加载相册
            self.load_album_images()

            messagebox.showinfo("成功", "图片已从相册中删除")

        except Exception as e:
            messagebox.showerror("错误", f"删除图片失败: {str(e)}")

    def add_image_to_album(self, image_path, has_words=True):
        """添加图片到相册"""
        if not image_path or not os.path.exists(image_path):
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查图片是否已存在
            cursor.execute("SELECT id FROM album WHERE image_path = ?", (image_path,))
            existing = cursor.fetchone()

            if existing:
                # 如果已存在，更新has_words状态
                cursor.execute(
                    "UPDATE album SET has_words = ? WHERE image_path = ?",
                    (1 if has_words else 0, image_path)
                )
            else:
                # 如果不存在，添加新记录
                cursor.execute(
                    "INSERT INTO album (image_path, has_words) VALUES (?, ?)",
                    (image_path, 1 if has_words else 0)
                )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"添加图片到相册失败: {str(e)}")
            return False
