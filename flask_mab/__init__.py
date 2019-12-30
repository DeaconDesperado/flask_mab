"""
    flask_mab
    ~~~~~~~~~

    This module implements all the extension logic for
    Multi-armed bandit experiments on Flask apps.

    :copyright: (c) 2013 by `Mark Grey <http://www.deacondesperado.com>`_.

    :license: BSD, see LICENSE for more details.
"""

from flask import current_app, g, request
import json
import flask_mab.storage
from flask_mab.mab import Mab
import types
from collections import namedtuple
from flask import _request_ctx_stack
from functools import wraps

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

__version__ = "2.0.1"

def choose_arm(bandit):
    """Route decorator for registering an impression conveinently

    :param bandit: The bandit/experiment to register for
    :type bandit: string
    """
    def decorator(func):
        #runs @ service init
        if not hasattr(func, 'bandits'):
            func.bandits = []
        func.bandits.append(bandit)

        @wraps(func)
        def wrapper(*args, **kwargs):
            #runs at endpoint hit
            add_args = []
            for bandit in func.bandits:
                #Fetch from request first here?
                arm_id, arm_value = suggest_arm_for(bandit)
                add_args.append((bandit, arm_value))
            kwargs.update(add_args)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def reward_endpt(bandit, reward_val=1):
    """Route decorator for rewards.

    :param bandit: The bandit/experiment to register rewards
                   for using arm found in cookie.
    :type bandit: string
    :param reward: The amount of reward this endpoint should
                   give its winning arm
    :type reward: float
    """
    def decorator(func):
        if not hasattr(func, 'rewards'):
            func.rewards = []
        func.rewards.append((bandit, reward_val))

        @wraps(func)
        def wrapper(*args, **kwargs):
            for bandit, reward_amt in func.rewards:
                if bandit in request.bandits.keys():
                    request.bandits_reward.add((bandit, request.bandits[bandit], reward_amt))
            return func(*args, **kwargs)
        return wrapper
    return decorator


class BanditMiddleware(object):
    """The main flask extension.
    Sets up all the necessary tracking for the bandit experiments
    """

    def __init__(self, app=None):
        """Attach MAB logic to a Flask application

        :param app: An optional Flask application
        """
        if app is not None:
            self.init_app(app)

    def _register_storage(self, app):
        storage_engine = getattr(
                flask_mab.storage,
                app.config.get('MAB_STORAGE_ENGINE', 'BanditStorage'))
        storage_opts = app.config.get('MAB_STORAGE_OPTS', tuple())
        storage_backend = storage_engine(*storage_opts)
        app.extensions['mab'].bandit_storage = storage_backend

    def init_app(self, app):
        """Attach Multi Armed Bandit to application and configure

        :param app: A flask application instance
        """
        app.config.setdefault('MAB_COOKIE_NAME', 'MAB')
        app.config.setdefault('MAB_COOKIE_PATH', '/')
        app.config.setdefault('MAB_COOKIE_TTL', None)
        app.config.setdefault('MAB_DEBUG_HEADERS', True)
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['mab'] = Mab(app)
        self._register_storage(app)
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

        app.extensions['mab'].bandits = {}
        app.extensions['mab'].reward_endpts = []
        app.extensions['mab'].pull_endpts = []

        app.extensions['mab'].debug_headers = app.config.get('MAB_DEBUG_HEADERS', True)
        app.extensions['mab'].cookie_name = app.config.get('MAB_COOKIE_NAME', "MAB")
        self._init_detection(app)

    def teardown(self, *args, **kwargs):
        """Stub for old flask versions
        """
        pass

    def _init_detection(self, app):
        """
        Attaches all request before/after handlers for bandits.

        Nested functions are as follows

        * detect_last_bandits: Loads any arms already assigned to this user
                               from the cookie.
        * persist_bandits:     Saves bandits down to storage engine at the end
                               of the request
        * remember_bandit_arms: Sets the cookie for all requests that pulled an arm
        * send_debug_header: Attaches a header for the MAB to the HTTP response for easier debugging
        """
        @app.before_request
        def detect_last_bandits():
            bandits = request.cookies.get(app.extensions['mab'].cookie_name)
            request.bandits_save = False
            request.bandits_reward = set()
            if bandits:
                request.bandits = json.loads(bandits)
            else:
                request.bandits = {}

        @app.after_request
        def persist_bandits(response):
            app.extensions['mab'].bandit_storage.save(app.extensions['mab'].bandits)
            return response

        @app.after_request
        def remember_bandit_arms(response):
            if request.bandits_save:
                for bandit_id,arm in request.bandits.items():
                    #hook event for saving an impression here
                    app.extensions['mab'].bandits[bandit_id].pull_arm(arm)

            for bandit_id, arm, reward_amt in request.bandits_reward:
                try:
                    app.extensions['mab'].bandits[bandit_id].reward_arm(arm, reward_amt)
                    #hook event for saving a reward line here
                except KeyError:
                    raise MABConfigException("Bandit %s not found" % bandit_id)

            response.set_cookie(
                    app.extensions['mab'].cookie_name,
                    json.dumps(request.bandits),
                    secure=True, httponly=True, samesite='Lax')
            return response

        @app.after_request
        def send_debug_header(response):
            if app.extensions['mab'].debug_headers and request.bandits_save:
                response.headers['X-MAB-Debug'] = "STORE; "+';'.join(
                        ['%s:%s' % (key, val) for key, val in request.bandits.items()])
            elif app.extensions['mab'].debug_headers:
                response.headers['X-MAB-Debug'] = "SAVED; "+';'.join(['%s:%s' % (key, val) for key, val in request.bandits.items()])
            return response

        app.add_bandit = types.MethodType(add_bandit, app)


def add_bandit(app, name, bandit=None):
    """Attach a bandit for an experiment

    :param name: The name of the experiment, will be used for lookups
    :param bandit: The bandit to use for this experiment
    :type bandit: Bandit
    """
    saved_bandits = app.extensions['mab'].bandit_storage.load()
    if name in saved_bandits.keys():
        app.extensions['mab'].bandits[name] = saved_bandits[name]
    else:
        app.extensions['mab'].bandits[name] = bandit


def suggest_arm_for(key):
    """Get an experimental outcome by id.  The primary way the implementor interfaces with their
    experiments.

    Suggests arms if not in cookie, using cookie val if present

    :param key: The bandit/experiment to get a suggested arm for
    :type key: string
    :param also_pull: Should we register a pull/impression at the same time as suggesting
    :raises KeyError: in case requested experiment does not exist
    """
    app = current_app
    try:
        #Try to get the selected bandits from cookie
        arm = app.extensions['mab'].bandits[key][request.bandits[key]]
        return arm["id"], arm["value"]
    except (AttributeError, TypeError, KeyError) as err:
        #Assign an arm for a new client
        try:
            arm = app.extensions['mab'].bandits[key].suggest_arm()
            request.bandits[key] = arm["id"]
            request.bandits_save = True
            return arm["id"], arm["value"]
        except KeyError:
            raise MABConfigException("Bandit %s not found" % key)

class MABConfigException(Exception):
    """Raised when internal state in MAB setup is invalid"""
    pass
