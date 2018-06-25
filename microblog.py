from dashboard.app import app, db
from dashboard.app.models import User, Bot, Role


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Bot': Bot, 'Role':Role}