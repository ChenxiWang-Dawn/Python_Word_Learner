import requests
import json
import base64
import os
from openai import OpenAI
from PIL import Image

# Hardcoded API key
HARDCODED_API_KEY = "sk-5ddc81d9a00048f898f0c80f405fdf24"

# Mock English class level (would be imported from another module in real use)
english_class = "雅思" ###需要从前端获取

class APIService:
    """API服务"""
    
    def __init__(self, api_key=""):
        # Simplify initialization to reduce errors
        self.api_key = "sk-5ddc81d9a00048f898f0c80f405fdf24"  # Hardcoded key
        
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
            print("INFO: API client initialized successfully.")
        except Exception as e:
            print(f"WARNING: Failed to initialize API client: {e}")
            self.client = None
    
    def set_api_key(self, api_key):
        """设置API密钥 (现在是空操作，因为密钥已硬编码)"""
        # This method is now a no-op because we're always using the hardcoded key
        pass
    
    def recognize_text(self, image_path):
        """识别图片中的文字 (使用 Qwen-VL)"""
        if not self.client:
            print("ERROR: API client not initialized despite hardcoded key.")
            return False, "API客户端未初始化", [], []
        
        try:
            # 获取图片分辨率
            img = Image.open(image_path)
            image_resolution = f"{img.width}x{img.height}"
            print(f"DEBUG: Image resolution: {image_resolution}")
            
            # 读取图片并转为base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 构建新的 prompt，注意对JSON模板中的花括号进行转义
            system_prompt = f"""你是一位专业的英语学习专家，专注于通过图片帮助用户学习英语。你的任务是根据用户提供的图片内容，生成相关的英语单词、短语，以提升用户的英语水平。

请按以下步骤进行：

1. 仔细观察图片，识别其中的关键元素，包括：人物、物体、动作、场景、形容词等
2. 从这些元素中提取5-8个符合{english_class}水平的重要英文单词
3. 基于这些提取的单词，构造一个完整的英文句子来描述图片内容
4. 确保句子中包含所有提取出的重要单词
5. 为每个单词确定在图片中的坐标位置

重要要求：
- 提取的单词必须在生成的描述句子中都能找到
- 描述句子应该自然流畅，同时包含所有重要单词
- 如果某个重要单词在自然描述中难以使用，可以适当调整句子结构来包含它

坐标要求：
- 坐标必须在图片范围内：x坐标在0到{img.width}之间，y坐标在0到{img.height}之间
- 尽量将坐标指向图片中与单词含义相关的物体或区域的中心位置
- 如果单词在图片中有明确对应的物体，将坐标指向该物体
- 如果单词是抽象概念或无法明确指向，将坐标设置在图片中心区域，但要错开不同单词的位置
- 多个单词的坐标不要完全重叠，可以在附近区域分散排列

图片分辨率：{image_resolution}

请以JSON数组格式返回，格式为：[{{"word": "单词", "position": [x, y]}}, {{"sentence":"包含所有单词的描述句子"}}]。只返回JSON数组，不要返回其他内容。"""
            
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            print("DEBUG: Sending request to API...")
            response = self.client.chat.completions.create(
                model="qwen-vl-max",
                messages=messages,
                max_tokens=2000
            )
            
            print(f"DEBUG: API Response: {response.choices[0].message.content}")
            
            # 尝试解析返回的JSON
            try:
                content = response.choices[0].message.content
                print(f"DEBUG: API Response: {content}")
                
                # 处理可能的markdown代码块
                cleaned_content = content.strip()
                if cleaned_content.startswith("```json"):
                    cleaned_content = cleaned_content[7:]
                if cleaned_content.endswith("```"):
                    cleaned_content = cleaned_content[:-3]
                cleaned_content = cleaned_content.strip()
                
                words_data = json.loads(cleaned_content)
                print(f"DEBUG: Parsed words data: {words_data}")
                
                if not isinstance(words_data, list):
                    print("ERROR: API response is not a list")
                    return False, "API返回格式错误", [], []
                
                # 提取单词、位置和句子
                words = []
                positions = []
                sentence = ""
                
                for item in words_data:
                    if isinstance(item, dict):
                        if "word" in item and "position" in item:
                            words.append(item["word"])
                            positions.append(item["position"])
                        elif "sentence" in item:
                            sentence = item["sentence"]
                
                print(f"DEBUG: Extracted words: {words}")
                print(f"DEBUG: Extracted positions: {positions}")
                print(f"DEBUG: Extracted sentence: {sentence}")
                
                return True, "识别成功", words, positions, sentence
            except json.JSONDecodeError as e:
                print(f"ERROR: Failed to parse API response as JSON: {e}")
                print(f"ERROR: Raw content: {response.choices[0].message.content}")
                return False, "API返回格式错误", [],[], []
            except Exception as e:
                print(f"ERROR: Unexpected error processing API response: {e}")
                return False, str(e), [],[],[]
                
        except Exception as e:
            print(f"ERROR: API call failed: {e}")
            return False, str(e), [],[], []
    
    def query_word_details(self, word):
        """查询单词详情 (使用 Qwen-Turbo)"""
        if not self.client:
            print("ERROR: API client not initialized despite hardcoded key.")
            return False, "API客户端未初始化", {}, "API客户端未初始化"
        
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
                model="qwen-turbo",
                messages=messages,
                max_tokens=200
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
                # 确保所有期望的键都存在
                data.setdefault("translation", "无法获取释义")
                data.setdefault("phonetic", "")
                data.setdefault("example", "无法获取例句")

                return True, "查询成功", data, ""
            except json.JSONDecodeError:
                print(f"Qwen Turbo response content: {content}")
                return False, "无法解析Qwen响应", {}, "无法解析API响应"
        except Exception as e:
            print(f"Qwen Turbo API Error: {e}")
            return False, f"查询过程中出错: {str(e)}", {}, f"查询过程中出错: {str(e)}"

    def translate_text(self, text):
        """翻译文本 (使用 Qwen-Turbo)"""
        if not self.client:
            return False, "API客户端未初始化", ""
        
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

# 可独立运行的测试函数
def main():
    """测试API服务的独立运行函数"""
    import sys
    
    # 默认图片路径，可以通过命令行参数传入
    default_image_path = "D:/project/word_learner/images/2023316133529_4801.jpg"
    image_path = sys.argv[1] if len(sys.argv) > 1 else default_image_path
    
    # 检查文件是否存在
    if not os.path.exists(image_path):
        print(f"错误: 图片文件 '{image_path}' 不存在")
        print(f"请确保文件路径正确，或指定其他图片路径: python api_service.py <图片路径>")
        return
    
    print(f"使用图片: {image_path}")
    
    # 初始化API服务
    api_service = APIService()
    
    # 测试图片识别
    print("=== 测试图片文字识别 ===")
    result = api_service.recognize_text(image_path)
    
    # 打印完整的返回结果
    print("\n=== 识别结果 ===")
    print(f"成功: {result[0]}")
    print(f"消息: {result[1]}")
    print(f"单词: {result[2]}")
    print(f"位置: {result[3]}")
    if len(result) > 4:
        print(f"句子: {result[4]}")
    
    # 如果有识别出单词，测试单词详情查询
    if result[0] and result[2]:
        first_word = result[2][0]
        print(f"\n=== 测试单词详情查询: '{first_word}' ===")
        detail_result = api_service.query_word_details(first_word)
        
        print("\n=== 单词详情 ===")
        print(f"成功: {detail_result[0]}")
        print(f"消息: {detail_result[1]}")
        print(f"数据: {detail_result[2]}")

# 当直接运行此文件时执行main函数
if __name__ == "__main__":
    main()