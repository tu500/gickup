import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'gickup',
    version = '1.0',
    url='https://github.com/tu500/gickup',
    author = 'Philip Matura',
    author_email = 'philip.m@tura-home.de',
    description = ('Automatic git backup script for multiple repositories'),
    keywords='git backup',
    license='AGPLv3+',
    packages=['gickup'],
    long_description=read('README.rst'),
    entry_points='''
            [console_scripts]
            gickup=gickup.__main__:main
        ''',
    classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 3 :: Only',
            'Topic :: Software Development :: Version Control :: Git',
            'Topic :: System :: Archiving :: Backup',
        ],
)
