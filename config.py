import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'chinese_app.db')
    # SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:rootroot@localhost/chinese'
    # SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:rootroot@host.docker.internal/chinese'
    SQLALCHEMY_DATABASE_URI = 'postgresql://{username}:{password}@{host}/{database_name}'.format(
        username=os.environ.get('USER'),
        password=os.environ.get('PASSWORD'),
        host='amvera-hahshkj2wkj-cnpg-chinese-flask-db-rw',
        database_name=os.environ.get('DBNAME')
    )
    TIMEZONE = 'UTC'
