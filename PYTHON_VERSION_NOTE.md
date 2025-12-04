# Python Version Compatibility Note

## Current Status

**Supported Python Versions:** 3.11, 3.12, 3.13  
**Not Supported:** Python 3.14

## Why Python 3.14 is Not Supported

The project dependencies include `pydantic` which requires `pydantic-core`, a Rust-based library that uses PyO3 bindings. As of December 2024:

- PyO3 v0.22.6 (used by pydantic-core) only supports Python up to 3.13
- Python 3.14 was released very recently and library support is still catching up
- The `PYO3_USE_ABI3_FORWARD_COMPATIBILITY` flag doesn't fully resolve the compatibility issues

## Recommended Action

**For Development:**
Use Python 3.11, 3.12, or 3.13. We recommend Python 3.11 as it matches the AWS App Runner deployment target.

**Installation:**
```bash
# Check your Python version
python --version

# If you have Python 3.14, install Python 3.11-3.13
# On Windows: Download from python.org
# On macOS: brew install python@3.11
# On Linux: Use your package manager (apt, yum, etc.)
```

## Future Compatibility

This limitation will be resolved when:
1. PyO3 releases a version supporting Python 3.14, AND
2. pydantic-core updates to use the new PyO3 version, AND
3. pydantic updates to use the new pydantic-core version

Monitor these issues:
- PyO3: https://github.com/PyO3/pyo3
- pydantic: https://github.com/pydantic/pydantic

## Deployment Note

AWS App Runner uses Python 3.11 runtime, so this limitation does not affect production deployment.
