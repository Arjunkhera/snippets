# Publishing to PyPI

Follow these steps to build and publish your package to PyPI:

## 1. Install build tools

```bash
pip install build twine
```

## 2. Build the package

Navigate to the repository root (where setup.py is located) and run:

```bash
python3 -m build
```

This will create both source distribution (.tar.gz) and wheel distribution (.whl) files in the dist/ directory.

## 3. Test your package

Before uploading to PyPI, you can install the package locally to test it:

```bash
pip install dist/akhera_ai_tools-0.1.0-py3-none-any.whl
```

## 4. Upload to Test PyPI (Optional but recommended)

Test PyPI is a separate instance of the package index intended for testing and experimentation:

```bash
python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

You'll need to create an account on Test PyPI if you don't have one.

## 5. Install from Test PyPI

```bash
pip3 install --index-url https://test.pypi.org/simple/ akhera-ai-tools
```

## 6. Upload to production PyPI

Once you've verified everything works correctly:

```bash
python3 -m twine upload dist/*
```

You'll need a PyPI account for this step.

## 7. Install from PyPI

After uploading, anyone can install your package with:

```bash
pip install akhera-ai-tools
```

## Important Notes

1. Package naming: Ensure your package name isn't already taken on PyPI
2. Version numbers: Follow semantic versioning (MAJOR.MINOR.PATCH)
3. Update version: Remember to update the version number in both setup.py and pyproject.toml for new releases 