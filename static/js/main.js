// Main JavaScript for KavakDataBot - Kavak Total Theme

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const questionForm = document.getElementById('questionForm');
    const questionInput = document.getElementById('question');
    const submitBtn = document.getElementById('submitBtn');
    const sessionIdInput = document.getElementById('sessionId');
    const chatContainer = document.getElementById('chatContainer');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');
    const newChatBtn = document.getElementById('newChatBtn');
    
    // Initialize session ID if not exists
    if (!sessionIdInput.value) {
        sessionIdInput.value = 'session_' + Date.now();
    }
    
    // Auto resize textarea as user types
    questionInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // New Chat button event with animation
    newChatBtn.addEventListener('click', function() {
        // Add button press animation
        this.classList.add('active');
        setTimeout(() => this.classList.remove('active'), 200);
        
        // Generate a new session ID
        sessionIdInput.value = 'session_' + Date.now();
        
        // Fade out existing chat
        chatContainer.style.opacity = '0';
        
        setTimeout(() => {
            // Clear chat container
            chatContainer.innerHTML = `
                <div class="empty-chat-container">
                    <i class="fas fa-robot"></i>
                    <h4>Bienvenido a KavakDataBot</h4>
                    <p>Haz una pregunta para comenzar la conversación...</p>
                </div>
            `;
            
            // Fade in new empty chat
            chatContainer.style.opacity = '1';
            
            // Clear input
            questionInput.value = '';
            questionInput.style.height = 'auto';
            questionInput.focus();
        }, 300);
    });
    
    // Handle form submission
    questionForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get form values
        const question = questionInput.value.trim();
        const sessionId = sessionIdInput.value;
        
        // Validate question
        if (!question) {
            showError('Por favor, ingresa una pregunta.');
            return;
        }
        
        // Reset UI state
        hideError();
        showLoading();
        
        // Add user message to chat
        addMessageToChat('user', question);
        
        // Clear input field and reset height
        questionInput.value = '';
        questionInput.style.height = 'auto';
        
        // Create form data
        const formData = new FormData();
        formData.append('question', question);
        formData.append('session_id', sessionId);
        formData.append('reset', 'false');
        
        // Send request to server
        fetch('/ask', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Ha ocurrido un error al procesar tu solicitud');
                });
            }
            return response.json();
        })
        .then(data => {
            hideLoading();
            if (data.response) {
                // Update session ID if provided
                if (data.session_id) {
                    sessionIdInput.value = data.session_id;
                }
                
                // Preparar la respuesta del bot
                let botResponse = data.response;
                
                // Si hay información sobre el documento utilizado, añadirla al final
                if (data.document_used && typeof data.document_used === 'string') {
                    botResponse += `\n\n<div class="document-source"><small class="text-muted"><i class="fas fa-file-alt me-1"></i>Fuente: ${data.document_used}</small></div>`;
                }
                
                // Add bot response to chat with slight delay for a more natural conversation flow
                setTimeout(() => {
                    addMessageToChat('bot', botResponse);
                }, 500);
            } else {
                showError('Se recibió una respuesta vacía del servidor.');
            }
        })
        .catch(error => {
            hideLoading();
            showError(error.message || 'No se pudo obtener una respuesta. Por favor, intenta de nuevo.');
            console.error('Error:', error);
        });
    });
    
    // Function to add a message to the chat
    function addMessageToChat(sender, message) {
        // Check if we need to clear the initial message
        if (chatContainer.querySelector('.empty-chat-container')) {
            chatContainer.innerHTML = '';
        }
        
        // Create message element
        const messageEl = document.createElement('div');
        messageEl.className = `chat-message ${sender}-message`;
        messageEl.style.opacity = '0';
        messageEl.style.transform = 'translateY(20px)';
        
        // Add avatar and content
        if (sender === 'user') {
            messageEl.innerHTML = `
                <div class="d-flex align-items-start">
                    <div class="avatar text-white rounded-circle me-2">
                        <i class="fas fa-user"></i>
                    </div>
                    <div class="message-content">
                        ${message}
                    </div>
                </div>
            `;
        } else {
            // Format bot response with Markdown-like formatting
            const formattedMessage = formatResponse(message);
            
            messageEl.innerHTML = `
                <div class="d-flex align-items-start">
                    <div class="avatar text-white rounded-circle me-2">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-content">
                        ${formattedMessage}
                    </div>
                </div>
            `;
        }
        
        // Add to chat container
        chatContainer.appendChild(messageEl);
        
        // Apply animation after a small delay
        setTimeout(() => {
            messageEl.style.opacity = '1';
            messageEl.style.transform = 'translateY(0)';
            messageEl.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            
            // Check if message content needs scroll and add 'scrollable' class accordingly
            const messageContent = messageEl.querySelector('.message-content');
            if (messageContent) {
                if (messageContent.scrollHeight > messageContent.clientHeight) {
                    messageContent.classList.add('scrollable');
                    
                    // Add scroll indicator when user scrolls
                    messageContent.addEventListener('scroll', function() {
                        const scrollIndicator = this.querySelector('.scroll-indicator');
                        
                        // Show bottom indicator when not scrolled to bottom
                        if (this.scrollHeight - this.scrollTop > this.clientHeight + 10) {
                            this.style.boxShadow = 'inset 0 -5px 10px -5px rgba(0,0,0,0.2)';
                        } else {
                            this.style.boxShadow = 'none';
                        }
                        
                        // Show top indicator when scrolled down
                        if (this.scrollTop > 10) {
                            this.style.boxShadow = 'inset 0 5px 10px -5px rgba(0,0,0,0.2)';
                        }
                        
                        // Show both indicators when in middle
                        if (this.scrollTop > 10 && this.scrollHeight - this.scrollTop > this.clientHeight + 10) {
                            this.style.boxShadow = 'inset 0 5px 10px -5px rgba(0,0,0,0.2), inset 0 -5px 10px -5px rgba(0,0,0,0.2)';
                        }
                    });
                    
                    // Add small hint that this is scrollable
                    const scrollHint = document.createElement('div');
                    scrollHint.className = 'text-center mt-2 small text-muted';
                    scrollHint.innerHTML = '<i class="fas fa-arrows-alt-v me-1"></i> Desplaza para ver más';
                    scrollHint.style.fontSize = '0.8rem';
                    scrollHint.style.opacity = '0.7';
                    messageEl.appendChild(scrollHint);
                    
                    // Hide hint after 3 seconds
                    setTimeout(() => {
                        scrollHint.style.opacity = '0';
                        scrollHint.style.transition = 'opacity 1s ease';
                        setTimeout(() => scrollHint.remove(), 1000);
                    }, 3000);
                }
            }
            
            // Always ensure we're scrolled to the bottom of the chat container after a new message
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 50);
    }
    
    // Helper function to format response with Markdown-like formatting
    function formatResponse(text) {
        // Format code blocks with language support (SQL, JavaScript, etc)
        text = text.replace(/```sql\s*([\s\S]*?)\s*```/gi, '<pre class="language-sql"><code>$1</code></pre>');
        text = text.replace(/```([a-z]*)\s*([\s\S]*?)\s*```/gi, '<pre class="language-$1"><code>$2</code></pre>');
        text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // Format inline code
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Format headers
        text = text.replace(/^### (.*$)/gm, '<h5 class="mt-3 mb-2">$1</h5>');
        text = text.replace(/^## (.*$)/gm, '<h4 class="mt-3 mb-2">$1</h4>');
        text = text.replace(/^# (.*$)/gm, '<h3 class="mt-3 mb-2">$1</h3>');
        
        // Format lists
        text = text.replace(/^\s*[\*\-]\s+(.*$)/gm, '<li>$1</li>');
        text = text.replace(/<\/li>\n<li>/g, '</li><li>');
        text = text.replace(/(<li>.*<\/li>)/gs, '<ul class="mb-3">$1</ul>');
        
        // Format bold
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Format italics
        text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // Format horizontal rules
        text = text.replace(/^\s*---\s*$/gm, '<hr class="my-3">');
        
        // Format tables (basic support)
        // This is a simple approach, a more robust solution would use regex captures
        if (text.indexOf('|') > -1) {
            const lines = text.split('\n');
            const tableLines = [];
            let inTable = false;
            let tableHTML = '<div class="table-responsive"><table class="table table-sm table-bordered my-3">';
            
            for (let i = 0; i < lines.length; i++) {
                if (lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
                    if (!inTable) {
                        inTable = true;
                        tableHTML += '<thead><tr>';
                        
                        // Process header
                        const headerCells = lines[i].split('|').slice(1, -1);
                        for (const cell of headerCells) {
                            tableHTML += `<th>${cell.trim()}</th>`;
                        }
                        
                        tableHTML += '</tr></thead><tbody>';
                        i++; // Skip the separator line
                    } else {
                        tableHTML += '<tr>';
                        const cells = lines[i].split('|').slice(1, -1);
                        for (const cell of cells) {
                            tableHTML += `<td>${cell.trim()}</td>`;
                        }
                        tableHTML += '</tr>';
                    }
                    
                    tableLines.push(i);
                } else if (inTable && i > 0 && tableLines.includes(i - 1)) {
                    // Skip separator line (usually contains |------|------|)
                    continue;
                } else if (inTable) {
                    inTable = false;
                    tableHTML += '</tbody></table></div>';
                    lines[tableLines[0]] = tableHTML;
                    
                    // Remove other table lines
                    for (let j = 1; j < tableLines.length; j++) {
                        lines[tableLines[j]] = '';
                    }
                    
                    tableLines.length = 0;
                }
            }
            
            if (inTable) {
                tableHTML += '</tbody></table></div>';
                lines[tableLines[0]] = tableHTML;
                
                // Remove other table lines
                for (let j = 1; j < tableLines.length; j++) {
                    lines[tableLines[j]] = '';
                }
            }
            
            text = lines.join('\n');
        }
        
        // Convert remaining newlines to <br> tags
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }
    
    // Helper function to show error with animation
    function showError(message) {
        errorMessage.textContent = message;
        errorAlert.style.display = 'block';
        errorAlert.style.opacity = '0';
        errorAlert.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            errorAlert.style.opacity = '1';
            errorAlert.style.transform = 'translateY(0)';
            errorAlert.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        }, 10);
        
        errorAlert.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    // Helper function to hide error with animation
    function hideError() {
        errorAlert.style.opacity = '0';
        errorAlert.style.transform = 'translateY(-20px)';
        errorAlert.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        
        setTimeout(() => {
            errorAlert.style.display = 'none';
        }, 300);
    }
    
    // Helper function to show loading indicator
    function showLoading() {
        loadingIndicator.style.display = 'flex';
        loadingIndicator.style.opacity = '0';
        
        setTimeout(() => {
            loadingIndicator.style.opacity = '1';
            loadingIndicator.style.transition = 'opacity 0.3s ease';
        }, 10);
        
        // Disable submit button while loading
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
    }
    
    // Helper function to hide loading indicator
    function hideLoading() {
        loadingIndicator.style.opacity = '0';
        loadingIndicator.style.transition = 'opacity 0.3s ease';
        
        setTimeout(() => {
            loadingIndicator.style.display = 'none';
        }, 300);
        
        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
    }
    
    // Add event listener for Enter key in the textarea
    questionInput.addEventListener('keydown', function(e) {
        // Submit form when pressing Enter without Shift key
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            questionForm.dispatchEvent(new Event('submit'));
        }
    });

    // Initial setup - focus on textarea
    questionInput.focus();
});
