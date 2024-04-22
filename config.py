import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'chinese_app.db')
    SQLALCHEMY_DATABASE_URI = 'mysql://root:rootroot@localhost/chinese'