import tkinter as tk
from tkinter import messagebox
import os
import sqlite3

# 导入应用程序
from app import WordLearnerApp
from api_service import APIService
from word_details import WordDetailsManager
from image_manager import ImageManager

def test_api_service():
    """测试API服务"""
    api = APIService("aaaaaa")
    api.set_mock_mode(True)
    
    # 测试识别文字
    success, message, words = api.recognize_text("dummy_path.jpg")
    print(f"识别文字: 成功={success}, 消息={message}, 单词数量={len(words)}")
    print(f"识别到的单词: {words}")
    
    # 测试查询单词详情
    success, message, data, error = api.query_word_details("apple")
    print(f"查询单词详情: 成功={success}, 消息={message}")
    print(f"单词详情: {data}")

def test_word_details_manager():
    """测试单词详情管理器"""
    db_path = "words.db"
    if not os.path.exists(db_path):
        init_database(db_path)
    
    manager = WordDetailsManager(db_path)
    
    # 获取所有单词
    words = manager.get_wordbook_words()
    print(f"生词本中有 {len(words)} 个单词:")
    for word in words:
        print(f"  - {word[0]}: {word[1]}")
    
    # 获取特定单词详情
    if words:
        word = words[0][0]
        details = manager.get_word_details(word)
        print(f"\n单词 '{word}' 的详情:")
        print(f"  - 翻译: {details[2]}")
        print(f"  - 例句: {details[3]}")
        print(f"  - 复习次数: {details[6]}")

def main():
    """主函数，启动应用程序的测试版本"""
    # 运行特定功能测试
    print("=== 测试API服务 ===")
    test_api_service()
    
    print("\n=== 测试单词详情管理器 ===")
    test_word_details_manager()
    
    # 是否启动GUI应用程序
    start_gui = input("\n是否启动GUI应用程序? (y/n): ").lower() == 'y'
    
    if start_gui:
        # 检查数据库是否存在，如果不存在则创建
        db_path = "words.db"
        if not os.path.exists(db_path):
            init_database(db_path)
        
        # 创建主窗口
        root = tk.Tk()
        
        # 创建应用程序实例
        app = WordLearnerApp(root)
        
        # 设置API服务为模拟模式
        app.api_service.set_mock_mode(True)
        
        # 显示提示信息
        messagebox.showinfo("测试模式", "应用程序正在以测试模式运行，将使用模拟数据而不是实际调用API。")
        
        # 启动主循环
        root.mainloop()

def init_database(db_path):
    """初始化数据库"""
    conn = sqlite3.connect(db_path)
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
        last_review_date TIMESTAMP,
        next_review_date TIMESTAMP,
        review_interval REAL DEFAULT 1
    )
    ''')
    
    # 创建复习记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS review_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER,
        review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT,
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
    
    # 添加一些示例单词
    sample_words = [
        ("apple", "苹果", "An apple a day keeps the doctor away.", None),
        ("book", "书", "I'm reading an interesting book.", None),
        ("cat", "猫", "My cat likes to sleep all day.", None),
        ("dog", "狗", "The dog is barking at the mailman.", None),
        ("elephant", "大象", "Elephants have long trunks.", None)
    ]
    
    for word, translation, example, image_path in sample_words:
        cursor.execute(
            "INSERT OR IGNORE INTO words (word, translation, example, image_path) VALUES (?, ?, ?, ?)",
            (word, translation, example, image_path)
        )
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()