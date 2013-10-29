import unittest
import os
import flask
from flask_mab import BanditMiddleware
from flask_mab import MABConfigException
import flask_mab.storage
from flask_mab.bandits import EpsilonGreedyBandit

import json

class MABCornerCases(unittest.TestCase):

    def test_no_storage(self):
        app = flask.Flask('test_app')
        with self.assertRaises(MABConfigException):
            mab = flask_mab.BanditMiddleware(app,"foo")

if __name__ == '__main__':
    unittest.main()
