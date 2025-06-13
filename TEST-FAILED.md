# TEST-FAILED.md

## Elenco dei Test Falliti

### 1. File: tests/api/test_documents.py
- test_upload_document_file
- test_upload_document_file_not_found
- test_upload_document_file_duplicate
- test_download_document_file
- test_download_document_file_not_found
- test_download_document_file_no_file

### 2. File: tests/api/test_documents_download.py
- test_download_document_success
- test_download_document_unauthorized
- test_download_document_not_found

### 3. File: tests/api/test_documents_upload.py
- test_upload_document_success
- test_upload_document_no_file
- test_upload_document_large_file
- test_upload_document_invalid_file_type
- test_upload_document_minio_error

### 4. File: tests/api/test_house_api.py
- test_create_house_authenticated
- test_list_houses_authenticated
- test_get_house_authenticated
- test_update_house_authenticated
- test_delete_house_authenticated
- test_house_endpoints_unauthenticated

### 5. File: tests/api/test_user_api.py
- test_create_user_success
- test_create_user_duplicate_email
- test_get_user_success
- test_get_user_not_found
- test_get_users_pagination
- test_update_user_success
- test_delete_user_success

## Raggruppamento per Categoria Concettuale

### Gestione Documenti
- **test_documents.py**: Upload, download, validazione, errori
- **test_documents_download.py**: Download, permessi, errori di accesso
- **test_documents_upload.py**: Upload, validazione, permessi, errori

### Gestione Case e Stanze
- **test_house_api.py**: Creazione, modifica, eliminazione case/stanze, permessi, errori

### Gestione Utenti
- **test_user_api.py**: Registrazione, login, modifica profilo, permessi, errori 