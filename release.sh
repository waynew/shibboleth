#!/bin/sh
set -e
python3 test_shibboleth.py
if [ $? -ne 0 ]; then
    echo "Tests failed"
    exit
fi
pyproject-build
twine check dist/shibboleth-$(python3 shibboleth.py version)-py3-none-any.whl
git tag -a $(python3 shibboleth.py version)
twine upload --config-file $HOME/.pypirc -u __token__ -r shibboleth dist/shibboleth-$(python3 shibboleth.py version)-py3-none-any.whl
