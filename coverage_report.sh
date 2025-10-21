#!/usr/bin/env bash
pytest --cov=. --cov-report=term-missing
coverage html
echo "✅ Coverage HTML generated at htmlcov/index.html"