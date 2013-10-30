import unittest
import os
import flask

from flask_mab import BanditMiddleware
import flask_mab.storage
from flask_mab.bandits import EpsilonGreedyBandit

from werkzeug.http import parse_cookie
import json
from test_utils import makeBandit
from threading import Thread
from multiprocessing import Pool
from copy import copy
from Queue import Queue

class MABTestCase(unittest.TestCase):

    def setUp(self):
        banditStorage = flask_mab.storage.JSONBanditStorage('./bandits.json')
        app = flask.Flask('test_app')
        mab = flask_mab.BanditMiddleware(app,banditStorage)
        mab.add_bandit('color_button', makeBandit("EpsilonGreedyBandit",epsilon=0.1))
        app.debug = True

        @app.route("/")
        def root():
            return flask.make_response("Hello!")

        @app.route("/show_btn")
        def assign_arm():
            assigned_arm = mab.suggest_arm_for("color_button",True)
            return flask.make_response("arm")

        @app.route("/show_btn_decorated")
        @mab.choose_arm("color_button")
        def assign_arm_decorated():
            return flask.make_response("assigned an arm")
        
        @app.route("/reward")
        def reward_cookie_arm():
            assigned_arm = mab.suggest_arm_for("color_button")
            mab.reward("color_button",assigned_arm[0],1.0)
            return flask.make_response("awarded the arm")

        @app.route("/reward_decorated")
        @mab.reward_endpt("color_button",1.0)
        def reward_decorated():
            assigned_arm = mab.suggest_arm_for("color_button")
            return flask.make_response("awarded the arm")

        self.app = app
        self.mab = mab
        self.app_client = app.test_client()

    def test_routing(self):
        rv = self.app_client.get("/")
        assert "Hello" in rv.data

    def test_suggest(self):
        self.mab.debug_headers = True
        rv = self.app_client.get("/show_btn")
        assert parse_cookie(rv.headers["Set-Cookie"])["MAB"]
        assert "MAB-Debug" in rv.headers.keys()
        chosen_arm = self.get_arm(rv.headers)["color_button"]
        assert self.mab["color_button"][chosen_arm]["pulls"] > 0
        assert json.loads(parse_cookie(rv.headers["Set-Cookie"])["MAB"])["color_button"] == chosen_arm

    def test_suggest_decorated(self):
        self.mab.debug_headers = True
        rv = self.app_client.get("/show_btn_decorated")
        assert parse_cookie(rv.headers["Set-Cookie"])["MAB"]
        assert "MAB-Debug" in rv.headers.keys()
        chosen_arm = self.get_arm(rv.headers)["color_button"]
        assert self.mab["color_button"][chosen_arm]["pulls"] > 0
        assert json.loads(parse_cookie(rv.headers["Set-Cookie"])["MAB"])["color_button"] == chosen_arm

    def test_from_cookie(self):
        first_req = self.app_client.get("/show_btn")
        assert "MAB-Debug" in first_req.headers.keys()
        chosen_arm = json.loads(parse_cookie(first_req.headers["Set-Cookie"])["MAB"])["color_button"]
        self.app_client.get("/reward")
        assert self.mab["color_button"][chosen_arm]["reward"] > 0

    def test_from_cookie_reward_decorated(self):
        first_req = self.app_client.get("/show_btn")
        assert "MAB-Debug" in first_req.headers.keys()
        chosen_arm = json.loads(parse_cookie(first_req.headers["Set-Cookie"])["MAB"])["color_button"]
        self.app_client.get("/reward_decorated")
        assert self.mab["color_button"][chosen_arm]["reward"] > 0

    def get_arm(self,headers):
        key_vals = [h.strip() for h in headers["MAB-Debug"].split(';')[1:]]
        return dict([tuple(tup.split(":")) for tup in key_vals])

    def test_new_session(self):
        first_req = self.app_client.get("/show_btn")
        assert first_req.headers['MAB-Debug'].split(';')[0].strip() == 'STORE'
        self.app_client.cookie_jar.clear()
        second_req = self.app_client.get("/show_btn")
        assert second_req.headers['MAB-Debug'].split(';')[0].strip() == 'STORE'

    def test_repeating_session(self):
        first_req = self.app_client.get("/show_btn")
        for i in xrange(30):
            req = self.app_client.get("/show_btn")
            assert req.headers['MAB-Debug'].split(';')[0].strip() == 'SAVED'

    def test_concurrency(self):
        """Test that concurrent clients do not get confused 
        bandit arms
        """

        def request_worker(test,iden,q):
            try:
                client = test.app.test_client()
                first_req = client.get("/show_btn")
                chosen_arm = json.loads(parse_cookie(first_req.headers["Set-Cookie"])["MAB"])["color_button"]
                assert first_req.headers['MAB-Debug'].split(';')[0].strip() == 'STORE'
                for i in xrange(400):
                    req = client.get("/show_btn")
                    #TODO: refactor this to regex
                    assert req.headers['MAB-Debug'].split(';')[1].split(':')[1] == chosen_arm
                    assert req.headers['MAB-Debug'].split(';')[0].strip() == 'SAVED'
                client.cookie_jar.clear()
                final_req = client.get("/show_btn")
                assert final_req.headers['MAB-Debug'].split(';')[0].strip() == 'STORE'
                q.put(True)
            except AssertionError,e:
                q.put(e)

        jobs = []
        q = Queue()
        for i in xrange(4):
            jobs.append(Thread(target=request_worker, args=(self,i,q)))

        map(lambda x: x.start(), jobs)
        map(lambda x: x.join(), jobs)
        while not q.empty():
            val = q.get()
            if isinstance(val,AssertionError):
                raise val

if __name__ == '__main__':
    unittest.main()
