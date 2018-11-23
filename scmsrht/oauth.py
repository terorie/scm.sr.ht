from srht.config import cfg
from srht.oauth import OAuthScope, AbstractOAuthService
from srht.oauth import meta_delegated_exchange
from srht.flask import DATE_FORMAT
from srht.database import db
from scmsrht.types import OAuthToken, User
from datetime import datetime

class ScmOAuthService(AbstractOAuthService):
    def __init__(self, site):
        super().__init__()
        self.client_id = cfg(site, "oauth-client-id")
        self.client_secret = cfg(site, "oauth-client-secret")
        self.revocation_url = "{}/oauth/revoke".format(cfg(site, "origin"))

    def get_client_id(self):
        return self.client_id

    def get_token(self, token, token_hash, scopes):
        now = datetime.utcnow()
        oauth_token = (OAuthToken.query
                .filter(OAuthToken.token_hash == token_hash)
                .filter(OAuthToken.expires > now)
        ).first()
        if oauth_token:
            return oauth_token
        _token, profile = meta_delegated_exchange(
                token, self.client_id, self.client_secret, self.revocation_url)
        expires = datetime.strptime(_token["expires"], DATE_FORMAT)
        scopes = set(OAuthScope(s) for s in _token["scopes"].split(","))
        user = User.query.filter(User.username == profile["username"]).first()
        if not user:
            user = User()
            user.username = profile.get("username")
            user.email = profile.get("email")
            user.paid = profile.get("paid")
            user.oauth_token = token
            user.oauth_token_expires = expires
            db.session.add(user)
            db.session.flush()
        oauth_token = OAuthToken(user, token, expires)
        oauth_token.scopes = ",".join(str(s) for s in scopes)
        db.session.add(oauth_token)
        db.session.commit()
        return oauth_token
