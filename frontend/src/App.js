import React from "react";
import "./App.css";
import ChatWindow from "./components/ChatWindow";

function App() {
  return (
    <div className="App">
      <header className="heading">
        <div className="heading-content">
          <div className="heading-title">
            <img 
              src="/logo.png" 
              alt="PartSelect" 
              className="heading-logo"
              onError={(e) => e.target.style.display = 'none'}
            />
            PartSelect Support
          </div>
        </div>
      </header>
      <main className="main-content">
        <ChatWindow />
      </main>
    </div>
  );
}

export default App;
