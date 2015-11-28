# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2015 BarraDev Consulting (<http://www.barradev.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

#
##############################################################################
# import werkzeug.contrib.sessions

import redis
from openerp import tools
from openerp.http import OpenERPSession, Root
from openerp.tools.func import lazy_property
from werkzeug.contrib.sessions import SessionStore

try:
    _redis_import = True
    import redis
except:
    _redis_import = False

try:
    import cPickle as pickle
except:
    import pickle

import logging

_logger = logging.getLogger(__name__)

# session_store_orig = http.session_store


# class Root(http.Root):
#     """Overrides Oddo Root class."""
#     def redis_config(self):

#         return False

#     @lazy_property
#     def session_store(self):
#         """Override function session_store and fallback to Odoo default"""
#         _logger.debug('HTTP sessions stored in: %s')
#         _logger.info('session store redis')
#         if self.redis_config:
#             return RedisSession
#         else:
#             return super(Root, self).session_store()

#         assert True

#     def session_store_redis(self):
#         assert True
# root_session_store_org = Root.session_store
redis_host = tools.config.get('redis_host', 'localhost')
redis_port = int(tools.config.get('redis_port', 6379))
redis_dbindex = int(tools.config.get('redis_dbindex', 1))
redis_password = tools.config.get('redis_pass', None)

class RedisSessionStore(SessionStore):
    def __init__(self, expire=1800, key_prefix='',
                 session_class=OpenERPSession,
                 redis_conn=None):
        super(SessionStore, self).__init__
        if redis_conn is None:
            self.redis_conn = redis.Redis(redis_host,
                                          redis_port,
                                          redis_dbindex,
                                          password=redis_password)
        self.redis = redis_conn
        # self.path = session_path()
        # self.path = '/'
        self.session_class = session_class
        self.expire = expire
        self.key_prefix = key_prefix

    def save(self, session):
        key = self._get_session_key(session.sid)
        data = pickle.dumps(dict(session))
        # _logger.info("Save: %s, %s", (key, data))
        self.redis.setex(key, data, self.expire)

    def delete(self, session):
        key = self._get_session_key(session.sid)
        self.redis.delete(key)

    def _get_session_key(self, sid):
        # _logger.info("SessionId: %s", sid)
        key = self.key_prefix + sid
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        return key

    def get(self, sid):
        key = self._get_session_key(sid)
        data = self.redis.get(key)
        # _logger.info("Get: %s, %s", (key, data))
        if data:
            self.redis.setex(key, data, self.expire)
            data = pickle.loads(data)
        else:
            data = {}
        return self.session_class(data, sid, False)


@lazy_property
def session_store(self):
    _logger.info('Starting HTTP session store with Redis')
    if not _redis_import:
        return self.org_session_store
    try:
        redis_conn = redis.Redis(redis_host,
                                 redis_port,
                                 redis_dbindex,
                                 password=redis_password)
        redis_conn.get('anything')
    except:
        _logger.info('Redis fail, using FileSystemSessionStore for session')
        return self.org_session_store

    return RedisSessionStore(session_class=OpenERPSession,
                             redis_conn=redis_conn)

Root.org_session_store = Root.session_store
Root.session_store = session_store
