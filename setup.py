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
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    entry_points = {
        'console_scripts': [
            'shibboleth=shibboleth:run',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Office/Business',
        'Topic :: Utilities',
    ],
)
