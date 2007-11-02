from setuptools import setup, find_packages
import sys, os

version = '0.9.7.1'

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
                        "https://svn.openplans.org/svn/ClockQueue/trunk#egg=ClockQueue-dev",
                        'http://svn.red-bean.com/bob/simplejson/trunk/#egg=simplejson-dev',
                        'http://www.openplans.org/projects/opencore/dependencies',
                        'https://svn.plone.org/svn/plone/plone.memoize/trunk#egg=plone.memoize-dev',
                        'http://download.savannah.nongnu.org/releases/pyprof/hprof-0.1.1.tar.gz#egg=hprof'],
      install_requires=[
          # -*- Extra requirements: -*-
          'hprof',
          "ClockQueue==dev,>=0.0",
          'simplejson',
          'decorator',
          'topp.featurelets>=0.2.1',
          'topp.utils>=0.2.6',
          'memojito',
          'OpencoreRedirect',
          'httplib2',
          'plone.memoize',
          'lxml>=2.0alpha',
          'plone.mail',
          'plone.app.form',
          'borg.localrole==1.0rc1',
          'wsseauth',
          ],
      extras_require=dict(ubuntu=['hprof'])
      )


