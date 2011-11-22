from setuptools import setup

setup(
    name='django-registration-email-only',
    version='0.1.0',
    author='Gabriel Grant',
    author_email='g@briel.ca',
    packages=['registration_email_only'],
    license='LGPL',
    long_description=open('README').read(),
    install_requires=[
        'django-registration',
        'simple-import',
        'pyDes',
    ],
)
