install:
	pip install -r requirements.txt

run:
	flask run

db-init:
	python init_db.py

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache