// PDF Question-Answering App JavaScript

class PDFQAApp {
    constructor() {
        this.apiBase = 'http://localhost:8000';
        this.currentDocuments = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDocuments();
        this.checkAPIHealth();
    }

    setupEventListeners() {
        // File upload
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.getElementById('uploadArea');
        const browseLink = uploadArea.querySelector('.browse-link');

        browseLink.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files[0]));

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            const file = e.dataTransfer.files[0];
            if (file && file.type === 'application/pdf') {
                this.handleFileSelect(file);
            } else {
                this.showStatus('Please select a PDF file', 'error');
            }
        });

        // Chat input
        const questionInput = document.getElementById('questionInput');
        const sendButton = document.getElementById('sendButton');
        const charCount = document.getElementById('charCount');

        questionInput.addEventListener('input', (e) => {
            const length = e.target.value.length;
            charCount.textContent = `${length}/500`;
            sendButton.disabled = length === 0;
        });

        questionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !sendButton.disabled) {
                this.sendQuestion();
            }
        });

        sendButton.addEventListener('click', () => this.sendQuestion());

        // Modal controls
        document.getElementById('modalClose').addEventListener('click', () => this.hideModal());
        document.getElementById('modalCancel').addEventListener('click', () => this.hideModal());
        document.getElementById('closeStatus').addEventListener('click', () => this.hideStatus());
    }

    async checkAPIHealth() {
        try {
            const response = await fetch(`${this.apiBase}/health`);
            if (response.ok) {
                this.showStatus('Connected to API', 'success');
                setTimeout(() => this.hideStatus(), 2000);
            } else {
                throw new Error('API not healthy');
            }
        } catch (error) {
            this.showStatus('Cannot connect to API. Please make sure the server is running.', 'error');
        }
    }

    async handleFileSelect(file) {
        if (!file) return;

        if (file.type !== 'application/pdf') {
            this.showStatus('Please select a PDF file', 'error');
            return;
        }

        if (file.size > 50 * 1024 * 1024) { // 50MB limit
            this.showStatus('File size too large. Maximum size is 50MB.', 'error');
            return;
        }

        await this.uploadFile(file);
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        this.showUploadProgress();
        this.showLoading('Uploading and processing PDF...');

        try {
            const response = await fetch(`${this.apiBase}/upload-pdf`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }

            const result = await response.json();
            this.showStatus(`PDF uploaded successfully: ${result.filename}`, 'success');
            
            // Wait for processing to complete
            await this.waitForProcessing(result.id, result.filename);
            
            this.loadDocuments();
            this.hideUploadProgress();

        } catch (error) {
            this.showStatus(`Upload failed: ${error.message}`, 'error');
            this.hideUploadProgress();
        } finally {
            this.hideLoading();
        }
    }

    async waitForProcessing(documentId, filename) {
        const maxAttempts = 30; // 30 seconds
        let attempts = 0;

        while (attempts < maxAttempts) {
            try {
                const response = await fetch(`${this.apiBase}/documents/${documentId}`);
                if (response.ok) {
                    const doc = await response.json();
                    if (doc.status === 'completed') {
                        this.showStatus(`Processing completed: ${filename}`, 'success');
                        return;
                    } else if (doc.status === 'failed') {
                        throw new Error('Processing failed');
                    }
                }
            } catch (error) {
                console.error('Error checking processing status:', error);
            }

            attempts++;
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        this.showStatus('Processing is taking longer than expected. Check back later.', 'warning');
    }

    async loadDocuments() {
        const documentsLoading = document.getElementById('documentsLoading');
        const documentsList = document.getElementById('documentsList');
        const selectedDocument = document.getElementById('selectedDocument');

        documentsLoading.style.display = 'block';

        try {
            const response = await fetch(`${this.apiBase}/documents`);
            if (!response.ok) throw new Error('Failed to load documents');

            const data = await response.json();
            this.currentDocuments = data.documents;

            // Update documents list
            if (this.currentDocuments.length === 0) {
                documentsList.innerHTML = '<div class="no-documents">No documents uploaded yet</div>';
            } else {
                documentsList.innerHTML = this.currentDocuments.map(doc => this.renderDocumentCard(doc)).join('');
                this.setupDocumentActions();
            }

            // Update document selector
            selectedDocument.innerHTML = '<option value="">All documents</option>' +
                this.currentDocuments
                    .filter(doc => doc.status === 'completed')
                    .map(doc => `<option value="${doc.id}">${doc.filename}</option>`)
                    .join('');

        } catch (error) {
            documentsList.innerHTML = '<div class="error">Failed to load documents</div>';
            console.error('Error loading documents:', error);
        } finally {
            documentsLoading.style.display = 'none';
        }
    }

    renderDocumentCard(doc) {
        const statusIcon = {
            'completed': 'fas fa-check-circle text-success',
            'processing': 'fas fa-spinner fa-spin text-warning',
            'failed': 'fas fa-exclamation-circle text-error'
        }[doc.status] || 'fas fa-question-circle';

        const uploadDate = new Date(doc.upload_date).toLocaleDateString();

        return `
            <div class="document-card" data-doc-id="${doc.id}">
                <div class="document-header">
                    <div class="document-title">
                        <i class="fas fa-file-pdf"></i>
                        <span title="${doc.filename}">${this.truncateText(doc.filename, 25)}</span>
                    </div>
                    <div class="document-status">
                        <i class="${statusIcon}"></i>
                    </div>
                </div>
                <div class="document-details">
                    <small>Uploaded: ${uploadDate}</small>
                    ${doc.chunk_count ? `<small>Chunks: ${doc.chunk_count}</small>` : ''}
                    ${doc.file_size ? `<small>Size: ${this.formatFileSize(doc.file_size)}</small>` : ''}
                </div>
                <div class="document-actions">
                    <button class="btn btn-sm btn-primary" onclick="app.selectDocument('${doc.id}')">
                        <i class="fas fa-comments"></i> Chat
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="app.confirmDeleteDocument('${doc.id}', '${doc.filename}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }

    setupDocumentActions() {
        // Document actions are handled by onclick attributes in the HTML
    }

    selectDocument(documentId) {
        const selectedDocument = document.getElementById('selectedDocument');
        selectedDocument.value = documentId;
        
        // Scroll to chat area
        document.querySelector('.chat-section').scrollIntoView({ behavior: 'smooth' });
        
        // Focus on input
        document.getElementById('questionInput').focus();
    }

    confirmDeleteDocument(documentId, filename) {
        this.showModal(
            'Delete Document',
            `Are you sure you want to delete "${filename}"? This action cannot be undone.`,
            () => this.deleteDocument(documentId)
        );
    }

    async deleteDocument(documentId) {
        this.hideModal();
        this.showLoading('Deleting document...');

        try {
            const response = await fetch(`${this.apiBase}/documents/${documentId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Delete failed');
            }

            this.showStatus('Document deleted successfully', 'success');
            this.loadDocuments();

        } catch (error) {
            this.showStatus(`Delete failed: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async sendQuestion() {
        const questionInput = document.getElementById('questionInput');
        const selectedDocument = document.getElementById('selectedDocument');
        const question = questionInput.value.trim();

        if (!question) return;

        // Add user message to chat
        this.addChatMessage('user', question);
        questionInput.value = '';
        document.getElementById('charCount').textContent = '0/500';
        document.getElementById('sendButton').disabled = true;

        // Show typing indicator
        const typingId = this.addChatMessage('assistant', '', true);

        try {
            const requestBody = {
                question: question,
                max_chunks: 5
            };

            if (selectedDocument.value) {
                requestBody.document_id = selectedDocument.value;
            }

            const response = await fetch(`${this.apiBase}/ask-question`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to get answer');
            }

            const result = await response.json();
            
            // Remove typing indicator and add actual response
            this.removeChatMessage(typingId);
            this.addChatMessage('assistant', result.answer, false, result);

        } catch (error) {
            this.removeChatMessage(typingId);
            this.addChatMessage('assistant', `Sorry, I encountered an error: ${error.message}`);
            this.showStatus(`Question failed: ${error.message}`, 'error');
        }
    }

    addChatMessage(sender, content, isTyping = false, metadata = null) {
        const chatMessages = document.getElementById('chatMessages');
        const messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${sender}-message`;
        messageElement.id = messageId;

        if (isTyping) {
            messageElement.innerHTML = `
                <div class="message-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            `;
        } else {
            const avatar = sender === 'user' 
                ? '<i class="fas fa-user"></i>' 
                : '<i class="fas fa-robot"></i>';

            let messageContent = `
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">
                    <div class="message-text">${this.formatMessage(content)}</div>
                    <div class="message-time">${new Date().toLocaleTimeString()}</div>
            `;

            if (metadata && sender === 'assistant') {
                messageContent += `
                    <div class="message-metadata">
                        <small>Confidence: ${(metadata.confidence * 100).toFixed(1)}%</small>
                        ${metadata.sources && metadata.sources.length > 0 ? 
                            `<small>Sources: ${metadata.sources.length} chunks</small>` : ''}
                    </div>
                `;
            }

            messageContent += '</div>';
            messageElement.innerHTML = messageContent;
        }

        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return messageId;
    }

    removeChatMessage(messageId) {
        const element = document.getElementById(messageId);
        if (element) {
            element.remove();
        }
    }

    formatMessage(text) {
        // Basic text formatting
        return text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    showUploadProgress() {
        document.getElementById('uploadProgress').style.display = 'block';
        document.querySelector('.upload-content').style.display = 'none';
    }

    hideUploadProgress() {
        document.getElementById('uploadProgress').style.display = 'none';
        document.querySelector('.upload-content').style.display = 'block';
    }

    showLoading(text = 'Loading...') {
        document.getElementById('loadingText').textContent = text;
        document.getElementById('loadingOverlay').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }

    showStatus(message, type = 'info') {
        const statusBar = document.getElementById('statusBar');
        const statusMessage = document.getElementById('statusMessage');
        
        statusBar.className = `status-bar ${type}`;
        statusMessage.textContent = message;
        statusBar.style.display = 'flex';

        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => this.hideStatus(), 3000);
        }
    }

    hideStatus() {
        document.getElementById('statusBar').style.display = 'none';
    }

    showModal(title, message, confirmCallback) {
        document.getElementById('modalTitle').textContent = title;
        document.getElementById('modalMessage').textContent = message;
        document.getElementById('modalOverlay').style.display = 'flex';
        
        // Remove existing listeners and add new one
        const confirmBtn = document.getElementById('modalConfirm');
        confirmBtn.replaceWith(confirmBtn.cloneNode(true));
        document.getElementById('modalConfirm').addEventListener('click', confirmCallback);
    }

    hideModal() {
        document.getElementById('modalOverlay').style.display = 'none';
    }

    truncateText(text, maxLength) {
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
}

// Initialize the app when the page loads
const app = new PDFQAApp();