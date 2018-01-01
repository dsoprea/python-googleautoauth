import os
import setuptools

_SHORT_DESCRIPTION = \
    "Library to streamline Google authentication from the command-line."

_APP_PATH = os.path.dirname(__file__)
_RESOURCES_PATH = os.path.join(_APP_PATH, 'googleautoauth', 'resources')

with open(os.path.join(_RESOURCES_PATH, 'README.rst')) as f:
    _LONG_DESCRIPTION = f.read()

with open(os.path.join(_RESOURCES_PATH, 'requirements.txt')) as f:
    _REQUIREMENTS = [s.strip() for s in f if s.strip() != '']

with open(os.path.join(_RESOURCES_PATH, 'version.txt')) as f:
    _VERSION = f.read().strip()

setuptools.setup(
    name="googleautoauth",
    version=_VERSION,
    description=_SHORT_DESCRIPTION,
    long_description=_LONG_DESCRIPTION,
    classifiers=[],
    keywords='google oauth oauth2',
    author='Dustin Oprea',
    author_email='dustin@randomingenuity.com',
    url="https://github.com/dsoprea/python-google-autoauth",
    packages=setuptools.find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    package_data={
        'googleautoauth': [
            'resources/README.rst',
            'resources/requirements.txt',
            'resources/version.txt',
        ],
    },
    scripts=[
    ],
    install_requires=_REQUIREMENTS,
)
