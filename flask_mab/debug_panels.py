from flask import current_app
from flask_debugtoolbar.panels import DebugPanel
from jinja2 import PackageLoader, ChoiceLoader

package_loader = PackageLoader('flask.ext.mab', 'templates')

def _maybe_patch_jinja_loader(jinja_env):
    """Patch the jinja_env loader to include flaskext.mongoengine
    templates folder if necessary.
    """
    if not isinstance(jinja_env.loader, ChoiceLoader):
        jinja_env.loader = ChoiceLoader([jinja_env.loader, package_loader])
    elif package_loader not in jinja_env.loader.loaders:
        jinja_env.loader.loaders.append(package_loader)

class BanditDebugPanel(DebugPanel):

    name = "Multi-Armed Bandit"
    has_content = True

    def __init__(self, *args, **kwargs):
        super(BanditDebugPanel, self).__init__(*args, **kwargs)
        _maybe_patch_jinja_loader(self.jinja_env)

    def nav_title(self):
        return "Multi-Armed Bandit"

    def title(self):
        return "Multi-Armed Bandit"

    def url(self):
        return ''

    def content(self):
        context = self.context.copy()
        return self.render('panels/mab-panel.html', context)
