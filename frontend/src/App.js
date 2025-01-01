import React from 'react';
import './App.css';
import LofiConverter from './components/LofiConverter';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Lofi Converter</h1>
      </header>
      <main>
        <LofiConverter />
      </main>
    </div>
  );
}

export default App;
