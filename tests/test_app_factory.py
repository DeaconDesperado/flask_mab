import unittest
import os
import flask

from flask_mab import BanditMiddleware,add_bandit,suggest_arm_for,reward,choose_arm,reward_endpt
import flask_mab.storage
from flask_mab.bandits import EpsilonGreedyBandit

from werkzeug.http import parse_cookie
import json
from test_utils import makeBandit
from random import choice

class MABTestCase(unittest.TestCase):

    def banditFactory(self, app):
        """Use a dictionary to look for different app setups.  Key is element name,
        list of tuples represent bandits (name, banditObj)
        """

        bandit_setups = {
            "test_app" :  [('color_button', makeBandit("EpsilonGreedyBandit",epsilon=0.1))],
            "some_other_app": [('bg_image', makeBandit("EpsilonGreedyBandit",epsilon=0.1))]
        }

        setup = bandit_setups.get(app.import_name, [])
        return setup.pop()

    def setUp(self):
        app = flask.Flask(choice(['test_app', 'some_other_app']))
        BanditMiddleware().init_app(app)
        app.debug = True
        name,bandit = self.banditFactory(app)
        self.name_to_test = name
        app.add_bandit(name,bandit)

        @app.route("/")
        def root():
            return flask.make_response("Hello!")

        @app.route("/show_btn")
        def assign_arm():
            assigned_arm = suggest_arm_for(self.name_to_test, True)
            return flask.make_response("arm")

        @app.route("/show_btn_decorated")
        @choose_arm(self.name_to_test)
        def assign_arm_decorated():
            return flask.make_response("assigned an arm")
        
        @app.route("/reward")
        def reward_cookie_arm():
            assigned_arm = suggest_arm_for(self.name_to_test)
            reward(self.name_to_test,assigned_arm[0],1.0)
            return flask.make_response("awarded the arm")

        @app.route("/reward_decorated")
        @reward_endpt(self.name_to_test,1.0)
        def reward_decorated():
            assigned_arm = suggest_arm_for(self.name_to_test)
            return flask.make_response("awarded the arm")

        self.app = app
        self.app_client = app.test_client()

    def test_routing(self):
        rv = self.app_client.get("/")
        assert "Hello" in rv.data

    def test_suggest(self):
        self.app.debug_headers = True
        rv = self.app_client.get("/show_btn")
        assert parse_cookie(rv.headers["Set-Cookie"])["MAB"]
        assert "X-MAB-Debug" in rv.headers.keys()
        chosen_arm = self.get_arm(rv.headers)[self.name_to_test]
        assert self.app.extensions['mab'].bandits[self.name_to_test][chosen_arm]["pulls"] > 0
        assert json.loads(parse_cookie(rv.headers["Set-Cookie"])["MAB"])[self.name_to_test] == chosen_arm

    def test_suggest_decorated(self):
        self.app.debug_headers = True
        rv = self.app_client.get("/show_btn_decorated")
        assert parse_cookie(rv.headers["Set-Cookie"])["MAB"]
        assert "X-MAB-Debug" in rv.headers.keys()
        chosen_arm = self.get_arm(rv.headers)[self.name_to_test]
        assert self.app.extensions['mab'].bandits[self.name_to_test][chosen_arm]["pulls"] > 0
        assert json.loads(parse_cookie(rv.headers["Set-Cookie"])["MAB"])[self.name_to_test] == chosen_arm

    def test_from_cookie(self):
        first_req = self.app_client.get("/show_btn")
        assert "X-MAB-Debug" in first_req.headers.keys()
        chosen_arm = json.loads(parse_cookie(first_req.headers["Set-Cookie"])["MAB"])[self.name_to_test]
        self.app_client.get("/reward")
        assert self.app.extensions['mab'].bandits[self.name_to_test][chosen_arm]["reward"] > 0

    def test_from_cookie_reward_decorated(self):
        first_req = self.app_client.get("/show_btn")
        assert "X-MAB-Debug" in first_req.headers.keys()
        chosen_arm = json.loads(parse_cookie(first_req.headers["Set-Cookie"])["MAB"])[self.name_to_test]
        self.app_client.get("/reward_decorated")
        assert self.app.extensions['mab'].bandits[self.name_to_test][chosen_arm]["reward"] > 0

    def get_arm(self,headers):
        key_vals = [h.strip() for h in headers["X-MAB-Debug"].split(';')[1:]]
        return dict([tuple(tup.split(":")) for tup in key_vals])

    def test_new_session(self):
        first_req = self.app_client.get("/show_btn")
        assert first_req.headers['X-MAB-Debug'].split(';')[0].strip() == 'STORE'
        self.app_client.cookie_jar.clear()
        second_req = self.app_client.get("/show_btn")
        assert second_req.headers['X-MAB-Debug'].split(';')[0].strip() == 'STORE'

    def test_repeating_session(self):
        first_req = self.app_client.get("/show_btn")
        for i in xrange(30):
            req = self.app_client.get("/show_btn")
            assert req.headers['X-MAB-Debug'].split(';')[0].strip() == 'SAVED'

    def test_concurrency(self):
        """Test that concurrent clients do not get confused 
        bandit arms
        """

        self.app.bandit_storage.flush()

if __name__ == '__main__':
    unittest.main()
