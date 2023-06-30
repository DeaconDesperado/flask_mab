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
        pass


if __name__ == "__main__":
    unittest.main()
