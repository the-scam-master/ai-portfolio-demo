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

function runPortfolioDemo() {
  const demoSteps = [
    { text: "What projects show your AI skills?", delay: 1000 },
    { text: "Favorite anime?", delay: 3000 },
    { text: "Show me Python skills", delay: 3000 },
    { action: "mobile-test", delay: 4000 }
  ];

  let stepIndex = 0;
  const userInput = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  
  function executeStep() {
    if (stepIndex >= demoSteps.length) return;
    
    const step = demoSteps[stepIndex];
    setTimeout(() => {
      if (step.text) {
        // Auto-type question
        userInput.value = step.text;
        sendBtn.click();
      } else if (step.action === "mobile-test") {
        // Toggle mobile view
        document.body.classList.toggle('mobile-preview');
        alert("Switching to mobile view! Press OK to continue...");
      }
      stepIndex++;
      executeStep();
    }, step.delay);
  }

  // Start demo after 2 seconds
  setTimeout(executeStep, 2000);
}

// Start demo when page loads
window.addEventListener('load', runPortfolioDemo);  
});


