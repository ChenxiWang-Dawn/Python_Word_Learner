import os
import sys
import unittest
import sqlite3
import tempfile
from PIL import Image
import shutil

# 导入要测试的模块
from word_details import WordDetailsManager
from image_manager import ImageManager
from api_service import APIService

class TestWordDetailsManager(unittest.TestCase):
    """测试WordDetailsManager类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.word_manager = WordDetailsManager(self.db_path)
        
        # 初始化数据库
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
        
        # 添加测试数据
        cursor.execute(
            "INSERT INTO words (word, translation, example, image_path, review_count) VALUES (?, ?, ?, ?, ?)",
            ("apple", "苹果", "I eat an apple every day.", "test_image.jpg", 3)
        )
        cursor.execute(
            "INSERT INTO words (word, translation, example, image_path, review_count) VALUES (?, ?, ?, ?, ?)",
            ("banana", "香蕉", "The monkey likes bananas.", "test_image2.jpg", 1)
        )
        
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """测试后清理"""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_get_wordbook_words(self):
        """测试获取生词本单词列表"""
        # 测试默认排序（添加时间）
        words = self.word_manager.get_wordbook_words()
        self.assertEqual(len(words), 2)
        
        # 测试按单词排序
        words = self.word_manager.get_wordbook_words(sort_option="单词")
        self.assertEqual(words[0][0], "apple")
        self.assertEqual(words[1][0], "banana")
        
        # 测试按复习次数排序
        words = self.word_manager.get_wordbook_words(sort_option="复习次数")
        self.assertEqual(words[0][0], "apple")
        self.assertEqual(words[0][3], 3)  # 复习次数
        
        # 测试搜索功能
        words = self.word_manager.get_wordbook_words(search_term="app")
        self.assertEqual(len(words), 1)
        self.assertEqual(words[0][0], "apple")
    
    def test_get_word_details(self):
        """测试获取单词详情"""
        # 测试获取存在的单词
        word_data = self.word_manager.get_word_details("apple")
        self.assertIsNotNone(word_data)
        self.assertEqual(word_data[1], "apple")
        self.assertEqual(word_data[2], "苹果")
        
        # 测试获取不存在的单词
        word_data = self.word_manager.get_word_details("nonexistent")
        self.assertIsNone(word_data)
    
    def test_delete_word(self):
        """测试删除单词"""
        # 测试删除存在的单词
        result = self.word_manager.delete_word("apple")
        self.assertTrue(result)
        
        # 验证单词已被删除
        word_data = self.word_manager.get_word_details("apple")
        self.assertIsNone(word_data)
        
        # 测试删除不存在的单词
        result = self.word_manager.delete_word("nonexistent")
        self.assertFalse(result)
    
    def test_add_word(self):
        """测试添加单词"""
        # 测试添加新单词
        result, status = self.word_manager.add_word("cat", "猫", "I have a cat.", "cat.jpg")
        self.assertTrue(result)
        self.assertEqual(status, "added")
        
        # 验证单词已添加
        word_data = self.word_manager.get_word_details("cat")
        self.assertIsNotNone(word_data)
        self.assertEqual(word_data[2], "猫")
        
        # 测试更新已存在的单词
        result, status = self.word_manager.add_word("cat", "猫咪", "Cats are cute.", "cat2.jpg")
        self.assertTrue(result)
        self.assertEqual(status, "updated")
        
        # 验证单词已更新
        word_data = self.word_manager.get_word_details("cat")
        self.assertEqual(word_data[2], "猫咪")
        self.assertEqual(word_data[3], "Cats are cute.")

class TestImageManager(unittest.TestCase):
    """测试ImageManager类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        self.image_manager = ImageManager(self.test_dir)
        
        # 创建测试图片
        self.test_image = Image.new('RGB', (100, 100), color='red')
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir)
    
    def test_save_image(self):
        """测试保存图片"""
        # 测试保存图片
        filepath = self.image_manager.save_image(self.test_image, "test")
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))
        
        # 测试保存空图片
        filepath = self.image_manager.save_image(None, "test")
        self.assertIsNone(filepath)
    
    def test_load_image(self):
        """测试加载图片"""
        # 先保存图片
        filepath = self.image_manager.save_image(self.test_image, "test")
        
        # 测试加载存在的图片
        loaded_image = self.image_manager.load_image(filepath)
        self.assertIsNotNone(loaded_image)
        self.assertEqual(loaded_image.size, (100, 100))
        
        # 测试加载不存在的图片
        loaded_image = self.image_manager.load_image("nonexistent.jpg")
        self.assertIsNone(loaded_image)

class TestAPIService(unittest.TestCase):
    """测试APIService类"""
    
    def setUp(self):
        """测试前准备"""
        self.api_service = APIService()
        # 启用模拟模式
        self.api_service.set_mock_mode(True)
    
    def test_recognize_text(self):
        """测试识别文字"""
        # 测试模拟模式下的识别
        success, message, words = self.api_service.recognize_text("dummy_path.jpg")
        self.assertTrue(success)
        self.assertIn("模拟数据", message)
        self.assertTrue(len(words) > 0)
    
    def test_query_word_details(self):
        """测试查询单词详情"""
        # 测试查询已知单词
        success, message, data, error = self.api_service.query_word_details("apple")
        self.assertTrue(success)
        self.assertIn("模拟数据", message)
        self.assertEqual(data["translation"], "苹果，一种常见的水果")
        
        # 测试查询未知单词（会生成随机数据）
        success, message, data, error = self.api_service.query_word_details("randomword")
        self.assertTrue(success)
        self.assertIn("随机模拟数据", message)
        self.assertTrue("translation" in data)

if __name__ == "__main__":
    unittest.main()