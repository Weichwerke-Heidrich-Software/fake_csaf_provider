# Python Style Guide

## String Quotation Marks

**Rule: Prefer single quotes (`'`) for string literals.**

### Guidelines:

1. **Default**: Use single quotes for all string literals
   ```python
   name = 'example'
   path = '/usr/local/bin'
   ```

2. **Exception - Apostrophes**: Use double quotes when the string contains single quotes/apostrophes
   ```python
   message = "don't forget"
   text = "it's working"
   ```

3. **Exception - Nested quotes**: Alternate quote types to avoid escaping
   ```python
   # In f-strings, use double quotes inside single-quoted f-strings
   f'{function("argument")}'
   ```

4. **Docstrings**: Use triple double-quotes (PEP 257 convention)
   ```python
   """This is a docstring."""
   ```

5. **Consistency**: When both quote types are equally valid, prefer single quotes for consistency
