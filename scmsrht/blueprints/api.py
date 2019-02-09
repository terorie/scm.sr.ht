from flask import Blueprint, current_app, request, redirect, abort, url_for
from scmsrht.repos.redirect import BaseRedirectMixin
from scmsrht.repos.repository import RepoVisibility
from scmsrht.access import UserAccess, has_access, get_repo, check_repo
from srht.validation import Validation, valid_url
from srht.oauth import oauth, current_token
from srht.database import db

# Disclaimer: this API is undocumented and subject to change
api = Blueprint("api", __name__)

repo_json = lambda r: {
    "id": r.id,
    "name": r.name,
    "description": r.description,
    "created": r.created,
    "updated": r.updated,
    "visibility": r.visibility.value
}

wh_json = lambda wh: {
    "id": wh.id,
    "created": wh.created,
    "description": wh.description,
    "url": wh.url,
    "validate_ssl": wh.validate_ssl,
    "repo": "~{}/{}".format(wh.repository.owner.username,
        wh.repository.name) if wh.repository else None
}

@api.route("/api/repos")
@oauth("repos")
def repos_GET():
    start = request.args.get('start') or -1
    Repository = current_app.Repository
    repos = Repository.query.filter(
            Repository.owner_id == current_token.user_id)
    if start != -1:
        repos = repos.filter(Repository.id <= start)
    repos = repos.order_by(Repository.id.desc()).limit(11).all()
    if len(repos) != 11:
        next_id = -1
    else:
        next_id = repos[-1].id
        repos = repos[:10]
    return {
        "next": next_id,
        "results": [repo_json(r) for r in repos]
    }

@api.route("/api/repos", methods=["POST"])
@oauth("repos:write")
def repos_POST():
    if not current_app.repo_api:
        abort(501)
    valid = Validation(request)
    repo = current_app.repo_api.create_repo(valid, current_token.user)
    if not valid.ok:
        return valid.response
    return repo_json(repo)

@api.route("/api/repos/~<owner>")
def repos_username_GET(owner):
    User = current_app.User
    user = User.query.filter(User.username == owner).first()
    if not user:
        abort(404)
    start = request.args.get('start') or -1
    Repository = current_app.Repository
    repos = (Repository.query
        .filter(Repository.owner_id == user.id)
        .filter(Repository.visibility == RepoVisibility.public)
    )
    if start != -1:
        repos = repos.filter(Repository.id <= start)
    repos = repos.order_by(Repository.id.desc()).limit(11).all()
    if len(repos) != 11:
        next_id = -1
    else:
        next_id = repos[-1].id
        repos = repos[:10]
    return {
        "next": next_id,
        "results": [repo_json(r) for r in repos]
    }

@api.route("/api/repos/~<owner>/<name>")
def repos_by_name_GET(owner, name):
    user, repo = check_repo(owner, name)
    if isinstance(repo, BaseRedirectMixin):
        return redirect(url_for(".repos_by_name_GET",
            owner=owner, name=repo.new_repo.name))
    return repo_json(repo)

def prop(valid, resource, prop, **kwargs):
    value = valid.optional(prop, **kwargs)
    if value:
        setattr(resource, prop, value)

@api.route("/api/repos/~<owner>/<name>", methods=["PUT"])
@oauth("repos:write")
def repos_by_name_PUT(owner, name):
    user, repo = check_repo(owner, name, authorized=current_token.user)
    if isinstance(repo, BaseRedirectMixin):
        abort(404)
    valid = Validation(request)
    prop(valid, repo, "visibility", cls=RepoVisibility)
    prop(valid, repo, "description", cls=str)
    db.session.commit()
    return repo_json(repo)
