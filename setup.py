from setuptools import setup, find_packages
import pkg_resources as pkr

import sys, os

version = '0.19.0-dev'

f = open('README.txt')
readme = f.read()
f.close()

name='opencore'

# Get strings from http://www.python.org/pypi?:action=list_classifiers
classifiers=[
    "Framework :: Plone",
    "Development Status :: 4 - Beta",
    "Environment :: Web Environment",
    "License :: OSI Approved :: GNU General Public License (GPL)",
    "Natural Language :: English",
    "Operating System :: Unix",
    "Programming Language :: Python",
    ]

setup(
    name=name,
    version=version,
    description="Software that drives http://coactivate.org",
    long_description=readme,
    classifiers=classifiers,
    keywords='coactivate.org',
    author='OpenCore developers',
    author_email='opencore-dev@lists.openplans.org',
    url='http://www.coactivate.org/projects/opencore',
    license='GPLv3',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    package_data={
        '': ['copy/*', 'ftests/*', '*py', '*zcml', '*txt'],
        },
    zip_safe=False,
    dependency_links=[
        'http://feedparser.googlecode.com/files/feedparser-4.1.zip',
        'http://download.savannah.nongnu.org/releases/pyprof/hprof-0.1.1.tar.gz#egg=hprof',
        'https://github.com/ejucovy/zope_i18n_fork_r105273/raw/master/dist/zope.i18n-3.7.2opencore.tar.gz#egg=zope.i18n-3.7.2opencore',
        ],
    install_requires=[
        'bzr',
        'borg.localrole==2.0.1',
        'decorator',
        'feedparser',
        'flunc>=0.6dev',
        'httplib2',
        'lxml>=2.0alpha5',
        'libopencore',
        "oc-js>=0.7",
        'oc-feed',
        'OpencoreRedirect',
        'plone.mail',
        'Products.CacheSetup==1.2.1',
        'Products.GenericSetup==1.4.1',
        'pysqlite',
        'simplejson',
        'SQLAlchemy',
        'sven',
        'Tempita',
        'topp.featurelets>=0.3.0',
        'topp.utils>=0.5.1',
        'uuid',
        'zc.queue',
        'zcmlloader',
        'zope.i18n==3.7.2opencore',
        ],
    
    extras_require=dict(ubuntu=['hprof']),
    
    # the opencore.versions are the names of the packages
    # these are what show up in the openplans-versions view
    entry_points="""
      [distutils.commands]
      zinstall = topp.utils.setup_command:zinstall
      [opencore.versions]
      opencore = opencore
      oc-js = opencore.js
      topp.utils = topp.utils
      topp.featurelets = topp.featurelets
      """,
    )
