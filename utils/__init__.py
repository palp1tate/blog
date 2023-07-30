import random

from flask import session
from qiniu import BucketManager
from qiniu import Auth, put_file, etag, put_data
import qiniu.config

from apps.article.models import ArticleType
from apps.user.models import User


def upload_qiniu(filestorage):
    # 需要填写你的 Access Key 和 Secret Key
    access_key = 'example'
    secret_key = 'example'

    # 构建鉴权对象
    q = Auth(access_key, secret_key)

    # 要上传的空间
    bucket_name = 'example'

    # 上传后保存的文件名
    filename=filestorage.filename
    ran=random.randint(1,100000)
    suffix=filename.rsplit('.')[-1]
    key = filename.rsplit('.')[0]+'_'+str(ran)+suffix

    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, key, 3600)

    ret, info = put_data(token, key, filestorage.read())
    return ret,info

def delete_qiniu(filename):
    access_key = 'example'
    secret_key = 'example'
    # 初始化Auth状态
    q = Auth(access_key, secret_key)
    # 初始化BucketManager
    bucket = BucketManager(q)

    # 你要测试的空间， 并且这个key在你空间中存在
    bucket_name = 'example'
    key = filename
    # 删除bucket_name 中的文件 key
    ret, info = bucket.delete(bucket_name, key)
    return info

def user_type():
    # 获取文章分类
    types = ArticleType.query.all()
    # 登录用户
    user = None
    user_id = session.get('uid', None)
    if user_id:
        user = User.query.get(user_id)
    return user, types