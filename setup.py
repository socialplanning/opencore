from setuptools import setup, find_packages
import pkg_resources as pkr

import sys, os

version = '0.13.0.dev'

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
      dependency_links=['https://svn.openplans.org/svn/topp.featurelets/trunk#egg=topp.featurelets-0.3.0',
                        'https://svn.openplans.org/svn/OpencoreRedirect/trunk#egg=OpencoreRedirect-dev',
                        "https://svn.openplans.org/svn/ClockQueue/trunk#egg=ClockQueue-dev",
                        'http://svn.red-bean.com/bob/simplejson/trunk/#egg=simplejson-dev',
                        'http://www.openplans.org/projects/opencore/dependencies',
                        'http://download.savannah.nongnu.org/releases/pyprof/hprof-0.1.1.tar.gz#egg=hprof',
                        'https://svn.openplans.org/svn/oc-js/trunk/#egg=oc-js-dev',
                        'https://svn.openplans.org/svn/flunc/trunk#egg=flunc-0.1.3',
                        'http://feedparser.googlecode.com/files/feedparser-4.1.zip',
                        'https://svn.openplans.org/svn/topp.utils/trunk#egg=topp.utils-dev',
                        'https://svn.openplans.org/svn/ZCMLLoader/trunk#egg=ZCMLLoader',
                        'https://svn.openplans.org/svn/opencore/plugins/oc-feed/trunk/#egg=oc-feed',
                        'https://svn.plone.org/svn/collective/borg/components/borg.localrole/trunk#egg=borg.localrole-dev',
                        ],

      install_requires=[
          # -*- Extra requirements: -*-
          "oc-js==dev,>=0.5",
          'oc-feed>=0.2',
          "ClockQueue==dev,>=0.0",
          'simplejson',
          'decorator',
          'feedparser',
          'topp.featurelets>=0.3.0',
          'topp.utils>=0.3.1dev,==dev',
          'OpencoreRedirect==dev,>=0.5dev',
          'httplib2',
          'lxml>=2.0alpha5',
          'plone.mail',
          'borg.localrole==dev,>=2.0.1dev-r66479',
          'wsseauth',
          'uuid',
          'flunc>=0.1.3',
          'zcmlloader',
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
