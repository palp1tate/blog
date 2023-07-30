from flask import Blueprint, render_template, request, redirect, url_for, g, jsonify, session

from apps.article.models import Article, ArticleType, Comment
from apps.user.models import User
from exts import db
from utils import user_type

article_bp=Blueprint('article',__name__,url_prefix='/article')

@article_bp.app_template_filter('cdecode')
def content_decode(content):
    content = content.decode('utf-8')
    return content

# 发表文章
@article_bp.route('/publish', methods=['POST', 'GET'])
def publish_article():
    if request.method == 'POST':
        title = request.form.get('title')
        type_id = request.form.get('type')
        content = request.form.get('content')
        # 添加文章
        article = Article()
        article.title = title
        article.type_id = type_id
        article.content = content.encode('utf-8')
        article.user_id = g.user.id
        db.session.add(article)
        db.session.commit()
        return redirect(url_for('user.index'))

# 文章详情
@article_bp.route('/detail')
def article_detail():
    referer = request.headers.get('Referer', None)
    # 获取文章对象通过id
    article_id = request.args.get('aid')
    article = Article.query.get(article_id)
    # 获取文章分类
    types=g.types
    # 登录用户
    user = None
    user_id = session.get('uid', None)
    if user_id:
        user = User.query.get(user_id)

    # 单独查询评论
    print(referer)
    if request.args.get('page',1)=='None':
        return redirect(referer)
    page = int(request.args.get('page', 1))
    comments = Comment.query.filter(Comment.article_id == article_id)\
        .order_by(-Comment.cdatetime)\
        .paginate(page=page, per_page=5)
    return render_template('article/detail.html', article=article,user=user, article_id=article_id,comments=comments)

# 点赞
@article_bp.route('/love')
def article_love():
    article_id = request.args.get('aid')
    tag = request.args.get('tag')
    article = Article.query.get(article_id)
    if tag == '1':
        article.love_num -= 1
    else:
        article.love_num += 1
    db.session.commit()
    return jsonify(num=article.love_num)

# 发表文章评论
@article_bp.route('/add_comment', methods=['GET', 'POST'])
def article_comment():
    if request.method == 'POST':
        comment_content = request.form.get('comment')
        user_id = g.user.id
        article_id = request.form.get('aid')
        # 评论模型
        comment = Comment()
        comment.comment = comment_content
        comment.user_id = user_id
        comment.article_id = article_id
        db.session.add(comment)
        db.session.commit()

        return redirect(url_for('article.article_detail') + "?aid=" + article_id)
    return redirect(url_for('user.index'))

# 文章分类检索
@article_bp.route('/type_search')
def type_search():
    # 获取用户和文章类型给导航使用
    user, types = user_type()

    # tid的获取
    tid = request.args.get('tid', 1)
    page = int(request.args.get('page', 1))

    # 分页器？？？？
    # pagination对象
    articles = Article.query.filter(Article.type_id == tid ).order_by(-Article.pdatetime).paginate(page=page, per_page=3)

    params = {
        'user': user,
        'types': types,
        'articles': articles,
        'tid': tid,
    }

    return render_template('article/article_type.html', **params)
