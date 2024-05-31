import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'chinese_app.db')
    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{os.environ['MYSQL_USER']}:{os.environ['MYSQL_PASSWORD']}@amvera-hahshkj2wkj-run-chinese-flask:80/chinese"
    # SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:rootroot@host.docker.internal/chinese'
    TIMEZONE = 'UTC'
