import React, { useState } from 'react';
import './App.css';
import { ThemeProvider, ThemeContext } from './context/ThemeContext';
import OverviewTotals from './components/OverviewTotals';
import WordsPerMessageByHour from './components/WordsPerMessageByHour';
import TopConversations from './components/TopConversations';
import Top15Emoji from './components/Top15Emoji';
import TopChatsByAttachments from './components/TopChatsByAttachments';
import SlowestResponseNonGroup from './components/SlowestResponseNonGroup';
import FastestResponseNonGroup from './components/FastestResponseNonGroup';
import EmojiTimeline from './components/EmojiTimeline';
import Top5ChatsTimeline from './components/Top5ChatsTimeline';
import TopConversation from './components/TopConversation';
import ResponseTimeByHour from './components/ResponseTimeByHour';
import MessagesSentTimelineSlide from './components/MessagesSentTimelineSlide';
import MessagesSentByHourSlide from './components/MessagesSentByHourSlide';
import SummarySlide from './components/SummarySlide';
import SetupTitle from './components/SetupTitle';
import BackupSelect from './components/BackupSelect';
// DatabaseParse removed — parsing is handled externally

const slides = [
  // Setup flow
  SetupTitle,
  BackupSelect,
  // Main slides
  OverviewTotals,
  WordsPerMessageByHour,
  TopConversation,
  TopConversations,
  Top5ChatsTimeline,
  ResponseTimeByHour,
  //FastestResponseNonGroup,
  //SlowestResponseNonGroup,
  Top15Emoji,
  EmojiTimeline,
  TopChatsByAttachments,
  MessagesSentTimelineSlide,
  MessagesSentByHourSlide,
  SummarySlide,
];

function App() {
  const [currentSlide, setCurrentSlide] = useState(0);
  React.useEffect(() => {
    document.title = 'iMessage Wrapped';
  }, []);
  

  const ThemeToggle = () => {
    const { theme, toggleTheme } = React.useContext(ThemeContext);
    React.useEffect(() => {
      document.documentElement.setAttribute('data-theme', theme || 'light');
    }, [theme]);
    return (
      <div className="theme-toggle">
        <button aria-label="Toggle theme" className="theme-button" onClick={() => toggleTheme()}>
          <span className="theme-icon">{theme === 'dark' ? '🌙' : '☀️'}</span>
        </button>
      </div>
    );
  };

  const goToNextSlide = () => {
    if (currentSlide < slides.length - 1) {
      setCurrentSlide(currentSlide + 1);
    }
  };

  const goToPreviousSlide = () => {
    if (currentSlide > 0) {
      // if coming back from parse page, go to select
      if (currentSlide === 2) {
        setCurrentSlide(1);
      } else {
        setCurrentSlide(currentSlide - 1);
      }
    }
  };

  const CurrentSlideComponent = slides[currentSlide];
  const setupCount = 2; // number of initial setup slides (SetupTitle, BackupSelect)
  const [backupLocation, setBackupLocation] = useState('');

  return (
    <ThemeProvider>
      <div className="App">
        <ThemeToggle />
      <div className="progress-bar">
        {slides.map((_, index) => (
          <div
            key={index}
            className={`progress-dot ${index === currentSlide ? 'active' : ''}`}
          ></div>
        ))}
      </div>
      <div className="slide-container">
        {(() => {
          const showBack = currentSlide > 0;
          // only show forward navigation for main slides before the last slide (hide on summary)
          const showForward = currentSlide >= setupCount && currentSlide < slides.length - 1;

          const renderCurrent = () => {
            // wire slide-specific props for the setup flow
            if (currentSlide === 0) {
              return <CurrentSlideComponent onStart={() => setCurrentSlide(1)} />;
            }
                if (currentSlide === 1) {
                const handleLoadWrapped = (providedPath) => {
                  // Only accept an explicit selection from the BackupSelect component
                  const effectivePath = providedPath || backupLocation;
                  if (!effectivePath) {
                    alert('Please choose a wrapped.json file first');
                    return;
                  }

                  try { window.__SELECTED_WRAPPED__ = effectivePath; } catch (e) {}
                  try { localStorage.setItem('wrappedJsonPath', effectivePath); } catch (e) {}
                  try { setBackupLocation(effectivePath); } catch (e) {}
                  // advance to first main slide
                  setCurrentSlide(2);
                };

                return (
                  <CurrentSlideComponent
                    onCreate={handleLoadWrapped}
                    onUseExisting={() => setCurrentSlide(2)}
                    backupLocation={backupLocation}
                    setBackupLocation={setBackupLocation}
                  />
                );
              }
            if (currentSlide === 2) {
              return <CurrentSlideComponent backupLocation={backupLocation} />;
            }

            return <CurrentSlideComponent key={currentSlide} backupLocation={backupLocation} />;
          };

          return (
            <>
              <div className="nav-left" onClick={goToPreviousSlide} style={{visibility: showBack ? 'visible' : 'hidden'}}>
                <span className="arrow">&#9664;</span>
              </div>
              <div className="slide-content">
                <div className="iphone-frame">
                  <div className="iphone-screen" style={{overflow: currentSlide === 0 ? 'hidden' : undefined}}>
                    {renderCurrent()}
                  </div>
                  <div className="iphone-bottom-hole" />
                </div>
              </div>
              <div className="nav-right" onClick={goToNextSlide} style={{visibility: showForward ? 'visible' : 'hidden'}}>
                <span className="arrow">&#9654;</span>
              </div>
            </>
          );
        })()}
      </div>
    </div>
    </ThemeProvider>
  );
}

export default App;
