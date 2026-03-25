from enum import Enum


class ResponseSignal(Enum):
    FILE_VALIDATION_FAILED = "file_validation_failed"
    FILE_VALIDATION_SUCCESS = "file_validation_success"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    FILE_UPLOADED_SUCCESSFULLY = "file_uploaded_successfully"
    FILE_UPLOADED_FAILED = "file_uploaded_failed"
    FILE_NOT_FOUND = "file_not_found"

    WIKI_SEARCH_RESULTS_FOUND = "wiki_search_results_found"
    WIKI_SEARCH_NO_RESULTS = "wiki_search_no_results"
    WIKI_FILE_UPLOADED_SUCCESSFULLY = "wiki_file_uploaded_successfully"
    WIKI_FILE_UPLOAD_FAILED = "wiki_file_upload_failed"
    WIKI_SEARCH_ERROR = "wiki_search_error"

    DB_CONNECTION_SUCCESS = "db_connection_success"
    DB_CONNECTION_FAILED = "db_connection_failed"

    CHUNKING_SUCCESS = "chunking_success"
    CHUNKING_FAILED = "chunking_failed"
    CHUNK_INSERTION_SUCCESSFUL = "chunk_insertion_successful"
    CHUNK_INSERTION_FAILED = "chunk_insertion_failed"
    CHUNK_DELETION_FAILED = "chunk_deletion_failed"
    CHUNK_DELETION_SUCCESSFUL = "chunk_deletion_successful"

    COLLECTION_CREATION_FAILED = "collection_creation_failed"
    COLLECTION_INFO_SUCCESSFUL = "collection_info_successful"
    COLLECTION_INFO_FAILED = "collection_info_failed"

    INTERNAL_SERVER_ERROR = "internal_server_error"
    INTERNAL_SERVER_ERROR_MESSAGE = "Oops! Something went wrong on our end. Please try again later."

    VALIDATION_FAILED = "validation_failed"
    VALIDATION_FAILED_MESSAGE = "The data provided is invalid or missing required fields."

    ASSET_RETRIEVAL_FAILED = "asset_retrieval_failed"
    ASSET_CREATION_FAILED = "asset_creation_failed"
