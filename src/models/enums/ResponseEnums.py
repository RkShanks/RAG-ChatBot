from enum import Enum


class ResponseSignal(Enum):
    FILE_VALIDATION_FAILED = "file_validation_failed"
    FILE_VALIDATION_SUCCESS = "file_validation_success"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    FILE_UPLOADED_SUCCESSFULLY = "file_uploaded_successfully"
    FILE_UPLOADED_FAILED = "file_uploaded_failed"
    WIKI_SEARCH_RESULTS_FOUND = "wiki_search_results_found"
    WIKI_SEARCH_NO_RESULTS = "wiki_search_no_results"
    WIKI_FILE_UPLOADED_SUCCESSFULLY = "wiki_file_uploaded_successfully"
    WIKI_FILE_UPLOAD_FAILED = "wiki_file_upload_failed"
    FILE_NOT_FOUND = "file_not_found"
    CHUNKING_SUCCESS = "chunking_success"