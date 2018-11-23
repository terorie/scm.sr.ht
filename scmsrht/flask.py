from scmsrht.repos import RepoApi
from scmsrht.types import User
from srht.flask import SrhtFlask
from jinja2 import FileSystemLoader, ChoiceLoader
import os

def lookup_user(email):
    return User.query.filter(User.email == email).one_or_none()

def lookup_or_register(db, exchange, profile, scopes):
    user = User.query.filter(User.username == profile["username"]).first()
    if not user:
        user = User()
        db.session.add(user)
    user.username = profile.get("username")
    user.email = profile.get("email")
    user.paid = profile.get("paid")
    user.oauth_token = exchange["token"]
    user.oauth_token_expires = exchange["expires"]
    user.oauth_token_scopes = scopes
    db.session.commit()
    return user

class ScmFlask(SrhtFlask):
    def __init__(self, site, name, db, repo_api_class):
        super().__init__(site, name)
        self.db = db
        self._repo_api_class = repo_api_class

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
                "lookup_user": lookup_user
            }

        @self.login_manager.user_loader
        def user_loader(username):
            # TODO: Switch to a session token
            return User.query.filter(User.username == username).one_or_none()

    def lookup_or_register(self, exchange, profile, scopes):
        return lookup_or_register(self.db, exchange, profile, scopes)

    def get_repo_api(self):
        return self._repo_api_class(self.db)
