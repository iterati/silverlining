from setuptools import setup, find_packages

setup(
    name='silverlining',
    version='0.1',
    py_modules=['silverlining'],
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
