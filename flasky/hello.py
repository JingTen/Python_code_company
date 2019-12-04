from flask import Flask,session,redirect,url_for,flash
from flask import request
from flask import render_template
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired
import os
from flask_sqlalchemy import SQLAlchemy
import pymysql
from flask_migrate import Migrate
import hashlib



app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.debug = True

# 初始化Flask-Bootstrap
bootstrap = Bootstrap(app)

# 初始化Flask-Monment
moment = Moment(app)

# 配置MySQL数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/flask?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 创建SQLAlchemy类的实例，为模型提供一个基类以及一系列辅助类和辅助函数，可用于定义模型的结构
db = SQLAlchemy(app)

# 创建迁移仓库，初始化Flask-Migrate
migrate = Migrate(app,db)

# 定义Role和User模型
# Flask-SQLAlchemy要求每个模型都定义主键 primary_key
class Role(db.Model):
    # 类变量__tablename__，定义在数据库中使用的表名/
    # 其余的类变量都是该模型的属性，定义为db.Column类的实例
    # db.Column类构造函数的第一个参数是数据库列和模型属性的类型/
    # 其余参数指定属性的配置选项
    __tablename__ = 'roles'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64),unique=True)
    # users属性代表这个关系的面向对象视角，返回与角色相关联的用户组成的列表（MORE）
    # User表明这个关系的另一端的模型
    # backref参数向User模型中添加一个role属性，从而定义反向关系；通过User实例的这个属性可以获取对应的Role模型对象，而不用再通过role_id外键获取
    # lazy='dynamic',禁止自动执行查询
    users = db.relationship('User',backref='role',lazy='dynamic')
    # 返回一个具有可读性的字符串表示模型，供调试和测试使用
    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(64),unique=True,index=True)
    # 以role_id为外键，并与roles表中的id建立联系
    role_id = db.Column(db.Integer,db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username


@app.route('/',methods=['GET', 'POST'])
def index():
    '''
    user_agent = request.headers.get('User-Agent')
    return '<p>Your browser is %s</p>' % user_agent
    #return '<h1>Hello World</h1>'

    #name = None
    form = NameForm()
    if form.validate_on_submit():
        #name = form.name.data
        #form.name.data = ''
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed your name!')
        session['name'] = form.name.data
        return redirect(url_for('index'))
    return render_template('index.html',form=form,name=session.get('name'),current_time=datetime.utcnow())
    '''
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
        else:
            session['known'] = True
        session['name'] = form.name.data
        print(type(session['name']),session['name'])
        print(session['name'].split(","))
        for i in session['name'].split(","):
            print(i)
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('index.html',form=form,name=session.get('name'),known=session.get('known',False),current_time=datetime.utcnow())


@app.route('/user/<name>')
def user(name):
    # return '<h1>Hello,{}!</h1>'.format(name)
    return render_template('user.html',name=name)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# 添加一个shell上下文；flask shell命令自动导入这些对象，使用app.shell_context_processor装饰器把对象导入列表
@app.shell_context_processor
def make_shell_context():
    return dict(db=db,User=User,Role=Role)




class NameForm(FlaskForm):
    name = StringField('What is your name?',validators=[DataRequired()])
    submit = SubmitField('Submit')



if __name__ == '__main__':
    app.run()



