from setuptools.command.install import install
from setuptools import setup
#from distutils.command import bdist_conda
from distutils.core import  Extension
import sys
import os

class PyhessioxxxInstall(install):

    def run(self):
        install.run(self)
        build_dir = "hessioxxx"
        cwd = os.getcwd() # get current directory
        try:
          os.chdir(build_dir)
          os.system("mkdir  bin out lib")
          os.system("make CDEBUGFLAGS=\"-g -O2\" DEFINES=\"-DCTA -DCTA_MAX_SC\"")
        finally:
          os.chdir(cwd)

pyhessio_module = Extension('pyhessio',
                    sources = ['pyhessio.c'],
                    include_dirs = ['hessioxxx/include',  '.'],
                    library_dirs = ['hessioxxx/lib'],
                    libraries = ['hessio'],
                    runtime_library_dirs = ['hessioxxx/lib']
                  )

# Get some values from the setup.cfg
from distutils import config
conf = config.ConfigParser()
conf.read(['setup.cfg'])
metadata = dict(conf.items('metadata'))

PACKAGENAME = metadata.get('package_name', 'packagename')
DESCRIPTION = metadata.get('description', 'Astropy affiliated package')
AUTHOR = metadata.get('author', '')
AUTHOR_EMAIL = metadata.get('author_email', '')
LICENSE = metadata.get('license', 'unknown')
URL = metadata.get('url', 'https://github.com/jacquemier/pyhessioxxx')
# VERSION should be PEP386 compatible (http://www.python.org/dev/peps/pep-0386)
VERSION = '0.0.dev0'

setup(name=PACKAGENAME,
      version=VERSION,
      description=DESCRIPTION,
      install_requires=['numpy'],
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      license=LICENSE,
      url=URL,
      ext_modules = [pyhessio_module],
      cmdclass={'install': PyhessioxxxInstall},
)

"""
classifiers=[
'Programming Language :: Python :: 3',
'Programming Language :: Python :: 3.2',
'Programming Language :: Python :: 3.3',
'Programming Language :: Python :: 3.4']
"""
