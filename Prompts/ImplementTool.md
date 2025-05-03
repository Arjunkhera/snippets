Please implement the Python function for the tool defined in the following Markdown specification.

**Tool Definition:**

```markdown
{PASTE_MARKDOWN_TOOL_DEFINITION_HERE}
```

**Instructions for the AI:**

1.  **Understand the Definition:** Carefully read the provided Markdown tool definition above.
2.  **Identify Key Elements:** Extract the function name, description, parameters (including name, type, requirement, description), success output structure, and all defined error output structures (including error codes and conditions) from the Markdown.
3.  **‼️ Ask for Clarification:** If any part of the tool definition (parameters, logic, error handling, constraints, output formats) is ambiguous, unclear, or seems incomplete, **STOP and ask clarifying questions** before proceeding with the implementation. Do *not* make assumptions about unclear requirements.
4.  **Implement the Function:** Once all requirements are clear, write the Python code for the function specified in the definition.
    *   The function signature should match the defined parameters (name, type hints).
    *   The implementation must strictly adhere to the logic described.
    *   **Crucially, ensure the Python function's signature (parameter names, type hints) and its docstring accurately reflect the details provided in the input Markdown and OpenAI JSON schema specifications.**
5.  **Handle Inputs:** Process input parameters according to their specified types and requirements.
6.  **Success Output:** On successful execution, return a dictionary matching the exact structure and data types defined in the "Success Output" section.
7.  **Error Handling:** Implement robust error handling. For each potential error condition identified in the "Error Output" or "Constraints and Behaviors" sections:
    *   Return a dictionary matching the exact error structure specified.
    *   Use the precise error codes defined in the documentation.
8.  **Constraints & Behaviors:** Strictly enforce all constraints and behaviors mentioned (e.g., input validation, size limits, specific logic).
9.  **Imports:** Include all necessary standard Python library imports (e.g., `os`, `json`, `datetime`). If the tool requires external libraries (as indicated in the description or constraints), clearly state these dependencies (e.g., using a comment `# Requires: library_name`).
10. **Docstrings:** Add a clear docstring to the Python function explaining its purpose, arguments (based on the parameters in the definition), return value (describing both success and error dictionary structures), and any specific behaviors or potential issues noted in the definition.
11. **Code Quality:** Write clean, readable, and efficient Python code. 
12. **Unit Tests:** 
    *   Write comprehensive unit tests for the implemented function using the `pytest` framework.
    *   Create a corresponding test file under a top-level `tests/` directory that mirrors the structure of the `ai_tools` package (e.g., code in `ai_tools/file_utils/fetch.py` should have tests in `tests/file_utils/test_fetch.py`).
    *   Tests should cover:
        *   Successful execution paths.
        *   Each defined error condition (ensure the correct error code and message format are returned).
        *   Edge cases mentioned in the constraints or implied by the logic (e.g., empty files, files at size limits, different encodings if applicable).
    *   Use mocking (`unittest.mock` or `pytest-mock`) where appropriate to isolate the function being tested from external dependencies (like file system interactions or external libraries). 