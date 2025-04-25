import os
import time
from PIL import Image

class ImageManager:
    """图片管理器"""
    
    def __init__(self, image_dir="images"):
        self.image_dir = image_dir
        
        # 确保图片目录存在
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)
    
    def save_image(self, img, prefix="img"):
        """保存图片并返回路径"""
        if not img:
            return None
        
        # 生成文件名
        timestamp = int(time.time())
        filename = f"{prefix}_{timestamp}.jpg"
        filepath = os.path.join(self.image_dir, filename)
        
        # 保存图片
        try:
            img.save(filepath, "JPEG")
            return filepath
        except Exception as e:
            print(f"保存图片失败: {str(e)}")
            return None
    
    def load_image(self, image_path):
        """加载图片"""
        try:
            if os.path.exists(image_path):
                return Image.open(image_path)
            return None
        except Exception as e:
            print(f"加载图片失败: {str(e)}")
            return None