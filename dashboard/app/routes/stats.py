from dashboard.app.routes import stats_bp
import requests
from flask import jsonify

@stats_bp.route("/tweeter-followers-count")
def tweeter_followers_count():
    resp = requests.get("https://cdn.syndication.twimg.com/widgets/followbutton/info.json?screen_names=autobotcloud")
    if resp.status_code == 200:
        followers_count = resp.json()[0]['followers_count']
        return jsonify(followers_count)
    return jsonify(0)