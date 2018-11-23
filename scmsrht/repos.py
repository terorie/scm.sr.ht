from scmsrht.types import Repository, RepoVisibility, Redirect
import re
import os.path
import shutil
import subprocess

def validate_name(valid, owner, repo_name):
    if not valid.ok:
        return None
    valid.expect(re.match(r'^[a-z._-][a-z0-9._-]*$', repo_name),
            "Name must match [a-z._-][a-z0-9._-]*", field="name")
    existing = (Repository.query
            .filter(Repository.owner_id == owner.id)
            .filter(Repository.name.ilike(repo_name))
            .first())
    if existing and existing.visibility == RepoVisibility.autocreated:
        return existing
    valid.expect(not existing, "This name is already in use.", field="name")
    return None

class RepoApi:
    def __init__(self, db):
        self.db = db

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
            repo = Repository()
            repo.name = repo_name
            repo.owner_id = owner.id
            repo.path = self.get_repo_path(owner, repo_name)
            self.db.session.add(repo)
            self.db.session.flush()
            self.do_init_repo(owner, repo)

        repo.description = description
        repo.visibility = visibility
        self.db.session.commit()
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

        _redirect = Redirect()
        _redirect.name = repo.name
        _redirect.path = repo.path
        _redirect.owner_id = repo.owner_id
        _redirect.new_repo_id = repo.id
        self.db.session.add(_redirect)

        self.do_move_repo(owner, repo, repo_name)

        repo.path = self.get_repo_path(owner, repo_name)
        repo.name = repo_name
        self.db.session.commit()
        return repo

    def do_move_repo(self, owner, repo, new_repo_name):
        raise NotImplementedError(
            "{} doesn't implement do_move_repo.".format(self.__class__))

    def delete_repo(self, repo):
        self.do_delete_repo(repo)
        self.db.session.delete(repo)
        self.db.session.commit()

    def do_delete_repo(self, repo):
        raise NotImplementedError(
            "{} doesn't implement do_delete_repo.".format(self.__class__))

class SimpleRepoApi(RepoApi):
    def __init__(self, db, repos_path):
        super().__init__(db)
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
