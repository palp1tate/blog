import time

import os

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from apps.article.models import Article_type, Article
from apps.user.models import User, Photo, AboutMe, MessageBoard
from apps.user.smssend import SmsSendAPIDemo
from apps.utils.util import upload_qiniu, delete_qiniu, user_type, send_duanxin
from exts import db, cache
from settings import Config

user_bp1 = Blueprint('user', __name__, url_prefix='/user')

required_login_list = ['/user/center',
                       '/user/change',
                       '/article/publish',
                       '/user/upload_photo',
                       '/user/photo_del',
                       '/article/add_comment',
                       '/user/aboutme',
                       '/user/showabout']


@user_bp1.before_app_first_request
def first_request():
    print('before_app_first_request')


# ****重点*****
@user_bp1.before_app_request
def before_request1():
    print('before_request1before_request1', request.path)
    if request.path in required_login_list:
        id = session.get('uid')
        if not id:
            return render_template('user/login.html')
        else:
            user = User.query.get(id)
            # g对象，本次请求的对象
            g.user = user


@user_bp1.after_app_request
def after_request_test(response):
    response.set_cookie('a', 'bbbb', max_age=19)
    print('after_request_test')
    return response


@user_bp1.teardown_app_request
def teardown_request_test(response):
    print('teardown_request_test')
    return response


# 自定义过滤器

@user_bp1.app_template_filter('decodetest')
def content_decode(content):
    content = content.decode('utf-8')
    print('-------------->content', )
    content = content[:100]
    return content


@user_bp1.app_template_filter('cdecode1')
def content_decode1(content):
    content = content.decode('utf-8')
    return content


# 首页
@user_bp1.route('/')
@cache.cached(timeout=50)
def index():
    # 1。cookie获取方式
    # uid = request.cookies.get('uid', None)
    # 2。session的获取,session底层默认获取
    # 2。session的方式：uid = session.get('uid')
    user, types = user_type()
    # 接收页码数
    page = int(request.args.get('page', 1))
    # 判断是否存在检索词汇
    search = request.args.get('search', '')
    # 有检索词汇
    if search:
        # 进行检索contains
        pagination = Article.query.filter(Article.title.contains(search)).order_by(-Article.pdatetime).paginate(
            page=page, per_page=3)
    else:
        # 获取文章列表   7 6 5  |  4 3 2 | 1
        pagination = Article.query.order_by(-Article.pdatetime).paginate(page=page, per_page=3)

    params = {
        'user': user,
        'types': types,
        'pagination': pagination,
        'search': search
    }

    for i in range(10):
        time.sleep(0.5)
    return render_template('user/index.html', **params)


# 用户注册
@user_bp1.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        repassword = request.form.get('repassword')
        phone = request.form.get('phone')
        email = request.form.get('email')
        if password == repassword:
            # 注册用户
            user = User()
            user.username = username
            # 使用自带的函数实现加密：generate_password_hash
            user.password = generate_password_hash(password)
            # print(password)
            user.phone = phone
            user.email = email
            # 添加并提交
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('user.index'))
    return render_template('user/register.html')


# 手机号码验证
@user_bp1.route('/checkphone', methods=['GET', 'POST'])
def check_phone():
    phone = request.args.get('phone')
    user = User.query.filter(User.phone == phone).all()
    print(user)
    # code: 400 不能用    200 可以用
    if len(user) > 0:
        return jsonify(code=400, msg='此号码已被注册')
    else:
        return jsonify(code=200, msg='此号码可用')


# 用户登录
@user_bp1.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        f = request.args.get('f')
        if f == '1':  # 用户名或者密码
            username = request.form.get('username')
            password = request.form.get('password')
            users = User.query.filter(User.username == username).all()
            for user in users:
                # 如果flag=True表示匹配，否则密码不匹配
                flag = check_password_hash(user.password, password)
                if flag:
                    # 1。cookie实现机制
                    # response = redirect(url_for('user.index'))
                    # response.set_cookie('uid', str(user.id), max_age=1800)
                    # return response
                    # 2。session机制,session当成字典使用
                    session['uid'] = user.id
                    return redirect(url_for('user.index'))
            else:
                return render_template('user/login.html', msg='用户名或者密码有误')
        elif f == '2':  # 手机号码与验证码
            print('----->22222')
            phone = request.form.get('phone')
            code = request.form.get('code')
            # 先验证验证码
            # 从缓存中获取根据key获取value
            valid_code = cache.get(phone)
            print('valid_code:' + str(valid_code))
            if code == valid_code:
                # 查询数据库
                user = User.query.filter(User.phone == phone).first()
                print(user)
                if user:
                    # 登录成功
                    session['uid'] = user.id
                    return redirect(url_for('user.index'))
                else:
                    return render_template('user/login.html', msg='此号码未注册')
            else:
                return render_template('user/login.html', msg='验证码有误！')

    return render_template('user/login.html')


# 发送短信息
@user_bp1.route('/sendMsg')
def send_message():
    phone = request.args.get('phone')
    # 补充验证手机号码是否注册，去数据库查询
    ret, code = send_duanxin(phone)
    # 验证是否发送成功
    if ret is not None:
        if ret["code"] == 200:
            # cache.set(key,value,timeout=second)
            cache.set(phone, code, timeout=180)
            return jsonify(code=200, msg='短信发送成功！')
        else:
            print("ERROR: ret.code=%s,msg=%s" % (ret['code'], ret['msg']))
            return jsonify(code=400, msg='短信发送失败！')


# 用户退出
@user_bp1.route('/logout')
def logout():
    # 1。 cookie的方式
    # response = redirect(url_for('user.index'))
    # 通过response对象的delete_cookie(key),key就是要删除的cookie的key
    # response.delete_cookie('uid')
    # 2。session的方式
    # del session['uid']
    session.clear()
    return redirect(url_for('user.index'))


# 用户中心
@user_bp1.route('/center')
def user_center():
    types = Article_type.query.all()
    photos = Photo.query.filter(Photo.user_id == g.user.id).all()
    return render_template('user/center.html', user=g.user, types=types, photos=photos)


# 图片的扩展名
ALLOWED_EXTENSIONS = ['jpg', 'png', 'gif', 'bmp']


# 用户信息修改
@user_bp1.route('/change', methods=['GET', 'POST'])
def user_change():
    if request.method == 'POST':
        username = request.form.get('username')
        phone = request.form.get('phone')
        email = request.form.get('email')
        # 只要有文件（图片），获取方式必须使用request.files.get(name)
        icon = request.files.get('icon')
        # print('======>', icon)  # FileStorage
        # 属性： filename 用户获取文件的名字
        # 方法:  save(保存路径)
        icon_name = icon.filename  # 1440w.jpg
        suffix = icon_name.rsplit('.')[-1]
        if suffix in ALLOWED_EXTENSIONS:
            icon_name = secure_filename(icon_name)  # 保证文件名是符合python的命名规则
            file_path = os.path.join(Config.UPLOAD_ICON_DIR, icon_name)
            icon.save(file_path)
            # 保存成功
            user = g.user
            user.username = username
            user.phone = phone
            user.email = email
            path = 'upload/icon'
            user.icon = os.path.join(path, icon_name)
            db.session.commit()
            return redirect(url_for('user.user_center'))
        else:
            return render_template('user/center.html', user=g.user, msg='必须是扩展名是：jpg,png,gif,bmp格式')

        # 查询一下手机号码
        # users = User.query.all()
        # for user in users:
        #     if user.phone == phone:
        #         # 说明数据库中已经有人注册此号码
        #         return render_template('user/center.html', user=g.user,msg='此号码已被注册')
        #

    return render_template('user/center.html', user=g.user)


# 发表文章
@user_bp1.route('/article', methods=['GET', 'POST'])
def publish_article():
    if request.method == 'POST':
        title = request.form.get('title')
        type = request.form.get('type')
        content = request.form.get('content')
        print(title, type, content)

        return render_template('article/test.html', content=content)
    return '发表失败！'


# 上传照片
@user_bp1.route('/upload_photo', methods=['GET', 'POST'])
def upload_photo():
    # 获取上传的内容
    photo = request.files.get('photo')  # FileStorage
    # photo.filename,photo.save(path)
    # 工具模块中封装方法
    ret, info = upload_qiniu(photo)
    if info.status_code == 200:
        photo = Photo()
        photo.photo_name = ret['key']
        photo.user_id = g.user.id
        db.session.add(photo)
        db.session.commit()
        return '上传成功！'
    else:
        return '上传失败！'


# 删除相册图片
@user_bp1.route('/photo_del')
def photo_del():
    pid = request.args.get('pid')
    photo = Photo.query.get(pid)
    filename = photo.photo_name
    # 封装好的一个删除七牛存储文件的函数
    info = delete_qiniu(filename)
    # 判断状态码
    if info.status_code == 200:
        # 删除数据库的内容
        db.session.delete(photo)
        db.session.commit()
        return redirect(url_for('user.user_center'))
    else:

        return render_template('500.html', err_msg='删除相册图片失败！')


# 我的相册
@user_bp1.route('/myphoto')
def myphoto():
    # 如果不转成整型，默认是str类型
    page = int(request.args.get('page', 1))
    # 分页操作
    # photos是一个pagination类型
    photos = Photo.query.paginate(page=page, per_page=3)
    #
    user, types = user_type()
    return render_template('user/myphoto.html', photos=photos, user=user, types=types)


# 关于用户介绍添加
@user_bp1.route('/aboutme', methods=['GET', 'POST'])
def about_me():
    content = request.form.get('about')
    # 添加信息
    try:
        aboutme = AboutMe()
        aboutme.content = content.encode('utf-8')
        aboutme.user_id = g.user.id
        db.session.add(aboutme)
        db.session.commit()
    except Exception as err:
        return redirect(url_for('user.user_center'))
    else:
        return render_template('user/aboutme.html', user=g.user)


# 展示关于我
@user_bp1.route('/showabout')
def show_about():
    user, types = user_type()
    return render_template('user/aboutme.html', user=g.user, types=types)


# 留言板
@user_bp1.route('/board', methods=['GET', 'POST'])
def show_board():
    # 获取登录用户信息
    uid = session.get('uid', None)
    user = None
    if uid:
        user = User.query.get(uid)

    # 查询所有的留言内容
    page = int(request.args.get('page', 1))
    boards = MessageBoard.query.order_by(-MessageBoard.mdatetime).paginate(page=page, per_page=5)
    # 判断请求方式
    if request.method == 'POST':
        content = request.form.get('board')
        print('======》', content)
        # 添加留言
        msg_board = MessageBoard()
        msg_board.content = content
        if uid:
            msg_board.user_id = uid
        db.session.add(msg_board)
        db.session.commit()
        return redirect(url_for('user.show_board'))
    return render_template('user/board.html', user=user, boards=boards)


# 留言删除
@user_bp1.route('/board_del')
def delete_board():
    bid = request.args.get('bid')
    if bid:
        msgboard = MessageBoard.query.get(bid)
        db.session.delete(msgboard)
        db.session.commit()
        return redirect(url_for('user.user_center'))


@user_bp1.route('/error')
def test_error():
    # print(request.headers)
    # print(request.headers.get('Accept-Encoding'))
    referer = request.headers.get('Referer', None)
    return render_template('500.html', err_msg='有误', referer=referer)
