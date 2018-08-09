import configparser
from dashboard.app.forms import SettingsForm
from dashboard.app import app, config_changed
from dashboard.app.authorizer import role_required
from flask import render_template
from . import settings_bp

@settings_bp.route('/',  methods=['GET', 'POST'])
@role_required('Admin')
def settings():
    form = SettingsForm()
    config = configparser.ConfigParser()
    if form.validate_on_submit():
        symbol = form.symbol.data
        time_frame = form.time_frame.data
        brick_size = form.brick_size.data
        sma = form.sma.data
        config.read(app.config['CONFIG_INI_FILE'])
        config['default'] = {'symbol' : symbol, 'time_frame' : time_frame, 'brick_size' : brick_size, 'sma' : sma}
        with open(app.config['CONFIG_INI_FILE'], 'w') as configfile:
            config.write(configfile)
        print("emitting event config changed")
        config_changed.send('settings')

    config.read(app.config['CONFIG_INI_FILE'])
    form.brick_size.data = config['default']['brick_size']
    form.time_frame.data = config['default']['time_frame']
    form.symbol.data = config['default']['symbol']
    form.sma.data = config['default']['sma']
    return render_template('settings/settings.html', form=form)
