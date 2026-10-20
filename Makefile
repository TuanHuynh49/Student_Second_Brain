.PHONY: setup demo eval plot

setup:
	pip install -r requirements.txt

demo:
	python main.py

eval:
	python -m tests.run_tests

plot:
	python -m src.evaluation.export_benchmark
