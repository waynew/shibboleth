from setuptools import setup, find_packages

with open('shibboleth.py') as f:
    code = compile(f.read(), 'shibboleth.py', 'exec')
    exec(code)

setup(
    name='shibboleth',
    version=__version__,
    author='Wayne Werner',
    author_email='waynejwerner@gmail.com',
    url='https://github.com/waynew/shibboleth',
    py_modules=['shibboleth'],
    entry_points = {
        'console_scripts': [
            'shibboleth=shibboleth:run',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Programming Language :: Python :: 3.6',
        'Topic :: Office/Business',
        'Topic :: Utilities',
    ],
)
