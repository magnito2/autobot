from dashboard.app import app, db, socketio
from dashboard.app.models import User, Bot, Role, Payment, Log, Feedback


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Bot': Bot, 'Role':Role, 'Payment':Payment, 'Log': Log, 'Feedback': Feedback}


if __name__ == "__main__":
    socketio.run(app)