from setuptools import setup, find_packages
import sys, os

version = '0.9.5'

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
                        'https://svn.openplans.org/svn/flunc/branches/setuptools-command#egg=flunc-0.1.1'
                        ],
      install_requires=[
          # -*- Extra requirements: -*-
          'simplejson',
          'topp.featurelets',
          'topp.utils',
          'memojito',
          'OpencoreRedirect',
          'httplib2',
          'plone.memoize',
          'lxml>=2.0alpha',
          'plone.mail',
          'plone.app.form',
          'borg.localrole==1.0rc1',
          'flunc==0.1.1'
          ],
      setup_requires=['flunc'],
      ftest_require=['flunc'],
      entry_points="""
      [distutils.setup_keywords]
      ftest_require=setuptools.dist:check_requirements
      [distutils.commands]
      ftest = flunc.command:ftest
      """,
      )

