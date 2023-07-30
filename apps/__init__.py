from flask import Flask

from apps.article.view import article_bp
from apps.user.view import user_bp
from exts import db, bootstrap, cache
import config

cache_config={
    'CACHE_TYPE':'redis',
    'CACHE_REDIS_HOST': '127.0.0.1',
    'CACHE_REDIS_PORT': 6379
}

def create_app():
    app=Flask(__name__,template_folder='../templates',static_folder='../static')
    app.config.from_object(config)
    db.init_app(app)
    bootstrap.init_app(app=app)

    # 初始化缓存文件
    cache.init_app(app=app,config=cache_config)

    # 注册蓝图
    app.register_blueprint(user_bp)
    app.register_blueprint(article_bp)
    return app