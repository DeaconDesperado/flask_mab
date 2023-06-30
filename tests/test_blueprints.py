import unittest
import os
import flask

from flask_mab import (
    BanditMiddleware,
    add_bandit,
    choose_arm,
    reward_endpt,
    MABConfigException,
)
import flask_mab.storage
from flask_mab.bandits import EpsilonGreedyBandit

from werkzeug.http import parse_cookie
import json
from utils import make_bandit

# TODO: write tests per http://stackoverflow.com/a/11027030/215608


class MABTestCase(unittest.TestCase):
    def setUp(self):
        banditStorage = flask_mab.storage.JSONBanditStorage("./bandits.json")
        bp = flask.Blueprint("test_bp", __name__)

        @bp.route("/")
        @choose_arm("some_bandit")
        def root(some_bandit):
            return "hello"

        @bp.route("/reward")
        @reward_endpt("some_bandit", 1.0)
        def reward_me():
            return "reward"

        self.bp = bp

    def test_proper_configuration(self):
        app = flask.Flask(__name__)
        BanditMiddleware().init_app(app)

        app.add_bandit("some_bandit", make_bandit("EpsilonGreedyBandit", epsilon=1.0))
        app.register_blueprint(self.bp)
        app_client = app.test_client()

        rv = app_client.get("/")
        assert parse_cookie(rv.headers["Set-Cookie"])["MAB"]

        assert "X-MAB-Debug" in rv.headers.keys()
        chosen_arm = self.get_arm(rv.headers)["some_bandit"]
        assert app.extensions["mab"].bandits["some_bandit"][chosen_arm]["pulls"] > 0
        assert (
            json.loads(parse_cookie(rv.headers["Set-Cookie"])["MAB"])["some_bandit"]
            == chosen_arm
        )

        app_client.get("/reward")
        assert app.extensions["mab"].bandits["some_bandit"][chosen_arm]["reward"] > 0

    def test_improper_configuration(self):
        app = flask.Flask(__name__)
        app.debug = True
        BanditMiddleware().init_app(app)

        app.register_blueprint(self.bp)
        app_client = app.test_client()

        with self.assertRaises(MABConfigException):
            rv = app_client.get("/")

        with self.assertRaises(MABConfigException):
            app_client.set_cookie("localhost", "MAB", '{"some_bandit": "blue"}')
            app_client.get("/reward")

    def get_arm(self, headers):
        key_vals = [h.strip() for h in headers["X-MAB-Debug"].split(";")[1:]]
        return dict([tuple(tup.split(":")) for tup in key_vals])
