document.addEventListener("DOMContentLoaded", function () {
    const LM_STUDIO_API_URL = 'http://localhost:1234/v1';
    const chatBox = document.getElementById("chat-box");
    const userMessageInput = document.getElementById("user-message");
    const sendButton = document.getElementById("send-message");
    const fileInput = document.getElementById("file-input");
    const filePreview = document.getElementById("file-preview");
    const modelSelector = document.getElementById("model-selector");

    const staticBaseUrl = window.appConfig.staticBaseUrl;
    const USER_AVATAR = staticBaseUrl +"images/user_avatar.png";
    const LM_AVATAR = staticBaseUrl +"images/lm_avatar.png";
    const THEMES_JSON = staticBaseUrl + "config/themes.json";

    models.forEach(model => {
        const option = document.createElement("option");
                option.value = model;
                option.textContent = model;
                modelSelector.appendChild(option);
    });

    // Display selected files
    fileInput.addEventListener('change', () => {
        filePreview.innerHTML = "";
        Array.from(fileInput.files).forEach(file => {
            filePreview.innerHTML += `<div>${file.name}</div>`;
        });
    });

    // Handle sending messages and files
    async function sendMessage() {
        const userMessage = userMessageInput.value.trim();
        const selectedModel = modelSelector.value;
        const files = Array.from(fileInput.files);

        if (!userMessage && files.length === 0) {
            console.warn("No message or files to send.");
            return;
        }

        // Append user's message to chat
        if (userMessage) {
            appendMessage('user', userMessage);
        }

        // Prepare the payload
        const payload = {
            model: selectedModel,
            chat_input: userMessage,
            file_upload: []
        };

        // Handle file reading
        if (files.length > 0) {
            for (const file of files) {
                const reader = new FileReader();
                const isTextFile = file.type.startsWith('text/');

                reader.onload = function (e) {
                    const content = e.target.result;
                    payload.file_upload.push({
                        filename: file.name,
                        type: file.type,
                        content: content
                    });
                };

                if (isTextFile) {
                    reader.readAsText(file);
                } else {
                    reader.readAsDataURL(file);
                }
            }
        }
        sendToAPI(payload);

        userMessageInput.value = "";
        fileInput.value = "";
        filePreview.innerHTML = "";
    }

    // Send payload to API
    function sendToAPI(payload) {
        fetch(`/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
            .then(response => response.json())
            .then(data => {
                console.log(data);
                appendMessage(data['role_name'], data['text_content'])
            })
            .catch(error => {
                console.error('Error communicating with LM Studio:', error);
                appendMessage('System', 'Failed to communicate with LM Studio.');
            });
    }

    // Stream message to chat
    function streamMessage(sender, message) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender === 'user' ? 'user-message' : 'lm-message');

        // Check for code blocks and apply Prism syntax highlighting
        if (message.includes('```')) {
            message = message.replace(/```(.*?)\n([\s\S]*?)```/g, (match, lang, code) => {
                const escapedCode = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                return `<pre><code class="language-${lang}">${Prism.highlight(escapedCode, Prism.languages[lang] || Prism.languages.markup, lang)}</code></pre>`;
            });
        }

        messageDiv.innerHTML = `
                    <img src="${sender === 'user' ? USER_AVATAR : LM_AVATAR}" alt="${sender}">
                    <div class="content">
                        <span>${message.replace(/\n/g, '<br>')}</span>
                        ${message.includes('```') ? `<button class="copy-button">Copy</button>` : ''}
                    </div>
                `;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

        // Add copy button functionality
        const copyButton = messageDiv.querySelector('.copy-button');
        if (copyButton) {
            copyButton.addEventListener('click', () => {
                navigator.clipboard.writeText(message.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>'))
                    .then(() => alert('Code copied to clipboard!'))
                    .catch(err => console.error('Failed to copy text: ', err));
            });
        }
    }

    // Append message to chat with syntax highlighting
    function appendMessage(sender, message) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender === 'user' ? 'user-message' : 'lm-message');

        // Check for code blocks and apply Prism syntax highlighting
        if (message.includes('```')) {
            message = message.replace(/```(.*?)\n([\s\S]*?)```/g, (match, lang, code) => {
                const escapedCode = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                return `<pre><code class="language-${lang}">${Prism.highlight(escapedCode, Prism.languages[lang] || Prism.languages.markup, lang)}</code></pre>`;
            });
        }

        messageDiv.innerHTML = `
                    <img src="${sender === 'user' ? USER_AVATAR : LM_AVATAR}" alt="${sender}">
                    <div class="content">
                        ${message.replace(/\n/g, '<br>')}
                        ${message.includes('```') ? `<button class="copy-button">Copy</button>` : ''}
                    </div>
                `;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

        // Add copy button functionality
        const copyButton = messageDiv.querySelector('.copy-button');
        if (copyButton) {
            copyButton.addEventListener('click', () => {
                navigator.clipboard.writeText(message.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>'))
                    .then(() => alert('Code copied to clipboard!'))
                    .catch(err => console.error('Failed to copy text: ', err));
            });
        }
    }

    // Event Listeners
    sendButton.addEventListener("click", sendMessage);

    userMessageInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    fetch(THEMES_JSON)
        .then(response => response.json())
        .then(themes => {
            const themeSelector = document.getElementById('theme-selector');
            Object.keys(themes).forEach(theme => {
                const option = document.createElement('option');
                option.value = theme;
                option.textContent = theme;
                themeSelector.appendChild(option);
            });

            // Apply saved theme from cookies
            const savedTheme = getCookie('selectedTheme');
            if (savedTheme && themes[savedTheme]) {
                themeSelector.value = savedTheme;
                applyTheme(themes[savedTheme]);
            }

            themeSelector.addEventListener('change', () => {
                const selectedTheme = themeSelector.value;
                setCookie('selectedTheme', selectedTheme, 365);
                applyTheme(themes[selectedTheme]);
            });
        });

    // Apply Theme
    function applyTheme(theme) {
        Object.entries(theme).forEach(([key, value]) => {
            document.documentElement.style.setProperty(key, value);
        });
    }

    // Cookies Helpers
    function setCookie(name, value, days) {
        const expires = new Date(Date.now() + days * 864e5).toUTCString();
        document.cookie = `${name}=${value}; expires=${expires}; path=/; SameSite=None; Secure`;
    }

    function getCookie(name) {
        return document.cookie.split('; ').find(row => row.startsWith(name + '='))?.split('=')[1];
    }

    // File Upload with Drag-and-Drop
    const fileUpload = document.querySelector('.file-upload');
    fileUpload.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileUpload.classList.add('dragover');
    });

    fileUpload.addEventListener('dragleave', () => {
        fileUpload.classList.remove('dragover');
    });

    fileUpload.addEventListener('drop', (e) => {
        e.preventDefault();
        fileUpload.classList.remove('dragover');
        const files = e.dataTransfer.files;
        console.log('Files dropped:', files);
    });

    // Restore selected model from cookie
    const savedModel = getCookie('selectedModel');
    if (savedModel) {
        modelSelector.value = savedModel;
    }

    // Save model selection to cookie
    modelSelector.addEventListener('change', () => {
        const selectedModel = modelSelector.value;
        setCookie('selectedModel', selectedModel, 365);
    });

});