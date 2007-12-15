from setuptools import setup, find_packages
import pkg_resources as pkr

import sys, os

version = '0.9.7.7p3'

f = open('README.txt')
readme = "".join(f.readlines())
f.close()

name='opencore'

setup(
    name=name,
      version=version,
      description="Software that drives http://openplans.org",
      long_description=readme,
      classifiers=[], # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      keywords='openplans openplans.org topp',
      author='The Open Planning Project',
      author_email='opencore-dev@lists.openplans.org',
      url='http://www.openplans.org/projects/opencore',
      license='GPLv3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      dependency_links=['https://svn.plone.org/svn/collective/wicked/WickedProduct/trunk#egg=WickedProduct',
                        'https://svn.plone.org/svn/collective/listen/branches/listen-repoze#egg=listen',
                        'https://svn.plone.org/svn/collective/ploneundelete/branches/repoze#egg=ploneundelete',
                        'https://svn.openplans.org/svn/topp.featurelets/branches/plone3#egg=topp.featurelets-0.2.2p3',
                        'https://svn.openplans.org/svn/OpencoreRedirect/branches/plone3#egg=OpencoreRedirect',
                        "https://svn.openplans.org/svn/ClockQueue/trunk#egg=ClockQueue-dev",
                        'http://svn.red-bean.com/bob/simplejson/trunk/#egg=simplejson-dev',
                        'http://www.openplans.org/projects/opencore/dependencies',
                        'https://svn.plone.org/svn/plone/plone.memoize/trunk#egg=plone.memoize-dev',
                        'http://download.savannah.nongnu.org/releases/pyprof/hprof-0.1.1.tar.gz#egg=hprof',
                        'http://zesty.ca/python/uuid.py#egg=uuid-dev',
                        'https://svn.openplans.org/svn/oc-js/trunk/#egg=oc-js-dev',
                        'https://svn.openplans.org/svn/flunc/trunk#egg=flunc-0.1.2',
                        'http://feedparser.googlecode.com/files/feedparser-4.1.zip',
                        'https://svn.plone.org/svn/collective/contentmigration/trunk#egg=Products.contentmigration-1.0b4',
                        'https://svn.plone.org/svn/collective/Products.SimpleAttachment/tags/3.0.2#egg=Products.SimpleAttachment-3.0.2',
                        ],
      install_requires=["ClockQueue==dev,>=0.0",
                        "listen",
                        "oc-js==dev,>=0.0",    
                        "ploneundelete",
                        'OpencoreRedirect',
                        'borg.localrole==1.1rc2',
                        'decorator',
                        'feedparser',
                        'flunc>=0.1.2',
                        'httplib2',
                        'lxml>=2.0alpha5',
                        'plone.app.form',
                        'plone.mail',
                        'plone.memoize',
                        'simplejson',
                        'topp.featurelets>=0.2.2p3dev',
                        'topp.utils>=0.3.0',
                        'uuid',
                        'wsseauth',
                        "WickedProduct",
                        'Products.contentmigration',
                        'Products.SimpleAttachment',
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
