"""
    flask_mab
    ~~~~~~~~~

    This module implements all the extension logic for Multi-armed bandit experiments on Flask apps.

    :copyright: (c) 2013 by `Mark Grey <http://www.deacondesperado.com>`_.

    :license: BSD, see LICENSE for more details.
"""

from flask import current_app,g,request
import json
from bandits import *
from storage import BanditStorage

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

class BanditMiddleware(object):
    """The main flask extension.
    Sets up all the necessary tracking for the bandit experiments
    """
    
    def __init__(self,app,storage):
        """Attach MAB logic to a Flask application
        
        :param app: A Flask application
        :param storage: A storage engine instance from the storage module
        """
        #TODO: use flask app config for cookie vals
        self.app = app
        if app is not None:
            self.init_app(app)
        self.bandits = {} 
        self.reward_endpts = []
        self.pull_endpts = []
        if not storage or not isinstance(storage,BanditStorage):
            raise MABConfigException("Must pass a storage engine to persist bandit vals")
        else:
            self.storage = storage

    def init_app(self,app):
        """Attach Multi Armed Bandit to application and configure

        :param app: A flask application instance
        """
        #config cookie name, cookie settings like lifetime etc
        app.config.setdefault('MAB_COOKIE_NAME','MAB')
        app.config.setdefault('MAB_COOKIE_PATH','/')
        app.config.setdefault('MAB_COOKIE_TTL',None)
        app.config.setdefault('MAB_DEBUG_HEADERS',True)
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)
        
        #TODO: change this to be config based
        self.debug_headers = app.config.get('MAB_DEBUG_HEADERS')
        self.cookie_name = app.config.get('MAB_COOKIE_NAME')
        self._init_detection()

    def teardown(self,*args,**kwargs):
        """Stub for old flask versions
        """
        pass

    def _init_detection(self):
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
        @self.app.before_request
        def pull_decorated_arms():
            for func,bandit in self.pull_endpts:
                if request.endpoint == func.__name__:
                    arm_tuple = self.suggest_arm_for(bandit,True)
                    setattr(func,bandit,arm_tuple[1])

        @self.app.before_request
        def detect_last_bandits():
            bandits = request.cookies.get(self.cookie_name)
            if bandits:
                request.cookie_arms = json.loads(bandits)

        @self.app.after_request
        def persist_bandits(response):
            self.storage.save(self.bandits)
            return response

        @self.app.after_request
        def call_after_request_callbacks(response):
            for callback in getattr(g, 'after_request_callbacks', ()):
                callback(response)
            return response

        @self.app.after_request
        def remember_bandit_arms(response):
            if hasattr(g,'arm_pulls_to_register'):
                response.set_cookie(self.cookie_name,json.dumps(g.arm_pulls_to_register))
            return response
        
        @self.app.before_request
        def after_callbacks():
            @after_this_request
            def run_reward_decorators(response):
                for func,bandit,reward in self.reward_endpts:
                    if request.endpoint == func.__name__:
                        self.reward(bandit,request.cookie_arms[bandit],1.0)
                return response


            @after_this_request
            def send_debug_header(response):
                if self.debug_headers and get_cookie_json(request,self.cookie_name): 
                    response.headers['MAB-Debug'] = "SAVED; "+';'.join(['%s:%s' % (key,val) for key,val in request.cookie_arms.items()])
                elif self.debug_headers and hasattr(g,'arm_pulls_to_register'):
                    response.headers['MAB-Debug'] = "STORE; "+';'.join(['%s:%s' % (key,val) for key,val in g.arm_pulls_to_register.items()])
                return response

    def add_bandit(self,name,bandit=None):
        """Attach a bandit for an experiment
        
        :param name: The name of the experiment, will be used for lookups
        :param bandit: The bandit to use for this experiment
        :type bandit: Bandit
        """
        saved_bandits = self.storage.load()
        if name in saved_bandits.keys():
            self.bandits[name] = saved_bandits[name]
        else:
            self.bandits[name] = bandit 

    def pull(self,bandit_id,arm):
        """Register a pull (impression) for an arm

        :param bandit: The bandit/experiment name
        :type bandit: string
        :param arm: The name of the arm
        :type arm: string
        """
        try:
            self.bandits[bandit_id].pull_arm(arm)
        except KeyError:
            #bandit does not exist
            pass

    def reward(self,bandit_id,arm,reward=1):
        """Register an arbitrary "reward" on an arm

        :param bandit_id: The bandit/experiment in question
        :type bandit_id: string
        :param arm: The arm to register reward for
        :type arm: string
        """
        try:
            self.bandits[bandit_id].reward_arm(arm,reward)
        except KeyError:
            #bandit does not exist
            pass

    def _register_persist_arm(self,bandit_id,arm_id):
        """Puts suggestions on the stack to be saved to a cookie
        after request
        """
        if not hasattr(g,'arm_pulls_to_register'):
            g.arm_pulls_to_register = {}
        print 'persist'
        g.arm_pulls_to_register[bandit_id] = arm_id

    def __getitem__(self,key):
        """Get an bandit/experiment by key
        """
        return self.bandits[key]

    def suggest_arm_for(self,key,also_pull=False):
        """Get an experimental outcome by id.  The primary way the implementor interfaces with their
        experiments.

        Suggests arms if not in cookie, using cookie val if present

        :param key: The bandit/experiment to get a suggested arm for
        :type key: string
        :param also_pull: Should we register a pull/impression at the same time as suggesting
        :type also_pull: bool
        :raises KeyError: in case requested experiment does not exist
        """
        try:
            cookie_arms = get_cookie_json(request,self.cookie_name) 
            arm = self.bandits[key][cookie_arms[key]]
            if also_pull:
                self.pull(key,arm["id"])
            return arm["id"],arm["value"]
        except (AttributeError,TypeError,ValueError), e:
            arm = self.bandits[key].suggest_arm()
            if also_pull:
                self.pull(key,arm["id"])
            self._register_persist_arm(key,arm["id"])
            return arm["id"],arm["value"]
        except KeyError,e:
            print e
            raise KeyError("No experiment defined for bandit key: %s" % key)

    def reward_endpt(self,bandit,reward=1):
        """Route decorator for rewards.

        :param bandit: The bandit/experiment to register rewards 
                       for using arm found in cookie.
        :type bandit: string
        :param reward: The amount of reward this endpoint should
                       give its winning arm
        :type reward: float
        """
        def decorator(f):
            self.reward_endpts.append((f,bandit,reward)) 
            return f
        return decorator

    def choose_arm(self,bandit):
        """Route decorator for registering an impression conveinently

        :param bandit: The bandit/experiment to register for
        :type bandit: string
        """
        def decorator(f):
            self.pull_endpts.append((f,bandit)) 
            return f
        return decorator


class MABConfigException(Exception):pass
