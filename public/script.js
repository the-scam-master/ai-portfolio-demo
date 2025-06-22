// Initialize the chat interface when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
  // Get DOM elements for the chat messages, user input, and send button
  const chatMessages = document.getElementById('chat-messages');
  const userInput = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  let source = null; // Tracks the EventSource for streaming responses

  // Scroll to the bottom of the chat messages container
  function scrollToBottom() {
    chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
  }

  // Create a message element for user or bot with avatar, content, and timestamp
  function createMessageElement(sender, content, isTyping = false) {
    const div = document.createElement('div');
    div.className = `message ${sender}-message`; // Apply user or bot message styling

    // Set avatar based on sender (Y for user, T for bot)
    const avatar = sender === 'user' ? 'Y' : 'T';
    // Get current time in 12-hour format (e.g., 3:45 PM)
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Show "Typing..." for bot's initial response, otherwise show the content
    const initialContent = isTyping ? '<em>Typing...</em>' : content;

    // Construct the message HTML with avatar, content, and timestamp
    div.innerHTML = `
      <div class="avatar">${avatar}</div>
      <div class="content">
        <span class="message-text">${initialContent}</span>
        <div class="timestamp">${time}</div>
      </div>
    `;

    // Append the message to the chat container and scroll to bottom
    chatMessages.appendChild(div);
    scrollToBottom();
    return div.querySelector('.message-text'); // Return the message text element for updates
  }

  // Close any existing EventSource stream to prevent multiple connections
  function stopPreviousStream() {
    if (source) {
      source.close();
      source = null;
    }
  }

  // Send user message to the API and handle the streaming response
  async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return; // Ignore empty messages

    stopPreviousStream(); // Close any previous streams

    // Display user message and create a placeholder for bot response
    createMessageElement('user', message);
    const botBubble = createMessageElement('bot', '', true);

    // Clear input field and keep it focused
    userInput.value = '';
    userInput.focus();

    try {
      // Send POST request to /api/chat with user message
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });

      // Check if response is valid and has a body
      if (!res.ok || !res.body) throw new Error('Failed to connect.');

      // Set up stream reader and text decoder
      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let done = false;
      let isFirstChunk = true; // Flag to clear "Typing..." on first chunk

      // Process streaming response chunks
      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;

        if (value) {
          const textChunk = decoder.decode(value, { stream: true });
          // Match lines starting with "data:" to extract JSON chunks
          const matches = textChunk.match(/data:\s*(.*?)\n/g);
          if (matches) {
            for (const line of matches) {
              const dataStr = line.replace(/^data:\s*/, '').trim();
              if (dataStr === '[DONE]') break; // End of stream

              try {
                const parsed = JSON.parse(dataStr);
                if (parsed.text) {
                  if (isFirstChunk) {
                    botBubble.innerHTML = ''; // Clear "Typing..." on first chunk
                    isFirstChunk = false;
                  }
                  // Use marked.parse to render full markdown, including links (fix for LinkedIn link rendering)
                  botBubble.innerHTML += marked.parse(parsed.text);
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
      botBubble.innerHTML = '**[Error receiving response]**'; // Display error in chat
    }
  }

  // Add event listeners for send button click and Enter key press
  sendBtn.addEventListener('click', sendMessage);
  userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });

  // Optional: Disable welcome message to match streaming UX
  // createMessageElement('bot', "Hi! I'm an AI assistant representing Tanmay Kalbande. Ask me anything!");
});
