#!/usr/bin/env python3
from setuptools import setup
import os
import subprocess

ver = os.environ.get("PKGVER") or subprocess.run(['git', 'describe', '--tags'],
      stdout=subprocess.PIPE).stdout.decode().strip()

setup(
  name = 'scmsrht',
  packages = [
      'scmsrht',
      'scmsrht.types',
      'scmsrht.blueprints',
      'scmsrht.alembic',
      'scmsrht.alembic.versions'
  ],
  version = ver,
  description = 'scm.sr.ht library',
  author = 'Drew DeVault',
  author_email = 'sir@cmpwn.com',
  url = 'https://git.sr.ht/~sircmpwn/scm.sr.ht',
  install_requires = ['srht', 'flask-login', 'redis<3', 'pygments'],
  license = 'AGPL-3.0',
  package_data={
      'scmsrht': [
          'templates/*.html',
          'hooks/*'
      ]
  }
)

