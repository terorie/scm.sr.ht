from datetime import datetime
from enum import IntFlag
from flask import abort, current_app, request
from flask_login import current_user
from scmsrht.repos.access import AccessMode
from scmsrht.repos.repository import RepoVisibility
from srht.database import db

class UserAccess(IntFlag):
    none = 0
    read = 1
    write = 2
    manage = 4

def check_repo(user, repo, authorized=current_user, tables=current_app):
    User = tables.User
    u = User.query.filter(User.username == user).first()
    if not u:
        abort(404)
    Repository = tables.Repository
    _repo = Repository.query.filter(Repository.owner_id == u.id)\
            .filter(Repository.name == repo).first()
    if not _repo:
        abort(404)
    if _repo.visibility == RepoVisibility.private:
        if not authorized or authorized.id != _repo.owner_id:
            abort(404)
    return u, _repo

def get_repo(owner_name, repo_name, tables=current_app):
    if owner_name[0] == "~":
        User = tables.User
        user = User.query.filter(User.username == owner_name[1:]).first()
        if user:
            Repository = tables.Repository
            repo = Repository.query.filter(Repository.owner_id == user.id)\
                .filter(Repository.name == repo_name).first()
        else:
            repo = None
        if user and not repo:
            Redirect = tables.Redirect
            repo = (Redirect.query
                    .filter(Redirect.owner_id == user.id)
                    .filter(Redirect.name == repo_name)
                ).first()
        return user, repo
    else:
        # TODO: organizations
        return None, None

def get_repo_or_redir(owner, repo, tables=current_app):
    owner, repo = get_repo(owner, repo)
    if not repo:
        abort(404)
    if not has_access(repo, UserAccess.read):
        abort(401)
    if isinstance(repo, tables.Redirect):
        view_args = request.view_args
        if not "repo" in view_args or not "owner" in view_args:
            return redirect(url_for(".summary",
                owner=repo.new_repo.owner.canonical_name,
                repo=repo.new_repo.name))
        view_args["owner"] = repo.new_repo.owner.canonical_name
        view_args["repo"] = repo.new_repo.name
        abort(redirect(url_for(request.endpoint, **view_args)))
    return owner, repo

def get_access(repo, user=None, tables=current_app):
    if not user:
        user = current_user
    if not repo:
        return UserAccess.none
    if isinstance(repo, tables.Redirect):
        # Just pretend they have full access for long enough to do the redirect
        return UserAccess.read | UserAccess.write | UserAccess.manage
    if not user:
        if repo.visibility == RepoVisibility.public or \
                repo.visibility == RepoVisibility.unlisted:
            return UserAccess.read
        return UserAccess.none
    if repo.owner_id == user.id:
        return UserAccess.read | UserAccess.write | UserAccess.manage
    acl = tables.Access.query.filter(
            tables.Access.repo_id == repo.id).first()
    if acl:
        acl.updated = datetime.utcnow()
        db.session.commit()
        if acl.mode == AccessMode.ro:
            return UserAccess.read
        else:
            return UserAccess.read | UserAccess.write
    if repo.visibility == RepoVisibility.private:
        return UserAccess.none
    return UserAccess.read

def has_access(repo, access, user=None, tables=current_app):
    return access in get_access(repo, user, tables=tables)

def check_access(owner_name, repo_name, access, tables=current_app):
    owner, repo = get_repo(owner_name, repo_name)
    if not owner or not repo:
        abort(404)
    a = get_access(repo, tables=tables)
    if not UserAccess.write in a:
        abort(404)
    if not access in a:
        abort(403)
    return owner, repo
