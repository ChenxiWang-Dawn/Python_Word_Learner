import requests
import json
import base64
import random
import os
from openai import OpenAI

class APIService:
    """API服务"""
    
    def __init__(self, api_key=""):
        # Prioritize environment variable, fallback to passed key
        dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", api_key)
        self.api_key = dashscope_api_key # Store the key being used
        
        if self.api_key:
             self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        else:
            self.client = None # No client if no key
            print("WARN: DashScope API key not found. API calls will fail unless mock_mode is True.")

        self.mock_mode = False  # Default to False, can be enabled later
        
        # 模拟数据
        self.mock_words = [
            "apple", "banana", "cat", "dog", "elephant", "fish", "giraffe", "house",
            "internet", "jungle", "king", "lion", "monkey", "notebook", "orange",
            "pencil", "queen", "rabbit", "sun", "tiger", "umbrella", "violin",
            "water", "xylophone", "yellow", "zebra", "book", "computer", "desk",
            "education", "family", "garden", "happiness", "information", "journey"
        ]
        
        self.mock_word_details = {
            "apple": {
                "translation": "苹果，一种常见的水果",
                "phonetic": "/ˈæpl/",
                "example": "An apple a day keeps the doctor away."
            },
            "book": {
                "translation": "书，书籍",
                "phonetic": "/bʊk/",
                "example": "I'm reading an interesting book about history."
            },
            "computer": {
                "translation": "电脑，计算机",
                "phonetic": "/kəmˈpjuːtər/",
                "example": "She uses her computer to write code."
            }
            # 可以添加更多模拟数据
        }
    
    def set_api_key(self, api_key):
        """设置API密钥并重新初始化客户端"""
        self.api_key = api_key
        # Re-initialize client with the new key
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        else:
            self.client = None
            print("WARN: DashScope API key removed or empty. API calls will fail unless mock_mode is True.")
    
    def set_mock_mode(self, mock_mode):
        """设置是否使用模拟数据"""
        self.mock_mode = mock_mode
    
    def recognize_text(self, image_path):
        """识别图片中的文字 (使用 Qwen-VL)"""
        if self.mock_mode:
            # 使用模拟数据
            num_words = random.randint(3, 10)
            words = random.sample(self.mock_words, num_words)
            description = f"This is a mock description containing words: {', '.join(words)}"
            return True, "识别成功（模拟数据）", words, description
        
        if not self.client:
            return False, "API客户端未初始化 (检查API密钥)", [], ""
        
        try:
            # 读取图片并转为base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            messages = [
                 {
                     "role": "system",
                     "content": "你是一位专业的英语学习专家，专注于通过图片帮助用户学习英语。你的任务是根据用户提供的图片内容，生成相关的英语单词、短语，以提升用户的英语水平。能够处理多种类型的图片，包括但不限于实物照片、插画、图表等。结合图片主题，提供实用的英语表达，适用于日常生活、工作或学术场景。请以JSON格式返回，包含两个字段：1. words: 提取的关键单词数组；2. description: 对图片内容的英文描述。描述必须自然地包含所有提取的单词，并确保每个单词都在描述中出现。格式为：{\"words\": [\"word1\", \"word2\", ...], \"description\": \"图片描述\"}。只返回JSON，不要返回其他内容。"
                 },
                 {
                     "role": "user",
                     "content": [
                         {
                             "type": "text",
                             "text": "提取图片中的关键信息，包括人物、动作、场景、形容词等。根据图片内容，生成准确且相关的多个英文词汇、短语，并提供一个完整的英文描述。描述必须自然地包含所有提取的单词。"
                         },
                         {
                             "type": "image_url",
                             "image_url": {
                                 "url": f"data:image/jpeg;base64,{base64_image}"
                             }
                         }
                     ]
                 }
             ]

            completion = self.client.chat.completions.create(
                model="qwen-vl-max", # Use Qwen VL model
                messages=messages,
                max_tokens=500 # 增加token限制以容纳描述
            )

            content = completion.choices[0].message.content
            
            # 解析JSON响应
            try:
                # 处理可能的markdown代码块
                cleaned_content = content.strip()
                if cleaned_content.startswith("```json"):
                    cleaned_content = cleaned_content[7:]
                if cleaned_content.endswith("```"):
                    cleaned_content = cleaned_content[:-3]
                cleaned_content = cleaned_content.strip()

                data = json.loads(cleaned_content)
                words = data.get("words", [])
                description = data.get("description", "")
                
                # 过滤非单词
                words = [w for w in words if isinstance(w, str) and w.strip()]
                
                # 验证描述是否包含所有单词
                missing_words = [word for word in words if word.lower() not in description.lower()]
                if missing_words:
                    # 如果描述中缺少某些单词，将它们添加到描述末尾
                    description += f"\n\nAdditional words: {', '.join(missing_words)}"
                
                return True, "识别成功 (Qwen)", words, description
            except json.JSONDecodeError:
                print(f"Qwen VL response content: {content}")
                return False, "无法解析Qwen识别结果", [], ""
        except Exception as e:
            print(f"Qwen VL API Error: {e}")
            return False, f"识别过程中出错: {str(e)}", [], ""
    
    def query_word_details(self, word):
        """查询单词详情 (使用 Qwen-Turbo)"""
        if self.mock_mode:
            # 使用模拟数据
            if word in self.mock_word_details:
                return True, "查询成功（模拟数据）", self.mock_word_details[word], ""
            else:
                # 生成随机数据
                mock_data = {
                    "translation": f"{word}的模拟翻译",
                    "phonetic": f"/{word[0]}{word[-1]}/",
                    "example": f"This is a mock example sentence using the word '{word}'."
                }
                return True, "查询成功（随机模拟数据）", mock_data, ""
        
        if not self.client:
            return False, "API客户端未初始化 (检查API密钥)", {}, "API客户端未初始化"
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "你是一个英语词典助手，请提供单词的中文释义、音标和英文例句。"
                },
                {
                    "role": "user",
                    "content": f"请提供单词 '{word}' 的中文释义、音标和一个英文例句，以JSON格式返回，格式为：{{\"translation\": \"中文释义\", \"phonetic\": \"音标\", \"example\": \"英文例句\"}}。只返回JSON，不要返回其他内容。"
                }
            ]

            completion = self.client.chat.completions.create(
                model="qwen-turbo", # Use Qwen text model
                messages=messages,
                max_tokens=200 # Keep existing max_tokens
            )

            content = completion.choices[0].message.content
            
            # 解析JSON响应
            try:
                # Handle potential markdown code blocks
                cleaned_content = content.strip()
                if cleaned_content.startswith("```json"):
                    cleaned_content = cleaned_content[7:]
                if cleaned_content.endswith("```"):
                    cleaned_content = cleaned_content[:-3]
                cleaned_content = cleaned_content.strip()

                data = json.loads(cleaned_content)
                # Ensure all expected keys are present, provide defaults if not
                data.setdefault("translation", "无法获取释义")
                data.setdefault("phonetic", "")
                data.setdefault("example", "无法获取例句")

                return True, "查询成功 (Qwen)", data, ""
            except json.JSONDecodeError:
                print(f"Qwen Turbo response content: {content}")
                return False, "无法解析Qwen响应", {}, "无法解析API响应"
        except Exception as e:
            # from openai import APIError, RateLimitError etc.
            print(f"Qwen Turbo API Error: {e}")
            return False, f"查询过程中出错: {str(e)}", {}, f"查询过程中出错: {str(e)}"

    def translate_text(self, text):
        """翻译文本 (使用 Qwen-Turbo)"""
        if self.mock_mode:
            # 使用模拟数据
            mock_translation = "这是一个模拟的中文翻译。"
            return True, "翻译成功（模拟数据）", mock_translation
        
        if not self.client:
            return False, "API客户端未初始化 (检查API密钥)", ""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "你是一位专业的翻译专家。请将英文文本翻译成中文，保持翻译的准确性和流畅性。只返回翻译结果，不要添加任何额外的解释或说明。"
                },
                {
                    "role": "user",
                    "content": f"请将以下英文文本翻译成中文：\n\n{text}"
                }
            ]

            completion = self.client.chat.completions.create(
                model="qwen-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.3  # 降低温度以获得更稳定的翻译结果
            )

            translation = completion.choices[0].message.content.strip()
            # 移除可能的引号和其他格式
            translation = translation.strip('"\'')
            return True, "翻译成功", translation
        except Exception as e:
            print(f"Translation API Error: {e}")
            return False, f"翻译过程中出错: {str(e)}", ""