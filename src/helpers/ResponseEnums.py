from enum import Enum


class ResponseSignal(Enum):
    # Format: ENUM_NAME = ("signal_string", "User-facing message")

    # --- Configuration & Setup ---
    API_KEY_MISSING = ("api_key_missing", "A required API key is missing from the server configuration.")
    LLM_CONFIGURATION_ERROR = ("llm_configuration_error", "The AI model client is missing required configuration IDs.")
    # --- General System ---
    INTERNAL_SERVER_ERROR = ("internal_server_error", "Oops! Something went wrong on our end. Please try again later.")
    VALIDATION_FAILED = ("validation_failed", "The data provided is invalid or missing required fields.")
    ASSET_RETRIEVAL_FAILED = ("asset_retrieval_failed", "Failed to retrieve the requested asset.")
    ASSET_CREATION_FAILED = ("asset_creation_failed", "Failed to create the asset.")

    # --- File Operations ---
    FILE_VALIDATION_FAILED = ("file_validation_failed", "The uploaded file failed validation checks.")
    FILE_VALIDATION_SUCCESS = ("file_validation_success", "File validated successfully.")
    FILE_TYPE_NOT_SUPPORTED = (
        "file_type_not_supported",
        "This file type is not supported. Please upload a valid format.",
    )
    FILE_SIZE_EXCEEDED = ("file_size_exceeded", "The file exceeds the maximum allowed size.")
    FILE_UPLOADED_SUCCESSFULLY = ("file_uploaded_successfully", "Your file was uploaded successfully.")
    FILE_UPLOADED_FAILED = ("file_uploaded_failed", "There was an error uploading your file. Please try again.")
    FILE_NOT_FOUND = ("file_not_found", "The requested file could not be found.")
    FILE_DELETED_SUCCESSFULLY = ("file_deleted_successfully", "The specific file and its vector data were permanently removed.")
    FILE_ALREADY_EXISTS = ("file_already_exists", "A file with this name already exists in the workspace. Please delete the old file first or rename before uploading.")

    # --- Wikipedia Operations ---
    WIKI_SEARCH_RESULTS_FOUND = ("wiki_search_results_found", "Wikipedia search results retrieved successfully.")
    WIKI_SEARCH_NO_RESULTS = ("wiki_search_no_results", "No Wikipedia articles matched your search.")
    WIKI_FILE_UPLOADED_SUCCESSFULLY = (
        "wiki_file_uploaded_successfully",
        "Wikipedia content successfully processed and saved.",
    )
    WIKI_FILE_UPLOAD_FAILED = ("wiki_file_upload_failed", "Failed to process and save the Wikipedia content.")
    WIKI_SEARCH_FAILED = ("wiki_search_failed", "The external Wikipedia service is currently unavailable.")

    # --- Database & Vector DB ---
    DB_CONNECTION_SUCCESS = ("db_connection_success", "Successfully connected to the database.")
    DB_CONNECTION_FAILED = ("db_connection_failed", "Failed to connect to the database infrastructure.")
    COLLECTION_CREATION_FAILED = ("collection_creation_failed", "Failed to create the database collection.")
    COLLECTION_INFO_SUCCESSFUL = ("collection_info_successful", "Collection information retrieved successfully.")
    COLLECTION_INFO_FAILED = ("collection_info_failed", "Failed to retrieve collection information.")
    COLLECTION_DELETION_FAILED = ("collection_deletion_failed", "Failed to delete the database collection.")
    PROJECT_CREATION_FAILED = ("project_creation_failed", "Failed to create or initialize the project space.")
    PROJECT_RETRIEVAL_FAILED = ("project_retrieval_failed", "Failed to retrieve the requested project data.")
    PROJECT_NOT_FOUND = ("project_not_found", "The requested project could not be found or you lack permission.")
    PROJECT_DELETED_SUCCESSFULLY = ("project_deleted_successfully", "Project and all associated data correctly purged.")

    # --- Chunking & Ingestion ---
    CHUNKING_SUCCESS = ("chunking_success", "Document successfully divided into manageable chunks.")
    CHUNKING_FAILED = ("chunking_failed", "An error occurred while processing the document into chunks.")
    CHUNK_INSERTION_SUCCESSFUL = ("chunk_insertion_successful", "Data successfully saved to the knowledge base.")
    CHUNK_INSERTION_FAILED = ("chunk_insertion_failed", "Failed to save data to the knowledge base.")
    CHUNK_DELETION_SUCCESSFUL = ("chunk_deletion_successful", "Data successfully removed from the knowledge base.")
    CHUNK_DELETION_FAILED = ("chunk_deletion_failed", "Failed to remove data from the knowledge base.")

    # --- NLP & RAG ---
    NLP_SEARCH_SUCCESSFUL = ("nlp_search_successful", "Search completed successfully.")
    NLP_SEARCH_FAILED = ("nlp_search_failed", "Our AI search engine encountered an error. Please try again.")
    NLP_CHAT_SUCCESSFUL = ("nlp_chat_successful", "AI response generated successfully.")
    NLP_CHAT_FAILED = ("nlp_chat_failed", "Failed to generate an AI response.")
    RERANKING_FAILED = ("reranking_failed", "The AI document sorting service is currently unavailable.")
    MODEL_LOADING_FAILED = ("model_loading_failed", "Failed to load the local AI model from disk or network.")
    EMBEDDING_FAILED = ("embedding_failed", "Failed to convert text into vector embeddings.")

    def __init__(self, signal: str, message: str):
        """Unpacks the tuple into accessible properties"""
        self.signal = signal
        self.message = message
