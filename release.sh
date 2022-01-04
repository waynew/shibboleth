#!/bin/sh
set -e
python3 test_shibboleth.py
if [ $? -ne 0 ]; then
    echo "Tests failed"
    exit
fi
twine check dist/shibboleth-$(python3 shibboleth.py version)-py3-none-any.whl
twine upload --config-file $HOME/.pypirc -u __token__ -r shibboleth dist/shibboleth-$(python3 shibboleth.py version)-py3-none-any.whl
