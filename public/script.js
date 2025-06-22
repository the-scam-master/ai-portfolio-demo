document.addEventListener('DOMContentLoaded', () => {
  const chatMessages = document.getElementById('chat-messages');
  const userInput = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  let source = null;

  function scrollToBottom() {
    chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
  }

  function createMessageElement(sender, content, isTyping = false) {
    const div = document.createElement('div');
    div.className = `message ${sender}-message`;

    const avatar = sender === 'user' ? 'Y' : 'T';
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const initialContent = isTyping ? '<em>Typing...</em>' : content;

    div.innerHTML = `
      <div class="avatar">${avatar}</div>
      <div class="content">
        <span class="message-text">${initialContent}</span>
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

    userInput.value = '';
    userInput.focus();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });

      if (!res.ok || !res.body) throw new Error('Failed to connect.');

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let done = false;
      let isFirstChunk = true;

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
                  if (isFirstChunk) {
                    botBubble.innerHTML = '';
                    isFirstChunk = false;
                  }
                  botBubble.innerHTML += marked.parseInline(parsed.text);
                  scrollToBottom();
                }
              } catch (err) {
                console.error('Invalid chunk:', dataStr);
              }
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
      botBubble.innerHTML = '**[Error receiving response]**';
    }
  }

  sendBtn.addEventListener('click', sendMessage);
  userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });

  // Optional welcome message (disable if using streaming UX only)
  // createMessageElement('bot', "Hi! I'm an AI assistant representing Tanmay Kalbande. Ask me anything!");
});
