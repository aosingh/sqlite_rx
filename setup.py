from os import path

from setuptools import find_packages, setup
from sqlite_rx import __version__


this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

VERSION = __version__
DISTNAME = 'sqlite_rx'
LICENSE = 'MIT License'
AUTHOR = 'Abhishek Singh'
MAINTAINER = 'Abhishek Singh'
MAINTAINER_EMAIL = 'abhishek.singh20141@gmail.com'
DESCRIPTION = ('Python SQLite Client and Server')
URL = 'https://github.com/aosingh/sqlite_rx'

PACKAGES = ['sqlite_rx']

INSTALL_REQUIRES = ['msgpack==1.0.3',
                    'pyzmq==22.3.0',
                    'tornado==6.1',
                    'click==8.0.4',
                    'billiard==3.6.4.0']

TEST_REQUIRE = ['pytest==7.1.1',
                'coverage==6.3.2']

classifiers = [
    'Topic :: Database :: Database Engines/Servers',
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Education',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3 :: Only',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Operating System :: POSIX :: Linux',
    'Operating System :: Unix',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: MacOS'
]
keywords = 'sqlite client server fast secure'


setup(
    name=DISTNAME,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=MAINTAINER_EMAIL,
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    description=DESCRIPTION,
    license=LICENSE,
    url=URL,
    version=VERSION,
    scripts=['bin/curve-keygen'],
    entry_points={
      'console_scripts': [
          'sqlite-server=sqlite_rx.cli.server:main'
      ]
    },
    packages=find_packages(exclude=("tests",)),
    package_dir={'sqlite_rx': 'sqlite_rx'},
    install_requires=INSTALL_REQUIRES,
    test_require=TEST_REQUIRE,
    include_package_data=True,
    classifiers=classifiers,
    keywords=keywords,
    python_requires='>=3.6'
)
