from flask import Flask

from apps.article.view import article_bp
from apps.article.views import article_bp1
from apps.user.view import user_bp
from apps.user.views import user_bp1
from exts import db, bootstrap, cache
from settings import DevelopmentConfig

config = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': '127.0.0.1',
    'CACHE_REDIS_PORT': 6379
}


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(DevelopmentConfig)
    # 初始化db
    db.init_app(app=app)
    # 初始化bootstrap
    bootstrap.init_app(app=app)
    # 初始化缓存文件
    cache.init_app(app=app, config=config)
    # 注册蓝图
    app.register_blueprint(user_bp1)
    app.register_blueprint(article_bp1)
    # print(app.url_map)
    return app
