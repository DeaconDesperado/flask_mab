from flask import current_app,g,request
import json
from bandits import *
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

def after_this_request(f):
    if not hasattr(g, 'after_request_callbacks'):
        g.after_request_callbacks = []
    g.after_request_callbacks.append(f)
    return f

class BanditMiddleware(object):
    def __init__(self,app,storage):
        self.app = app
        if app is not None:
            self.init_app(app)
        self.bandits = {} 
        self.cookie_arms = None
        if not storage:
            raise Exception("Must pass a storage engine to persist bandit vals")
        else:
            self.storage = storage

    def init_app(self,app):
        """Attach Multi Armed Bandit to application and configure

        :param app: A flask application instance
        """
        #config cookie name, cookie settings like lifetime etc
        #persistence info, zodb?
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)
        
        #TODO: change this to be config based
        self.debug_headers = True
        self.init_detection()

    def teardown(self,*args,**kwargs):
        pass

    def init_detection(self):
        @self.app.before_request
        def detect_last_bandits():
            bandits = request.cookies.get("MAB")
            if bandits:
                self.cookie_arms = json.loads(bandits)
                print self.cookie_arms

        @self.app.after_request
        def persist_bandits(response):
            self.storage.save(self.bandits)
            return response

        @self.app.after_request
        def call_after_request_callbacks(response):
            for callback in getattr(g, 'after_request_callbacks', ()):
                callback(response)
            return response

        @self.app.before_request
        def after_callbacks():
            @after_this_request
            def remember_bandit_arms(response):
                if hasattr(g,'arm_pulls_to_register'):
                    response.set_cookie("MAB",json.dumps(g.arm_pulls_to_register))
                return response

            @after_this_request
            def send_debug_header(response):
                if self.debug_headers and self.cookie_arms:
                    response.headers['MAB-Debug'] = "SAVED; "+';'.join(['%s:%s' % (key,val) for key,val in self.cookie_arms.items()])
                elif self.debug_headers and hasattr(g,'arm_pulls_to_register'):
                    response.headers['MAB-Debug'] = "STORE; "+';'.join(['%s:%s' % (key,val) for key,val in g.arm_pulls_to_register.items()])
                return response

    def add_bandit(self,name,bandit=None):
        saved_bandits = self.storage.load()
        if name in saved_bandits.keys():
            self.bandits[name] = saved_bandits[name]
        else:
            self.bandits[name] = bandit 

    def pull(self,bandit,arm):
        try:
            self.bandits[bandit].pull_arm(arm)
        except KeyError:
            #bandit does not exist
            pass

    def reward(self,bandit,arm,reward=1):
        try:
            print self.bandits[bandit]
            self.bandits[bandit].reward_arm(arm,reward)
        except KeyError:
            #bandit does not exist
            pass

    def register_persist_arm(self,bandit_id,arm_id):
        #persist bandit val in after request callback
        if not hasattr(g,'arm_pulls_to_register'):
            g.arm_pulls_to_register = {}
        g.arm_pulls_to_register[bandit_id] = arm_id

    def __getitem__(self,key):
        return self.bandits[key]

    def suggest_arm_for(self,key,also_pull=False):
        """Get an experimental outcome by id.  The primary way the implementor interfaces with their
        experiments.

        Suggests arms if not in cookie, using cookie val if present

        :raises KeyError: in case requested experiment does not exist
        """
        try:
            arm = self.bandits[key][self.cookie_arms[key]]
            if also_pull:
                self.pull(key,arm["id"])
            return arm["id"],arm["value"]
        except (AttributeError,TypeError):
            arm = self.bandits[key].suggest_arm()
            if also_pull:
                self.pull(key,arm["id"])
            self.register_persist_arm(key,arm["id"])
            return arm["id"],arm["value"]
        except KeyError,e:
            print e
            raise KeyError("No experiment defined for bandit key: %s" % key)

    def reward_endpt(self,bandit,reward=1):
        def decorator(f):
            return f
        return decorator


#decorator for bandit suggest arm, bypass if cookie is set
#decorator for bandit arm pull at route
#decorator for bandit arm reward at route
