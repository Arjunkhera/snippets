# AI Tools

A collection of utilities for AI-related tasks.

## Installation

```bash
pip install akhera-ai-tools
```

## Features

### File System Utilities

The package provides utilities for securely reading file contents:

```python
from ai_tools.file_system.get_file_data import get_file_data

# Read a text file
result = get_file_data('/path/to/file.txt')
if 'data' in result:
    content = result['data']
    # Process content
else:
    error_code = result['error_code']
    error_message = result['error_message']
    # Handle error

# PDF support included
pdf_result = get_file_data('/path/to/document.pdf')
```

## Requirements

- Python 3.6+
- pypdf (for PDF file handling)