#!/usr/bin/env python3
from distutils.core import setup
import subprocess
import os
import site
import sys

ver = os.environ.get("PKGVER") or subprocess.run(['git', 'describe', '--tags'],
      stdout=subprocess.PIPE).stdout.decode().strip()

setup(
  name = 'scmsrht',
  packages = [
      'scmsrht',
      'scmsrht.blueprints',
      'scmsrht.repos',
  ],
  version = ver,
  description = 'scm.sr.ht library',
  author = 'Ludovic Chabant',
  author_email = 'ludovic@chabant.com',
  url = 'https://git.sr.ht/~sircmpwn/scm.sr.ht',
  install_requires = ['srht'],
  license = 'AGPL-3.0',
  package_data={
      'scmsrht': [
          'templates/*.html',
          'templates/partials/*.html',
      ]
  }
)

