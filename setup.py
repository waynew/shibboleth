from setuptools import setup, find_packages


setup(
    name='shibboleth',
    version='0.1.0',
    author='Wayne Werner',
    author_email='waynejwerner@gmail.com',
    url='https://github.com/waynew/shibboleth',
    packages=find_packages(),
    entry_points = {
        'console_scripts': [
            'shibboleth=shibboleth:run',
        ],
    },
)
