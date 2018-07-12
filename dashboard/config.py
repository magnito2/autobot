import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = 'krb2wSPWmW8c1R-82DkF7A'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = "autobotcloudabc@gmail.com"
    MAIL_PASSWORD = "kesh2828"


    SECURITY_PASSWORD_SALT = "$2b$12$UoI9MPk8Z5C54aliCZxTyu"

    RECAPTCHA_PUBLIC_KEY = "6LdQemAUAAAAAMHl64OR_uzU8Cde9l_iIO8mzjFi"
    RECAPTCHA_PRIVATE_KEY = "6LdQemAUAAAAAPhsgYHuqYC5mvR0CzqfN502RuFF"

    ADMINS = ['autobotcloudabc@gmail.com']
    DEBUG = True

    HMAC_KEY = "Gmc8gWKlZGaxipc4lww12g"

    COINSPAYMENT_PUBLIC_KEY = "8e1f09d7c218d8a8c47ffc90fbca64765f2c1c7fe539e21a9d66009e76387df2"
    COINSPAYMENT_PRIVATE_KEY = "d5Db3c99b69a2f916DBF0782D9331356b8d067848b787734f7BA51A4Ce32Bc6a"
    COINS_PAYMENT_AMOUNT = 0.01

    STATIC_FOLDER = basedir + "/static"
    CONFIG_INI_FILE = basedir + "/configs/config.ini"

    ITEMS_PER_PAGE = 10 #used by pagination