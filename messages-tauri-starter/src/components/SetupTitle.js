import React from 'react';
import './SetupTitle.css';

const SetupTitle = ({ onStart }) => {
  return (
    <div className="slide title-slide">
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%'}}>
        <h1 style={{fontSize: '3rem', marginBottom: '1rem'}}>iMessage Wrapped</h1>
        <p style={{opacity: 0.85, marginBottom: '2rem'}}>A quick look at your messaging year</p>
        <button className="get-started" onClick={onStart}>Get Started</button>
      </div>
    </div>
  );
};

export default SetupTitle;
