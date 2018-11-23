from flask import Blueprint, request
from scmsrht.access import get_repo, has_access, UserAccess

repo = Blueprint('repo', __name__)

@repo.route("/authorize")
def authorize_http_access():
    original_uri = request.headers.get("X-Original-URI")
    original_uri = original_uri.split("/")
    owner, repo = original_uri[1], original_uri[2]
    owner, repo = get_repo(owner, repo)
    if not repo:
        return "authorized", 200
    if not has_access(repo, UserAccess.read):
        return "unauthorized", 403
    return "authorized", 200
