# Release Checklist

## Before Release

- Update version in `pyproject.toml`
- Confirm `README.md` is current
- Confirm `LICENSE` is present
- Confirm package name is available on PyPI
- Commit and push all changes to GitHub

## Local Validation

```powershell
python -m pip install --upgrade pip setuptools wheel build twine
python -m build
python -m twine check dist/*
```

## TestPyPI Publish

```powershell
python -m twine upload --repository testpypi dist/*
```

## PyPI Publish

```powershell
python -m twine upload dist/*
```

## GitHub Actions Secrets

Add these repository secrets in GitHub:

- `TEST_PYPI_API_TOKEN`
- `PYPI_API_TOKEN`

## GitHub Actions Release Flow

- Use `Actions > Publish Python Package` and choose `testpypi` for a dry run
- Create a GitHub Release to publish to PyPI automatically

## After Release

- Verify install from PyPI
- Tag the release in GitHub
- Update changelog or release notes if you maintain them
