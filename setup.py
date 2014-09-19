from setuptools import setup

setup(
    name='silverlining',
    version='0.1',
    packages=['silverlining'],
    install_requires=[
        'click',
        'soundcloud',
        'requests',
        'fuzzywuzzy',
    ],
    entry_points='''
        [console_scripts]
        silverlining=silverlining:cli
    ''',
)
