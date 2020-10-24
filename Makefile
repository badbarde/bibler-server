start: 
	uvicorn src.bibler.biblerAPI:bibler --reload

activate:
	- source /home/barde/git/BIBler/BIBler-server/BIBlerServer/bin/activate

test: activate
	pytest src -vv
coverage: 
	coverage run --source=bibler -m pytest src -vv
coverage-report: coverage
	coverage report -m
coverage-html: coverage
	coverage html
	firefox htmlcov/index.html