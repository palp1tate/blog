# blog
a blog system with much powerful function implemented by flask

视频来源：https://www.bilibili.com/video/BV17z4y1X7UZ/?spm_id_from=333.999.0.0&vd_source=84fc27804252448ba51ef3b6abfd5d36

学习文档和源码均已上传Github。

下载：
```bash
git clone https://github.com/palp1tate/blog.git
```

配置`config.py`

```python
SECRET_KEY='uestcwxy666chong'  #该项可任意，用于加密session
# 数据库配置信息
HOSTNAME = "127.0.0.1"
PORT = 3306
USERNAME = "root"
PASSWORD ='example'
DATABASE = "blog"
DB_URI=f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4"
SQLALCHEMY_DATABASE_URI=DB_URI
```

在本地创建数据库`blog`，然后在项目根目录运行：
```bash
flask db init
flask db migrate
flask db upgrade
```

另外关于云存储（用的是七牛云），发送手机短信（网易易盾）的部分也需要配置，当然你也可以更换其他运营商。云存储相关配置在`utils`包下的`__init__.py`里，发短信相关配置在`user`目录下的`smssend.py`和`view.py`中。这两部分配置可能需要多花些时间。

在终端运行`python app.py`，最后访问网址：<http://127.0.0.1:5000/user> 即可

部分页面如下：

![image](https://github.com/palp1tate/blog/assets/120303802/84e3a54f-2d52-4541-b83b-cac04f4788b0)

![image](https://github.com/palp1tate/blog/assets/120303802/225f57d8-fd82-4992-8812-b20297db30b8)

![image](https://github.com/palp1tate/blog/assets/120303802/b22767c7-c7ea-493a-b219-472eea2e78ce)

![image](https://github.com/palp1tate/blog/assets/120303802/f91010c2-fc7c-4c06-815d-e11c92277287)

![image](https://github.com/palp1tate/blog/assets/120303802/cf649c43-a841-4989-92b9-05f5e839832b)

![image](https://github.com/palp1tate/blog/assets/120303802/88d10e52-a813-43ab-b0d0-4c946212e6e0)






