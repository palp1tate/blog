import random

from flask import session
from qiniu import Auth, put_file, etag, put_data, BucketManager
import qiniu.config

from apps.article.models import Article_type
from apps.user.models import User
from apps.user.smssend import SmsSendAPIDemo, SecretPair


def upload_qiniu(filestorage):
    # 需要填写你的 Access Key 和 Secret Key
    access_key = '1fXvG9wkbN7AgRUG6usHDcRP5Bb85apcovRAIITP'
    secret_key = 'Aqf1lPAmUG72EdZJ7PxKtWHfWDYNdUycZP1TaAIN'
    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    # 要上传的空间
    bucket_name = 'myblog202006'
    # 上传后保存的文件名
    filename = filestorage.filename
    ran = random.randint(1, 1000)
    suffix = filename.rsplit('.')[-1]
    key = filename.rsplit('.')[0] + '_' + str(ran) + '.' + suffix
    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, key, 3600)
    # 要上传文件的本地路径
    # localfile = './sync/bbb.jpg'
    # ret, info = put_file(token, key, localfile)
    ret, info = put_data(token, key, filestorage.read())
    return ret, info


def delete_qiniu(filename):
    # 需要填写你的 Access Key 和 Secret Key
    access_key = '1fXvG9wkbN7AgRUG6usHDcRP5Bb85apcovRAIITP'
    secret_key = 'Aqf1lPAmUG72EdZJ7PxKtWHfWDYNdUycZP1TaAIN'
    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    # 要上传的空间
    bucket_name = 'myblog202006'
    # 初始化BucketManager
    bucket = BucketManager(q)
    # key就是要删除的文件的名字
    key = filename
    ret, info = bucket.delete(bucket_name, key)
    return info


def user_type():
    # 获取文章分类
    types = Article_type.query.all()
    # 登录用户
    user = None
    user_id = session.get('uid', None)
    if user_id:
        user = User.query.get(user_id)
    return user, types


# 发送短信息
def send_duanxin(phone):
    SECRET_ID = "dcc535cbfaefa2a24c1e6610035b6586"  # 产品密钥ID，产品标识
    SECRET_KEY = "d28f0ec3bf468baa7a16c16c9474889e"  # 产品私有密钥，服务端生成签名信息使用，请严格保管，避免泄露
    BUSINESS_ID = "748c53c3a363412fa963ed3c1b795c65"  # 业务ID，易盾根据产品业务特点分配
    secret_pair = SecretPair(SECRET_ID, SECRET_KEY)
    api = SmsSendAPIDemo(BUSINESS_ID, secret_pair)
    # 验证码随机产生
    code = ""
    for i in range(4):
        ran = random.randint(0, 9)
        code += str(ran)

    params = {
        "mobile": phone,
        "templateId": "11732",
        "paramType": "json",
        "params": {"code": code}
    }

    ret = api.send(params)
    return ret, code
