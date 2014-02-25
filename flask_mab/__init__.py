"""
    flask_mab
    ~~~~~~~~~

    This module implements all the extension logic for Multi-armed bandit experiments on Flask apps.

    :copyright: (c) 2013 by `Mark Grey <http://www.deacondesperado.com>`_.

    :license: BSD, see LICENSE for more details.
"""

from flask import current_app,g,request
import json
import storage
import types
from bunch import Bunch
from functools import wraps

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

def after_this_request(f):
    """Uses a list of deferred callbacks to act upon at
    request end
    """
    if not hasattr(g, 'after_request_callbacks'):
        g.after_request_callbacks = []
    g.after_request_callbacks.append(f)
    return f

def get_cookie_json(request,cookie_name):
    try:
        return json.loads(request.cookies.get(cookie_name,''))
    except ValueError:
        return False

def choose_arm(app,bandit):
    """Route decorator for registering an impression conveinently

    :param bandit: The bandit/experiment to register for
    :type bandit: string
    """
    def decorator(f):
        app.extensions['mab'].pull_endpts.append((f,bandit)) 
        return f
    return decorator

def reward_endpt(app, bandit,reward=1):
    """Route decorator for rewards.

    :param bandit: The bandit/experiment to register rewards 
                   for using arm found in cookie.
    :type bandit: string
    :param reward: The amount of reward this endpoint should
                   give its winning arm
    :type reward: float
    """
    def decorator(f):
        app.extensions['mab'].reward_endpts.append((f,bandit,reward)) 
        return f
    return decorator

class BanditMiddleware(object):
    """The main flask extension.
    Sets up all the necessary tracking for the bandit experiments
    """
    
    def __init__(self,app=None):
        """Attach MAB logic to a Flask application
        
        :param app: A Flask application
        :param storage: A storage engine instance from the storage module
        """
        #TODO: use flask app config for cookie vals
        if app is not None:
            self.init_app(app)

    def _register_storage(self,app):
        storage_engine = getattr(storage, app.config.get('MAB_STORAGE_ENGINE','JSONBanditStorage')) 
        storage_opts = app.config.get('MAB_STORAGE_OPTS',("./bandits.json",))
        storage_backend = storage_engine(*storage_opts)
        app.bandit_storage = storage_backend

    def init_app(self,app):
        """Attach Multi Armed Bandit to application and configure

        :param app: A flask application instance
        """
        #config cookie name, cookie settings like lifetime etc
        app.config.setdefault('MAB_COOKIE_NAME','MAB')
        app.config.setdefault('MAB_COOKIE_PATH','/')
        app.config.setdefault('MAB_COOKIE_TTL',None)
        app.config.setdefault('MAB_DEBUG_HEADERS',True)
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['mab'] = Bunch() 
        self._register_storage(app)
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

        app.extensions['mab'].bandits = {} 
        app.extensions['mab'].reward_endpts = []
        app.extensions['mab'].pull_endpts = []
        
        #TODO: change this to be config based
        app.extensions['mab'].debug_headers = app.config.get('MAB_DEBUG_HEADERS')
        app.extensions['mab'].cookie_name = app.config.get('MAB_COOKIE_NAME')
        self._init_detection(app)

    def teardown(self,*args,**kwargs):
        """Stub for old flask versions
        """
        pass

    def _init_detection(self,app):
        """
        Attaches all request before/after handlers for bandits.

        Nested functions are as follows
        
        * pull_decorated_arms: performs arm pulls for flask endpoints
                               decorated with the :func:`choose_arm`
                               decorator
        * detect_last_bandits: Loads any arms already assigned to this user
                               from the cookie.
        * persist_bandits:     Saves bandits down to storage engine at the end
                               of the request
        * call_after_request_callbacks: Runs all deferred req callbacks
        * run_reward_decorators: reward any arms for which the decorated request 
                                 and stored cookie value match
        * remember_bandit_arms: Sets the cookie for all requests that pulled an arm
        * send_debug_header: Attaches a header for the MAB to the HTTP response for easier debugging
        """
        @app.before_request
        def pull_decorated_arms():
            #TODO: Dont maintain a list of endts, sniff request view funcs
            for func,bandit in app.extensions['mab'].pull_endpts:
                if request.endpoint == func.__name__:
                    arm_tuple = suggest_arm_for(bandit,True)
                    setattr(func,bandit,arm_tuple[1])

        @app.before_request
        def detect_last_bandits():
            #TODO: figure out a way to generalize this request assignment at all stages
            bandits = request.cookies.get(app.extensions['mab'].cookie_name)
            if bandits:
                request.cookie_arms = json.loads(bandits)

        @app.after_request
        def persist_bandits(response):
            app.bandit_storage.save(app.extensions['mab'].bandits)
            return response

        @app.after_request
        def call_after_request_callbacks(response):
            for callback in getattr(g, 'after_request_callbacks', ()):
                callback(response)
            return response

        @app.after_request
        def remember_bandit_arms(response):
            if hasattr(g,'arm_pulls_to_register'):
                response.set_cookie(app.extensions['mab'].cookie_name,json.dumps(g.arm_pulls_to_register))
            return response
        
        @app.before_request
        def after_callbacks():
            @after_this_request
            def run_reward_decorators(response):
                #TODO: dont maintain a list, sniff matched request function
                for func,bandit,reward_amt in app.extensions['mab'].reward_endpts:
                    if request.endpoint == func.__name__:
                        reward(bandit,request.cookie_arms[bandit],reward_amt)
                return response


            @after_this_request
            def send_debug_header(response):
                if app.extensions['mab'].debug_headers and get_cookie_json(request,app.extensions['mab'].cookie_name): 
                    response.headers['X-MAB-Debug'] = "SAVED; "+';'.join(['%s:%s' % (key,val) for key,val in request.cookie_arms.items()])
                elif app.extensions['mab'].debug_headers and hasattr(g,'arm_pulls_to_register'):
                    response.headers['X-MAB-Debug'] = "STORE; "+';'.join(['%s:%s' % (key,val) for key,val in g.arm_pulls_to_register.items()])
                return response
        
        #TODO: This will no longer be necessary if request sniffing works
        app.choose_arm = types.MethodType(choose_arm, app)
        app.reward_endpt = types.MethodType(reward_endpt, app)
        app.add_bandit = types.MethodType(add_bandit, app)

def _register_persist_arm(bandit_id,arm_id):
    """Puts suggestions on the stack to be saved to a cookie
    after request
    """
    if not hasattr(g,'arm_pulls_to_register'):
        g.arm_pulls_to_register = {}
    g.arm_pulls_to_register[bandit_id] = arm_id

#Public methods for operations on the app's bandit properties below

def add_bandit(app,name,bandit=None):
    """Attach a bandit for an experiment
    
    :param name: The name of the experiment, will be used for lookups
    :param bandit: The bandit to use for this experiment
    :type bandit: Bandit
    """
    saved_bandits = app.bandit_storage.load()
    if name in saved_bandits.keys():
        app.extensions['mab'].bandits[name] = saved_bandits[name]
    else:
        app.extensions['mab'].bandits[name] = bandit 

def pull(bandit_id,arm):
    """Register a pull (impression) for an arm

    :param bandit: The bandit/experiment name
    :type bandit: string
    :param arm: The name of the arm
    :type arm: string
    """
    app = current_app
    try:
        app.extensions['mab'].bandits[bandit_id].pull_arm(arm)
    except KeyError:
        #bandit does not exist
        pass

def reward(bandit_id,arm,reward=1):
    """Register an arbitrary "reward" on an arm

    :param bandit_id: The bandit/experiment in question
    :type bandit_id: string
    :param arm: The arm to register reward for
    :type arm: string
    """
    app = current_app
    try:
        app.extensions['mab'].bandits[bandit_id].reward_arm(arm,reward)
    except KeyError:
        #bandit does not exist
        pass


def suggest_arm_for(key,also_pull=False):
    """Get an experimental outcome by id.  The primary way the implementor interfaces with their
    experiments.

    Suggests arms if not in cookie, using cookie val if present

    :param key: The bandit/experiment to get a suggested arm for
    :type key: string
    :param also_pull: Should we register a pull/impression at the same time as suggesting
    :type also_pull: bool
    :raises KeyError: in case requested experiment does not exist
    """
    app = current_app
    try:
        cookie_arms = get_cookie_json(request,app.config.get("MAB_COOKIE_NAME")) 
        arm = app.extensions['mab'].bandits[key][cookie_arms[key]]
        if also_pull:
            pull(key,arm["id"])
        return arm["id"],arm["value"]
    except (AttributeError,TypeError,ValueError), e:
        arm = app.extensions['mab'].bandits[key].suggest_arm()
        if also_pull:
            pull(key,arm["id"])
        _register_persist_arm(key,arm["id"])
        return arm["id"],arm["value"]
    except KeyError,e:
        raise KeyError("No experiment defined for bandit key: %s" % key)

class MABConfigException(Exception):pass
