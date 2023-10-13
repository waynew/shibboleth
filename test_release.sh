#!/bin/sh
set -e
python test_shibboleth.py
if [ $? -ne 0 ]; then
    echo "Tests failed"
    exit
fi
python -m build
twine check dist/shibboleth-$(python shibboleth.py version)-py3-none-any.whl
git tag -a $(python shibboleth.py version)
twine upload --config-file $HOME/.pypirc -u __token__ -r test_shibboleth dist/shibboleth-$(python shibboleth.py version)-py3-none-any.whl --verbose
