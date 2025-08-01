# Contributing to Regalator WMS

Thank you for your interest in contributing to Regalator WMS! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### 1. Fork the Repository
1. Go to [https://github.com/yourusername/regalator](https://github.com/yourusername/regalator)
2. Click the "Fork" button in the top right corner
3. Clone your forked repository to your local machine

### 2. Set Up Development Environment
```bash
# Clone your fork
git clone https://github.com/yourusername/regalator.git
cd regalator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements.txt[dev]

# Set up pre-commit hooks
pre-commit install
```

### 3. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes
- Follow the coding standards outlined below
- Write tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 5. Commit Your Changes
```bash
git add .
git commit -m "feat: add new feature description"
```

### 6. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## 📋 Development Guidelines

### Code Style
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions small and focused

### Django Conventions
- Follow Django's coding style
- Use Django's built-in features when possible
- Write model methods for business logic
- Use Django's ORM efficiently

### Testing
- Write tests for all new functionality
- Maintain test coverage above 80%
- Use descriptive test names
- Test both success and error cases

### Documentation
- Update README.md for new features
- Add docstrings to new functions
- Update API documentation if applicable
- Include usage examples

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test wms
python manage.py test subiekt

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Code Quality Checks
```bash
# Format code
black regalator/

# Sort imports
isort regalator/

# Lint code
flake8 regalator/

# Type checking (if using mypy)
mypy regalator/
```

## 🐛 Bug Reports

### Before Reporting
1. Check if the issue has already been reported
2. Try to reproduce the issue with the latest version
3. Check the documentation and existing issues

### Bug Report Template
```markdown
**Bug Description**
A clear description of what the bug is.

**Steps to Reproduce**
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

**Expected Behavior**
A clear description of what you expected to happen.

**Actual Behavior**
A clear description of what actually happened.

**Environment**
- OS: [e.g. Windows 10, macOS 12]
- Python Version: [e.g. 3.9.7]
- Django Version: [e.g. 4.2.0]
- Browser: [e.g. Chrome 91]

**Additional Context**
Add any other context about the problem here.
```

## 💡 Feature Requests

### Feature Request Template
```markdown
**Feature Description**
A clear description of the feature you'd like to see.

**Use Case**
Describe the specific use case or problem this feature would solve.

**Proposed Solution**
Describe your proposed solution or implementation approach.

**Alternative Solutions**
Describe any alternative solutions you've considered.

**Additional Context**
Add any other context, screenshots, or examples.
```

## 📝 Pull Request Guidelines

### Before Submitting
- [ ] Code follows the project's style guidelines
- [ ] All tests pass
- [ ] New tests are added for new functionality
- [ ] Documentation is updated
- [ ] No sensitive data is included

### Pull Request Template
```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

## Checklist
- [ ] I have read the [CONTRIBUTING.md](CONTRIBUTING.md) file
- [ ] My code follows the project's coding standards
- [ ] I have tested my changes thoroughly
- [ ] I have updated the documentation as needed
```

## 🏷️ Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

### Examples
```
feat: add product sync functionality
fix: resolve database connection issue
docs: update installation instructions
style: format code according to PEP 8
```

## 🎯 Areas for Contribution

### High Priority
- Bug fixes
- Security improvements
- Performance optimizations
- Documentation improvements

### Medium Priority
- New features
- UI/UX improvements
- Test coverage improvements
- Code refactoring

### Low Priority
- Cosmetic changes
- Minor documentation updates
- Code style improvements

## 📞 Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: support@regalator.com
- **Documentation**: Check the README.md and inline code documentation

## 🙏 Recognition

Contributors will be recognized in:
- The project's README.md file
- Release notes
- The project's website (if applicable)

Thank you for contributing to Regalator WMS! 🚀 