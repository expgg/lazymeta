# Contributing to LazyMeta

Thank you for your interest in contributing to **LazyMeta**! We welcome bug reports, feature enhancements, and documentation improvements.

---

## 🛠️ Development Setup

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/expgg/lazymeta.git
   cd lazymeta
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install Dependencies in Editable Mode**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Run the Test Suite**
   Ensure all tests pass before submitting changes:
   ```bash
   pytest
   ```

---

## 📌 Code Style & Standards

- **Python 3.10+** compatibility.
- Follow **PEP 8** style conventions.
- Never hardcode credentials, access tokens, or test secrets.
- Add unit tests for any new scheduling logic, parsing features, or API error handlers.

---

## 📝 Commit Convention

We follow conventional commit format:
- `feat:` New user-facing feature or enhancement
- `fix:` Bug fix
- `docs:` Documentation updates
- `test:` Adding or updating tests
- `refactor:` Code restructuring without functional changes
- `ci:` Continuous integration changes

---

## 🔒 Reporting Security Issues

If you discover a security vulnerability or credential leak risk, please do **NOT** open a public issue. Instead, report it privately to the maintainers.
