from time import sleep

import config
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from apps.article.models import ArticleType, Article
from apps.user.smssend import SmsSendAPIDemo
from exts import db, cache
from apps.user.models import User, Photo, AboutMe, MessageBoard
from utils import upload_qiniu, delete_qiniu, user_type

user_bp=Blueprint('user',__name__,url_prefix='/user')

required_login_list = ['/user/center',
                        '/user/change',
                        '/article/publish',
                        '/user/upload_photo',
                        '/user/photo_del',
                        '/article/add_comment',
                        '/user/aboutme',
                        '/user/showabout']


# @user_bp.before_app_first_request
# def first_request():
#     print('before_app_first_request')

# ****重点*****
@user_bp.before_app_request
def before_request():
    types = ArticleType.query.all()
    g.types=types
    if request.path in required_login_list:
        uid = session.get('uid')
        if not uid:
            return redirect(url_for('user.login'))
        else:
            user = User.query.get(uid)
            # g对象，本次请求的对象,给g对象增加user属性
            g.user = user

# 首页
@user_bp.route('/')
# @cache.cached(timeout=60)
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
    return render_template('user/index.html', **params)



# 用户注册
@user_bp.route('/register', methods=['GET', 'POST'])
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
            return redirect(url_for('user.login'))
        else:
            return redirect(url_for('user.register'))
    return render_template('user/register.html')


# 手机号码验证
@user_bp.route('/checkphone', methods=['GET', 'POST'])
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
@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        f=request.args.get('f')
        if f=='1':
            username = request.form.get('username')
            password = request.form.get('password')
            users = User.query.filter(User.username == username).all()

            for user in users:
                # 如果flag=True表示匹配，否则密码不匹配
                flag = check_password_hash(user.password, password)
                if flag:
                    # 1.cookie实现机制
                    # response = redirect(url_for('user.index'))
                    # response.set_cookie('uid', str(user.id), max_age=3600)
                    # return response
                #2.session机制，session当成字典使用
                    session['uid']=user.id
                    return redirect(url_for('user.index'))
            else:
                return render_template('user/login.html', msg='用户名或者密码有误')

        elif f == '2':  # 手机号码与验证码
            phone = request.form.get('phone')
            code = request.form.get('code')
            # 先验证验证码
            valid_code = session.get(phone)
            print('valid_code:' + str(valid_code))
            if code == valid_code:
                # 查询数据库
                user = User.query.filter(User.phone == phone).first()

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
@user_bp.route('/sendMsg')
def send_message():
    phone = request.args.get('phone')
    # 补充验证手机号码是否注册，去数据库查询

    SECRET_ID = "bf1c975510263973590da6ad72396f8b"  # 产品密钥ID，产品标识
    SECRET_KEY = "f5dba1b718fe80dcd8a32790a085e7e0"  # 产品私有密钥，服务端生成签名信息使用，请严格保管，避免泄露
    BUSINESS_ID = "efe6943a157c4663a7a05542c3cba1ee"  # 业务ID，易盾根据产品业务特点分配
    api = SmsSendAPIDemo(SECRET_ID, SECRET_KEY, BUSINESS_ID)
    params = {
        "mobile": phone,
        "templateId": "10084",
        "paramType": "json",
        "params": "json格式字符串"
    }
    ret = api.send(params)
    print(ret)
    session[phone]='985211'
    return jsonify(code=200, msg='短信发送成功！')
    # if ret is not None:
    #     if ret["code"] == 200:
    #         taskId = ret["result"]["taskId"]
    #         print("taskId = %s" % taskId)
    #         return jsonify(code=200, msg='短信发送成功！')
    #     else:
    #         print("ERROR: ret.code=%s,msg=%s" % (ret['code'], ret['msg']))
    #         return jsonify(code=400, msg='短信发送失败！')

# 用户中心
@user_bp.route('/center')
def user_center():
    photos=Photo.query.filter(Photo.user_id==g.user.id).all()

    return render_template('user/center.html', user=g.user,photos=photos)


# 图片的扩展名
ALLOWED_EXTENSIONS = ['jpg', 'png', 'gif', 'jpeg']

# 用户信息修改
@user_bp.route('/change', methods=['GET', 'POST'])
def user_change():
    if request.method == 'POST':
        username = request.form.get('username')
        phone = request.form.get('phone')
        email = request.form.get('email')
        # 只要有图片，获取方式必须使用request.files.get(name)
        icon = request.files.get('icon')
        # print('======>', icon)  # FileStorage
        # 属性： filename 用户获取文件的名字
        # 方法:  save(保存路径)
        icon_name = icon.filename  # 1440w.jpg
        # 扩展名
        suffix = icon_name.rsplit('.')[-1]
        if suffix in ALLOWED_EXTENSIONS:
            icon_name = secure_filename(icon_name)  # 保证文件名是符合python的命名规则
            file_path = config.UPLOAD_ICON_DIR+'/'+icon_name
            icon.save(file_path)
            # 保存成功 /ttmp/
            user = g.user
            user.username = username
            user.phone = phone
            user.email = email
            path = 'upload/icon/'
            user.icon = path+icon_name
            db.session.commit()
            return redirect(url_for('user.user_center'))
        else:
            return render_template('user/center.html', user=g.user, msg='必须是扩展名是：jpg,png,gif,jpeg格式')

    return render_template('user/center.html', user=g.user)


@user_bp.route('/logout')
def logout():
    referer = request.headers.get('Referer', None)
    if referer:
        response = redirect(referer)
    else:
        response = redirect(url_for('user.index'))
    # 通过response对象的delete_cookie(key),key就是要删除的cookie的key
    # response.delete_cookie('uid')
    # del session['uid']
    session.clear()
    return response

# 上传照片
@user_bp.route('/upload_photo', methods=['GET', 'POST'])
def upload_photo():
    referer = request.headers.get('Referer', None)
    # 获取上传的内容
    photo = request.files.get('photo',None)  # FileStorage
    if len(photo.filename)!=0:
        # photo.filename,photo.save(path)
        # 工具模块中封装方法
        ret, info = upload_qiniu(photo)
        if info.status_code == 200:
            photo = Photo()
            photo.photo_name = ret['key']
            photo.user_id = g.user.id
            db.session.add(photo)
            db.session.commit()
            return redirect(url_for('user.user_center'))
        else:
            return render_template('500.html', err_msg='上传图片失败！', referer=referer)
    else:
        return render_template('500.html', err_msg='上传图片失败！', referer=referer)


# 我的相册
@user_bp.route('/myphoto')
def myphoto():
    page = int(request.args.get('page', 1))
    # 分页操作
    photos = Photo.query.paginate(page=page, per_page=3)
    user_id = session.get('uid',None)
    user = None
    if user_id:
        user = User.query.get(user_id)
    return render_template('user/myphoto.html', photos=photos, user=user)

# 删除相册图片
@user_bp.route('/photo_del')
def photo_del():
    referer = request.headers.get('Referer', None)
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
        return render_template('500.html', err_msg='删除相册图片失败！',referer=referer)

# 关于用户介绍添加
@user_bp.route('/aboutme', methods=['GET', 'POST'])
def about_me():
    content = request.form.get('about')
    # 添加信息
    if not AboutMe.query.filter(AboutMe.user_id == g.user.id).first():
        aboutme = AboutMe()
        aboutme.content = content.encode('utf-8')
        aboutme.user_id = g.user.id
        db.session.add(aboutme)
        db.session.commit()
    else:
        aboutme=AboutMe.query.filter(AboutMe.user_id == g.user.id).first()
        aboutme.content = content.encode('utf-8')
        db.session.commit()
    return render_template('user/aboutme.html', user=g.user)

# 展示关于我
@user_bp.route('/showabout')
def show_about():
    return render_template('user/aboutme.html', user=g.user)

# 留言板
@user_bp.route('/board', methods=['GET', 'POST'])
def show_board():
    # 获取登录用户信息
    referer = request.headers.get('Referer', None)
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
        # 添加留言
        msg_board = MessageBoard()
        msg_board.content = content
        if uid:
            msg_board.user_id = uid
        db.session.add(msg_board)
        db.session.commit()
        return redirect(url_for('user.show_board'))
    return render_template('user/board.html', user=user, boards=boards,referer=referer)

# 留言删除
@user_bp.route('/board_del')
def delete_board():
    bid = request.args.get('bid')
    if bid:
        msgboard = MessageBoard.query.get(bid)
        db.session.delete(msgboard)
        db.session.commit()
        return redirect(url_for('user.user_center'))