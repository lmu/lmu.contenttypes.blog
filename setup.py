from setuptools import setup, find_packages
import os

version = '1.0'

setup(name='lmu.contenttypes.blog',
      version=version,
      description="LMU Content Types for Blogs",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.rst")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        'Framework :: Plone',
        'License :: OSI Approved :: GPL',
        'Programming Language :: Python',
        'Natural Language :: English',
        'Natural Language :: German',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Quality Assurance',
        ],
      keywords='Plone LMU Dexterity Content Type Blog',
      author='Alexander Loechel',
      author_email='Alexander.Loechel@lmu.de',
      url='https://github.com/loechel/lmu.contenttypes.blog',
      license='GPLv2',
      packages=find_packages('src',exclude=['ez_setup']),
      package_dir={'': 'src'},
      namespace_packages=['lmu', 'lmu.contenttype'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'plone.app.dexterity',
          'plone.namedfile [blobs]',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      # The next two lines may be deleted after you no longer need
      # addcontent support from paster and before you distribute
      # your package.
      setup_requires=["PasteScript"],
      paster_plugins = ["ZopeSkel"],

      )
