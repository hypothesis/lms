import os

from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, 'README.markdown')) as f:
    README = f.read()

setup(
    name='lms',
    description='Hypothesis Canvas app',
    long_description=README,
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    url='https://github.com/hypothesis/lms',
    keywords='web pyramid pylons',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points="""\
    [console_scripts]
    devdata = lms.scripts:devdata
    """,
)
