from ai_tools.file_system.get_file_data import get_file_data

# Read a text file
result = get_file_data('/Users/akhera/Desktop/Repositories/document-service/document-da/src/main/java/com/intuit/fds/fdp/authorization/service/ShareService.java')

if 'data' in result:
    content = result['data']
    # Process content
else:
    error_code = result['error_code']
    error_message = result['error_message']
    # Handle error

# PDF support included
pdf_result = get_file_data('/path/to/document.pdf')

print(pdf_result)