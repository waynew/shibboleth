from setuptools import setup, find_packages


setup(
    name='shibboleth',
    version='0.1.7',
    author='Wayne Werner',
    author_email='waynejwerner@gmail.com',
    url='https://github.com/waynew/shibboleth',
    py_modules=['shibboleth'],
    entry_points = {
        'console_scripts': [
            'shibboleth=shibboleth:run',
        ],
    },
)
