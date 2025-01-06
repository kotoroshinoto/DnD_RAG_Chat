        document.addEventListener("DOMContentLoaded", function () {
            const LM_STUDIO_API_URL = 'http://192.168.1.107:1234/v1';
            const chatBox = document.getElementById("chat-box");
            const userMessageInput = document.getElementById("user-message");
            const sendButton = document.getElementById("send-message");
            const fileInput = document.getElementById("file-input");
            const filePreview = document.getElementById("file-preview");
            const modelSelector = document.getElementById("model-selector");

            const USER_AVATAR = 'user_avatar.png';
            const LM_AVATAR = 'lm_avatar.png';

            // Fetch available models
            fetch(`${LM_STUDIO_API_URL}/models`)
                .then(response => response.json())
                .then(data => {
                    data.data.forEach(model => {
                        const option = document.createElement("option");
                        option.value = model.id;
                        option.textContent = model.id;
                        modelSelector.appendChild(option);
                    });
                })
                .catch(error => console.error("Failed to fetch models:", error));

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
                    messages: [
                        { role: "user", content: userMessage || "Attached file(s):" }
                    ]
                };

                // Handle file reading
                if (files.length > 0) {
                    for (const file of files) {
                        const reader = new FileReader();
                        const isTextFile = file.type.startsWith('text/');

                        reader.onload = function (e) {
                            const content = e.target.result;
                            if (isTextFile) {
                                // Include file contents directly in the message
                                payload.messages.push({
                                    role: "user",
                                    content: `File Name: ${file.name}\nContents:\n${content}`
                                });
                            } else {
                                // For non-text files, mention the file
                                payload.messages.push({
                                    role: "user",
                                    content: `Attached non-text file: ${file.name} (Type: ${file.type})`
                                });
                            }

                            // If all files are processed, send to API
                            if (payload.messages.length === files.length + 1) {
                                sendToAPI(payload);
                            }
                        };

                        if (isTextFile) {
                            reader.readAsText(file);
                        } else {
                            reader.readAsDataURL(file);
                        }
                    }
                } else {
                    sendToAPI(payload);
                }

                userMessageInput.value = "";
                fileInput.value = "";
                filePreview.innerHTML = "";
            }

            // Send payload to API
            function sendToAPI(payload) {
                fetch(`${LM_STUDIO_API_URL}/chat/completions`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.choices && data.choices[0] && data.choices[0].message) {
                        streamMessage('lm', data.choices[0].message.content);
                    } else {
                        appendMessage('lm', 'Error: Unexpected response format.');
                        console.error('Unexpected response:', data);
                    }
                })
                .catch(error => {
                    console.error('Error communicating with LM Studio:', error);
                    appendMessage('lm', 'Failed to communicate with LM Studio.');
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
			
			fetch('themes.json')
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