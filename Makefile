publish:
	python3 setup.py sdist bdist_wheel
	pip install twine
	python3 -m twine upload --repository testpypi dist/* -u ${PYPI_USER} -p "${PYPI_PASSWORD}"

