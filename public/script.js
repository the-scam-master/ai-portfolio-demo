document.addEventListener('DOMContentLoaded', () => {
  const chatMessages = document.getElementById('chat-messages');
  const userInput = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  const suggestions = document.querySelector('.suggestions');
  let source = null;

  // Store recent messages for context
  const conversationHistory = [];

  function scrollToBottom() {
    chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
  }

  function adjustChatHeight() {
    const chatMessages = document.getElementById('chat-messages');
    const headerHeight = document.querySelector('.header').offsetHeight;
    const inputAreaHeight = document.querySelector('.input-area').offsetHeight;
    const suggestionsHeight = suggestions ? suggestions.offsetHeight : 0;
    const totalHeight = headerHeight + inputAreaHeight + suggestionsHeight;

    if (window.innerWidth <= 768) {
      const viewportHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;
      chatMessages.style.height = `${viewportHeight - totalHeight}px`;
    }
  }

  // Run on page load and when the window resizes (e.g., keyboard opens)
  window.addEventListener('load', adjustChatHeight);
  window.addEventListener('resize', adjustChatHeight);

  function createMessageElement(sender, content = '', isTyping = false) {
    const div = document.createElement('div');
    div.className = `message ${sender}-message`;
    const avatar = sender === 'user' ? 'Y' : 'T';
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const messageText = isTyping
      ? '<em>Typing...</em>'
      : marked.parse(content);

    div.innerHTML = `
      <div class="avatar">${avatar}</div>
      <div class="content">
        <div class="message-text">${messageText}</div>
        <div class="timestamp">${time}</div>
      </div>
    `;

    chatMessages.appendChild(div);
    scrollToBottom();
    return div.querySelector('.message-text');
  }

  function stopPreviousStream() {
    if (source) {
      source.close();
      source = null;
    }
  }

  async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    stopPreviousStream();
    createMessageElement('user', message);
    const botBubble = createMessageElement('bot', '', true);

    // Add user message to history
    conversationHistory.push({ role: 'user', content: message });
    userInput.value = '';
    userInput.focus();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          history: conversationHistory.slice(-40) // Limit context to last 40 messages
        }),
      });

      if (!res.ok || !res.body) throw new Error('Failed to connect.');

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let done = false;
      let fullText = '';

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;

        if (value) {
          const textChunk = decoder.decode(value, { stream: true });
          const matches = textChunk.match(/data:\s*(.*?)\n/g);

          if (matches) {
            for (const line of matches) {
              const dataStr = line.replace(/^data:\s*/, '').trim();
              if (dataStr === '[DONE]') break;

              try {
                const parsed = JSON.parse(dataStr);
                if (parsed.text) {
                  fullText += parsed.text;
                  botBubble.innerHTML = marked.parse(fullText);
                  scrollToBottom();
                }
              } catch (err) {
                console.error('Invalid chunk:', dataStr);
              }
            }
          }
        }
      }

      // Add bot reply to history
      conversationHistory.push({ role: 'bot', content: fullText });

    } catch (err) {
      console.error(err);
      botBubble.innerHTML = marked.parse('**Oops, something went wrong!** Try again or ask me later.');
      const retryBtn = document.createElement('button');
      retryBtn.className = 'retry-btn';
      retryBtn.textContent = 'Retry';
      retryBtn.addEventListener('click', sendMessage);
      botBubble.parentElement.appendChild(retryBtn);
    }
  }

  // Handle suggested questions
  document.querySelectorAll('.suggestion').forEach(span => {
    span.addEventListener('click', () => {
      userInput.value = span.dataset.query;
      suggestions.style.display = 'none'; // Hide suggestions after click
      sendMessage();
      adjustChatHeight(); // Recalculate chat height
    });
  });

  sendBtn.addEventListener('click', sendMessage);
  userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });

  // Initial message
  createMessageElement(
    'bot',
    "Hi! I'm an AI assistant representing **Tanmay Kalbande**.\n\nAsk me about his [projects](https://github.com/tanmay-kalbande?tab=repositories), skills, experience, or hobbies!"
  );

// Add this to the bottom of your public/script.js file
function runPortfolioDemo() {
  const demoSteps = [
    { 
      text: "What projects show your AI skills?", 
      typingDelay: 50,       // 50ms per character typing speed
      beforeDelay: 2000,     // 2s before starting
      afterDelay: 8000       // 8s after sending
    },
    { 
      text: "Favorite anime?", 
      typingDelay: 40,
      beforeDelay: 3000,     // 3s before starting
      afterDelay: 5000       // 5s after sending
    },
    { 
      text: "Show me your best data visualization project", 
      typingDelay: 45,
      beforeDelay: 3000,     // 3s before starting
      afterDelay: 10000      // 10s after sending
    }
  ];

  let stepIndex = 0;
  const userInput = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  
  // Create typing indicator
  const typingIndicator = document.createElement('div');
  typingIndicator.className = 'typing-indicator';
  typingIndicator.innerHTML = `
    <div class="dot"></div>
    <div class="dot"></div>
    <div class="dot"></div>
  `;
  document.body.appendChild(typingIndicator);
  
  function showTypingIndicator() {
    typingIndicator.style.display = 'block';
    typingIndicator.style.opacity = '1';
  }
  
  function hideTypingIndicator() {
    typingIndicator.style.opacity = '0';
    setTimeout(() => {
      typingIndicator.style.display = 'none';
    }, 500);
  }
  
  async function executeStep() {
    if (stepIndex >= demoSteps.length) return;
    
    const step = demoSteps[stepIndex];
    
    // Initial delay before starting this step
    await new Promise(r => setTimeout(r, step.beforeDelay));
    
    showTypingIndicator();
    
    // Clear input and type character by character
    userInput.value = "";
    const text = step.text;
    
    for (let i = 0; i < text.length; i++) {
      await new Promise(r => setTimeout(r, step.typingDelay));
      userInput.value = text.substring(0, i+1);
      
      // Position indicator near input field
      const inputRect = userInput.getBoundingClientRect();
      typingIndicator.style.left = `${inputRect.left - 50}px`;
      typingIndicator.style.top = `${inputRect.top - 40}px`;
    }
    
    hideTypingIndicator();
    
    // Send question
    sendBtn.click();
    
    // Wait after sending
    await new Promise(r => setTimeout(r, step.afterDelay));
    
    stepIndex++;
    executeStep();
  }

  // Start demo after initial delay
  setTimeout(executeStep, 3000);
}

// Add typing indicator styles
const typingStyles = document.createElement('style');
typingStyles.textContent = `
  .typing-indicator {
    position: fixed;
    display: none;
    opacity: 0;
    transition: opacity 0.3s;
    background: rgba(30, 30, 30, 0.8);
    padding: 8px 12px;
    border-radius: 24px;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  }
  
  .typing-indicator .dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #4ea6ff;
    border-radius: 50%;
    margin: 0 3px;
    animation: typing-bounce 1.4s infinite ease-in-out both;
  }
  
  .typing-indicator .dot:nth-child(1) {
    animation-delay: -0.32s;
  }
  
  .typing-indicator .dot:nth-child(2) {
    animation-delay: -0.16s;
  }
  
  @keyframes typing-bounce {
    0%, 80%, 100% { transform: translateY(0); }
    40% { transform: translateY(-8px); }
  }
`;
document.head.appendChild(typingStyles);

// Start demo when page loads
window.addEventListener('load', runPortfolioDemo);

});


