CI/CD and releases
==================

Pull requests run the configured build, lint, documentation, and version
consistency workflows. The source of truth for the released version is
``.release-please-manifest.json``. release-please updates ``pyproject.toml``,
``src/py_dem_bones/__version__.py``, documentation and citation metadata in
the release pull request. CI checks that these surfaces agree.

Release sequence
----------------

1. Merge a Conventional Commit (for example ``feat: add DCC adapter`` or
   ``fix: validate pose layout``) to ``main``.
2. ``release-please.yml`` opens or updates a release pull request with the
   proposed version and changelog. Review its diff and CI results.
3. Merge the release pull request. release-please creates ``vX.Y.Z`` and a
   GitHub Release.
4. The tag triggers ``release.yml``. The workflow checks the tag against
   ``pyproject.toml``, builds and tests wheels and a source distribution,
   attaches artifacts to the GitHub Release, then publishes to PyPI through
   Trusted Publishing.

``RELEASE_PLEASE_TOKEN`` (or ``PERSONAL_ACCESS_TOKEN``) must be a token
permitted to create release pull requests and tags. GitHub's default
``GITHUB_TOKEN`` does not trigger downstream workflows when it creates a tag.
PyPI Trusted Publishing must trust this repository and its ``release``
environment. Publication requires successful artifact jobs on the exact tag.

The release workflow can also be dispatched manually for build diagnosis;
manual dispatch does not publish a new package. Never edit version files or
create a release tag by hand as part of normal publication.
