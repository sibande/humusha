from setuptools import setup

setup(
    name='Humusha',
    version='0.01',
    long_description=__doc__,
    packages=['humusha'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask',
        'Flask-SQLAlchemy',
        'Flask-DebugToolbar',
    ]
)
