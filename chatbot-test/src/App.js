import React from 'react';
import './App.css';
import ChatBot from './components/ChatBot';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 Chatbot Test Page</h1>
        <p>Testing the PE/VC chatbot independently</p>
      </header>
      
      <main style={{ padding: '40px', minHeight: '60vh' }}>
        <div style={{ 
          maxWidth: '800px', 
          margin: '0 auto', 
          backgroundColor: 'white', 
          padding: '30px', 
          borderRadius: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
        }}>
          <h2>Welcome to the Chatbot Test</h2>
          <p>Look for the floating 💬 button in the bottom-right corner.</p>
          <p>Click it to open the chatbot and start asking questions!</p>
          
          <h3>Sample Questions:</h3>
          <ul style={{ textAlign: 'left' }}>
            <li>How do I invest?</li>
            <li>What is the minimum investment?</li>
            <li>How do I access my documents?</li>
          </ul>
        </div>
      </main>
      
      {/* ChatBot component - renders floating button */}
      <ChatBot 
        userId="test-investor-123" 
        portalName="Test Portal" 
      />
    </div>
  );
}

export default App;