from setuptools import setup, find_packages
import pkg_resources as pkr

import sys, os

version = '0.12.2dev'

f = open('README.txt')
readme = f.read()
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
      package_data={
        '': ['copy/*', 'ftests/*', '*py', '*zcml', '*txt'],
      },
      zip_safe=False,
      dependency_links=["http://svn.openplans.org/eggs/",
                        'http://download.savannah.nongnu.org/releases/pyprof/hprof-0.1.1.tar.gz#egg=hprof',
                        'https://svn.openplans.org/svn/oc-js/tags/0.6.1#egg=oc-js-0.6.1',
                        'http://feedparser.googlecode.com/files/feedparser-4.1.zip',
                        ],

      install_requires=[
          # -*- Extra requirements: -*-
          "oc-js==0.6.1",
          'oc-feed==0.1',
          "ClockQueue==0.1.1",
          'simplejson==1.7.3',
          'decorator==2.2.0',
          'feedparser==4.1',
          'topp.featurelets==0.2.2',
          'topp.utils==0.5',
          'OpencoreRedirect==0.4.1',
          'httplib2==0.4.0',
          'plone.memoize==1.0.4',
          'lxml==2.0.3',
          'plone.mail==0.1dev',
          'plone.app.form==0.1dev_r15470',
          'borg.localrole==1.0rc1',
          'wsseauth==0.1',
          'uuid==1.30',
          'flunc==0.3',
          'zcmlloader==0.1',
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
