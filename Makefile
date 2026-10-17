.PHONY: setup demo eval

setup:
	pip install -r requirements.txt

demo:
	python main.py

eval:
	python -m tests.run_tests
