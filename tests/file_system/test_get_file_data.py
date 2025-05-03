import os
import sys
import pathlib
import pytest
from unittest.mock import patch, MagicMock, mock_open
from typing import Union

# Add project root to sys.path to allow importing ai_tools
# Adjust the path depth as necessary based on your project structure
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the function to test AFTER modifying sys.path
from ai_tools.file_system.get_file_data import get_file_data, MAX_FILE_SIZE_BYTES, DISALLOWED_PATHS_PATTERNS

# Mock pypdf globally for tests unless specifically un-mocked
MOCK_PYPDF_AVAILABLE = True  # Control pypdf presence for testing PDF_LIB_MISSING
mock_pypdf = MagicMock()
mock_pdf_reader_instance = MagicMock()
mock_pdf_page = MagicMock()
mock_pdf_page.extract_text.return_value = "Mock PDF text page 1. Mock PDF text page 2."
mock_pdf_reader_instance.pages = [mock_pdf_page, mock_pdf_page]  # Simulate two pages

# Conditionally mock based on MOCK_PYPDF_AVAILABLE
if MOCK_PYPDF_AVAILABLE:
    sys.modules['pypdf'] = mock_pypdf
    mock_pypdf.PdfReader.return_value = mock_pdf_reader_instance
else:
    if 'pypdf' in sys.modules:
        del sys.modules['pypdf']
    # Also need to patch the import within the module itself if it was already imported
    patch('ai_tools.file_system.get_file_data.pypdf', None).start()


# --- Fixtures ---

@pytest.fixture
def temp_file(tmp_path: pathlib.Path):
    """Fixture to create a temporary file for testing."""

    def _create_file(filename: str, content: Union[str, bytes] = "Hello, world!", encoding: str = 'utf-8',
                     size_bytes: int = -1):
        file_path = tmp_path / filename
        if size_bytes == -1:
            if encoding is None and isinstance(content, bytes):
                file_path.write_bytes(content)
            elif isinstance(content, str):
                # Default case: write text using specified or default encoding
                file_path.write_text(content, encoding=encoding)
            else:
                # Handle cases where encoding is specified but content is bytes, or other mismatches
                # Might need more specific error handling depending on desired behavior
                raise TypeError(f"Incompatible content type ({type(content).__name__}) and encoding ('{encoding}')")
        else:
            # Create a file of specific size (content might not match if size is large)
            with open(file_path, 'wb') as f:
                # Write some initial content if needed, then fill the rest
                initial_bytes = content.encode(encoding) if isinstance(content, str) else content
                if len(initial_bytes) < size_bytes:
                    f.write(initial_bytes)
                    f.seek(size_bytes - 1)
                    f.write(b'\0')
                else:
                    f.write(initial_bytes[:size_bytes])  # Truncate if initial content is larger
        return str(file_path.resolve())  # Return absolute path as string

    return _create_file


@pytest.fixture
def temp_dir(tmp_path: pathlib.Path):
    """Fixture to create a temporary directory."""
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    return str(dir_path.resolve())


# --- Test Cases ---

# --- Success Cases ---
def test_get_file_data_success_text(temp_file, mocker):
    # Mock disallowed check for temporary paths
    mocker.patch('ai_tools.file_system.get_file_data._is_path_disallowed', return_value=False)
    file_content = "This is a test text file.\nWith multiple lines."
    file_path = temp_file("test.txt", file_content)
    result = get_file_data(file_path)
    assert result == {"data": file_content}


def test_get_file_data_success_code(temp_file, mocker):
    # Mock disallowed check for temporary paths
    mocker.patch('ai_tools.file_system.get_file_data._is_path_disallowed', return_value=False)
    file_content = "def hello():\n    print('Hello')"
    file_path = temp_file("script.py", file_content)
    result = get_file_data(file_path)
    assert result == {"data": file_content}


def test_get_file_data_success_empty_file(temp_file, mocker):
    # Mock disallowed check for temporary paths
    mocker.patch('ai_tools.file_system.get_file_data._is_path_disallowed', return_value=False)
    file_path = temp_file("empty.txt", "")
    result = get_file_data(file_path)
    assert result == {"data": ""}


@patch('ai_tools.file_system.get_file_data.pypdf', mock_pypdf)  # Ensure mock is used
def test_get_file_data_success_pdf(temp_file, mocker):
    # Mock disallowed check for temporary paths
    mocker.patch('ai_tools.file_system.get_file_data._is_path_disallowed', return_value=False)
    if not MOCK_PYPDF_AVAILABLE: pytest.skip("pypdf mock disabled")
    # Reset mock calls for this specific test
    mock_pypdf.reset_mock()
    mock_pdf_reader_instance.reset_mock()
    mock_pdf_page.reset_mock()
    mock_pdf_page.extract_text.return_value = "Mock PDF text. "
    mock_pdf_reader_instance.pages = [mock_pdf_page, mock_pdf_page]
    mock_pypdf.PdfReader.return_value = mock_pdf_reader_instance

    # Create a dummy file (content doesn't matter as pypdf is mocked)
    file_path = temp_file("document.pdf", "dummy pdf content", size_bytes=100)

    # Mock stat size to be > 0 to avoid the empty check path
    mocker.patch("os.stat", return_value=MagicMock(st_size=100))

    result = get_file_data(file_path)
    assert result == {"data": "Mock PDF text. Mock PDF text. "}
    mock_pypdf.PdfReader.assert_called_once()
    assert mock_pdf_page.extract_text.call_count == 2


@patch('ai_tools.file_system.get_file_data.pypdf', mock_pypdf)
def test_get_file_data_success_empty_pdf(temp_file, mocker):
    # Mock disallowed check for temporary paths
    mocker.patch('ai_tools.file_system.get_file_data._is_path_disallowed', return_value=False)
    if not MOCK_PYPDF_AVAILABLE: pytest.skip("pypdf mock disabled")
    mock_pypdf.reset_mock()
    mock_pdf_reader_instance.reset_mock()
    mock_pdf_page.reset_mock()
    mock_pdf_page.extract_text.return_value = ""  # Simulate empty extraction
    mock_pdf_reader_instance.pages = [mock_pdf_page]
    mock_pypdf.PdfReader.return_value = mock_pdf_reader_instance

    file_path = temp_file("empty.pdf", "", size_bytes=0)  # Create 0-byte file

    # Mock stat size to be 0
    mocker.patch("os.stat", return_value=MagicMock(st_size=0))

    result = get_file_data(file_path)
    assert result == {"data": ""}  # Success with empty data for 0-byte pdf
    mock_pypdf.PdfReader.assert_called_once()


# --- Error Cases ---

def test_get_file_data_error_file_not_found(tmp_path):
    non_existent_path = str((tmp_path / "non_existent_file.txt").resolve())
    result = get_file_data(non_existent_path)
    assert result["error_code"] == "FILE_NOT_FOUND"
    assert "does not exist" in result["error_message"]


def test_get_file_data_error_path_is_directory(temp_dir):
    result = get_file_data(temp_dir)
    assert result["error_code"] == "PATH_IS_DIRECTORY"
    assert "points to a directory" in result["error_message"]


def test_get_file_data_error_permission_read(temp_file, mocker):
    # Mock disallowed check for temporary paths
    mocker.patch('ai_tools.file_system.get_file_data._is_path_disallowed', return_value=False)
    file_path = temp_file("restricted.txt")
    # Mock open to raise PermissionError
    mocker.patch("builtins.open", mock_open(read_data=""))  # Need mock_open to avoid real open
    mocker.patch("builtins.open", side_effect=PermissionError("Permission denied"))
    result = get_file_data(file_path)
    assert result["error_code"] == "PERMISSION_ERROR"
    assert "Permission denied" in result["error_message"]


def test_get_file_data_error_decoding(temp_file, mocker):
    # Mock disallowed check for temporary paths
    mocker.patch('ai_tools.file_system.get_file_data._is_path_disallowed', return_value=False)
    # Create file with non-utf8 content
    file_path = temp_file("bad_encoding.txt", b'\x80abc', encoding=None)  # Write raw bytes

    # Mock open specifically for this path to raise UnicodeDecodeError
    original_open = open

    def side_effect_open(*args, **kwargs):
        if args[0] == pathlib.Path(file_path):
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")
        return original_open(*args, **kwargs)

    mocker.patch("builtins.open", side_effect=side_effect_open)

    result = get_file_data(file_path)
    assert result["error_code"] == "DECODING_ERROR"
    assert "Failed to decode" in result["error_message"]


def test_get_file_data_error_unsupported_type(temp_file, mocker):
    # Mock disallowed check for temporary paths
    mocker.patch('ai_tools.file_system.get_file_data._is_path_disallowed', return_value=False)
    file_path = temp_file("image.png", "dummy png")
    result = get_file_data(file_path)
    assert result["error_code"] == "UNSUPPORTED_FILE_TYPE"
    assert "file type ('.png') is not supported" in result["error_message"]


def test_get_file_data_error_file_too_large(temp_file, mocker):
    # Mock disallowed check for temporary paths
    mocker.patch('ai_tools.file_system.get_file_data._is_path_disallowed', return_value=False)
    file_path = temp_file("large_file.txt", size_bytes=MAX_FILE_SIZE_BYTES + 1)
    # Mock stat to return large size (though temp_file creates it, explicit mock is safer)
    mocker.patch("os.stat", return_value=MagicMock(st_size=MAX_FILE_SIZE_BYTES + 1))

    result = get_file_data(file_path)
    assert result["error_code"] == "FILE_TOO_LARGE"
    assert f"exceeds the maximum allowed size" in result["error_message"]


def test_get_file_data_success_file_at_max_size(temp_file, mocker):
    # Mock disallowed check for temporary paths
    mocker.patch('ai_tools.file_system.get_file_data._is_path_disallowed', return_value=False)
    file_content = "Content exactly at limit"
    # Create file exactly at max size
    file_path = temp_file("max_size_file.txt", content=file_content, size_bytes=MAX_FILE_SIZE_BYTES)
    # Mock stat to ensure exact size is reported
    mocker.patch("os.stat", return_value=MagicMock(st_size=MAX_FILE_SIZE_BYTES))

    # Mock open to return the expected content (since size_bytes creation might pad)
    mocked_open = mock_open(read_data=file_content)
    mocker.patch("builtins.open", mocked_open)

    result = get_file_data(file_path)
    assert result == {"data": file_content}


def test_get_file_data_error_relative_path(tmp_path):
    relative_path = "relative_file.txt"
    (tmp_path / relative_path).touch()  # Create the file
    # Intentionally pass the relative path string
    result = get_file_data(relative_path)
    assert result["error_code"] == "RELATIVE_PATH_NOT_SUPPORTED"
    assert "Only absolute file paths are supported" in result["error_message"]


def test_get_file_data_error_invalid_input_type():
    result = get_file_data(123)  # Pass integer instead of string
    assert result["error_code"] == "INVALID_INPUT"
    assert "must be a non-empty string" in result["error_message"]


def test_get_file_data_error_invalid_input_empty():
    result = get_file_data("")  # Pass empty string
    assert result["error_code"] == "INVALID_INPUT"
    assert "must be a non-empty string" in result["error_message"]


@patch('ai_tools.file_system.get_file_data.pypdf', None)  # Simulate pypdf not installed
def test_get_file_data_error_pdf_lib_missing(temp_file, mocker):
    # Mock disallowed check for temporary paths
    mocker.patch('ai_tools.file_system.get_file_data._is_path_disallowed', return_value=False)
    # Must re-patch pypdf inside the local module to None for this test specifically
    with patch('ai_tools.file_system.get_file_data.pypdf', None):
        file_path = temp_file("mydoc.pdf", "dummy pdf content")
        result = get_file_data(file_path)
        assert result["error_code"] == "PDF_LIB_MISSING"
        assert "requires the 'pypdf' library" in result["error_message"]


@patch('ai_tools.file_system.get_file_data.pypdf', mock_pypdf)
def test_get_file_data_error_pdf_parsing_failed(temp_file, mocker):
    # Mock disallowed check for temporary paths
    mocker.patch('ai_tools.file_system.get_file_data._is_path_disallowed', return_value=False)
    if not MOCK_PYPDF_AVAILABLE: pytest.skip("pypdf mock disabled")
    mock_pypdf.reset_mock()
    mock_pdf_reader_instance.reset_mock()
    # Mock PdfReader creation or page extraction to raise an error
    mock_pypdf.PdfReader.side_effect = Exception("Mock pypdf failure")

    file_path = temp_file("broken.pdf", "dummy pdf content")
    mocker.patch("os.stat", return_value=MagicMock(st_size=100))  # Ensure size > 0

    result = get_file_data(file_path)
    assert result["error_code"] == "PDF_PARSING_FAILED"
    assert "Failed to parse the PDF file" in result["error_message"]
    assert "Mock pypdf failure" in result["error_message"]
    mock_pypdf.PdfReader.side_effect = None  # Reset side effect
    mock_pypdf.PdfReader.return_value = mock_pdf_reader_instance  # Restore normal mock


@patch('ai_tools.file_system.get_file_data.pypdf', mock_pypdf)
def test_get_file_data_error_pdf_parsing_failed_empty_result(temp_file, mocker):
    # Mock disallowed check for temporary paths
    mocker.patch('ai_tools.file_system.get_file_data._is_path_disallowed', return_value=False)
    if not MOCK_PYPDF_AVAILABLE: pytest.skip("pypdf mock disabled")
    mock_pypdf.reset_mock()
    mock_pdf_reader_instance.reset_mock()
    mock_pdf_page.reset_mock()
    mock_pdf_page.extract_text.return_value = ""  # Simulate no text extracted
    mock_pdf_reader_instance.pages = [mock_pdf_page]
    mock_pypdf.PdfReader.return_value = mock_pdf_reader_instance

    file_path = temp_file("image_based.pdf", "dummy", size_bytes=500)  # Size > 0
    mocker.patch("os.stat", return_value=MagicMock(st_size=500))  # Mock size > 0

    result = get_file_data(file_path)
    assert result["error_code"] == "PDF_PARSING_FAILED"
    assert "Failed to extract text from the PDF" in result["error_message"]


def test_get_file_data_error_os_error_read(temp_file, mocker):
    # Mock disallowed check for temporary paths
    mocker.patch('ai_tools.file_system.get_file_data._is_path_disallowed', return_value=False)
    file_path = temp_file("os_error.txt")
    # Mock open to raise generic OSError
    mocker.patch("builtins.open", mock_open(read_data=""))
    mocker.patch("builtins.open", side_effect=OSError("Disk read error"))
    result = get_file_data(file_path)
    assert result["error_code"] == "FILE_READ_ERROR"
    assert "An OS error occurred" in result["error_message"]
    assert "Disk read error" in result["error_message"]


def test_get_file_data_error_unknown_processing(temp_file, mocker):
    # Mock disallowed check for temporary paths
    mocker.patch('ai_tools.file_system.get_file_data._is_path_disallowed', return_value=False)
    file_path = temp_file("unknown_error.txt")
    # Mock the read call to raise an unexpected error
    mocked_open = mock_open(read_data="test")
    mocked_open.side_effect = ValueError("Something unexpected")  # Raise non-OSError/PermissionError/UnicodeError
    mocker.patch("builtins.open", mocked_open)

    result = get_file_data(file_path)
    assert result["error_code"] == "UNKNOWN_ERROR"
    assert "An unexpected error occurred" in result["error_message"]
    assert "Something unexpected" in result["error_message"]


def test_get_file_data_error_unknown_setup(mocker):
    # Mock pathlib.Path instantiation to raise an error
    mocker.patch("pathlib.Path", side_effect=Exception("Path setup failed"))
    result = get_file_data("/some/absolute/path.txt")
    assert result["error_code"] == "UNKNOWN_ERROR"
    assert "An unexpected error occurred" in result["error_message"]
    assert "Path setup failed" in result["error_message"] 