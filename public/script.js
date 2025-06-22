document.addEventListener('DOMContentLoaded', () => {
  const chatMessages = document.getElementById('chat-messages');
  const userInput = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  let lastUserMessage = '';

  function scrollToBottom() {
    chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
  }

  function addMessageToUI(content, sender, showRetry = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    const avatar = sender === 'user' ? 'Y' : 'T';
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const innerContent = sender === 'bot'
      ? marked.parse(content)
      : content.replace(/\n/g, '<br>');

    messageDiv.innerHTML = `
      <div class="avatar">${avatar}</div>
      <div class="content">
        ${innerContent}
        <div class="timestamp">${time}</div>
        ${showRetry ? `<div class="retry-button">↺ Try Again</div>` : ''}
      </div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    if (showRetry) {
      messageDiv.querySelector('.retry-button').addEventListener('click', () => {
        userInput.value = lastUserMessage;
        userInput.focus();
      });
    }
  }

  function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message bot-message typing-indicator';
    indicator.innerHTML = `
      <div class="avatar">T</div>
      <div class="content"><em>Typing...</em></div>
    `;
    chatMessages.appendChild(indicator);
    scrollToBottom();
    return indicator;
  }

  async function sendMessage() {
    const message = userInput.value.trim();
    if (!message || message.length > 300) return;

    lastUserMessage = message;
    addMessageToUI(message, 'user');
    userInput.value = '';
    userInput.focus();

    const typing = showTypingIndicator();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      });

      const data = await res.json();
      const reply = data.reply || "Sorry, I couldn't generate a response.";
      addMessageToUI(reply, 'bot', true);
    } catch (err) {
      console.error(err);
      addMessageToUI("Sorry, I'm having trouble right now. Please try again later.", 'bot');
    } finally {
      typing.remove();
    }
  }

  sendBtn.addEventListener('click', sendMessage);
  userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });

  addMessageToUI(
    "Hi! I'm an AI assistant representing Tanmay Kalbande. Feel free to ask me anything about his skills, projects, and experience!",
    'bot'
  );
});
