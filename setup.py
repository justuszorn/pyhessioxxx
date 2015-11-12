from setuptools import setup, Extension

pyhessio_module = Extension(
    'hessio.hessioc',
    sources=['hessio/src/hessio.c'],
    include_dirs = ['include',  '.'],
    libraries=['hessio'],
    define_macros=[('CTA', None), ('CTA_MAX_SC', None)]
)

NAME = 'hessio'
VERSION = '0.0.dev0'
AUTHOR = ''
AUTHOR_EMAIL = ''
URL = ''
DESCRIPTION = ''
LICENSE = ''

setup(
    name=NAME,
    packages=['hessio'],
    version=VERSION,
    description=DESCRIPTION,
    install_requires=['numpy'],
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    url=URL,
    ext_modules=[pyhessio_module],
)
