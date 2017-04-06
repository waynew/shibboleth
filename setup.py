from setuptools import setup, find_packages

with open('shibboleth.py') as f:
    code = compile(f.read(), 'shibboleth.py', 'exec')
    exec(code)

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='shibboleth',
    version=__version__,
    author='Wayne Werner',
    author_email='waynejwerner@gmail.com',
    url='https://github.com/waynew/shibboleth',
    py_modules=['shibboleth'],
    long_description=read('README.rst'),
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
