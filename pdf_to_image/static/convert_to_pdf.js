// Convert to PDF JavaScript functionality
class ConvertToPDF {
    constructor() {
        this.currentFile = null;
        this.isProcessing = false;
        this.init();
    }

    init() {
        this.setupDragAndDrop();
        this.setupFileInput();
        this.setupButtons();
    }

    setupDragAndDrop() {
        const dragDropArea = document.querySelector('.drag-drop');
        if (!dragDropArea) return;

        // Create file input if it doesn't exist
        let fileInput = document.getElementById('file-input');
        if (!fileInput) {
            fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.id = 'file-input';
            fileInput.style.display = 'none';
            fileInput.accept = this.getAcceptedFileTypes();
            document.body.appendChild(fileInput);
        }

        // Click to select file
        dragDropArea.addEventListener('click', () => {
            if (!this.isProcessing) {
                fileInput.click();
            }
        });

        // Drag and drop events
        dragDropArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            dragDropArea.classList.add('drag-over');
        });

        dragDropArea.addEventListener('dragleave', () => {
            dragDropArea.classList.remove('drag-over');
        });

        dragDropArea.addEventListener('drop', (e) => {
            e.preventDefault();
            dragDropArea.classList.remove('drag-over');
            
            if (!this.isProcessing) {
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileSelection(files[0]);
                }
            }
        });
    }

    setupFileInput() {
        const fileInput = document.getElementById('file-input');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileSelection(e.target.files[0]);
                }
            });
        }
    }

    setupButtons() {
        const processBtn = document.querySelector('button[type="submit"]');
        const clearBtn = document.querySelector('button[type="button"]');

        if (processBtn) {
            processBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.processFile();
            });
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.clearFile();
            });
        }
    }

    getAcceptedFileTypes() {
        const path = window.location.pathname;
        
        if (path.includes('jpg_to_pdf')) {
            return '.jpg,.jpeg,.png,.bmp,.tiff,.tif,.gif';
        } else if (path.includes('word_to_pdf')) {
            return '.doc,.docx';
        } else if (path.includes('excel_to_pdf')) {
            return '.xls,.xlsx';
        } else if (path.includes('powerpoint_to_pdf')) {
            return '.ppt,.pptx';
        } else if (path.includes('html_to_pdf')) {
            return '.html,.htm';
        } else if (path.includes('zip_to_pdf')) {
            return '.zip';
        }
        
        return '*';
    }

    getApiEndpoint() {
        const path = window.location.pathname;
        
        if (path.includes('jpg_to_pdf')) {
            return '/api/jpg_to_pdf';
        } else if (path.includes('word_to_pdf')) {
            return '/api/word_to_pdf';
        } else if (path.includes('excel_to_pdf')) {
            return '/api/excel_to_pdf';
        } else if (path.includes('powerpoint_to_pdf')) {
            return '/api/powerpoint_to_pdf';
        } else if (path.includes('html_to_pdf')) {
            return '/api/html_to_pdf';
        } else if (path.includes('zip_to_pdf')) {
            return '/api/zip_to_pdf';
        }
        
        return null;
    }

    handleFileSelection(file) {
        this.currentFile = file;
        this.updateUI(file);
    }

    updateUI(file) {
        const dragDropArea = document.querySelector('.drag-drop');
        if (dragDropArea) {
            dragDropArea.innerHTML = `
                <div class="file-info">
                    <strong>Selected File:</strong> ${file.name}<br>
                    <strong>Size:</strong> ${this.formatFileSize(file.size)}<br>
                    <strong>Type:</strong> ${file.type || 'Unknown'}
                </div>
            `;
        }

        // Enable process button
        const processBtn = document.querySelector('button[type="submit"]');
        if (processBtn) {
            processBtn.disabled = false;
            processBtn.textContent = 'Convert to PDF';
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async processFile() {
        if (!this.currentFile || this.isProcessing) return;

        const endpoint = this.getApiEndpoint();
        if (!endpoint) {
            this.showError('Invalid page or endpoint not found');
            return;
        }

        this.isProcessing = true;
        this.updateProcessingUI(true);

        try {
            const formData = new FormData();
            formData.append('file', this.currentFile);
            
            // Add default options
            formData.append('page_size', 'A4');
            formData.append('quality', '95');

            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                // Handle file download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `converted_${this.currentFile.name.split('.')[0]}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                this.showSuccess('File converted successfully!');
            } else {
                const errorData = await response.json();
                this.showError(errorData.error || 'Conversion failed');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.isProcessing = false;
            this.updateProcessingUI(false);
        }
    }

    updateProcessingUI(processing) {
        const processBtn = document.querySelector('button[type="submit"]');
        const dragDropArea = document.querySelector('.drag-drop');

        if (processBtn) {
            processBtn.disabled = processing;
            processBtn.textContent = processing ? 'Converting...' : 'Convert to PDF';
        }

        if (processing && dragDropArea) {
            const fileInfo = dragDropArea.querySelector('.file-info');
            if (fileInfo) {
                fileInfo.innerHTML += '<br><div class="processing">Processing...</div>';
            }
        }
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showMessage(message, type) {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.message');
        existingMessages.forEach(msg => msg.remove());

        // Create new message
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;
        messageDiv.style.cssText = `
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            ${type === 'error' ? 'background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;' : 'background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;'}
        `;

        const container = document.querySelector('.tool-form-container');
        if (container) {
            container.insertBefore(messageDiv, container.firstChild);
        }

        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }

    clearFile() {
        this.currentFile = null;
        this.isProcessing = false;

        // Reset UI
        const dragDropArea = document.querySelector('.drag-drop');
        if (dragDropArea) {
            dragDropArea.innerHTML = '<strong>Select or drag and drop your files here</strong>';
        }

        const processBtn = document.querySelector('button[type="submit"]');
        if (processBtn) {
            processBtn.disabled = true;
            processBtn.textContent = 'Process File';
        }

        // Clear file input
        const fileInput = document.getElementById('file-input');
        if (fileInput) {
            fileInput.value = '';
        }

        // Remove messages
        const messages = document.querySelectorAll('.message');
        messages.forEach(msg => msg.remove());
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ConvertToPDF();
});

// Add some basic CSS for drag and drop
const style = document.createElement('style');
style.textContent = `
    .drag-drop {
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    
    .drag-drop.drag-over {
        background-color: #e3f2fd !important;
        border-color: #2196f3 !important;
    }
    
    .file-info {
        text-align: left;
        padding: 10px;
        background-color: #f5f5f5;
        border-radius: 4px;
        margin: 10px 0;
    }
    
    .processing {
        color: #2196f3;
        font-weight: bold;
        margin-top: 10px;
    }
    
    button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
`;
document.head.appendChild(style);
