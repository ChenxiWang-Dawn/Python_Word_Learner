import sqlite3

class WordDetailsManager:
    """单词详情管理器"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def get_wordbook_words(self, search_term="", sort_option="添加时间"):
        """获取生词本单词列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT word, translation, added_date, review_count FROM words"
        params = []
        
        if search_term:
            query += " WHERE word LIKE ? OR translation LIKE ?"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        # 根据排序选项设置ORDER BY子句
        if sort_option == "单词":
            query += " ORDER BY word"
        elif sort_option == "复习次数":
            query += " ORDER BY review_count DESC"
        else:  # 默认按添加时间排序
            query += " ORDER BY added_date DESC"
        
        cursor.execute(query, params)
        words = cursor.fetchall()
        conn.close()
        
        return words
    
    def get_word_details(self, word):
        """获取单词详情"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, word, translation, example, image_path, added_date, review_count, last_review_date FROM words WHERE word = ?",
            (word,)
        )
        word_data = cursor.fetchone()
        conn.close()
        
        return word_data
    
    def delete_word(self, word):
        """删除单词"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取单词ID
            cursor.execute("SELECT id FROM words WHERE word = ?", (word,))
            word_id = cursor.fetchone()
            
            if word_id:
                # 删除复习记录
                cursor.execute("DELETE FROM review_records WHERE word_id = ?", (word_id[0],))
                # 删除单词
                cursor.execute("DELETE FROM words WHERE id = ?", (word_id[0],))
                conn.commit()
                return True
            else:
                return False
        except Exception as e:
            print(f"删除单词失败: {str(e)}")
            return False
        finally:
            conn.close()
    
    def add_word(self, word, translation, example, image_path):
        """添加单词到生词本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查是否已存在
            cursor.execute("SELECT id FROM words WHERE word = ?", (word,))
            existing = cursor.fetchone()
            
            if existing:
                # 如果已存在，更新
                cursor.execute(
                    "UPDATE words SET translation = ?, example = ?, image_path = ? WHERE word = ?",
                    (translation, example, image_path, word)
                )
                result = "updated"
            else:
                # 如果不存在，插入新记录
                cursor.execute(
                    "INSERT INTO words (word, translation, example, image_path) VALUES (?, ?, ?, ?)",
                    (word, translation, example, image_path)
                )
                result = "added"
            
            conn.commit()
            return True, result
        except Exception as e:
            print(f"添加单词失败: {str(e)}")
            return False, str(e)
        finally:
            conn.close()