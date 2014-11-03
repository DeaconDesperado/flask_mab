test:
	python setup.py nosetests

upload_docs:
	PYTHONPATH=./ sphinx-build docs doc
	python setup.py upload_docs
