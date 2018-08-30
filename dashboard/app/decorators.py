from threading import Thread
from hashlib import md5
from sqlalchemy import desc, or_
from dashboard.app import app
from flask import abort

def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper

def gravitate(email, size):
    digest = md5(email.lower().encode('utf-8')).hexdigest()
    return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
        digest, size)

def get_paginated_list(klass, start, limit):
    # check if page exists
    def get_paginated_list(klass, url, start, limit):
        # check if page exists
        results = klass.query.all()
        count = len(results)
        if (count < start):
            abort(404)
        # make response
        obj = {}
        obj['start'] = start
        obj['limit'] = limit
        obj['count'] = count
        # make URLs
        # make previous url
        if start == 1:
            obj['previous'] = ''
        else:
            start_copy = max(1, start - limit)
            limit_copy = start - 1
            obj['previous'] = url + '?start=%d&limit=%d' % (start_copy, limit_copy)
        # make next url
        if start + limit > count:
            obj['next'] = ''
        else:
            start_copy = start + limit
            obj['next'] = url + '?start=%d&limit=%d' % (start_copy, limit)
        # finally extract result according to bounds
        obj['results'] = results[(start - 1):(start - 1 + limit)]
        return obj

def my_get_paginated_list(klass, page=1, search_word = None):
    # check if page exists
    if not search_word:
        results = klass.query.order_by(desc(klass.created)).paginate(page, app.config['ITEMS_PER_PAGE'], False)
    else:
        results = klass.query.filter(or_((prop.like(f'%{search_word}%')) for prop in klass.searchable_fields()))\
        .order_by(desc(klass.created)).paginate(page, app.config['ITEMS_PER_PAGE'], False)
    res =  _from_obj_paginated_list(results, page)
    res['search_word'] = search_word
    return res

def _from_obj_paginated_list(paginate_obj, page):
    obj = {}
    results = paginate_obj
    if not results:
        obj["error"] = {"msg": "page not found", "code": 404}
    # make response
    obj['pages'] = [page for page in results.iter_pages()]
    obj['results'] = [result.serialize for result in results.items]
    obj['page'] = page
    return obj