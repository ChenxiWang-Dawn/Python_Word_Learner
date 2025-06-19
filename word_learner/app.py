import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sqlite3
import json
from PIL import Image, ImageTk
import threading
import time

# 导入自定义模块
from camera import CameraCapture
from review import ReviewManager
from words import WordsManager
from album import AlbumManager
from utils import resize_image, pronounce_word, open_online_dictionary
from word_details import WordDetailsManager
from image_manager import ImageManager
from api_service import APIService

class WordLearnerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 拍照学单词 - Photo Word Learning")
        self.root.geometry("1200x900")  # 增加窗口大小
        self.root.minsize(1000, 800)    # 增加最小尺寸
        
        # 设置窗口图标和属性
        try:
            # 如果有图标文件的话
            if os.path.exists("word_learner/images/icon.ico"):
                self.root.iconbitmap("word_learner/images/icon.ico")
        except:
            pass
            
        # 设置窗口居中
        self.center_window()
        
        # 配置
        self.api_key = "sk-5ddc81d9a00048f898f0c80f405fdf24"  # 需要设置OpenAI API密钥
        # 确保数据库路径指向word_learner目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(script_dir, "words.db")
        self.current_image_path = None
        self.recognized_words = []
        self.current_word_index = 0
        self.current_page = "camera"  # 当前显示的页面
        
        # 初始化服务和管理器
        self.init_services()
        
        # 初始化数据库
        self.init_database()
        
        # 初始化主题系统
        self.init_themes()
        
        # 设置样式（在创建UI之前）
        self.set_styles()
        
        # 创建UI
        self.create_ui()
        
        # 确保窗口大小合适
        self.root.update()
        min_height = self.navbar.winfo_reqheight() + self.status_bar.winfo_reqheight() + 700
        if self.root.winfo_height() < min_height:
            self.root.geometry(f"{self.root.winfo_width()}x{min_height}")
    
    def center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = 1200
        height = 900
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def init_services(self):
        """初始化各种服务和管理器"""
        self.api_service = APIService(self.api_key)
        # self.api_service.set_mock_mode(True)
        self.image_manager = ImageManager()
        self.word_details_manager = WordDetailsManager(self.db_path)
    
    def init_database(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建单词表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE,
            translation TEXT,
            example TEXT,
            image_path TEXT,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            review_count INTEGER DEFAULT 0,
            last_review_date TIMESTAMP
        )
        ''')
        
        # 检查是否需要添加新字段
        cursor.execute("PRAGMA table_info(words)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 添加缺失的字段
        if "next_review_date" not in columns:
            cursor.execute("ALTER TABLE words ADD COLUMN next_review_date TIMESTAMP")
        
        if "review_interval" not in columns:
            cursor.execute("ALTER TABLE words ADD COLUMN review_interval REAL DEFAULT 1")
        
        # 创建复习记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS review_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER,
            review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT,  -- "recognized", "fuzzy", "forgotten"
            FOREIGN KEY (word_id) REFERENCES words (id)
        )
        ''')
        
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
    
    def init_themes(self):
        """初始化主题系统"""
        # 默认主题
        self.current_theme = "blue"
        
        # 主题配置
        self.themes = {
            "blue": {
                "name": "蓝色主题",
                "primary": "#3670ee",      # RGB(54, 112, 238)
                "primary_hover": "#2861de", # RGB(40, 97, 222)
                "description": "经典蓝色，专业稳重"
            },
            "orange": {
                "name": "橙色主题", 
                "primary": "#e67e22",      # 优化后的橙色，更温和
                "primary_hover": "#d35400", # 深橙色，对比更明显
                "description": "温暖橙色，活力舒适"
            },
            "green": {
                "name": "深绿主题",
                "primary": "#27ae60",      # 深绿色，专业感
                "primary_hover": "#1e8449", # 更深的绿色
                "description": "自然绿色，清新护眼"
            }
        }
    
    def load_settings(self):
        """加载用户设置"""
        try:
            # 从数据库或配置文件加载主题设置
            # 这里暂时使用默认值，您可以后续添加持久化存储
            pass
        except:
            pass
    
    def save_theme_setting(self, theme_name):
        """保存主题设置"""
        self.current_theme = theme_name
        # 这里可以添加到数据库或配置文件的持久化存储
        # 暂时只在内存中保存
        
        # 更新所有相关组件的样式
        self.update_theme_colors()
    
    def update_theme_colors(self):
        """更新主题颜色"""
        # 重新设置样式
        self.set_styles()
        
        # 更新导航栏按钮颜色
        if hasattr(self, 'nav_buttons'):
            # 更新拍照按钮的颜色为当前主题色
            if "camera" in self.nav_buttons:
                current_theme_config = self.themes[self.current_theme]
                btn = self.nav_buttons["camera"]
                btn["color"] = current_theme_config["primary"]
                
                # 如果是当前活跃按钮，立即更新颜色
                if hasattr(self, 'active_nav_button') and self.active_nav_button == "camera":
                    self.update_nav_active_state("camera")
    
    def on_theme_change(self, theme_key):
        """处理主题切换"""
        if theme_key != self.current_theme:
            self.save_theme_setting(theme_key)
            
            # 显示提示信息
            if hasattr(self, 'status_bar'):
                theme_name = self.themes[theme_key]["name"]
                self.status_bar.config(text=f"已切换到 {theme_name}")
    
    def show_help(self):
        """显示帮助弹窗"""
        # 创建帮助对话框
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("📚 拍照学单词 - 使用帮助")
        help_dialog.geometry("600x500")
        help_dialog.transient(self.root)
        help_dialog.grab_set()
        help_dialog.resizable(False, False)
        
        # 设置对话框居中
        help_dialog.update_idletasks()
        x = (help_dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (help_dialog.winfo_screenheight() // 2) - (500 // 2)
        help_dialog.geometry(f"600x500+{x}+{y}")
        
        # 创建主框架
        main_frame = ttk.Frame(help_dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(main_frame, 
                               text="📚 拍照学单词使用指南", 
                               font=("SF Pro Display", 18, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 创建滚动框架
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 改进的鼠标滚轮支持
        def _on_mousewheel(event):
            # 检查Canvas是否有滚动内容
            if canvas.winfo_exists():
                # Windows系统
                if event.delta:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                # Linux系统
                elif event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")
        
        def _bind_to_mousewheel(event):
            # 绑定多种滚轮事件以支持不同平台
            canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows
            canvas.bind_all("<Button-4>", _on_mousewheel)   # Linux向上
            canvas.bind_all("<Button-5>", _on_mousewheel)   # Linux向下
            # 设置焦点到canvas
            canvas.focus_set()
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        
        # 绑定鼠标进入和离开事件
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # 确保Canvas可以获得焦点
        canvas.bind("<Button-1>", lambda e: canvas.focus_set())
        
        # 帮助内容
        help_content = [
            {
                "title": "🎯 主要功能",
                "content": "通过拍照或上传图片并识别文字的方式来学习英语单词，让学习更直观有趣！"
            },
            {
                "title": "📷 拍照识别",
                "steps": [
                    "点击底部导航栏的「📷 拍照识别」进入拍照页面",
                    "点击「拍照」按钮调用摄像头拍摄包含英文的照片",
                    "或点击「上传图片」选择手机相册中的图片",
                    "点击「识别文字」自动识别图片中的英文单词"
                ]
            },
            {
                "title": "📖 单词学习",
                "steps": [
                    "识别完成后，在图片上会显示识别到的单词标签",
                    "点击任意单词标签查看详细释义、音标和例句",
                    "点击「发音」按钮听取标准读音",
                    "点击「添加到生词本」收藏重要单词"
                ]
            },
            {
                "title": "📚 生词本管理",
                "steps": [
                    "在「📚 生词本」页面查看已收藏的单词",
                    "支持搜索和排序功能，快速找到目标单词",
                    "可以查看单词详情、删除不需要的单词",
                    "支持导出生词本为文件保存"
                ]
            },
            {
                "title": "🎯 练习复习",
                "steps": [
                    "在「🔄 复习」页面进行单词复习测试",
                    "在「📖 单词」页面进行填词练习",
                    "系统会根据你的学习情况智能安排复习计划",
                    "多种练习模式帮助巩固记忆"
                ]
            },
            {
                "title": "⚙️ 个性化设置",
                "steps": [
                    "在「⚙️ 设置」页面配置API密钥启用在线查询",
                    "选择喜欢的应用主题（蓝色/橙色/深绿）",
                    "自定义学习偏好和界面样式"
                ]
            }
        ]
        
        # 添加帮助内容
        for item in help_content:
            # 章节标题
            section_frame = ttk.Frame(scrollable_frame)
            section_frame.pack(fill=tk.X, pady=(0, 15))
            
            title_label = ttk.Label(section_frame, 
                                   text=item["title"], 
                                   font=("SF Pro Display", 14, "bold"))
            title_label.pack(anchor=tk.W, pady=(0, 8))
            
            if "content" in item:
                # 简单内容
                content_label = ttk.Label(section_frame, 
                                        text=item["content"],
                                        font=("SF Pro Display", 11),
                                        wraplength=520,
                                        justify=tk.LEFT)
                content_label.pack(anchor=tk.W, padx=(10, 0))
            
            elif "steps" in item:
                # 步骤列表
                for i, step in enumerate(item["steps"], 1):
                    step_label = ttk.Label(section_frame, 
                                         text=f"{i}. {step}",
                                         font=("SF Pro Display", 11),
                                         wraplength=500,
                                         justify=tk.LEFT)
                    step_label.pack(anchor=tk.W, padx=(10, 0), pady=(2, 0))
        
        # 布局滚动组件
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        #ttk.Button(button_frame, text="知道了", 
        #          command=help_dialog.destroy).pack(side=tk.RIGHT)
        
        # 设置焦点并确保滚轮事件在对话框打开后立即可用
        help_dialog.focus_set()
        help_dialog.after(100, lambda: canvas.focus_set())  # 延迟设置焦点
    
    def create_ui(self):
        """创建现代化用户界面"""
        # 创建主框架 - 使用现代化的内边距
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 添加标题栏
        self.create_header()
        
        # 创建内容区域
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # 创建底部导航栏
        self.create_bottom_navbar()
        
        # 创建底部状态栏
        self.create_statusbar()
        
        # 初始化相册管理器
        self.album_manager = AlbumManager(self.root, self.db_path, self.status_bar)
        
        # 初始化复习管理器
        self.review_manager = ReviewManager(self.root, self.db_path, self.api_key, self.status_bar)
        
        # 初始化单词管理器
        self.words_manager = WordsManager(self.root, self.db_path, self.api_key, self.status_bar, self.review_manager)
        
        # 创建不同的页面框架
        self.pages = {}
        self.pages["camera"] = self.create_camera_page()
        self.pages["wordbook"] = self.create_wordbook_page()
        self.pages["settings"] = self.create_settings_page()
        self.pages["review"] = self.review_manager.create_review_page(self.content_frame)
        self.pages["words"] = self.words_manager.create_words_page(self.content_frame)
        self.pages["album"] = self.album_manager.create_album_page(self.content_frame)

        # 默认显示相机页面
        self.show_page("camera")
    
    def create_header(self):
        """创建应用标题栏"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 应用标题
        title_label = ttk.Label(header_frame, 
                               text="📚 拍照学单词", 
                               font=("SF Pro Display", 24, "bold"),
                               foreground="#1f2937")
        title_label.pack(side=tk.LEFT)
        
        # 副标题
        subtitle_label = ttk.Label(header_frame, 
                                  text="通过拍照识别英文单词，智能学习助手", 
                                  font=("SF Pro Display", 12),
                                  foreground="#6b7280")
        subtitle_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # 右侧快捷操作
        actions_frame = ttk.Frame(header_frame)
        actions_frame.pack(side=tk.RIGHT)
        
        # 添加一些快捷按钮
        help_btn = ttk.Button(actions_frame, text="❓ 帮助", style="Secondary.TButton",
                             command=self.show_help)
        help_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        #settings_btn = ttk.Button(actions_frame, text="⚙️ 设置", style="Secondary.TButton",
        #                         command=lambda: self.show_page("settings"))
        #settings_btn.pack(side=tk.RIGHT)
    
    def show_page(self, page_name):
        """显示指定页面"""
        # 隐藏所有页面
        for page in self.pages.values():
            page.pack_forget()
        
        # 显示选定页面
        self.pages[page_name].pack(fill=tk.BOTH, expand=True)
        
        # 更新状态栏
        page_titles = {
            "camera": "📷 拍照识别",
            "wordbook": "📚 生词本",
            "album": "🖼️ 相册",
            "words": "📝 单词练习",
            "review": "🎯 复习模式",
            "settings": "⚙️ 设置"
        }
        self.status_bar.config(text=f"当前页面: {page_titles.get(page_name, page_name)}")
        
        # 更新当前页面名称
        self.current_page = page_name
        
        # 如果是复习页面，开始复习
        if page_name == "review":
            self.review_manager.start_review()
        
        # 如果是单词页面，加载单词
        elif page_name == "words":
            self.words_manager.load_words()

        # 如果是相册页面，刷新相册
        elif page_name == "album":
            self.album_manager.load_album_images()
    
    def create_bottom_navbar(self):
        """创建现代化底部导航栏"""
        # 创建主导航容器，使用渐变背景色
        self.navbar_container = tk.Frame(self.root, bg="#f8fafc", height=80)
        self.navbar_container.pack(side=tk.BOTTOM, fill=tk.X, pady=0)
        self.navbar_container.pack_propagate(False)
        
        # 创建导航栏内部框架
        self.navbar = tk.Frame(self.navbar_container, bg="#ffffff", height=75)
        self.navbar.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.navbar.pack_propagate(False)
        
        # 添加阴影效果（通过边框模拟）
        shadow_frame = tk.Frame(self.navbar_container, bg="#e2e8f0", height=1)
        shadow_frame.pack(fill=tk.X, side=tk.TOP)
        
        # 获取当前主题配置
        theme_config = self.themes[self.current_theme]
        
        # 导航按钮数据 - 包含图标和文字
        nav_items = [
            {"name": "camera", "icon": "📷", "text": "拍照识别", "color": theme_config['primary']},
            {"name": "wordbook", "icon": "📚", "text": "生词本", "color": "#10b981"},
            {"name": "album", "icon": "🖼️", "text": "相册", "color": "#f59e0b"},
            {"name": "words", "icon": "📖", "text": "单词", "color": "#8b5cf6"},
            {"name": "review", "icon": "🔄", "text": "复习", "color": "#ef4444"},
            {"name": "settings", "icon": "⚙️", "text": "设置", "color": "#6b7280"}
        ]
        
        # 存储按钮引用
        self.nav_buttons = {}
        self.nav_indicators = {}
        
        # 创建导航按钮
        for i, item in enumerate(nav_items):
            # 创建按钮容器
            btn_container = tk.Frame(self.navbar, bg="#ffffff")
            btn_container.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=2)
            
            # 创建按钮 - 水平布局
            btn_frame = tk.Frame(btn_container, bg="#ffffff", cursor="hand2")
            btn_frame.pack(expand=True, fill=tk.BOTH, pady=8)
            
            # 图标标签 - 左侧显示
            icon_label = tk.Label(btn_frame, text=item["icon"], 
                                font=("Apple Color Emoji", 18), 
                                bg="#ffffff", fg=item["color"])
            icon_label.pack(side=tk.LEFT, padx=(8, 4))
            
            # 文字标签 - 右侧显示，更清晰的字体和颜色
            text_label = tk.Label(btn_frame, text=item["text"], 
                                font=("SF Pro Display", 11, "normal"), 
                                bg="#ffffff", fg="#1a202c")
            text_label.pack(side=tk.LEFT, padx=(0, 8))
            
            # 活跃指示器
            indicator = tk.Frame(btn_container, bg="#ffffff", height=3)
            indicator.pack(side=tk.BOTTOM, fill=tk.X, padx=8)
            
            # 存储引用
            self.nav_buttons[item["name"]] = {
                "container": btn_container,
                "frame": btn_frame,
                "icon": icon_label,
                "text": text_label,
                "color": item["color"]
            }
            self.nav_indicators[item["name"]] = indicator
            
            # 绑定点击事件
            def make_nav_handler(page_name):
                return lambda e: self.handle_nav_click(page_name)
            
            for widget in [btn_frame, icon_label, text_label]:
                widget.bind("<Button-1>", make_nav_handler(item["name"]))
                widget.bind("<Enter>", lambda e, btn=item["name"]: self.on_nav_hover(btn, True))
                widget.bind("<Leave>", lambda e, btn=item["name"]: self.on_nav_hover(btn, False))
        
        # 设置默认活跃按钮
        self.active_nav_button = "camera"
        self.update_nav_active_state("camera")
    
    def handle_nav_click(self, page_name):
        """处理导航按钮点击"""
        if page_name != self.active_nav_button:
            # 添加点击动画效果
            self.animate_nav_click(page_name)
            
            # 更新活跃状态
            self.update_nav_active_state(page_name)
            
            # 切换页面
            self.show_page(page_name)
            self.active_nav_button = page_name
    
    def animate_nav_click(self, page_name):
        """导航按钮点击动画"""
        btn = self.nav_buttons[page_name]
        
        # 点击缩放效果
        def scale_down():
            btn["icon"].config(font=("Apple Color Emoji", 16))
            self.root.after(100, scale_up)
        
        def scale_up():
            btn["icon"].config(font=("Apple Color Emoji", 18))
        
        scale_down()
    
    def on_nav_hover(self, page_name, is_enter):
        """导航按钮悬停效果"""
        btn = self.nav_buttons[page_name]
        
        if is_enter and page_name != self.active_nav_button:
            # 悬停效果 - 背景色变化
            btn["frame"].config(bg="#f1f5f9")
            btn["icon"].config(bg="#f1f5f9")
            btn["text"].config(bg="#f1f5f9", fg=btn["color"], font=("SF Pro Display", 11, "bold"))
        else:
            # 恢复默认状态
            if page_name == self.active_nav_button:
                btn["frame"].config(bg="#eff6ff")
                btn["icon"].config(bg="#eff6ff")
                btn["text"].config(bg="#eff6ff", fg=btn["color"], font=("SF Pro Display", 11, "bold"))
            else:
                btn["frame"].config(bg="#ffffff")
                btn["icon"].config(bg="#ffffff")
                btn["text"].config(bg="#ffffff", fg="#374151", font=("SF Pro Display", 11))
    
    def update_nav_active_state(self, active_page):
        """更新导航栏活跃状态"""
        for page_name, btn in self.nav_buttons.items():
            indicator = self.nav_indicators[page_name]
            
            if page_name == active_page:
                # 活跃状态 - 蓝色背景和指示器
                btn["frame"].config(bg="#eff6ff")
                btn["icon"].config(bg="#eff6ff", fg=btn["color"])
                btn["text"].config(bg="#eff6ff", fg=btn["color"], font=("SF Pro Display", 11, "bold"))
                indicator.config(bg=btn["color"])
            else:
                # 非活跃状态 - 默认样式
                btn["frame"].config(bg="#ffffff")
                btn["icon"].config(bg="#ffffff", fg="#9ca3af")
                btn["text"].config(bg="#ffffff", fg="#6b7280", font=("SF Pro Display", 11))
                indicator.config(bg="#ffffff")
    
    def save_settings(self):
        """保存设置"""
        self.api_key = self.api_key_var.get().strip()
        # 更新API服务的API密钥
        self.api_service.set_api_key(self.api_key)
        # 更新复习管理器的API密钥
        self.review_manager.api_key = self.api_key
        # 更新单词管理器的API密钥
        self.words_manager.api_key = self.api_key
        messagebox.showinfo("成功", "设置已保存")
    
    def load_wordbook_words(self, search_term=""):
        """加载生词本单词"""
        # 清空现有项
        for item in self.word_tree.get_children():
            self.word_tree.delete(item)
        
        # 获取单词列表
        words = self.word_details_manager.get_wordbook_words(search_term, self.sort_var.get())
        
        # 添加到树形视图
        for word in words:
            self.word_tree.insert("", tk.END, values=word)
    
    def view_wordbook_details(self, selection):
        """查看生词本中单词的详情"""
        if not selection:
            messagebox.showinfo("提示", "请先选择一个单词")
            return
        
        item_id = selection[0]
        word = self.word_tree.item(item_id, "values")[0]
        
        # 从数据库获取详细信息
        word_data = self.word_details_manager.get_word_details(word)
        
        if not word_data:
            messagebox.showerror("错误", "无法获取单词详情")
            return
        
        # 创建详情对话框
        details_dialog = tk.Toplevel(self.root)
        details_dialog.title(f"单词详情 - {word}")
        details_dialog.geometry("600x500")
        details_dialog.transient(self.root)
        details_dialog.grab_set()
        
        # 显示单词信息
        ttk.Label(details_dialog, text=word, font=("Arial", 18, "bold")).pack(pady=(20, 10))
        
        # 释义
        ttk.Label(details_dialog, text="释义:", font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=20, pady=(10, 0))
        translation_text = tk.Text(details_dialog, height=4, wrap=tk.WORD)
        translation_text.pack(fill=tk.X, padx=20, pady=5)
        translation_text.insert(tk.END, word_data[2] or "")
        translation_text.config(state=tk.DISABLED)
        
        # 例句
        ttk.Label(details_dialog, text="例句:", font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=20, pady=(10, 0))
        example_text = tk.Text(details_dialog, height=6, wrap=tk.WORD)
        example_text.pack(fill=tk.X, padx=20, pady=5)
        example_text.insert(tk.END, word_data[3] or "")
        example_text.config(state=tk.DISABLED)
        
        # 图片
        if word_data[4]:  # image_path
            try:
                img = Image.open(word_data[4])
                img = resize_image(img, 300, 200)
                photo = ImageTk.PhotoImage(img)
                
                img_label = ttk.Label(details_dialog)
                img_label.pack(pady=10)
                img_label.config(image=photo)
                img_label.image = photo
            except Exception as e:
                ttk.Label(details_dialog, text=f"无法加载图片: {str(e)}").pack(pady=10)
        
        # 统计信息
        stats_frame = ttk.Frame(details_dialog)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(stats_frame, text=f"添加日期: {word_data[5]}").pack(side=tk.LEFT, padx=5)
        ttk.Label(stats_frame, text=f"复习次数: {word_data[6] or 0}").pack(side=tk.LEFT, padx=5)
        
        if word_data[7]:  # last_review_date
            ttk.Label(stats_frame, text=f"上次复习: {word_data[7]}").pack(side=tk.LEFT, padx=5)
        
        # 按钮区域
        btn_frame = ttk.Frame(details_dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(btn_frame, text="发音", 
                  command=lambda: pronounce_word(word)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="在线查询", 
                  command=lambda: open_online_dictionary(word)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="关闭", 
                  command=details_dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def delete_wordbook_word(self, selection):
        """删除生词本中的单词"""
        if not selection:
            messagebox.showinfo("提示", "请先选择一个单词")
            return
        
        item_id = selection[0]
        word = self.word_tree.item(item_id, "values")[0]
        
        if messagebox.askyesno("确认", f"确定要删除单词 '{word}' 吗？"):
            # 删除单词
            if self.word_details_manager.delete_word(word):
                # 从树形视图中移除
                self.word_tree.delete(item_id)
                messagebox.showinfo("成功", f"单词 '{word}' 已删除")
            else:
                messagebox.showerror("错误", f"删除单词 '{word}' 失败")
    
    def export_wordbook(self):
        """导出生词本"""
        # 获取保存路径
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="导出生词本"
        )
        
        if not file_path:
            return
        
        # 获取所有单词
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT word, translation, example FROM words ORDER BY word")
        words = cursor.fetchall()
        conn.close()
        
        # 写入文件
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for word in words:
                    f.write(f"{word[0]}\t{word[1]}\t{word[2]}\n")
            
            messagebox.showinfo("成功", f"生词本已导出到 {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def create_wordbook_page(self):
        """创建生词本页面"""
        page = ttk.Frame(self.content_frame)
        
        # 顶部控制区域
        control_frame = ttk.Frame(page)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 搜索框
        ttk.Label(control_frame, text="搜索:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(control_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # 绑定回车键
        search_entry.bind("<Return>", lambda e: self.load_wordbook_words(self.search_var.get()))
        
        ttk.Button(control_frame, text="搜索", 
                  command=lambda: self.load_wordbook_words(self.search_var.get())).pack(side=tk.LEFT, padx=5)
        
        # 排序选项
        ttk.Label(control_frame, text="排序:").pack(side=tk.LEFT, padx=(20, 5))
        self.sort_var = tk.StringVar(value="添加时间")
        sort_options = ["添加时间", "单词", "复习次数"]
        sort_combo = ttk.Combobox(control_frame, textvariable=self.sort_var, values=sort_options, state="readonly", width=10)
        sort_combo.pack(side=tk.LEFT, padx=5)
        
        # 绑定排序变化事件
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self.load_wordbook_words(self.search_var.get()))
        
        # 导出按钮
        ttk.Button(control_frame, text="导出", command=self.export_wordbook).pack(side=tk.RIGHT, padx=5)
        
        # 单词列表区域
        list_frame = ttk.Frame(page)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建树形视图
        columns = ("word", "translation", "added_date", "review_count")
        self.word_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.word_tree.heading("word", text="单词")
        self.word_tree.heading("translation", text="释义")
        self.word_tree.heading("added_date", text="添加日期")
        self.word_tree.heading("review_count", text="复习次数")
        
        # 设置列宽
        self.word_tree.column("word", width=150)
        self.word_tree.column("translation", width=300)
        self.word_tree.column("added_date", width=150)
        self.word_tree.column("review_count", width=80)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.word_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.word_tree.configure(yscrollcommand=scrollbar.set)
        
        self.word_tree.pack(fill=tk.BOTH, expand=True)
        
        # 绑定双击事件
        self.word_tree.bind("<Double-1>", lambda e: self.view_wordbook_details(self.word_tree.selection()))
        
        # 右键菜单
        self.word_menu = tk.Menu(self.word_tree, tearoff=0)
        self.word_menu.add_command(label="查看详情", command=lambda: self.view_wordbook_details(self.word_tree.selection()))
        self.word_menu.add_command(label="删除", command=lambda: self.delete_wordbook_word(self.word_tree.selection()))
        
        # 绑定右键点击事件
        self.word_tree.bind("<Button-3>", self.show_word_menu)
        
        # 加载单词
        self.load_wordbook_words()
        
        return page
    
    def show_word_menu(self, event):
        """显示单词右键菜单"""
        # 获取点击位置的项
        item = self.word_tree.identify_row(event.y)
        if item:
            # 选中该项
            self.word_tree.selection_set(item)
            # 显示菜单
            self.word_menu.post(event.x_root, event.y_root)
    
    def create_settings_page(self):
        """创建设置页面"""
        page = ttk.Frame(self.content_frame)
        
        # 创建设置框架
        settings_frame = ttk.LabelFrame(page, text="应用设置")
        settings_frame.pack(fill=tk.BOTH, expand=False, padx=20, pady=20)
        
        # API密钥设置
        ttk.Label(settings_frame, text="DashScope API密钥:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        
        self.api_key_var = tk.StringVar(value=self.api_key)
        api_key_entry = ttk.Entry(settings_frame, textvariable=self.api_key_var, width=50, show="*")
        api_key_entry.pack(fill=tk.X, padx=10, pady=5)
        
        # 显示/隐藏密钥
        self.show_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="显示密钥", variable=self.show_key_var, 
                       command=lambda: api_key_entry.config(show="" if self.show_key_var.get() else "*")).pack(anchor=tk.W, padx=10)
        
        # 主题设置
        theme_frame = ttk.LabelFrame(page, text="主题设置")
        theme_frame.pack(fill=tk.BOTH, expand=False, padx=20, pady=20)
        
        ttk.Label(theme_frame, text="选择应用主题:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # 主题选择变量
        self.theme_var = tk.StringVar(value=self.current_theme)
        
        # 主题选择框架
        theme_selection_frame = ttk.Frame(theme_frame)
        theme_selection_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 创建主题选择按钮
        for theme_key, theme_info in self.themes.items():
            theme_btn_frame = ttk.Frame(theme_selection_frame)
            theme_btn_frame.pack(fill=tk.X, pady=5)
            
            # 主题单选按钮
            theme_radio = ttk.Radiobutton(
                theme_btn_frame,
                text=theme_info["name"],
                variable=self.theme_var,
                value=theme_key,
                command=lambda key=theme_key: self.on_theme_change(key)
            )
            theme_radio.pack(side=tk.LEFT)
            
            # 主题颜色预览
            color_preview = tk.Frame(theme_btn_frame, 
                                   bg=theme_info["primary"], 
                                   width=30, height=20)
            color_preview.pack(side=tk.LEFT, padx=(10, 5))
            color_preview.pack_propagate(False)
            
            # 主题描述
            ttk.Label(theme_btn_frame, 
                     text=theme_info["description"],
                     font=("SF Pro Display", 10),
                     foreground="#6b7280").pack(side=tk.LEFT, padx=(5, 0))
        
        # 保存按钮
        ttk.Button(settings_frame, text="保存设置", command=self.save_settings).pack(anchor=tk.W, padx=10, pady=10)
        
        # 关于信息
        about_frame = ttk.LabelFrame(page, text="关于")
        about_frame.pack(fill=tk.BOTH, expand=False, padx=20, pady=20)
        
        ttk.Label(about_frame, text="拍照学单词 v1.0").pack(anchor=tk.W, padx=10, pady=(10, 0))
        ttk.Label(about_frame, text="一个帮助你通过拍照学习英语单词的应用").pack(anchor=tk.W, padx=10, pady=(5, 0))
                
        return page
    
    def create_camera_page(self):
        """创建相机/拍照页面"""
        page = ttk.Frame(self.content_frame)
        
        # 创建左右分栏
        left_frame = ttk.Frame(page, width=500)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.right_frame = ttk.Frame(page, width=500)  # 保存right_frame的引用
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 左侧图片区域 - 简洁风格
        self.image_frame = ttk.LabelFrame(left_frame, text="图片预览")
        self.image_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 图片Canvas容器 - 移除内边距让Canvas完全填满
        canvas_container = tk.Frame(self.image_frame, bg="#e9ecef", relief=tk.SOLID, bd=1)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 图片区域改为Canvas - 移除固定尺寸，让其完全填满容器
        self.image_canvas = tk.Canvas(canvas_container, bg="#f8f9fa", highlightthickness=0)
        self.image_canvas.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # 添加句子显示区域
        self.sentence_frame = ttk.LabelFrame(left_frame, text="图片描述")
        self.sentence_frame.pack(fill=tk.BOTH, expand=False, pady=5)
        
        # 创建文本显示区域
        self.sentence_text = tk.Text(self.sentence_frame, height=5, wrap=tk.WORD, width=50)
        self.sentence_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.sentence_text.config(state=tk.DISABLED)
        
        # 添加填词区域
        self.fill_words_frame = ttk.LabelFrame(left_frame, text="填词练习")
        self.fill_words_frame.pack(fill=tk.BOTH, expand=False, pady=5)
        self.fill_words_frame.pack_forget()  # 初始时隐藏
        
        # 图片操作按钮
        img_buttons_frame = ttk.Frame(left_frame)
        img_buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)  # 改为底部对齐
        
        # 初始化相机捕获
        self.camera_capture = CameraCapture(self.root)
        
        self.take_photo_btn = ttk.Button(img_buttons_frame, text="拍照", command=self.take_photo)
        self.take_photo_btn.pack(side=tk.LEFT, padx=5)
        
        self.upload_btn = ttk.Button(img_buttons_frame, text="上传图片", command=self.upload_image)
        self.upload_btn.pack(side=tk.LEFT, padx=5)
        
        self.recognize_btn = ttk.Button(img_buttons_frame, text="识别文字", command=self.recognize_text)
        self.recognize_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加填词按钮
        self.fill_words_btn = ttk.Button(img_buttons_frame, text="开始填词", command=self.toggle_fill_words)
        self.fill_words_btn.pack(side=tk.LEFT, padx=5)
        
        # 右侧单词区域
        # 单词列表区域 (移除这部分)
        self.word_list_frame = ttk.LabelFrame(self.right_frame, text="识别到的单词")
        self.word_list_frame.pack(fill=tk.BOTH, expand=False, pady=5, ipady=5)
        
        # 单词列表 (移除这部分)
        self.word_listbox = tk.Listbox(self.word_list_frame, height=6)
        self.word_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.word_listbox.bind('<<ListboxSelect>>', self.on_word_select)
        
        # 单词详情区域
        self.word_detail_frame = ttk.LabelFrame(self.right_frame, text="单词详情")
        self.word_detail_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 单词标签
        self.word_label = ttk.Label(self.word_detail_frame, text="", font=("Arial", 16, "bold"))
        self.word_label.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # 添加音标标签
        self.phonetic_label = ttk.Label(self.word_detail_frame, text="", font=("Arial", 12))
        self.phonetic_label.pack(anchor=tk.W, padx=10, pady=(0, 5))
        
        # 发音按钮
        self.pronounce_btn = ttk.Button(self.word_detail_frame, text="发音", command=self.pronounce_word)
        self.pronounce_btn.pack(anchor=tk.W, padx=10, pady=5)
        
        # 释义文本框
        ttk.Label(self.word_detail_frame, text="释义:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.translation_text = tk.Text(self.word_detail_frame, height=4, wrap=tk.WORD)
        self.translation_text.pack(fill=tk.X, expand=False, padx=10, pady=5)
        self.translation_text.config(state=tk.DISABLED)
        
        # 例句文本框
        ttk.Label(self.word_detail_frame, text="例句:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.example_text = tk.Text(self.word_detail_frame, height=6, wrap=tk.WORD)
        self.example_text.pack(fill=tk.X, expand=False, padx=10, pady=5)
        self.example_text.config(state=tk.DISABLED)
        
        # 操作按钮区域
        self.action_frame = ttk.Frame(self.word_detail_frame)
        self.action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 添加到生词本按钮
        self.add_btn = ttk.Button(self.action_frame, text="添加到生词本", command=self.add_to_wordbook)
        self.add_btn.pack(side=tk.LEFT, padx=5)
        
        # 查询按钮
        self.query_btn = ttk.Button(self.action_frame, text="在线查询", command=self.query_online)
        self.query_btn.pack(side=tk.LEFT, padx=5)
        
        # 显示默认图片
        self.show_default_image()
        
        return page
    
    def create_overlay(self):
        """创建右侧区域的蒙层"""
        # 创建蒙层框架
        self.overlay = ttk.Frame(self.right_frame)
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # 创建样式
        style = ttk.Style()
        style.configure("Overlay.TFrame", 
                       background="#e8f4f8")  # 浅蓝色背景
        
        # 设置蒙层样式
        self.overlay.configure(style="Overlay.TFrame")
        
        # 创建内容容器
        content_frame = ttk.Frame(self.overlay)
        content_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # 添加图标（使用文本符号代替）
        icon_label = ttk.Label(content_frame, 
                             text="✏️", 
                             font=("Arial", 48),
                             background="#e8f4f8",
                             foreground="#2c7da0")
        icon_label.pack(pady=(0, 20))
        
        # 添加主标题
        title_label = ttk.Label(content_frame, 
                              text="填词练习中", 
                              font=("Arial", 24, "bold"),
                              background="#e8f4f8",
                              foreground="#1a5276")  # 深蓝色文字
        title_label.pack(pady=(0, 10))
        
        # 添加副标题
        subtitle_label = ttk.Label(content_frame,
                                 text="请专注于填写单词",
                                 font=("Arial", 14),
                                 background="#e8f4f8",
                                 foreground="#2874a6")  # 中蓝色文字
        subtitle_label.pack()
        
        # 添加提示文本
        hint_label = ttk.Label(content_frame,
                             text='完成后点击"结束填词"按钮',
                             font=("Arial", 12),
                             background="#e8f4f8",
                             foreground="#3498db")  # 浅蓝色文字
        hint_label.pack(pady=(20, 0))
        
        # 将蒙层置于顶层
        self.overlay.lift()
    
    def remove_overlay(self):
        """移除右侧区域的蒙层"""
        if hasattr(self, 'overlay'):
            self.overlay.destroy()
            delattr(self, 'overlay')

    def toggle_fill_words(self):
        """切换填词练习状态"""
        if self.fill_words_frame.winfo_ismapped():  # 如果填词区域当前是显示的
            # 结束填词
            self.fill_words_frame.pack_forget()  # 隐藏填词区域
            self.root.update_idletasks()  # 处理所有待处理的任务
            
            # 确保图片描述区域已准备好
            self.sentence_text.config(state=tk.NORMAL)
            self.sentence_text.config(state=tk.DISABLED)
            
            # 显示图片描述
            self.sentence_frame.pack(fill=tk.BOTH, expand=False, pady=5)
            self.fill_words_btn.config(text="开始填词")
            self.status_bar.config(text="填词练习已结束")
            
            # 移除蒙层
            self.remove_overlay()
            
            # 重新显示单词标签
            if hasattr(self, 'recognized_words') and hasattr(self, 'recognized_words_positions'):
                if hasattr(self, 'original_img_width') and hasattr(self, 'original_img_height'):
                    self.draw_word_labels(self.recognized_words, self.recognized_words_positions, 
                                        self.original_img_width, self.original_img_height)
            
            # 强制立即更新界面
            self.root.update_idletasks()
            self.root.update()
        else:
            # 检查是否已经识别了文字
            if not self.recognized_words:
                messagebox.showinfo("提示", "请先识别图片中的单词")
                return
                
            # 检查是否有描述文本
            if not self.sentence_text.get(1.0, tk.END).strip():
                messagebox.showinfo("提示", "没有可用的描述文本")
                return
                
            # 隐藏单词标签
            self.image_canvas.delete("word_label")
            
            # 开始填词
            self.start_fill_words()
            self.fill_words_btn.config(text="结束填词")
            
            # 添加蒙层
            self.create_overlay()
            
            self.root.update_idletasks()
            self.root.update()
    
    def take_photo(self):
        """拍照"""
        # 打开相机窗口
        self.camera_capture.open_camera()
        
        # 等待拍照完成
        self.root.wait_window(self.camera_capture.camera_window)
        
        # 检查是否有拍摄的图片
        if self.camera_capture.frame:
            # 显示图片
            self.display_image(self.camera_capture.frame)
            
            # 保存图片
            self.current_image_path = self.image_manager.save_image(self.camera_capture.frame, "photo")
            
            # 清空单词列表
            self.word_listbox.delete(0, tk.END)
            self.recognized_words = []
            
            # 清空图片描述
            self.sentence_text.config(state=tk.NORMAL)
            self.sentence_text.delete(1.0, tk.END)
            self.sentence_text.config(state=tk.DISABLED)
            
            # 隐藏填词练习区域
            self.fill_words_frame.pack_forget()
            # 显示图片描述区域
            self.sentence_frame.pack(fill=tk.BOTH, expand=False, pady=5)
            # 重置填词按钮文本
            self.fill_words_btn.config(text="开始填词")
            
            # 更新状态栏
            self.status_bar.config(text="拍照成功，可以点击\"识别文字\"按钮识别单词")
    
    def upload_image(self):
        """上传图片"""
        # 打开文件对话框
        file_path = filedialog.askopenfilename(
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif"), ("所有文件", "*.*")],
            title="选择图片"
        )
        
        if not file_path:
            return
        
        try:
            # 加载图片
            img = Image.open(file_path)
            
            # 显示图片
            self.display_image(img)
            
            # 保存图片路径
            self.current_image_path = file_path
            
            # 清空单词列表
            self.word_listbox.delete(0, tk.END)
            self.recognized_words = []
            
            # 清空图片描述
            self.sentence_text.config(state=tk.NORMAL)
            self.sentence_text.delete(1.0, tk.END)
            self.sentence_text.config(state=tk.DISABLED)
            
            # 隐藏填词练习区域
            self.fill_words_frame.pack_forget()
            # 显示图片描述区域
            self.sentence_frame.pack(fill=tk.BOTH, expand=False, pady=5)
            # 重置填词按钮文本
            self.fill_words_btn.config(text="开始填词")
            
            # 更新状态栏
            self.status_bar.config(text="图片加载成功，可以点击\"识别文字\"按钮识别单词")
        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片: {str(e)}")
    
    def recognize_text(self):
        """识别图片中的文字，并获取原始图片尺寸进行坐标缩放"""
        if not self.current_image_path:
            messagebox.showerror("错误", "请先选择图片")
            return
        
        # 创建进度条对话框
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("识别进度")
        progress_dialog.geometry("400x150")
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()
        progress_dialog.resizable(False, False)
        
        # 设置对话框居中
        progress_dialog.update_idletasks()
        x = (progress_dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (progress_dialog.winfo_screenheight() // 2) - (150 // 2)
        progress_dialog.geometry(f"400x150+{x}+{y}")
        
        # 进度对话框内容
        progress_frame = ttk.Frame(progress_dialog)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        ttk.Label(progress_frame, text="🔍 正在识别图片中的文字...", 
                 font=("SF Pro Display", 14, "bold")).pack(pady=(0, 15))
        
        # 进度条
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, 
                                      maximum=100, length=350)
        progress_bar.pack(pady=(0, 10))
        
        # 状态标签
        status_label = ttk.Label(progress_frame, text="准备开始识别...", 
                                font=("SF Pro Display", 10))
        status_label.pack()
        
        # 强制更新显示
        progress_dialog.update()
        
        try:
            # 步骤1: 读取图片
            status_label.config(text="正在读取图片...")
            progress_var.set(20)
            progress_dialog.update()
            
            # 获取原始图片尺寸
            try:
                original_image = Image.open(self.current_image_path)
                original_img_width, original_img_height = original_image.size
            except Exception as e:
                progress_dialog.destroy()
                messagebox.showerror("错误", f"无法读取图片尺寸: {e}")
                self.status_bar.config(text="图片尺寸读取失败")
                return
            
            # 步骤2: 发送API请求
            status_label.config(text="正在发送API请求...")
            progress_var.set(40)
            progress_dialog.update()
            
            # 调用API识别文字
            # api_service.recognize_text 返回: success, message, words, positions, sentence
            success, message, recognized_words_list, recognized_words_positions, description = self.api_service.recognize_text(self.current_image_path)
            
            # 保存识别结果和原始图片尺寸
            self.recognized_words_positions = recognized_words_positions
            self.original_img_width = original_img_width
            self.original_img_height = original_img_height
            
            # 步骤3: 处理识别结果
            status_label.config(text="正在处理识别结果...")
            progress_var.set(70)
            progress_dialog.update()
            
            if success:
                self.recognized_words = recognized_words_list # 直接使用返回的单词列表
                
                # 步骤4: 更新界面
                status_label.config(text="正在更新界面...")
                progress_var.set(90)
                progress_dialog.update()
                
                # 更新单词列表框
                self.word_listbox.delete(0, tk.END)
                for word in self.recognized_words:
                    self.word_listbox.insert(tk.END, word)
                
                # 重新显示图片
                if isinstance(self.current_image_path, str): # 如果是路径，则打开
                    img_to_display = Image.open(self.current_image_path)
                else: # 如果已经是Image对象
                    img_to_display = self.current_image_path 
                self.display_image(img_to_display)
                
                # 在图片上绘制单词标签，传入原始尺寸用于缩放
                self.draw_word_labels(self.recognized_words, recognized_words_positions, original_img_width, original_img_height)
                
                # 更新图片描述
                self.sentence_text.config(state=tk.NORMAL)
                self.sentence_text.delete(1.0, tk.END)
                self.sentence_text.insert(tk.END, description) # 使用API返回的句子
                self.sentence_text.config(state=tk.DISABLED)
                
                # 高亮显示识别到的单词 (如果需要)
                self.highlight_words(description, self.recognized_words)
                
                # 步骤5: 完成
                status_label.config(text="识别完成！")
                progress_var.set(100)
                progress_dialog.update()
                
                # 如果有单词，并且希望默认选中第一个并查询详情
                if self.recognized_words:
                    self.word_listbox.selection_set(0) # 选中列表中的第一个单词
                    self.on_word_select(None) # 触发选中事件，None作为event参数
                
                # 延迟一点时间让用户看到完成状态，然后关闭进度框
                self.root.after(500, progress_dialog.destroy)
                
                self.status_bar.config(text=message)
            else:
                progress_dialog.destroy()
                self.status_bar.config(text=message)
                messagebox.showerror("错误", message)
        except Exception as e:
            progress_dialog.destroy()
            self.status_bar.config(text="识别失败")
            messagebox.showerror("错误", f"识别失败: {str(e)}")
    
    def update_sentence_display(self, words):
        """更新句子显示区域"""
        # 清空文本区域
        self.sentence_text.config(state=tk.NORMAL)
        self.sentence_text.delete(1.0, tk.END)
        
        if not words:
            self.sentence_text.config(state=tk.DISABLED)
            return
            
        # 创建句子
        sentence = " ".join(words)
        
        # 插入句子，并为每个单词添加红色标记
        start_index = "1.0"
        for word in words:
            # 找到单词在句子中的位置
            word_start = sentence.find(word, int(start_index.split(".")[1]) - 1)
            if word_start != -1:
                # 插入单词前的文本
                if word_start > 0:
                    self.sentence_text.insert(tk.END, sentence[:word_start])
                
                # 插入红色单词
                self.sentence_text.insert(tk.END, word, "red")
                self.sentence_text.tag_configure("red", foreground="red")
                
                # 更新起始位置
                start_index = f"1.{word_start + len(word)}"
                sentence = sentence[word_start + len(word):]
        
        # 插入剩余的文本
        if sentence:
            self.sentence_text.insert(tk.END, sentence)
        
        self.sentence_text.config(state=tk.DISABLED)
    
    def on_word_select(self, event):
        """当选择单词列表中的单词时"""
        selection = self.word_listbox.curselection()
        if selection:
            index = selection[0]
            word = self.recognized_words[index]
            self.current_word_index = index
            
            # 显示单词
            self.word_label.config(text=word)
            
            # 清空音标、释义和例句
            self.phonetic_label.config(text="")
            self.translation_text.config(state=tk.NORMAL)
            self.translation_text.delete(1.0, tk.END)
            self.translation_text.config(state=tk.DISABLED)
            self.example_text.config(state=tk.NORMAL)
            self.example_text.delete(1.0, tk.END)
            self.example_text.config(state=tk.DISABLED)
            
            # 高亮显示描述中的当前选中单词
            self.highlight_selected_word(word)
            
            # 查询单词详情
            self.query_word_details(word)
    
    def highlight_selected_word(self, word):
        """高亮显示描述中选中的单词"""
        # 启用文本编辑
        self.sentence_text.config(state=tk.NORMAL)
        
        # 清除现有的选中高亮
        self.sentence_text.tag_remove("selected", "1.0", tk.END)
        
        # 查找并高亮选中的单词
        start_pos = "1.0"
        found = False
        last_valid_pos = None
        
        while True:
            # 查找单词（不区分大小写）
            start_pos = self.sentence_text.search(r'\y' + word + r'\y', start_pos, tk.END, nocase=True, regexp=True)
            if not start_pos:
                break
                
            found = True
            last_valid_pos = start_pos  # 保存最后一个有效位置
            
            # 计算结束位置
            end_pos = f"{start_pos}+{len(word)}c"
            
            # 添加选中高亮标签
            self.sentence_text.tag_add("selected", start_pos, end_pos)
            
            # 更新搜索起始位置
            start_pos = end_pos
        
        # 配置选中高亮样式（使用不同的颜色和样式）
        self.sentence_text.tag_config("selected", 
                                    foreground="blue",  # 使用蓝色
                                    font=("Arial", 10, "bold", "underline"),  # 加粗和下划线
                                    background="#FFFF00")  # 黄色背景
        
        # 禁用文本编辑
        self.sentence_text.config(state=tk.DISABLED)
        
        # 确保选中的单词可见（只有在找到单词时才滚动）
        if found and last_valid_pos:
            self.sentence_text.see(last_valid_pos)
    
    def query_word_details(self, word):
        """查询单词详情"""
        if not word:
            return
        
        if not self.api_key:
            messagebox.showinfo("提示", "请先在设置中配置API密钥")
            self.show_page("settings")
            return
        
        # 显示加载中
        self.status_bar.config(text=f"正在查询单词 '{word}' 的详情...")
        self.root.update()
        
        # 先检查数据库中是否已有该单词
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT translation, example FROM words WHERE word = ?", (word,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # 如果数据库中已有该单词，直接使用
            translation, example = result
            
            # 更新界面
            self.update_word_details(word, "", translation, example)
            
            # 更新状态栏
            self.status_bar.config(text=f"已从数据库加载单词 '{word}' 的详情")
        else:
            # 否则调用API查询
            success, message, data, error = self.api_service.query_word_details(word)
            
            if success:
                # 更新界面
                self.update_word_details(
                    word, 
                    data.get("phonetic", ""), 
                    data.get("translation", ""), 
                    data.get("example", "")
                )
                
                # 更新状态栏
                self.status_bar.config(text=f"已查询单词 '{word}' 的详情")
            else:
                # 显示错误信息
                self.status_bar.config(text=error)
    
    def update_word_details(self, word, phonetic, translation, example):
        """更新单词详情显示"""
        # 更新音标
        self.phonetic_label.config(text=phonetic)
        
        # 更新释义
        self.translation_text.config(state=tk.NORMAL)
        self.translation_text.delete(1.0, tk.END)
        self.translation_text.insert(tk.END, translation)
        self.translation_text.config(state=tk.DISABLED)
        
        # 更新例句
        self.example_text.config(state=tk.NORMAL)
        self.example_text.delete(1.0, tk.END)
        self.example_text.insert(tk.END, example)
        self.example_text.config(state=tk.DISABLED)
    
    def pronounce_word(self):
        """发音当前单词"""
        word = self.word_label.cget("text")
        if not word:
            return
        
        success, message = pronounce_word(word)
        if not success:
            self.status_bar.config(text=message)
    
    def query_online(self):
        """在线查询当前单词"""
        word = self.word_label.cget("text")
        if not word:
            return
        
        success, message = open_online_dictionary(word)
        if not success:
            self.status_bar.config(text=message)
    
    def add_to_wordbook(self):
        """添加当前单词到生词本"""
        word = self.word_label.cget("text")
        if not word:
            messagebox.showinfo("提示", "请先选择一个单词")
            return
        
        # 获取释义和例句
        translation = self.translation_text.get(1.0, tk.END).strip()
        example = self.example_text.get(1.0, tk.END).strip()
        
        # 添加到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查是否已存在
            cursor.execute("SELECT id FROM words WHERE word = ?", (word,))
            existing = cursor.fetchone()
            
            if existing:
                # 如果已存在，询问是否更新
                if messagebox.askyesno("提示", f"单词 '{word}' 已存在于生词本中，是否更新?"):
                    cursor.execute(
                        "UPDATE words SET translation = ?, example = ?, image_path = ? WHERE word = ?",
                        (translation, example, self.current_image_path, word)
                    )
                    messagebox.showinfo("成功", f"单词 '{word}' 已更新")
            else:
                # 如果不存在，插入新记录
                cursor.execute(
                    "INSERT INTO words (word, translation, example, image_path) VALUES (?, ?, ?, ?)",
                    (word, translation, example, self.current_image_path)
                )
                messagebox.showinfo("成功", f"单词 '{word}' 已添加到生词本")
            
            conn.commit()

            # 添加图片到相册（这是关键的修复）
            if self.current_image_path:
                self.album_manager.add_image_to_album(self.current_image_path, has_words=True)

        except Exception as e:
            messagebox.showerror("错误", f"添加单词失败: {str(e)}")
        finally:
            conn.close()
    
    def show_default_image(self):
        """显示简洁的默认图片预览界面"""
        # 延迟绘制，确保Canvas尺寸已经确定
        self.root.after(100, self._draw_default_image)
        
        # 绑定Canvas尺寸变化事件
        self.image_canvas.bind("<Configure>", self._on_canvas_resize)
    
    def _draw_default_image(self):
        """实际绘制默认图片界面"""
        # 清空画布
        self.image_canvas.delete("all")
        
        # 获取实际画布尺寸
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        # 如果画布尺寸太小，等待尺寸更新
        if canvas_width <= 10 or canvas_height <= 10:
            self.root.after(100, self._draw_default_image)
            return
        
        # 绘制完全填满的背景
        self.image_canvas.create_rectangle(0, 0, canvas_width, canvas_height, 
                                         fill="#f8f9fa", outline="", width=0, tags="default")
        
        # 计算居中位置
        icon_x = canvas_width // 2
        icon_y = canvas_height // 2 - 40
        
        # 使用大号相机emoji图标
        self.image_canvas.create_text(icon_x, icon_y, 
                                    text="📷", 
                                    font=("Apple Color Emoji", 64), 
                                    fill="#495057", tags="default")
        
        # 主标题文字
        self.image_canvas.create_text(icon_x, icon_y+45, 
                                    text="点击拍照或上传图片", 
                                    font=("SF Pro Display", 16, "bold"), 
                                    fill="#2c3e50", tags="default")
        
        # 副标题文字
        self.image_canvas.create_text(icon_x, icon_y+75, 
                                    text="开始您的英语学习之旅", 
                                    font=("SF Pro Display", 12), 
                                    fill="#6c757d", tags="default")
        
        # 绑定点击事件
        self.image_canvas.bind("<Button-1>", self.on_canvas_click)
        self.image_canvas.configure(cursor="hand2")
    
    def _on_canvas_resize(self, event):
        """Canvas尺寸变化时重新绘制默认界面"""
        # 只有在显示默认界面时才重新绘制
        if self.image_canvas.find_withtag("default"):
            self.root.after(50, self._draw_default_image)
    
    def on_canvas_click(self, event):
        """当点击空白画布时显示操作选项"""
        # 创建弹出菜单
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="📷 拍照", command=self.take_photo)
        menu.add_command(label="📁 上传图片", command=self.upload_image)
        
        # 在鼠标位置显示菜单
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def display_image(self, img):
        """在界面上显示图片（完全填满Canvas）"""
        # 获取实际Canvas尺寸
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        # 如果Canvas尺寸还未确定，使用默认值
        if canvas_width <= 10 or canvas_height <= 10:
            canvas_width = 450
            canvas_height = 320
        
        # 计算缩放比例以填满整个画布
        img_width, img_height = img.size
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        
        # 使用较大的缩放比例确保图片完全填满画布
        scale = max(scale_x, scale_y)
        
        # 计算新的尺寸
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # 缩放图片
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)
        
        # 如果图片比画布大，裁剪中心部分
        if new_width > canvas_width or new_height > canvas_height:
            # 计算裁剪区域（居中裁剪）
            left = (new_width - canvas_width) // 2
            top = (new_height - canvas_height) // 2
            right = left + canvas_width
            bottom = top + canvas_height
            
            img_resized = img_resized.crop((left, top, right, bottom))
        
        # 创建PhotoImage
        self._canvas_img = ImageTk.PhotoImage(img_resized)
        self.image_canvas.delete("all")
        
        # 在画布上显示图片（填满整个画布）
        self.image_canvas.create_image(0, 0, anchor=tk.NW, image=self._canvas_img)
        
        # 移除点击事件绑定和手型光标
        self.image_canvas.unbind("<Button-1>")
        self.image_canvas.unbind("<Configure>")
        self.image_canvas.configure(cursor="")
    
    def create_statusbar(self):
        """创建状态栏"""
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, before=self.navbar)
    
    def set_styles(self):
        """设置现代化界面样式"""
        style = ttk.Style()
        
        # 设置主题
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        
        # 获取当前主题配置
        theme_config = self.themes[self.current_theme]
        
        # 定义现代化配色方案（使用主题颜色）
        colors = {
            'primary': theme_config['primary'],      # 主题主色
            'primary_dark': theme_config['primary_hover'], # 主题深色
            'secondary': '#10b981',    # 翠绿
            'accent': '#f59e0b',       # 橙色
            'background': '#f8fafc',   # 浅灰白
            'surface': '#ffffff',      # 纯白
            'text_primary': '#1f2937', # 深灰
            'text_secondary': '#6b7280', # 中灰
            'border': '#e5e7eb',       # 浅灰边框
            'success': '#059669',      # 成功绿
            'warning': '#d97706',      # 警告橙
            'error': '#dc2626'         # 错误红
        }
        
        # 配置全局样式
        style.configure("TFrame", 
                       background=colors['background'],
                       relief='flat')
        
        style.configure("TLabel", 
                       background=colors['background'],
                       foreground=colors['text_primary'],
                       font=("SF Pro Display", 11))
        
        style.configure("TLabelframe", 
                       background=colors['background'],
                       relief='flat',
                       borderwidth=1)
        
        style.configure("TLabelframe.Label", 
                       background=colors['background'],
                       foreground=colors['text_primary'],
                       font=("SF Pro Display", 12, "bold"))
        
        # 现代化按钮样式
        style.configure("TButton",
                       padding=(20, 12),
                       font=("SF Pro Display", 11, "bold"),
                       background=colors['primary'],
                       foreground='white',
                       borderwidth=0,
                       relief='flat',
                       focuscolor='none')
        
        style.map("TButton",
                 background=[('active', colors['primary_dark']),
                           ('pressed', colors['primary_dark']),
                           ('disabled', colors['border'])],
                 foreground=[('disabled', colors['text_secondary'])])
        
        # 导航按钮样式
        style.configure("Nav.TButton",
                       padding=(15, 10),
                       font=("SF Pro Display", 10, "bold"),
                       background=colors['surface'],
                       foreground=colors['text_primary'],
                       borderwidth=1,
                       relief='solid',
                       focuscolor='none')
        
        style.map("Nav.TButton",
                 background=[('active', colors['primary']),
                           ('pressed', colors['primary_dark'])],
                 foreground=[('active', 'white'),
                           ('pressed', 'white')],
                 bordercolor=[('active', colors['primary']),
                            ('pressed', colors['primary_dark']),
                            ('!active', colors['border'])])
        
        # 成功按钮样式
        style.configure("Success.TButton",
                       padding=(15, 8),
                       font=("SF Pro Display", 11, "bold"),
                       background=colors['success'],
                       foreground='white',
                       borderwidth=0,
                       relief='flat',
                       focuscolor='none')
        
        style.map("Success.TButton",
                 background=[('active', '#047857'),
                           ('pressed', '#065f46')])
        
        # 警告按钮样式
        style.configure("Warning.TButton",
                       padding=(15, 8),
                       font=("SF Pro Display", 11, "bold"),
                       background=colors['warning'],
                       foreground='white',
                       borderwidth=0,
                       relief='flat',
                       focuscolor='none')
        
        style.map("Warning.TButton",
                 background=[('active', '#b45309'),
                           ('pressed', '#92400e')])
        
        # 次要按钮样式
        style.configure("Secondary.TButton",
                       padding=(15, 8),
                       font=("SF Pro Display", 11),
                       background=colors['surface'],
                       foreground=colors['text_primary'],
                       borderwidth=1,
                       relief='solid',
                       focuscolor='none')
        
        style.map("Secondary.TButton",
                 background=[('active', colors['background']),
                           ('pressed', colors['border'])],
                 bordercolor=[('active', colors['primary']),
                            ('!active', colors['border'])])
        
        # 文本框样式
        style.configure("TEntry",
                       padding=10,
                       font=("SF Pro Display", 11),
                       borderwidth=1,
                       relief='solid',
                       focuscolor=colors['primary'])
        
        # 列表框样式
        style.configure("TTreeview",
                       background=colors['surface'],
                       foreground=colors['text_primary'],
                       font=("SF Pro Display", 11),
                       borderwidth=1,
                       relief='solid')
        
        style.configure("TTreeview.Heading",
                       background=colors['background'],
                       foreground=colors['text_primary'],
                       font=("SF Pro Display", 11, "bold"),
                       relief='flat')
        
        # 进度条样式
        style.configure("TProgressbar",
                       background=colors['primary'],
                       troughcolor=colors['border'],
                       borderwidth=0,
                       relief='flat')
        
        # 设置根窗口背景
        self.root.configure(bg=colors['background'])

    def highlight_words(self, text, words):
        """高亮显示文本中的单词"""
        self.sentence_text.config(state=tk.NORMAL)
        self.sentence_text.tag_remove("highlight", "1.0", tk.END)
        for word in words:
            start_pos = "1.0"
            while True:
                start_pos = self.sentence_text.search(r'\y' + word + r'\y', start_pos, tk.END, nocase=True, regexp=True)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(word)}c"
                self.sentence_text.tag_add("highlight", start_pos, end_pos)
                start_pos = end_pos
        self.sentence_text.tag_config("highlight", foreground="red", font=("Arial", 10, "bold"))
        self.sentence_text.config(state=tk.DISABLED)

    def draw_word_labels(self, words, positions, original_width, original_height):
        """在图片Canvas上根据大模型返回的坐标绘制单词标签，智能避让重叠。"""
        self.image_canvas.delete("word_label")
        
        # 获取实际Canvas尺寸
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        # 如果Canvas尺寸还未确定，使用默认值
        if canvas_width <= 10 or canvas_height <= 10:
            canvas_width = 450
            canvas_height = 320

        if original_width == 0 or original_height == 0:
            print("警告: 原始图片尺寸为0，无法进行坐标缩放。")
            self.status_bar.config(text="警告: 原始图片尺寸为0，无法缩放标签。")
            return
            
        scale_x = canvas_width / original_width
        scale_y = canvas_height / original_height

        if not words or not positions or len(words) != len(positions):
            self.status_bar.config(text="警告: 单词或位置信息不完整，部分标签可能无法显示。")
            if words and positions:
                min_len = min(len(words), len(positions))
                words = words[:min_len]
                positions = positions[:min_len]
            else:
                return

        drawn_rects = [] # 用于存储已绘制标签的边界框 (x1, y1, x2, y2)

        for i, word in enumerate(words):
            if i < len(positions) and positions[i] and isinstance(positions[i], list) and len(positions[i]) == 2:
                pos_original = positions[i]
                x_orig, y_orig = pos_original[0], pos_original[1]
                
                x_center_scaled = x_orig * scale_x
                y_center_scaled = y_orig * scale_y

                font_size = 10 
                padding = 4
                text_width_estimate = len(word) * font_size * 0.7
                text_height_estimate = font_size + 4
                
                # 标签总尺寸（包含padding）
                label_width = text_width_estimate + 2 * padding
                label_height = text_height_estimate + 2 * padding

                # 智能避让策略：尝试多个位置
                candidate_positions = [
                    (x_center_scaled, y_center_scaled),  # 原始位置
                    (x_center_scaled, y_center_scaled - label_height - 5),  # 上方
                    (x_center_scaled, y_center_scaled + label_height + 5),  # 下方
                    (x_center_scaled - label_width - 5, y_center_scaled),  # 左侧
                    (x_center_scaled + label_width + 5, y_center_scaled),  # 右侧
                    (x_center_scaled - label_width//2, y_center_scaled - label_height - 5),  # 左上
                    (x_center_scaled + label_width//2, y_center_scaled - label_height - 5),  # 右上
                    (x_center_scaled - label_width//2, y_center_scaled + label_height + 5),  # 左下
                    (x_center_scaled + label_width//2, y_center_scaled + label_height + 5),  # 右下
                ]
                
                best_position = None
                min_overlap_area = float('inf')
                
                for candidate_x, candidate_y in candidate_positions:
                    # 确保标签在Canvas范围内
                    rect_x1 = max(0, candidate_x - label_width / 2)
                    rect_y1 = max(0, candidate_y - label_height / 2)
                    rect_x2 = min(canvas_width, candidate_x + label_width / 2)
                    rect_y2 = min(canvas_height, candidate_y + label_height / 2)
                    
                    # 如果标签被裁剪得太多，跳过这个位置
                    if rect_x2 - rect_x1 < label_width * 0.7 or rect_y2 - rect_y1 < label_height * 0.7:
                        continue
                    
                    # 计算与已有标签的重叠面积
                    total_overlap_area = 0
                    for dr_x1, dr_y1, dr_x2, dr_y2 in drawn_rects:
                        # 计算重叠区域
                        overlap_x1 = max(rect_x1, dr_x1)
                        overlap_y1 = max(rect_y1, dr_y1)
                        overlap_x2 = min(rect_x2, dr_x2)
                        overlap_y2 = min(rect_y2, dr_y2)
                        
                        if overlap_x1 < overlap_x2 and overlap_y1 < overlap_y2:
                            overlap_area = (overlap_x2 - overlap_x1) * (overlap_y2 - overlap_y1)
                            total_overlap_area += overlap_area
                    
                    # 选择重叠面积最小的位置
                    if total_overlap_area < min_overlap_area:
                        min_overlap_area = total_overlap_area
                        best_position = (candidate_x, candidate_y, rect_x1, rect_y1, rect_x2, rect_y2)
                    
                    # 如果找到完全不重叠的位置，直接使用
                    if total_overlap_area == 0:
                        break
                
                if best_position is None:
                    # 如果没有找到合适位置，使用原始位置
                    current_x_center = x_center_scaled
                    current_y_center = y_center_scaled
                    rect_x1 = current_x_center - label_width / 2
                    rect_y1 = current_y_center - label_height / 2
                    rect_x2 = current_x_center + label_width / 2
                    rect_y2 = current_y_center + label_height / 2
                else:
                    current_x_center, current_y_center, rect_x1, rect_y1, rect_x2, rect_y2 = best_position

                rect_tag = f"rect_{i}"
                text_tag = f"text_{i}"
                group_tag = f"word_group_{i}"

                # 绘制标签背景
                self.image_canvas.create_rectangle(rect_x1, rect_y1, rect_x2, rect_y2, 
                                                   fill="#FFFFE0", 
                                                   outline="#FFA500", 
                                                   width=2,
                                                   tags=("word_label", rect_tag, group_tag))
                
                # 绘制文字
                self.image_canvas.create_text(current_x_center, current_y_center, 
                                              text=word, 
                                              fill="#FF4500", 
                                              font=("Arial", font_size, "bold"), 
                                              anchor=tk.CENTER,
                                              tags=("word_label", text_tag, group_tag))
                
                # 记录已绘制的标签边界框
                drawn_rects.append((rect_x1, rect_y1, rect_x2, rect_y2))
                
                # 绑定点击事件
                self.image_canvas.tag_bind(group_tag, "<Button-1>", lambda e, idx=i: self.on_word_label_click(idx))
                
                # 添加悬停效果
                def on_label_enter(event, tag=group_tag):
                    self.image_canvas.itemconfig(f"{tag}&&rect_{i}", fill="#FFFACD", outline="#FF8C00")
                
                def on_label_leave(event, tag=group_tag):
                    self.image_canvas.itemconfig(f"{tag}&&rect_{i}", fill="#FFFFE0", outline="#FFA500")
                
                self.image_canvas.tag_bind(group_tag, "<Enter>", on_label_enter)
                self.image_canvas.tag_bind(group_tag, "<Leave>", on_label_leave)
            else:
                self.status_bar.config(text=f"警告: 单词'{word}'位置信息异常")

    def on_word_label_click(self, index):
        """点击图片上的单词标签时，显示单词详情"""
        if index < len(self.recognized_words):
            self.current_word_index = index
            word = self.recognized_words[index]
            self.word_label.config(text=word)
            
            # 清空之前的详情
            self.phonetic_label.config(text="")
            self.translation_text.config(state=tk.NORMAL)
            self.translation_text.delete(1.0, tk.END)
            self.translation_text.config(state=tk.DISABLED)
            self.example_text.config(state=tk.NORMAL)
            self.example_text.delete(1.0, tk.END)
            self.example_text.config(state=tk.DISABLED)
            
            self.highlight_selected_word(word) # 高亮图片描述中的词（如果保留该功能）
            self.query_word_details(word)
        # else:
            # print(f"Error: Word index {index} out of bounds for recognized_words.") # 日志

    def read_description(self):
        """朗读图片描述"""
        if not self.sentence_text.get(1.0, tk.END).strip():
            messagebox.showinfo("提示", "没有可朗读的描述")
            return
            
        description = self.sentence_text.get(1.0, tk.END).strip()
        success, message = pronounce_word(description)
        if not success:
            self.status_bar.config(text=message)

    def translate_description(self):
        """翻译图片描述"""
        if not self.sentence_text.get(1.0, tk.END).strip():
            messagebox.showinfo("提示", "没有可翻译的描述")
            return
            
        description = self.sentence_text.get(1.0, tk.END).strip()
        
        try:
            # 显示加载状态
            self.status_bar.config(text="正在翻译...")
            self.root.update()
            
            # 调用API翻译
            success, message, translation = self.api_service.translate_text(description)
            
            if success:
                # 更新翻译显示
                self.translation_text.config(state=tk.NORMAL)
                self.translation_text.delete(1.0, tk.END)
                self.translation_text.insert(tk.END, translation)
                self.translation_text.config(state=tk.DISABLED)
                
                self.status_bar.config(text="翻译完成")
            else:
                self.status_bar.config(text=message)
                messagebox.showerror("错误", message)
        except Exception as e:
            self.status_bar.config(text=f"翻译过程中出错: {str(e)}")
            messagebox.showerror("错误", f"翻译过程中出错: {str(e)}")

    def show_hint(self):
        """显示当前单词的提示"""
        # 获取当前焦点所在的输入框
        focused_widget = self.root.focus_get()
        
        # 检查是否是Text控件
        if not isinstance(focused_widget, tk.Text):
            # 如果没有焦点在输入框上，尝试获取最后一个有焦点的输入框
            if hasattr(self, 'last_focused_entry') and self.last_focused_entry:
                focused_widget = self.last_focused_entry
                focused_widget.focus_set()
            else:
                self.status_bar.config(text="请先选择一个输入框")
                return
        
        # 找到对应的单词和输入框
        current_word = None
        current_entry_index = -1
        current_word_index = -1  # 当前是第几个单词
        
        # 获取所有单词位置，按起始位置排序
        sorted_positions = sorted(self.word_positions, key=lambda x: x['start'])
        
        # 遍历所有单词
        for i, pos in enumerate(sorted_positions):
            entries = self.word_entries[pos['start']]
            if focused_widget in entries:
                current_word = pos['word']
                current_entry_index = entries.index(focused_widget)
                current_word_index = i + 1  # 当前是第几个单词（从1开始）
                break
        
        if current_word is None:
            self.status_bar.config(text="请先选择一个输入框")
            return
            
        # 创建弹层窗口
        hint_window = tk.Toplevel(self.root)
        hint_window.title("单词提示")
        
        # 设置弹层窗口大小
        window_width = 300
        window_height = 150
        
        # 计算窗口位置（居中显示）
        x = self.root.winfo_x() + (self.root.winfo_width() - window_width) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - window_height) // 2
        hint_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 设置弹层窗口样式
        hint_window.configure(bg='#e8f4f8')  # 浅蓝色背景
        hint_window.attributes('-topmost', True)  # 保持在最顶层
        
        # 创建内容框架
        content_frame = ttk.Frame(hint_window, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 显示当前单词
        word_label = ttk.Label(content_frame, 
                             text=current_word,
                             font=("Arial", 24, "bold"),
                             foreground="#1a5276")  # 深蓝色文字
        word_label.pack(pady=(0, 10))
        
        # 显示当前单词位置和字母位置
        position_label = ttk.Label(content_frame,
                                 text=f"第 {current_word_index} 个单词，填写第 {current_entry_index + 2} 个字母",
                                 font=("Arial", 12),
                                 foreground="#2874a6")  # 中蓝色文字
        position_label.pack(pady=(0, 10))
        
        # 添加倒计时标签
        countdown_label = ttk.Label(content_frame,
                                  text="3",
                                  font=("Arial", 12),
                                  foreground="#3498db")  # 浅蓝色文字
        countdown_label.pack(pady=(0, 10))
        
        # 添加关闭按钮
        close_button = ttk.Button(content_frame,
                                text="关闭",
                                command=hint_window.destroy)
        close_button.pack()
        
        # 倒计时函数
        def update_countdown(count):
            if count > 0:
                countdown_label.config(text=str(count))
                hint_window.after(1000, update_countdown, count - 1)
            else:
                hint_window.destroy()
        
        # 开始倒计时
        update_countdown(3)
        
        # 更新状态栏
        self.status_bar.config(text=f"提示：显示当前单词")

    def on_entry_focus(self, event):
        """当输入框获得焦点时"""
        self.last_focused_entry = event.widget

    def start_fill_words(self):
        """开始填词练习"""
        if not self.recognized_words:
            messagebox.showinfo("提示", "请先识别图片中的单词")
            return
            
        # 获取原始描述文本
        original_text = self.sentence_text.get(1.0, tk.END).strip()
        if not original_text:
            messagebox.showinfo("提示", "没有可用的描述文本")
            return
            
        # 按长度排序单词，确保先替换长单词，避免部分替换
        sorted_words = sorted(self.recognized_words, key=len, reverse=True)
        
        # 存储每个单词的位置信息
        self.word_positions = []
        
        # 创建填词文本
        fill_text = original_text
        for word in sorted_words:
            # 记录单词的位置（忽略大小写）
            start_pos = fill_text.lower().find(word.lower())
            if start_pos != -1:
                # 保存原始单词（保持原始大小写）
                original_word = fill_text[start_pos:start_pos + len(word)]
                self.word_positions.append({
                    'word': original_word,  # 使用原始大小写的单词
                    'start': start_pos,
                    'end': start_pos + len(word)
                })
        
        # 清空填词区域
        for widget in self.fill_words_frame.winfo_children():
            widget.destroy()
        
        # 创建文本显示区域
        text_frame = ttk.Frame(self.fill_words_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建文本组件用于自动换行
        self.fill_words_text = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 13), height=10)
        self.fill_words_text.pack(fill=tk.BOTH, expand=True)
        
        # 创建输入框字典
        self.word_entries = {}
        
        # 分割文本并创建输入框
        last_end = 0
        for pos in sorted(self.word_positions, key=lambda x: x['start']):
            # 添加单词前的文本
            if pos['start'] > last_end:
                text = fill_text[last_end:pos['start']]
                self.fill_words_text.insert(tk.END, text)
            
            # 创建单词的输入框容器
            word_frame = ttk.Frame(self.fill_words_frame)
            
            # 添加首字母标签（使用原始大小写）
            first_letter_label = ttk.Label(word_frame, text=pos['word'][0], font=("Arial", 13, "bold"))
            first_letter_label.pack(side=tk.LEFT, padx=(0, 2))
            
            # 为剩余字母创建输入框
            letter_entries = []
            for i in range(1, len(pos['word'])):  # 从第二个字母开始
                entry = tk.Text(word_frame, width=1, height=1, font=("Arial", 13))
                entry.pack(side=tk.LEFT, padx=0)
                
                # 设置输入框样式
                entry.configure(
                    relief=tk.SOLID,
                    borderwidth=1,
                    background="#f0f0f0",  # 浅灰色背景
                    selectbackground="#a6a6a6",  # 选中文本的背景色
                    selectforeground="black"  # 选中文本的前景色
                )
                
                # 绑定按键事件
                entry.bind('<KeyRelease>', lambda e, word=pos['word'], index=i: self.check_single_letter(e, word, index))
                entry.bind('<Tab>', self.move_to_next_letter)
                
                # 确保输入框可以接收焦点
                entry.config(takefocus=1)
                
                # 绑定点击事件
                entry.bind('<Button-1>', lambda e: e.widget.focus_set())
                
                # 绑定焦点事件
                entry.bind('<FocusIn>', self.on_entry_focus)
                
                letter_entries.append(entry)
            
            # 存储这个单词的所有输入框
            self.word_entries[pos['start']] = letter_entries
            
            # 将单词的输入框容器插入到文本中
            self.fill_words_text.window_create(tk.END, window=word_frame)
            
            last_end = pos['end']
        
        # 添加最后一个单词后的文本
        if last_end < len(fill_text):
            text = fill_text[last_end:]
            self.fill_words_text.insert(tk.END, text)
        
        # 禁用文本编辑，只允许在输入框中输入
        self.fill_words_text.config(state=tk.DISABLED)
        
        # 隐藏图片描述，显示填词区域
        self.sentence_frame.pack_forget()
        self.fill_words_frame.pack(fill=tk.BOTH, expand=False, pady=5)
        
        # 将焦点设置到第一个输入框
        if self.word_entries:
            first_word_entries = next(iter(self.word_entries.values()))
            first_word_entries[0].focus_set()
            # 初始化最后一个焦点输入框
            self.last_focused_entry = first_word_entries[0]
        
        # 更新状态栏
        self.status_bar.config(text="开始填词练习，输入正确的单词，按Tab键切换到下一个位置")
        
        # 创建按钮容器
        button_frame = ttk.Frame(self.fill_words_frame)
        button_frame.pack(pady=10)
        
        # 添加提示按钮
        if not hasattr(self, 'hint_btn'):
            self.hint_btn = ttk.Button(button_frame, 
                                     text="💡 提示", 
                                     style="Hint.TButton",
                                     command=self.show_hint)
            self.hint_btn.pack(pady=5)

    def check_single_letter(self, event, correct_word, letter_index):
        """检查单个字母的输入"""
        entry = event.widget
        user_letter = entry.get("1.0", tk.END).strip()
        
        # 如果输入超过一个字符，只保留第一个
        if len(user_letter) > 1:
            entry.delete("1.0", tk.END)
            entry.insert("1.0", user_letter[0])
        
        # 检查字母是否正确
        if user_letter and user_letter.lower() == correct_word[letter_index].lower():
            entry.configure(foreground="green")
            # 自动移动到下一个输入框
            self.move_to_next_letter_auto(entry)
        else:
            entry.configure(foreground="red")
        
        # 检查是否所有单词都正确
        correct_count = 0
        for pos, entries in self.word_entries.items():
            word = next(p['word'] for p in self.word_positions if p['start'] == pos)
            is_word_correct = True
            # 检查除首字母外的所有字母
            for i, entry in enumerate(entries):
                if entry.get("1.0", tk.END).strip().lower() != word[i + 1].lower():  # i + 1 因为跳过了首字母
                    is_word_correct = False
                    break
            if is_word_correct:
                correct_count += 1
        
        # 更新状态栏
        total_words = len(self.recognized_words)
        if correct_count == total_words:
            self.status_bar.config(text="恭喜！所有单词都填写正确！")
            # 检查提示按钮是否存在
            if hasattr(self, 'hint_btn') and self.hint_btn.winfo_exists():
                self.hint_btn.config(state=tk.DISABLED)
            # 播放完成音效
            self.play_completion_sound()
            # 显示恭喜弹层
            self.show_congratulations()
        else:
            #self.status_bar.config(text=f"填写 {correct_count}/{total_words} 个单词")
            # 检查提示按钮是否存在
            if hasattr(self, 'hint_btn') and self.hint_btn.winfo_exists():
                self.hint_btn.config(state=tk.NORMAL)

    def move_to_next_letter_auto(self, current_entry):
        """自动移动到下一个字母输入框"""
        # 找到当前输入框所在的单词
        for entries in self.word_entries.values():
            if current_entry in entries:
                current_index = entries.index(current_entry)
                if current_index < len(entries) - 1:
                    # 移动到下一个字母
                    entries[current_index + 1].focus_set()
                else:
                    # 移动到下一个单词的第一个字母
                    next_word_found = False
                    for next_entries in self.word_entries.values():
                        if next_entries == entries:
                            next_word_found = True
                            continue
                        if next_word_found:
                            next_entries[0].focus_set()
                            break
                break

    def play_completion_sound(self):
        """播放完成音效"""
        try:
            import winsound
            # Windows系统使用winsound
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        except ImportError:
            try:
                import os
                # macOS系统使用afplay
                os.system('afplay /System/Library/Sounds/Glass.aiff')
            except:
                # 如果都失败了，使用简单的蜂鸣声
                print('\a')  # 打印ASCII bell字符

    def move_to_next_letter(self, event):
        """移动到下一个字母输入框"""
        current_entry = event.widget
        # 找到当前输入框所在的单词
        for entries in self.word_entries.values():
            if current_entry in entries:
                current_index = entries.index(current_entry)
                if current_index < len(entries) - 1:
                    # 移动到下一个字母
                    entries[current_index + 1].focus_set()
                else:
                    # 移动到下一个单词的第一个字母
                    next_word_found = False
                    for next_entries in self.word_entries.values():
                        if next_entries == entries:
                            next_word_found = True
                            continue
                        if next_word_found:
                            next_entries[0].focus_set()
                            break
                break
        
        return "break"  # 阻止默认的Tab行为

    def show_congratulations(self):
        """显示恭喜弹层"""
        # 创建弹层窗口
        congrats_window = tk.Toplevel(self.root)
        congrats_window.title("恭喜")
        
        # 设置弹层窗口大小
        window_width = 300
        window_height = 200
        
        # 计算窗口位置（居中显示）
        x = self.root.winfo_x() + (self.root.winfo_width() - window_width) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - window_height) // 2
        congrats_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 设置弹层窗口样式
        congrats_window.configure(bg='#e8f4f8')  # 浅蓝色背景
        congrats_window.attributes('-topmost', True)  # 保持在最顶层
        
        # 创建内容框架
        content_frame = ttk.Frame(congrats_window, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加图标
        icon_label = ttk.Label(content_frame, 
                             text="🎉", 
                             font=("Arial", 48),
                             background="#e8f4f8",
                             foreground="#2c7da0")
        icon_label.pack(pady=(0, 10))
        
        # 添加恭喜文本
        congrats_label = ttk.Label(content_frame, 
                                 text="恭喜！", 
                                 font=("Arial", 24, "bold"),
                                 background="#e8f4f8",
                                 foreground="#1a5276")
        congrats_label.pack(pady=(0, 5))
        
        # 添加完成文本
        complete_label = ttk.Label(content_frame,
                                 text="所有单词都填写正确！",
                                 font=("Arial", 14),
                                 background="#e8f4f8",
                                 foreground="#2874a6")
        complete_label.pack(pady=(0, 10))
        
        # 添加倒计时标签
        countdown_label = ttk.Label(content_frame,
                                  text="3",
                                  font=("Arial", 12),
                                  background="#e8f4f8",
                                  foreground="#3498db")
        countdown_label.pack(pady=(0, 10))
        
        # 倒计时函数
        def update_countdown(count):
            if count > 0:
                countdown_label.config(text=str(count))
                congrats_window.after(1000, update_countdown, count - 1)
            else:
                congrats_window.destroy()
        
        # 开始倒计时
        update_countdown(3)

# 主程序入口
if __name__ == "__main__":
    root = tk.Tk()
    app = WordLearnerApp(root)
    root.mainloop()