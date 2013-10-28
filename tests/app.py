import unittest
import os
import flask

from flask_mab.flask_mab import BanditMiddleware
import flask_mab.storage

app = flask.Flask('test_app')

@app.route("/")
def root():
    return flask.make_response(200,"Hello!")

class MABTestCase(unittest.TestCase):

    def setUp(self):
        banditStorage = flask_mab.storage.JSONBanditStorage('./bandits.json')
        print dir(flask_mab)
        mab = flask_mab.BanditMiddleware(app,banditStorage)
        self.app = app.test_client()

    def test_routing(self):
        rv = self.app.get("/")
        assert "Hello" in rv.data



if __name__ == '__main__':
    unittest.main()
