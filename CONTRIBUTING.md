# Contributing to py-dem-bones

Thank you for considering contributing to py-dem-bones! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on our [GitHub issue tracker](https://github.com/loonghao/py-dem-bones/issues) with the following information:

- A clear, descriptive title
- A detailed description of the issue
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment information (OS, Python version, etc.)

### Suggesting Enhancements

We welcome suggestions for enhancements! Please create an issue with:

- A clear, descriptive title
- A detailed description of the proposed enhancement
- Any relevant examples or use cases

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Run tests to ensure your changes don't break existing functionality
5. Commit your changes (`git commit -m 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature-name`)
7. Create a new Pull Request

## Development Setup

### Prerequisites

- Python 3.7 or higher
- C++ compiler (GCC, Clang, or MSVC)
- CMake 3.15 or higher
- Eigen3
- Git

### Installation for Development

1. Clone the repository:
   ```bash
   git clone https://github.com/loonghao/py-dem-bones.git
   cd py-dem-bones
   ```

2. Install the package in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Running Tests

```bash
pytest
```

Or use nox:

```bash
nox -s pytest
```

### Building Documentation

```bash
nox -s docs
```

To serve the documentation with live reloading:

```bash
nox -s docs-serve
```

## Coding Standards

- Follow PEP 8 for Python code
- Use Google-style docstrings
- Write tests for new features
- Keep the code clean and maintainable

## License

By contributing to py-dem-bones, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
