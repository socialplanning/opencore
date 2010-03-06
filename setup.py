from setuptools import setup, find_packages
import pkg_resources as pkr

import sys, os

version = '0.18.0dev'

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
    description="Software that drives http://openplans.org",
    long_description=readme,
    classifiers=classifiers,
    keywords='openplans openplans.org topp',
    author='The Open Planning Project',
    author_email='opencore-dev@lists.openplans.org',
    url='http://www.openplans.org/projects/opencore',
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
        'https://svn.openplans.org/svn/opencore/plugins/oc-feed/tags/0.4#egg=oc_feed-0.4',
        'https://svn.openplans.org/svn/OpencoreRedirect/trunk#egg=OpencoreRedirect-dev',
        'http://svn.red-bean.com/bob/simplejson/trunk/#egg=simplejson-dev',
        'https://svn.openplans.org/svn/ZCMLLoader/trunk#egg=ZCMLLoader',
        'https://svn.openplans.org/svn/flunc/trunk#egg=flunc-0.6dev',
        'http://svn.sccs.swarthmore.edu/egj/zope_i18n_fork_r105273#egg=zope.i18n-3.7.2opencore',
        'https://svn.openplans.org/svn/opencore/integrationlib/trunk#egg=opencore_integrationlib-dev',
        ],
    install_requires=[
        'borg.localrole==2.0.1',
        'decorator',
        'feedparser',
        'flunc>=0.6dev',
        'httplib2',
        'lxml>=2.0alpha5',
        "oc-js>=0.7",
        'oc-feed>=0.4',
        'OpencoreRedirect==dev,>=0.5dev',
        'opencore_integrationlib',
        'plone.mail',
        'Products.CacheSetup==1.2',
        'Products.GenericSetup==1.4.1',
        'simplejson',
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
