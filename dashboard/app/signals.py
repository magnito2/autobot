from dashboard.app import app_signals

config_changed = app_signals.signal('config-changed')
new_bot_created = app_signals.signal('new-bot-created')
get_bot_status = app_signals.signal('get-bot-status')
destroy_bot = app_signals.signal('stop-bot')
confirm_change_config = app_signals.signal('confirm-change-config')
confirmed_do_change_settings = app_signals.signal('confirmed-do-change-settings')

new_user_registered = app_signals.signal('new-user-created')
new_payment_made = app_signals.signal('new-payment-made')

bot_error_log = app_signals.signal('bot-raised-error')

request_renko_bricks = app_signals.signal('request-renko-bricks')