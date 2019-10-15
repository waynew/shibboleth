#!/bin/sh
set -e
python3 setup.py bdist_wheel
twine check dist/shibboleth-$(python3 shibboleth.py version)-py3-none-any.whl
git tag $(python3 shibboleth.py version)
twine upload --config-file $HOME/.pypirc -u __token__ -r shibboleth dist/shibboleth-$(python3 shibboleth.py version)-py3-none-any.whl
