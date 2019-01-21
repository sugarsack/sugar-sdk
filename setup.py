from setuptools import setup

setup(
    name='sugar-sdk',
    version='0.1',
    packages=['sugarsdk'],
    url='https://github.com/sugarsack/sugar-sdk',
    license='Apache 2.0',
    author='Bo Maryniuk',
    author_email='bo@maryniuk.net',
    description='Sugar SDK',
    scripts=["scripts/sugar-mkmod"],
)
