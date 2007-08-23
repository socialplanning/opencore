from setuptools import setup, find_packages
import sys, os

version = '0.9.2'

f = open('README.txt')
readme = "".join(f.readlines())
f.close()

setup(name='opencore',
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
      dependency_links=['https://svn.openplans.org/svn/OpencoreRedirect/trunk#egg=OpencoreRedirect',
                        'http://www.openplans.org/projects/opencore/dependencies',
                        'https://svn.plone.org/svn/plone/plone.memoize/trunk#egg=plone.memoize-dev', 
                        'https://svn.openplans.org/svn/topp/topp.messages/trunk#egg=topp.messages-dev'],
      install_requires=[
          # -*- Extra requirements: -*-
          'topp.featurelets',
          'topp.utils',
          'topp.messages',
          'memojito',
          'OpencoreRedirect',
          'httplib2',
          'simplejson',
          'plone.memoize',
          'cabochonclient',
          'lxml'
          ]
      )

