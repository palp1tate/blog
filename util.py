import random

from qiniu import Auth, put_file, etag, put_data
import qiniu.config
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

