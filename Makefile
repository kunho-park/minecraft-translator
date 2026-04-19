.PHONY: release help

# Default target
help:
	@echo "Usage: make release v=v2.0.2"

# Clean version for internal use (removes leading v if present)
CLEAN_VERSION := $(patsubst v%,%,$(v))
# Tag version for git (always starts with v)
TAG_VERSION := v$(CLEAN_VERSION)

release:
ifndef v
	$(error Please supply a version number using v=vX.Y.Z)
endif
	@echo "Bumping version to $(TAG_VERSION)..."
	python tools/bump_version.py $(TAG_VERSION)
	@echo "Creating git tag..."
	git add pyproject.toml gui/__init__.py src/__init__.py
	git commit -m "Release $(TAG_VERSION)"
	git tag $(TAG_VERSION)
	@echo "Pushing to origin..."
	git push origin HEAD
	git push origin $(TAG_VERSION)
	@echo "Release $(TAG_VERSION) completed!"

