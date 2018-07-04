from dashboard.app import app, db
from dashboard.app.models import User, Bot, Role, Payment


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Bot': Bot, 'Role':Role, 'Payment':Payment}


if __name__ == "__main__":
    app.run()