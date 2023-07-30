from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_caching  import Cache

bootstrap=Bootstrap()
db=SQLAlchemy()
cache=Cache()