# Contributing to MedicalSpy

Thank you for considering contributing to MedicalSpy! Here are the guidelines for contributing to the project.

## Development Environment Setup

1. Fork the repository and clone your fork:
   ```bash
   git clone https://github.com/your-username/medicalspy.git
   cd medicalspy
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r project_requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file and set the appropriate values
   ```

4. Test the application:
   ```bash
   python run_tests.py
   ```

5. Run the application:
   ```bash
   python run.py
   ```

## Code Style

- Follow PEP 8 style guidelines for Python code.
- Use docstrings for all functions, classes, and modules.
- Keep line length to a maximum of 100 characters.
- Include type hints where appropriate.

## Pull Request Process

1. Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. Make your changes and commit them with clear, descriptive messages.

3. Push your branch to your fork:
   ```bash
   git push origin feature/my-new-feature
   ```

4. Submit a pull request from your branch to the main repository's main branch.

5. Ensure your PR includes:
   - A clear description of the changes
   - Any relevant issue numbers
   - Updates to documentation if necessary
   - Passing tests for your changes

## Testing

- Write tests for new features and bug fixes.
- Run the test suite before submitting a PR:
  ```bash
  python run_tests.py
  ```

## Database Changes

- Use SQLAlchemy models for all database operations.
- Test migrations thoroughly before submitting.
- Document any schema changes in your PR description.

## API Documentation

- Update API documentation for any new or modified endpoints.
- Document parameters, return values, and status codes.

## Reporting Bugs

- Use the issue tracker to report bugs.
- Include detailed steps to reproduce the issue.
- Mention your OS, Python version, and any relevant environment details.

## Feature Requests

- Use the issue tracker to suggest new features.
- Clearly describe the feature and its benefits.
- If possible, outline a potential implementation approach.

## Code of Conduct

- Be respectful and inclusive in your interactions.
- Welcome contributors of all backgrounds and skill levels.
- Focus on constructive feedback and collaboration.

Thank you for contributing to MedicalSpy!