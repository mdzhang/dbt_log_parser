test-publish:
	rm -rf dist/
	python3 setup.py sdist bdist_wheel
	pip install twine
	python3 -m twine upload --repository testpypi dist/* -u ${PYPI_USER} -p "${PYPI_PASSWORD}"

prod-publish:
	rm -rf dist/
	python3 setup.py sdist bdist_wheel
	pip install twine
	python3 -m twine upload --repository pypi dist/* -u ${PYPI_USER} -p "${PYPI_PASSWORD}"
