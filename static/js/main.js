/**
 * Medical Chatbot - Main JavaScript
 * Handles chat functionality, UI interactions, and theme management
 */

// ==================== State Management ====================
const state = {
    isLoading: false,
    messageHistory: [],
    currentTheme: localStorage.getItem('theme') || 'dark'
};

// ==================== DOM Elements ====================
const elements = {
    chatForm: document.getElementById('chatForm'),
    messageInput: document.getElementById('messageInput'),
    sendBtn: document.getElementById('sendBtn'),
    chatMessages: document.getElementById('chatMessages'),
    welcomeMessage: document.getElementById('welcomeMessage'),
    typingIndicator: document.getElementById('typingIndicator'),
    clearBtn: document.getElementById('clearBtn'),
    themeToggle: document.getElementById('themeToggle'),
    charCount: document.getElementById('charCount'),
    toast: document.getElementById('toast'),
    questionChips: document.querySelectorAll('.question-chip')
};

// ==================== Initialization ====================
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    attachEventListeners();
    autoResizeTextarea();
    loadChatHistory();
});

// ==================== Theme Management ====================
function initializeTheme() {
    applyTheme();
    updateThemeIcon();
}

function toggleTheme() {
    state.currentTheme = state.currentTheme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', state.currentTheme);
    applyTheme();
    updateThemeIcon();
}

function applyTheme() {
    document.documentElement.setAttribute('data-theme', state.currentTheme);
    if (state.currentTheme === 'dark') {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
}

function updateThemeIcon() {
    const icon = elements.themeToggle.querySelector('i');
    icon.className = state.currentTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
}

// ==================== Event Listeners ====================
function attachEventListeners() {
    // Form submission
    elements.chatForm.addEventListener('submit', handleFormSubmit);
    
    // Input handling
    elements.messageInput.addEventListener('input', handleInputChange);
    elements.messageInput.addEventListener('keydown', handleKeyDown);
    
    // Button clicks
    elements.clearBtn.addEventListener('click', handleClearChat);
    elements.themeToggle.addEventListener('click', toggleTheme);
    
    // Quick question chips
    elements.questionChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const question = chip.textContent;
            elements.messageInput.value = question;
            handleInputChange();
            elements.messageInput.focus();
        });
    });
}

// ==================== Form Handling ====================
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const message = elements.messageInput.value.trim();
    
    if (!message || state.isLoading) {
        return;
    }
    
    // Hide welcome message on first interaction
    if (elements.welcomeMessage) {
        elements.welcomeMessage.style.display = 'none';
    }
    
    // Add user message to UI
    addMessage('user', message);
    
    // Clear input
    elements.messageInput.value = '';
    handleInputChange();
    elements.messageInput.style.height = 'auto';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send message to backend
    try {
        state.isLoading = true;
        const response = await sendMessage(message);
        
        hideTypingIndicator();
        
        if (response.error) {
            showToast(response.error, 'error');
            return;
        }
        
        // Add bot response to UI
        addMessage('bot', response.response);
        
    } catch (error) {
        hideTypingIndicator();
        showToast('Failed to get response. Please try again.', 'error');
        console.error('Error:', error);
    } finally {
        state.isLoading = false;
    }
}

// ==================== Input Handling ====================
function handleInputChange() {
    const value = elements.messageInput.value;
    const length = value.length;
    
    // Update character count
    elements.charCount.textContent = `${length}/1000`;
    
    // Enable/disable send button
    elements.sendBtn.disabled = length === 0 || state.isLoading;
    
    // Auto-resize textarea
    elements.messageInput.style.height = 'auto';
    elements.messageInput.style.height = elements.messageInput.scrollHeight + 'px';
}

function handleKeyDown(e) {
    // Send on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        elements.chatForm.dispatchEvent(new Event('submit'));
    }
}

function autoResizeTextarea() {
    elements.messageInput.style.height = 'auto';
}

// ==================== API Communication ====================
async function sendMessage(message) {
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Network error');
    }
    
    return await response.json();
}

async function loadChatHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (data.history && data.history.length > 0) {
            if (elements.welcomeMessage) {
                elements.welcomeMessage.style.display = 'none';
            }
            data.history.forEach(msg => {
                addMessage(msg.role, msg.message, false);
            });
            scrollToBottom();
        }
    } catch (error) {
        console.error('Failed to load chat history:', error);
    }
}

async function clearChatHistory() {
    try {
        const response = await fetch('/api/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            elements.chatMessages.innerHTML = '';
            if (elements.welcomeMessage) {
                elements.welcomeMessage.style.display = 'flex';
            }
            showToast('Chat history cleared', 'success');
        }
    } catch (error) {
        showToast('Failed to clear history', 'error');
        console.error('Error:', error);
    }
}

// ==================== UI Updates ====================
function addMessage(role, content, animate = true) {
    const wrapper = document.createElement('div');
    wrapper.className = `flex gap-3 ${role === 'user' ? 'flex-row-reverse text-right' : ''}`;
    if (animate) {
        wrapper.classList.add('message-enter');
    }

    const avatar = document.createElement('div');
    avatar.className = role === 'user'
        ? 'w-11 h-11 rounded-2xl bg-gradient-to-br from-emerald-400 to-sky-500 text-white flex items-center justify-center shadow-lg shrink-0'
        : 'w-11 h-11 rounded-2xl bg-white/10 text-brand-200 flex items-center justify-center shrink-0';
    avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

    const bubble = document.createElement('div');
    bubble.className = role === 'user'
        ? 'max-w-full rounded-3xl rounded-tr-md bg-gradient-to-br from-emerald-400 to-sky-500 px-4 py-3 text-sm leading-relaxed text-white shadow-glow'
        : 'max-w-full rounded-3xl rounded-tl-md border border-white/10 bg-white/80 px-4 py-3 text-left text-sm leading-relaxed text-slate-800 shadow-inner backdrop-blur dark:border-white/10 dark:bg-slate-900/60 dark:text-slate-100';

    bubble.innerHTML = formatMessage(content);

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);

    elements.chatMessages.appendChild(wrapper);
    scrollToBottom();
}

function formatMessage(content) {
    let formatted = content.replace(/\n/g, '<br>');

    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

    const lines = formatted.split('<br>');
    const structuredLines = lines.map(line => {
        const trimmed = line.trim();
        if (trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
            return { type: 'ul', value: `<li>${trimmed.substring(2)}</li>` };
        }
        const orderedMatch = trimmed.match(/^(\d+)\.\s+/);
        if (orderedMatch) {
            return { type: 'ol', value: `<li>${trimmed.substring(orderedMatch[0].length)}</li>` };
        }
        return { type: 'text', value: line };
    });

    let currentList = null;
    const finalLines = [];

    const closeList = () => {
        if (currentList) {
            finalLines.push(`</${currentList}>`);
            currentList = null;
        }
    };

    structuredLines.forEach(item => {
        if (item.type === 'text') {
            closeList();
            finalLines.push(item.value);
            return;
        }

        if (item.type !== currentList) {
            closeList();
            finalLines.push(`<${item.type}>`);
            currentList = item.type;
        }
        finalLines.push(item.value);
    });

    closeList();

    formatted = finalLines.join('');

    formatted = formatted
        .replace(/<ul>/g, '<ul class="mb-3 list-disc space-y-1 pl-5 text-left text-sm">')
        .replace(/<ol>/g, '<ol class="mb-3 list-decimal space-y-1 pl-5 text-left text-sm">')
        .replace(/<li>/g, '<li class="leading-relaxed">');
    
    return formatted;
}

function showTypingIndicator() {
    elements.typingIndicator.style.display = 'flex';
    scrollToBottom();
}

function hideTypingIndicator() {
    elements.typingIndicator.style.display = 'none';
}

function scrollToBottom() {
    if (!elements.chatMessages) return;
    setTimeout(() => {
        elements.chatMessages.scroll({
            top: elements.chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }, 50);
}

function showToast(message, type = 'info') {
    elements.toast.textContent = message;
    elements.toast.className = `toast show ${type}`;
    
    setTimeout(() => {
        elements.toast.className = 'toast';
    }, 3000);
}

// ==================== Clear Chat Handler ====================
function handleClearChat() {
    if (state.isLoading) {
        return;
    }
    
    // Show confirmation
    if (elements.chatMessages.children.length === 0) {
        showToast('No messages to clear', 'info');
        return;
    }
    
    if (confirm('Are you sure you want to clear the chat history?')) {
        clearChatHistory();
    }
}

// ==================== Utility Functions ====================
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ==================== Error Handling ====================
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});

// ==================== Service Worker (Optional) ====================
if ('serviceWorker' in navigator) {
    // Uncomment to enable service worker for PWA features
    // navigator.serviceWorker.register('/sw.js').catch(console.error);
}

// ==================== Export for testing ====================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        addMessage,
        formatMessage,
        showToast
    };
}

