# Contributing Guide

Thank you for helping improve the Real Estate AI platform.

## Workflow
1. Create a feature branch
2. Make focused changes
3. Add or update tests
4. Run the final validation scripts
5. Open a pull request with a short summary

## Guidelines
- Keep changes small and reviewable
- Prefer organized placement for scripts, tests, and docs
- Avoid adding temporary files to the repository root
- Document behavior changes in the relevant markdown files
- Do not commit generated logs or cache files

## Testing
Run the final validation suite before submitting changes:
- `python tests/test_final_validation.py`

## Style
- Use clear docstrings for public functions
- Prefer explicit error handling
- Keep platform launchers in `scripts/`
