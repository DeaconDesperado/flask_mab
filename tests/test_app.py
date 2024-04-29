import unittest
import os
import flask

from flask_mab import BanditMiddleware, add_bandit, choose_arm, reward_endpt
import flask_mab.storage
from flask_mab.bandits import EpsilonGreedyBandit

from werkzeug.http import parse_cookie
import json
from utils import make_bandit
from threading import Thread
from multiprocessing import Pool
from copy import copy
from queue import Queue


class MABTestCase(unittest.TestCase):
    def setUp(self):
        banditStorage = flask_mab.storage.JSONBanditStorage("./bandits.json")
        app = flask.Flask("test_app")
        flask_mab.BanditMiddleware(app)
        app.add_bandit("color_button", make_bandit("EpsilonGreedyBandit", epsilon=0.1))
        app.debug = True

        @app.route("/")
        def root():
            return "Hello"

        @app.route("/show_btn_decorated")
        @choose_arm("color_button")
        def assign_arm_decorated(color_button):
            return flask.make_response("assigned an arm")

        @app.route("/reward_decorated")
        @reward_endpt("color_button", 1.0)
        def reward_decorated():
            return flask.make_response("awarded the arm")

        self.app = app
        self.app.config["MAB_DEBUG_HEADERS"] = True
        self.app_client = app.test_client()

    def test_routing(self):
        rv = self.app_client.get("/")
        assert "Hello".encode() in rv.data

    def test_suggest_decorated(self):
        rv = self.app_client.get("/show_btn_decorated")
        assert parse_cookie(rv.headers["Set-Cookie"])["MAB"]
        assert "X-MAB-Debug" in rv.headers.keys()
        chosen_arm = self.get_arm(rv.headers)["color_button"]
        assert (
            self.app.extensions["mab"].bandits["color_button"][chosen_arm]["pulls"] > 0
        )
        assert (
            json.loads(parse_cookie(rv.headers["Set-Cookie"])["MAB"])["color_button"][0]
            == chosen_arm
        )

    def test_from_cookie_reward_decorated(self):
        first_req = self.app_client.get("/show_btn_decorated")
        assert "X-MAB-Debug" in first_req.headers.keys()
        chosen_arm, _ = json.loads(
            parse_cookie(first_req.headers["Set-Cookie"])["MAB"]
        )["color_button"]
        self.app_client.get("/reward_decorated")
        assert (
            self.app.extensions["mab"].bandits["color_button"][chosen_arm]["reward"] > 0
        )

    def get_arm(self, headers):
        key_vals = [h.strip() for h in headers["X-MAB-Debug"].split(";")[1:]]
        return dict([tuple(tup.split(":")) for tup in key_vals])

    def test_new_session(self):
        first_req = self.app_client.get("/show_btn_decorated")
        assert first_req.headers["X-MAB-Debug"].split(";")[0].strip() == "STORE"
        self.app_client.set_cookie("MAB", "x", max_age=0)
        second_req = self.app_client.get("/show_btn_decorated")
        assert second_req.headers["X-MAB-Debug"].split(";")[0].strip() == "STORE"

    def test_repeating_session(self):
        first_req = self.app_client.get("/show_btn_decorated")
        for i in range(30):
            req = self.app_client.get("/show_btn_decorated")
            assert req.headers["X-MAB-Debug"].split(";")[0].strip() == "SAVED"

    def test_concurrency(self):
        """Test that concurrent clients do not get confused
        bandit arms
        """

        self.app.extensions["mab"].bandit_storage.flush()

        def request_worker(test, iden, q):
            try:
                client = test.app.test_client()
                first_req = client.get("/show_btn_decorated")
                chosen_arm, _ = json.loads(
                    parse_cookie(first_req.headers["Set-Cookie"])["MAB"]
                )["color_button"]
                assert first_req.headers["X-MAB-Debug"].split(";")[0].strip() == "STORE"
                for i in range(400):
                    req = client.get("/show_btn_decorated")
                    # TODO: refactor this to regex
                    assert (
                        req.headers["X-MAB-Debug"].split(";")[1].split(":")[1]
                        == chosen_arm
                    )
                    assert req.headers["X-MAB-Debug"].split(";")[0].strip() == "SAVED"
                self.app_client.set_cookie("MAB", "x", max_age=0)
                final_req = client.get("/show_btn_decorated")
                assert final_req.headers["X-MAB-Debug"].split(";")[0].strip() == "STORE"
                q.put(True)
            except AssertionError(e):
                q.put(e)

        jobs = []
        q = Queue()
        for i in range(4):
            jobs.append(Thread(target=request_worker, args=(self, i, q)))

        map(lambda x: x.start(), jobs)
        map(lambda x: x.join(), jobs)
        while not q.empty():
            val = q.get()
            if isinstance(val, AssertionError):
                raise val


if __name__ == "__main__":
    unittest.main()
