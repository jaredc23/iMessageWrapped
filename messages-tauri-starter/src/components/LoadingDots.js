import React from 'react';

const LoadingDots = () => {
  return (
    <div className="slide">
      <div className="loading-dots" role="status" aria-label="Loading">
        <span className="dot" />
        <span className="dot" />
        <span className="dot" />
      </div>
    </div>
  );
};

export default LoadingDots;
