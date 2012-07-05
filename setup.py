from setuptools import setup

setup(
    name='Zabalaza',
    version='0.01',
    long_description=__doc__,
    packages=['zabalaza'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask',
        'Flask-SQLAlchemy',
        'Flask-DebugToolbar',
    ]
)
