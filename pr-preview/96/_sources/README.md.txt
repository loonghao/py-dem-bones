# py-dem-bones Documentation

This directory contains the documentation for the py-dem-bones project.

## Building the Documentation

To build the documentation locally, you can use the following command:

```bash
python -m nox -s docs
```

This will build the documentation in the `docs/_build/html` directory.

## Serving the Documentation

To serve the documentation locally with live reloading, you can use the following command:

```bash
python -m nox -s docs-server
```

This will start a local web server and open the documentation in your default web browser.

## Documentation Structure

- `conf.py`: Sphinx configuration file
- `index.rst`: Main documentation page
- `api.rst`: API documentation
- `examples.rst`: Examples documentation
- `_static/`: Static files (CSS, JavaScript, images)
- `_build/`: Build directory (generated)

## GitHub Pages Deployment

The documentation is automatically deployed to GitHub Pages when changes are pushed to the main branch. Pull requests also get a preview deployment.

- Main branch documentation: https://loonghao.github.io/py-dem-bones/latest/
- PR preview: https://loonghao.github.io/py-dem-bones/pr-preview/{PR_NUMBER}/

## Notes for Windows Users

When building the documentation on Windows, the `cairosvg` package is not required and will be skipped. The documentation will still build correctly, but SVG images will be replaced with placeholder images.

On Linux (including CI environments), the `cairosvg` package will be installed and used to convert SVG images to PNG.
