# Contributing to NexusCore

Thank you for considering contributing to NexusCore.

## How to Contribute

1. **Open an issue** first for bugs, enhancements, or design changes.
2. **Fork the repository** and create a feature branch (`git checkout -b feature/my-feature`).
3. **Write clear commit messages** following [Conventional Commits](https://www.conventionalcommits.org/).
4. **Add or update tests** when changing behavior.
5. **Run linting and tests** before submitting a pull request:

   ```bash
   cd backend
   ruff check .
   ruff format --check .
   pytest
   ```

6. **Open a Pull Request** with a clear description and link to the issue.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Violations can be reported to info@jorahone.com.

## Style Guidelines

- Use Python 3.12+ syntax.
- Follow the existing project structure and naming conventions.
- Keep functions small and focused.
- Document public APIs and environment variables.
