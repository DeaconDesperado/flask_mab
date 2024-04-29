from flask import current_app, request
from flask_debugtoolbar.panels import DebugPanel
from jinja2 import PackageLoader, ChoiceLoader
import json

package_loader = PackageLoader("flask_mab", "templates")


def _maybe_patch_jinja_loader(jinja_env):
    """Patch the jinja_env loader to include
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
        return ""

    def process_request(self, request):
        self.raw_cookie = request.cookies.get(
            current_app.extensions["mab"].cookie_name, "{}"
        )

    def content(self):
        context = self.context.copy()
        context["cookie_name"] = current_app.extensions["mab"].cookie_name
        context["raw_cookie"] = self.raw_cookie
        context["storage_engine"] = current_app.config.get("MAB_STORAGE_ENGINE")
        context["storage_opts"] = current_app.config.get("MAB_STORAGE_OPTS", tuple())
        context["bandits"] = current_app.extensions["mab"].bandits.items()
        context["assigned"] = request.bandits
        return self.render("panels/mab-panel.html", context)
