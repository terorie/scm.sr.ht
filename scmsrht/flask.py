from jinja2 import FileSystemLoader, ChoiceLoader
from srht.database import db
from srht.flask import SrhtFlask
import os

class ScmSrhtFlask(SrhtFlask):
    def __init__(self, site, name, *,
                access_class, redirect_class, repository_class, user_class,
                repo_api,
                **kwargs):
        super().__init__(site, name, **kwargs)

        self.User = user_class

        self.Access = access_class
        self.Redirect = redirect_class
        self.Repository = repository_class
        self.User = user_class

        self.repo_api = repo_api

        choices = [self.jinja_loader,
                   FileSystemLoader(os.path.join(
                       os.path.dirname(__file__),
                       "templates"))]
        self.jinja_loader = ChoiceLoader(choices)

        self.url_map.strict_slashes = False

        from scmsrht.blueprints.api import api
        from scmsrht.blueprints.manage import manage
        from scmsrht.blueprints.public import public

        self.register_blueprint(api)
        self.register_blueprint(manage)
        self.register_blueprint(public)

        @self.context_processor
        def inject():
            return {
                "lookup_user": self.lookup_user
            }

    def lookup_user(self, email):
        return self.User.query.filter(self.User.email == email).one_or_none()
