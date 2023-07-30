import os

SECRET_KEY='uestcwxy666chong'
# 数据库配置信息
HOSTNAME = "127.0.0.1"
PORT = 3306
USERNAME = "yourusername"
PASSWORD ='yourpassword'
DATABASE = "blog"
DB_URI=f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4"
SQLALCHEMY_DATABASE_URI=DB_URI

# 项目路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 静态文件夹的路径
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
# 头像的上传目录
UPLOAD_ICON_DIR = STATIC_DIR+'/upload/icon'
# 相册的上传目录
UPLOAD_PHOTO_DIR = STATIC_DIR+'/upload/photo'
