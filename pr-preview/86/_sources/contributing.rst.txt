Contributing
============

Contributions to py-dem-bones are welcome! Here's how you can contribute:

Setting Up Development Environment
---------------------------------

1. Clone the repository:

   .. code-block:: bash

       git clone https://github.com/loonghao/py-dem-bones.git
       cd py-dem-bones

2. Create a virtual environment and install development dependencies:

   .. code-block:: bash

       python -m venv venv
       source venv/bin/activate  # On Windows: venv\Scripts\activate
       pip install -e ".[dev]"

3. Install pre-commit hooks:

   .. code-block:: bash

       pre-commit install

Development Workflow
------------------

1. Create a new branch for your feature or bugfix:

   .. code-block:: bash

       git checkout -b feature/your-feature-name

2. Make your changes and write tests for them.

3. Run the tests to make sure everything works:

   .. code-block:: bash

       pytest

4. Build the documentation to ensure it's correct:

   .. code-block:: bash

       cd docs
       make html

5. Commit your changes and push them to your fork:

   .. code-block:: bash

       git commit -m "Add your feature description"
       git push origin feature/your-feature-name

6. Create a pull request on GitHub.

Code Style
---------

This project follows the Google Python Style Guide. We use ``ruff`` for linting and formatting.

To check your code style:

.. code-block:: bash

    ruff check .

To automatically fix style issues:

.. code-block:: bash

    ruff format .

Building the Documentation
------------------------

The documentation is built using Sphinx. To build it locally:

.. code-block:: bash

    cd docs
    make html

The built documentation will be in ``docs/_build/html``.

Running Tests
-----------

We use pytest for testing. To run the tests:

.. code-block:: bash

    pytest

To run tests with coverage:

.. code-block:: bash

    pytest --cov=py_dem_bones

Releasing
--------

1. Update the version number in ``pyproject.toml`` and ``src/py_dem_bones/__init__.py``.
2. Update the changelog.
3. Commit the changes:

   .. code-block:: bash

       git commit -m "Bump version to x.y.z"

4. Tag the release:

   .. code-block:: bash

       git tag -a vx.y.z -m "Version x.y.z"

5. Push the changes and tag:

   .. code-block:: bash

       git push origin main --tags

The GitHub Actions workflow will automatically build and publish the release to PyPI.
