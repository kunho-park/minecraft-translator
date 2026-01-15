.PHONY: release help

# Default target
help:
	@echo "Usage: make release v=v2.0.2"

release:
ifndef v
	$(error Please supply a version number using v=vX.Y.Z)
endif
	@echo "Bumping version to $(v)..."
	python tools/bump_version.py $(v)
	@echo "Creating git tag..."
	git add pyproject.toml gui/__init__.py src/__init__.py
	git commit -m "Release $(v)"
	git tag $(v)
	@echo "Pushing to origin..."
	git push origin HEAD
	git push origin $(v)
	@echo "Release $(v) completed!"

