from flask import Flask, render_template

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():

    return render_template('dashboard.html')

@app.route("/chart")
def chart():
    return render_template('chart.html')

@app.route("/binance")
def binance():
    return render_template('binance.html')

@app.route("/settings")
def settings():
    return render_template('settings.html')

@app.route("/logs")
def logs():
    return render_template('logs.html')

@app.route("/account")
def account():
    return render_template('account.html')

if __name__ == '__main__':
    app.run(debug=True)
