from srht.database import db
from scmsrht.repos.repository import RepoVisibility
import abc
import os.path
import re
import shutil
import subprocess

class AbstractRepoApi(abc.ABC):
    """
    Implements a base API for repository management.
    """
    def __init__(self, redirect_class, repository_class):
        self.Redirect = redirect_class
        self.Repository = repository_class

    def get_repo_path(self, owner, repo_name):
        raise NotImplementedError(
            "{} doesn't implement get_repo_path.".format(self.__class__))

    def create_repo(self, valid, owner):
        repo_name = valid.require("name", friendly_name="Name")
        description = valid.optional("description")
        visibility = valid.optional("visibility",
                default="public",
                cls=RepoVisibility)
        repo = validate_name(valid, owner, repo_name)
        if not valid.ok:
            return None

        if not repo:
            repo = self.Repository()
            repo.name = repo_name
            repo.owner_id = owner.id
            repo.path = self.get_repo_path(owner, repo_name)
            db.session.add(repo)
            db.session.flush()
            self.do_init_repo(owner, repo)

        repo.description = description
        repo.visibility = visibility
        db.session.commit()
        return repo

    def do_init_repo(self, owner, repo):
        raise NotImplementedError(
            "{} doesn't implement do_init_repo.".format(self.__class__))

    def rename_repo(self, owner, repo, valid):
        repo_name = valid.require("name")
        valid.expect(repo.name != repo_name,
                "This is the same name as before.", field="name")
        if not valid.ok:
            return None
        validate_name(valid, owner, repo_name)
        if not valid.ok:
            return None

        _redirect = self.Redirect()
        _redirect.name = repo.name
        _redirect.path = repo.path
        _redirect.owner_id = repo.owner_id
        _redirect.new_repo_id = repo.id
        db.session.add(_redirect)

        self.do_move_repo(owner, repo, repo_name)

        repo.path = self.get_repo_path(owner, repo_name)
        repo.name = repo_name
        db.session.commit()
        return repo

    def do_move_repo(self, owner, repo, new_repo_name):
        raise NotImplementedError(
            "{} doesn't implement do_move_repo.".format(self.__class__))

    def delete_repo(self, repo):
        self.do_delete_repo(repo)
        db.session.delete(repo)
        db.session.commit()

    def do_delete_repo(self, repo):
        raise NotImplementedError(
            "{} doesn't implement do_delete_repo.".format(self.__class__))

    def validate_name(self, valid, owner, repo_name):
        """
        Checks if a name is available for creating a new repository.
        """
        if not valid.ok:
            return None
        valid.expect(re.match(r'^[a-z._-][a-z0-9._-]*$', repo_name),
                "Name must match [a-z._-][a-z0-9._-]*", field="name")
        existing = (self.Repository.query
                .filter(self.Repository.owner_id == owner.id)
                .filter(self.Repository.name.ilike(repo_name))
                .first())
        if existing and existing.visibility == RepoVisibility.autocreated:
            return existing
        valid.expect(not existing, "This name is already in use.", field="name")
        return None

class SimpleRepoApi(AbstractRepoApi):
    def __init__(self, repos_path, redirect_class, repository_class):
        super().__init__(redirect_class=redirect_class,
                repository_class=repository_class)
        self.repos_path = repos_path

    def get_repo_path(self, owner, repo_name):
        return os.path.join(self.repos_path, "~" + owner.username, repo_name)

    def do_move_repo(self, owner, repo, new_repo_name):
        new_path = self.get_repo_path(owner, new_repo_name)
        subprocess.run(["mv", repo.path, new_path])

    def do_delete_repo(self, repo):
        try:
            shutil.rmtree(repo.path)
        except FileNotFoundError:
            pass
