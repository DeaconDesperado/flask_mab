from example.example_app import app
from flask_debugtoolbar import DebugToolbarExtension

if __name__ == "__main__":
    app.debug = True
    app.secret_key = "foobar"
    toolbar = DebugToolbarExtension(app)
    app.config['DEBUG_TB_PANELS'] = app.config.get("DEBUG_TB_PANELS", []) + ("flask.ext.mab.debug_panels.BanditDebugPanel",)
    app.run()

