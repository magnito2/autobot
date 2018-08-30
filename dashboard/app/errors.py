from flask import render_template, jsonify, request
from dashboard.app import app, db


@app.errorhandler(404)
def not_found_error(error):
    if request.content_type == 'application/json':
        return jsonify(
            {'error': True, 'msg': 'API endpoint {!r} does not exist on this server'.format(request.path)}), error.code
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if request.content_type == 'application/json':
        return jsonify(
            {'error': True, 'msg': 'Internal server error'}), error.code
    return render_template('errors/500.html'), 500

@app.errorhandler(400)
def internal_error(error):
    db.session.rollback()
    if request.content_type == 'application/json':
        return jsonify(
            {'error': True, 'msg': f'Error processing request, {error}'}), error.code
    return jsonify({'error': True, "msg": str(error), "content-type" : request.content_type }), 400