from os import path

from setuptools import find_packages, setup


this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

VERSION = '1.1.2'
DISTNAME = 'sqlite_rx'
LICENSE = 'MIT License'
AUTHOR = 'Abhishek Singh'
MAINTAINER = 'Abhishek Singh'
MAINTAINER_EMAIL = 'abhishek.singh20141@gmail.com'
DESCRIPTION = 'Python SQLite Client and Server'
URL = 'https://github.com/aosingh/sqlite_rx'

PACKAGES = ['sqlite_rx']

INSTALL_REQUIRES = ['msgpack==1.0.4',
                    'pyzmq==23.2.0',
                    'tornado==6.2',
                    'billiard==4.0.2']

CLI_REQUIRES = ['click==8.1.3', 'rich==12.0.1', 'pygments==2.11.2']

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
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Operating System :: POSIX :: Linux',
    'Operating System :: Unix',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: MacOS'
]
keywords = 'sqlite client server fast secure'

project_urls = {"Documentation" : "https://aosingh.github.io/sqlite_rx/",
                "Source":  "https://github.com/aosingh/sqlite_rx",
                "Bug Tracker": "https://github.com/aosingh/sqlite_rx/issues",
                "CI": "https://github.com/aosingh/sqlite_rx/actions",
                "Release Notes": "https://github.com/aosingh/sqlite_rx/releases",
                "License": "https://github.com/aosingh/sqlite_rx/blob/master/LICENSE"}


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
    project_urls=project_urls,
    version=VERSION,
    scripts=['bin/curve-keygen'],
    entry_points={
      'console_scripts': [
          'sqlite-server=sqlite_rx.cli.server:main',
          'sqlite-client=sqlite_rx.cli.client:main'
      ]
    },
    extras_require={
      'cli': CLI_REQUIRES
    },
    packages=find_packages(exclude=("tests",)),
    package_dir={'sqlite_rx': 'sqlite_rx'},
    install_requires=INSTALL_REQUIRES,
    test_require=TEST_REQUIRE,
    include_package_data=True,
    classifiers=classifiers,
    keywords=keywords,
    python_requires='>=3.7'
)
