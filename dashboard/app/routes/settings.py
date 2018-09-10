import configparser
from dashboard.app.forms import SettingsForm
from dashboard.app import app
from dashboard.app.authorizer import role_required
from flask import render_template, request, jsonify
from . import settings_bp
from dashboard.app.signals import config_changed, confirm_change_config, confirmed_do_change_settings, trade_manually

@settings_bp.route('/',  methods=['GET', 'POST'])
@role_required('Admin')
def settings():
    form = SettingsForm()
    config = configparser.ConfigParser()
    if form.validate_on_submit():
        symbol = form.symbol.data
        time_frame = form.time_frame.data
        brick_size = form.brick_size.data
        #sma = form.sma.data
        ztl_res = form.ztl_resolution.data
        config.read(app.config['CONFIG_INI_FILE'])
        params = {
            "symbol": symbol,
            "time_frame": time_frame,
            "brick_size": brick_size,
            #"sma": sma,
            "ztl_resolution" : ztl_res,
            "old_symbol": config['default']['symbol'],
            "indicator" : "ZTL"
        }
        if config['default']['symbol'] and config['default']['symbol'] != symbol:
            #emit confirm symbol changed
            confirm_change_config.send("settings", params=params)
        else:
            old_configs = config['default']
            if old_configs['time_frame'] != time_frame or old_configs['brick_size'] != brick_size or old_configs['ztl_resolution'] != ztl_res:
                confirmed_do_change_settings.send(params)
                config_changed.send("settings")
    config.read(app.config['CONFIG_INI_FILE'])
    form.brick_size.data = config['default']['brick_size']
    form.time_frame.data = config['default']['time_frame']
    form.symbol.data = config['default']['symbol']
    #form.sma.data = config['default']['sma']
    form.ztl_resolution.data = config['default']['ztl_resolution']
    if request.is_json:
        return jsonify({
            "symbol" : form.symbol.data,
            "brick_size" : form.brick_size.data,
            #"sma" : form.sma.data,
            "time_frame" : form.time_frame.data,
            "ztl_resolution" : form.ztl_resolution.data,
            "errors" : form.errors
        })
    return render_template('settings/settings.html', form=form)


@settings_bp.route("/manual-trade", methods = ['POST'])
#@role_required('Admin')
def do_manual_trade():
    content = request.json
    if 'action' in content:
        action = content['action']
        if action in ['BUY','SELL']:
            trade_manually.send(action)
            return jsonify({'action' : action, 'success' : True})
    return jsonify({'success' : False}), 404