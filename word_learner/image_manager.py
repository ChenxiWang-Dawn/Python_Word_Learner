import os
import time
import sys
import tempfile
from PIL import Image


class ImageManager:
    """图片管理器"""

    def __init__(self, image_dir="images"):
        # 获取可写的图片目录
        self.image_dir = self.get_writable_image_dir(image_dir)

        # 确保图片目录存在
        self.ensure_image_dir_exists()

    def get_writable_image_dir(self, default_dir_name):
        """获取可写的图片目录"""
        app_name = "WordLearner"

        # 如果在打包环境中，不能使用相对路径
        if hasattr(sys, '_MEIPASS'):
            print("检测到打包环境，使用用户文档目录")

            # 优先使用用户文档目录
            try:
                # macOS: ~/Documents/WordLearner/images
                documents_dir = os.path.expanduser("~/Documents")
                if os.path.exists(documents_dir) and os.access(documents_dir, os.W_OK):
                    app_dir = os.path.join(documents_dir, app_name)
                    image_dir = os.path.join(app_dir, default_dir_name)
                    print(f"使用文档目录: {image_dir}")
                    return image_dir
            except Exception as e:
                print(f"无法使用文档目录: {e}")

            # 备选：用户主目录
            try:
                home_dir = os.path.expanduser("~")
                if os.path.exists(home_dir) and os.access(home_dir, os.W_OK):
                    app_dir = os.path.join(home_dir, app_name)
                    image_dir = os.path.join(app_dir, default_dir_name)
                    print(f"使用主目录: {image_dir}")
                    return image_dir
            except Exception as e:
                print(f"无法使用主目录: {e}")

            # 最后备选：系统临时目录
            temp_dir = tempfile.gettempdir()
            image_dir = os.path.join(temp_dir, app_name, default_dir_name)
            print(f"使用临时目录: {image_dir}")
            return image_dir

        else:
            # 开发环境，使用原来的相对路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            image_dir = os.path.join(current_dir, default_dir_name)
            print(f"开发环境，使用相对路径: {image_dir}")
            return image_dir

    def ensure_image_dir_exists(self):
        """确保图片目录存在"""
        try:
            if not os.path.exists(self.image_dir):
                os.makedirs(self.image_dir, exist_ok=True)
                print(f"已创建图片目录: {self.image_dir}")
            else:
                print(f"图片目录已存在: {self.image_dir}")

            # 检查目录是否可写
            if not os.access(self.image_dir, os.W_OK):
                print(f"警告: 图片目录不可写: {self.image_dir}")
                # 尝试使用临时目录
                temp_dir = tempfile.gettempdir()
                self.image_dir = os.path.join(temp_dir, "WordLearner_temp_images")
                os.makedirs(self.image_dir, exist_ok=True)
                print(f"改用临时目录: {self.image_dir}")

        except OSError as e:
            print(f"创建图片目录失败: {e}")
            # 使用系统临时目录作为最后的备选方案
            self.image_dir = tempfile.gettempdir()
            print(f"改用系统临时目录: {self.image_dir}")
        except Exception as e:
            print(f"设置图片目录时出现未知错误: {e}")
            self.image_dir = tempfile.gettempdir()
            print(f"改用系统临时目录: {self.image_dir}")

    def save_image(self, img, prefix="img"):
        """保存图片并返回路径"""
        if not img:
            print("错误: 没有提供图片对象")
            return None

        # 再次检查目录是否存在和可写
        if not os.path.exists(self.image_dir):
            self.ensure_image_dir_exists()

        if not os.access(self.image_dir, os.W_OK):
            print(f"错误: 图片目录不可写: {self.image_dir}")
            return None

        # 生成文件名
        timestamp = int(time.time())
        filename = f"{prefix}_{timestamp}.jpg"
        filepath = os.path.join(self.image_dir, filename)

        # 保存图片
        try:
            # 确保是PIL Image对象
            if hasattr(img, 'save'):
                img.save(filepath, "JPEG", quality=85)
                print(f"图片已保存: {filepath}")
                return filepath
            else:
                print(f"错误: 不支持的图片类型: {type(img)}")
                return None

        except Exception as e:
            print(f"保存图片失败: {str(e)}")
            # 尝试使用PNG格式
            try:
                png_filepath = filepath.replace('.jpg', '.png')
                img.save(png_filepath, "PNG")
                print(f"图片已保存为PNG格式: {png_filepath}")
                return png_filepath
            except Exception as e2:
                print(f"PNG格式保存也失败: {str(e2)}")
                return None

    def load_image(self, image_path):
        """加载图片"""
        try:
            if not image_path:
                print("错误: 图片路径为空")
                return None

            if os.path.exists(image_path):
                img = Image.open(image_path)
                print(f"图片加载成功: {image_path}")
                return img
            else:
                print(f"错误: 图片文件不存在: {image_path}")
                return None

        except Exception as e:
            print(f"加载图片失败: {str(e)}")
            return None

    def get_image_dir(self):
        """获取当前图片目录路径"""
        return self.image_dir

    def cleanup_old_images(self, days_old=7):
        """清理指定天数前的旧图片"""
        try:
            if not os.path.exists(self.image_dir):
                return

            current_time = time.time()
            cutoff_time = current_time - (days_old * 24 * 60 * 60)

            cleaned_count = 0
            for filename in os.listdir(self.image_dir):
                filepath = os.path.join(self.image_dir, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if file_time < cutoff_time:
                        try:
                            os.remove(filepath)
                            cleaned_count += 1
                        except Exception as e:
                            print(f"删除旧图片失败 {filepath}: {e}")

            if cleaned_count > 0:
                print(f"已清理 {cleaned_count} 个旧图片文件")

        except Exception as e:
            print(f"清理旧图片时出错: {e}")