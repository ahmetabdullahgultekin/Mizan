# Contributing to Mizan

Thank you for your interest in contributing to Mizan Core Engine! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Scholarly Accuracy](#scholarly-accuracy)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker & Docker Compose
- Git

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/mizan.git
   cd mizan
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/mizan.git
   ```

## Development Setup

### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Start Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d db redis

# Run migrations
alembic upgrade head

# Start the API (development mode)
uvicorn mizan.api.main:app --reload
```

### Verify Setup

```bash
# Run tests
pytest

# Run linting
ruff check src/
mypy src/mizan
```

## Making Changes

### Branch Naming

Create a descriptive branch name:

- `feature/add-root-extraction` - New features
- `fix/abjad-calculation-error` - Bug fixes
- `docs/update-api-reference` - Documentation
- `refactor/simplify-letter-counter` - Code refactoring
- `test/add-property-tests` - Test additions

### Workflow

1. Create a new branch from `main`:
   ```bash
   git checkout main
   git pull upstream main
   git checkout -b feature/your-feature-name
   ```

2. Make your changes in small, logical commits

3. Write or update tests as needed

4. Ensure all tests pass:
   ```bash
   pytest
   ```

5. Run linting and formatting:
   ```bash
   ruff check src/ --fix
   ruff format src/
   mypy src/mizan
   ```

## Submitting Changes

### Pull Request Process

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Create a Pull Request on GitHub

3. Fill out the PR template completely

4. Wait for review and address any feedback

### PR Requirements

- [ ] All tests pass
- [ ] Code follows project style guidelines
- [ ] Documentation is updated if needed
- [ ] Commit messages are clear and descriptive
- [ ] PR description explains the changes

### Commit Messages

Follow conventional commits format:

```
type(scope): brief description

Longer explanation if needed.

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Example:
```
feat(abjad): add Maghribi numeral system support

Implements the Western/Maghribi Abjad numeral system
as an alternative to the default Mashriqi system.

Closes #45
```

## Coding Standards

### Python Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use Ruff for linting and formatting

### Architecture

- Follow Hexagonal Architecture principles
- Domain layer must have no external dependencies
- Use dependency injection for infrastructure
- Keep functions small and focused

### Naming Conventions

- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

### Docstrings

Use Google-style docstrings:

```python
def calculate_abjad(text: str, system: AbjadSystem) -> AbjadValue:
    """Calculate the Abjad value of Arabic text.

    Args:
        text: Arabic text to analyze.
        system: The Abjad numeral system to use.

    Returns:
        AbjadValue containing the calculated value and breakdown.

    Raises:
        ValueError: If the text contains no Arabic letters.
    """
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Unit tests (no external dependencies)
│   └── domain/     # Domain layer tests
├── integration/    # Integration tests (with database/cache)
└── property/       # Property-based tests (Hypothesis)
```

### Writing Tests

- Test one thing per test function
- Use descriptive test names
- Include both positive and negative cases
- Use fixtures for common setup

```python
class TestAbjadCalculator:
    """Tests for AbjadCalculator service."""

    def test_calculate_allah_returns_66(self, calculator: AbjadCalculator):
        """Test that 'Allah' calculates to 66."""
        result = calculator.calculate("الله", AbjadSystem.MASHRIQI)
        assert result.value == 66

    def test_calculate_empty_string_raises_error(self, calculator: AbjadCalculator):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError):
            calculator.calculate("", AbjadSystem.MASHRIQI)
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src/mizan --cov-report=html

# Specific file
pytest tests/unit/domain/test_services.py

# Specific test
pytest -k "test_calculate_allah"
```

## Documentation

### Code Documentation

- All public functions/classes must have docstrings
- Complex logic should have inline comments
- Update README.md for user-facing changes

### API Documentation

- FastAPI auto-generates OpenAPI docs
- Add descriptive summaries to endpoints
- Include example requests/responses

## Scholarly Accuracy

### Critical Requirement

Mizan is a scholarly tool. **Accuracy is paramount.**

### Before Changing Calculations

1. **Research the standard**: Verify against authoritative sources
2. **Document your sources**: Add references in code comments
3. **Test against known values**: Use verified scholarly data
4. **Update STANDARDS.py**: Document any new standards

### Authoritative Sources

- [Tanzil.net](https://tanzil.net) - Primary Quran text
- [Quran.com](https://quran.com) - Quranic Arabic Corpus
- Classical Islamic scholarship (Ibn Kathir, etc.)
- Academic papers on Quranic studies

### Verification Process

When modifying counting or calculation logic:

```python
# VERIFIED: Al-Fatiha = 139 letters
# Source: Tanzil.net, Modern computational standard
# Date verified: 2025-01-XX
def count_letters(self, text: str) -> int:
    ...
```

## Questions?

- Open an issue for questions
- Join discussions on GitHub
- Tag maintainers for urgent matters

---

Thank you for contributing to Mizan!

**بارك الله فيكم** - *May Allah bless you*
