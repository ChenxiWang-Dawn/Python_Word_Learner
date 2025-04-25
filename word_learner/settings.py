import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

class SettingsManager:
    """设置管理器"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        
        # 默认设置
        self.api_key = ""
        self.show_translation_on_image = False
        self.show_phonetic_on_image = False
        self.english_level = "四级"
        self.english_levels = ["小学", "初中", "高中", "四级", "六级", "专业八级"]
        
        # 加载设置
        self.load_settings()
    
    def load_settings(self):
        """从数据库加载设置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 确保设置表存在
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        conn.commit()
        
        # 加载设置
        cursor.execute("SELECT key, value FROM settings")
        settings = dict(cursor.fetchall())
        
        # 应用设置
        self.api_key = settings.get("api_key", "")
        self.show_translation_on_image = settings.get("show_translation_on_image", "0") == "1"
        self.show_phonetic_on_image = settings.get("show_phonetic_on_image", "0") == "1"
        self.english_level = settings.get("english_level", "四级")
        
        conn.close()
    
    def save_settings(self):
        """保存设置到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 保存设置
        settings = {
            "api_key": self.api_key,
            "show_translation_on_image": "1" if self.show_translation_on_image else "0",
            "show_phonetic_on_image": "1" if self.show_phonetic_on_image else "0",
            "english_level": self.english_level
        }
        
        for key, value in settings.items():
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_word_levels(self):
        """获取各等级的单词列表（示例数据）"""
        # 实际应用中应该从数据库或文件中加载
        return {
            "小学": ["apple", "book", "cat", "dog", "egg", "fish", "good", "happy"],
            "初中": ["ability", "benefit", "consider", "determine", "efficient", "famous", "generate"],
            "高中": ["abandon", "bachelor", "calculate", "decade", "elaborate", "facilitate", "genuine"],
            "四级": ["abolish", "bizarre", "contempt", "deteriorate", "eloquent", "formidable", "gratify"],
            "六级": ["abstruse", "cacophony", "deleterious", "ephemeral", "fastidious", "garrulous", "hegemony"],
            "专业八级": ["abeyance", "bellicose", "circumlocution", "desuetude", "ebullient", "fecund", "gainsay"]
        }
    
    def filter_words_by_level(self, words):
        """根据英语等级筛选单词"""
        # 获取词库数据
        word_levels = self.get_word_levels()
        
        # 获取当前选择的等级
        current_level = self.english_level
        current_level_index = self.english_levels.index(current_level)
        
        # 获取主词库单词
        primary_words = set(word_levels[current_level])
        
        # 创建临近难度的词库列表
        nearby_levels = []
        
        # 添加比当前等级高一级的词库
        if current_level_index < len(self.english_levels) - 1:
            higher_level = self.english_levels[current_level_index + 1]
            nearby_levels.append(set(word_levels[higher_level]))
        
        # 添加比当前等级低一级的词库
        if current_level_index > 0:
            lower_level = self.english_levels[current_level_index - 1]
            nearby_levels.append(set(word_levels[lower_level]))
        
        # 添加其他词库
        other_levels = []
        for i, level in enumerate(self.english_levels):
            if i != current_level_index and i != current_level_index - 1 and i != current_level_index + 1:
                other_levels.append(set(word_levels[level]))
        
        # 筛选单词
        filtered_words = []
        remaining_words = []
        
        # 首先检查每个单词是否在主词库中
        for word in words:
            word_lower = word.lower()
            if word_lower in primary_words:
                filtered_words.append((word, True))  # 主词库单词
            else:
                remaining_words.append(word)
        
        # 如果主词库单词不足50%，尝试从临近词库和其他词库中补充
        if len(filtered_words) < len(words) * 0.5:
            # 需要从主词库中补充的单词数量
            needed_primary = max(0, int(len(words) * 0.5) - len(filtered_words))
            
            # 从临近词库中查找单词
            for nearby_level in nearby_levels:
                for word in remaining_words[:]:
                    word_lower = word.lower()
                    if word_lower in nearby_level:
                        filtered_words.append((word, False))  # 非主词库单词
                        remaining_words.remove(word)
                        
                        if len(filtered_words) >= len(words):
                            break
                if len(filtered_words) >= len(words):
                    break
            
            # 如果还有剩余单词，从其他词库中查找
            if remaining_words and len(filtered_words) < len(words):
                for other_level in other_levels:
                    for word in remaining_words[:]:
                        word_lower = word.lower()
                        if word_lower in other_level:
                            filtered_words.append((word, False))  # 非主词库单词
                            remaining_words.remove(word)
                            
                            if len(filtered_words) >= len(words):
                                break
                    if len(filtered_words) >= len(words):
                        break
        
        # 添加剩余未匹配的单词
        for word in remaining_words:
            filtered_words.append((word, False))  # 非主词库单词
        
        return filtered_words

def create_settings_page(parent, settings_manager, save_callback):
    """创建设置页面"""
    page = ttk.Frame(parent)
    
    # 创建设置框架
    settings_frame = ttk.LabelFrame(page, text="应用设置")
    settings_frame.pack(fill=tk.BOTH, expand=False, padx=20, pady=20)
    
    # API密钥设置
    ttk.Label(settings_frame, text="OpenAI API密钥:").pack(anchor=tk.W, padx=10, pady=(10, 0))
    
    api_key_var = tk.StringVar(value=settings_manager.api_key)
    api_key_entry = ttk.Entry(settings_frame, textvariable=api_key_var, width=50, show="*")
    api_key_entry.pack(fill=tk.X, padx=10, pady=5)
    
    # 显示/隐藏密钥
    show_key_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(settings_frame, text="显示密钥", variable=show_key_var, 
                   command=lambda: api_key_entry.config(show="" if show_key_var.get() else "*")).pack(anchor=tk.W, padx=10)
    
    # 显示设置
    display_frame = ttk.LabelFrame(page, text="显示设置")
    display_frame.pack(fill=tk.BOTH, expand=False, padx=20, pady=20)
    
    # 在图片上显示翻译
    show_translation_var = tk.BooleanVar(value=settings_manager.show_translation_on_image)
    ttk.Checkbutton(display_frame, text="在图片上显示翻译", variable=show_translation_var).pack(anchor=tk.W, padx=10, pady=5)
    
    # 在图片上显示音标
    show_phonetic_var = tk.BooleanVar(value=settings_manager.show_phonetic_on_image)
    ttk.Checkbutton(display_frame, text="在图片上显示音标", variable=show_phonetic_var).pack(anchor=tk.W, padx=10, pady=5)
    
    # 英语等级设置
    level_frame = ttk.LabelFrame(page, text="英语等级设置")
    level_frame.pack(fill=tk.BOTH, expand=False, padx=20, pady=20)
    
    ttk.Label(level_frame, text="设置你的英语等级:").pack(anchor=tk.W, padx=10, pady=(10, 0))
    
    english_level_var = tk.StringVar(value=settings_manager.english_level)
    level_combo = ttk.Combobox(level_frame, textvariable=english_level_var, 
                              values=settings_manager.english_levels, state="readonly", width=15)
    level_combo.pack(anchor=tk.W, padx=10, pady=5)
    
    ttk.Label(level_frame, text="设置英语等级后，从图片中识别的单词优先从符合英语等级的主词库中选择，\n并保证主词库单词占比至少为50%。剩余单词优先从临近难度的词库中匹配。").pack(anchor=tk.W, padx=10, pady=5)
    
    # 保存按钮
    def save_settings():
        settings_manager.api_key = api_key_var.get().strip()
        settings_manager.show_translation_on_image = show_translation_var.get()
        settings_manager.show_phonetic_on_image = show_phonetic_var.get()
        settings_manager.english_level = english_level_var.get()
        
        if settings_manager.save_settings():
            messagebox.showinfo("成功", "设置已保存")
            if save_callback:
                save_callback()
        else:
            messagebox.showerror("错误", "保存设置失败")
    
    ttk.Button(page, text="保存设置", command=save_settings).pack(anchor=tk.W, padx=20, pady=10)
    
    # 关于信息
    about_frame = ttk.LabelFrame(page, text="关于")
    about_frame.pack(fill=tk.BOTH, expand=False, padx=20, pady=20)
    
    ttk.Label(about_frame, text="拍照学单词 v1.0").pack(anchor=tk.W, padx=10, pady=(10, 0))
    ttk.Label(about_frame, text="一个帮助你通过拍照学习英语单词的应用").pack(anchor=tk.W, padx=10, pady=(5, 0))
            
    return page