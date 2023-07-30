from flask import g

from apps import create_app
from flask_migrate import Migrate
from apps.user.models import *
from apps.article.models import *


app=create_app()
migrate=Migrate(app=app,db=db)



if __name__ == '__main__':
    app.run(host='0.0.0.0')
