try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'My Project',
    'author': 'Nathan Butler',
    'url': 'https://github.com/butlern/projectname',
    'download_url': 'Where to download it.',
    'author_email': 'nathan.butler@gmail.com',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['NAME'],
    'scripts': [],
    'name': 'projectname',
}

setup(**config)
