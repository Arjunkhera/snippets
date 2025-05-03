# Tool: get_file_data

**Description:**

Takes the absolute path of a file stored on the local machine and returns its text contents as a string. It differentiates behavior based on file type: directly reads text/code files (assuming UTF-8), parses PDF files to extract text, and rejects unsupported types like images or binaries based on their extension. It also enforces security restrictions by disallowing access to common system directories and limits the maximum file size.

**Function Name:**

`get_file_data`

**Input Parameters:**

*   **`file_path`** (`str`, Required): The absolute path to the text, code, or PDF file to be read.

**Success Output:**

Upon successful execution, returns a dictionary with a single key:

*   `data` (`str`): The text content of the file. For text/code files, this is the raw content decoded as UTF-8. For PDF files, this is the text extracted by the parser.

Example Success Output:
```json
{
  "data": "This is the content of the file..."
}
```

**Error Outputs:**

If an error occurs, the tool returns a dictionary containing `error_code` and `error_message`:

*   **File Not Found:**
    ```json
    {
      "error_code": "FILE_NOT_FOUND",
      "error_message": "The specified file path does not exist."
    }
    ```
*   **Path is Directory:**
    ```json
    {
      "error_code": "PATH_IS_DIRECTORY",
      "error_message": "The specified path points to a directory, not a file."
    }
    ```
*   **Permission Denied:**
    ```json
    {
      "error_code": "PERMISSION_ERROR",
      "error_message": "Permission denied when trying to read the file."
    }
    ```
*   **Decoding Error (Text/Code Files):**
    ```json
    {
      "error_code": "DECODING_ERROR",
      "error_message": "Failed to decode the file content (for non-PDF text/code files), possibly not standard UTF-8 text."
    }
    ```
*   **PDF Parsing Failed:**
    ```json
    {
      "error_code": "PDF_PARSING_FAILED",
      "error_message": "Failed to parse the PDF file."
    }
    ```
*   **Unsupported File Type:**
    ```json
    {
      "error_code": "UNSUPPORTED_FILE_TYPE",
      "error_message": "The file type (based on extension) is not supported (e.g., image, binary). Only text, code, and PDF files are processed."
    }
    ```
*   **File Too Large:**
    ```json
    {
      "error_code": "FILE_TOO_LARGE",
      "error_message": "The file exceeds the maximum allowed size of 30MB."
    }
    ```
*   **Disallowed Path:**
    ```json
    {
      "error_code": "DISALLOWED_PATH",
      "error_message": "Accessing the specified path is disallowed for security reasons."
    }
    ```
*   **Unknown Error:**
    ```json
    {
      "error_code": "UNKNOWN_ERROR",
      "error_message": "An unexpected error occurred while trying to read the file."
    }
    ```

**Constraints & Behaviors:**

*   **Maximum File Size:** 30MB. Files larger than this will trigger the `FILE_TOO_LARGE` error.
*   **File Type Handling:** Determined primarily by file extension.
    *   **Supported Text/Code:** Attempts direct read and UTF-8 decoding (e.g., `.txt`, `.py`, `.java`, `.md`, `.json`, `.xml`, `.csv`, `.html`, `.css`, `.js`).
    *   **Supported PDF:** Attempts text extraction using a PDF parser (e.g., `.pdf`).
    *   **Unsupported:** Rejects common image, binary, and archive extensions (e.g., `.png`, `.jpg`, `.gif`, `.exe`, `.zip`, `.tar.gz`) with `UNSUPPORTED_FILE_TYPE` error.
*   **Security:** Access to certain system paths is blocked. Attempts to access files within disallowed directories (e.g., `/etc/`, `/var/`, `C:\Windows\`) will result in the `DISALLOWED_PATH` error. The specific list of disallowed paths is implementation-dependent but covers common system/sensitive directories.
*   **Path Requirement:** Requires an absolute file path. 