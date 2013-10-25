from flask import current_app
import json
from bandits import *

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

class BanditMiddleware(object):
    def __init__(self,app):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self,app):
        """Attach Multi Armed Bandit to application and configure

        :param app: A flask application instance
        """
        #cookie name, cookie settings like lifetime etc
        #persistence info, zodb?
        #before after handlers for bandit pull
        #debug header
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)
        
        #register beforerequest cookie check

    def add_bandit(self,name,bandit):
        #if is list plural, else single
        #check persistence for every id, and if not present, init @ 0 for vals
        #if present, use Bandit.fromdict
        pass

    def teardown(self):
        #persist values
        #set cookie for persist
        pass

    def get_value(self,bandit):
        bandit = self[bandit]
        #return determined cookie arm for specified bandit
    
    def reward(self,bandit):
        #reward the cookie bandit arm for specified bandit
        pass

    def __getitem__(self,key):
        #get bandit by key
        pass

    def __setitem__(self,key,bandit):
        #set bandit by key
        pass

#decorator for bandit suggest arm, bypass if cookie is set
#decorator for bandit arm pull at route
#decorator for bandit arm reward at route
