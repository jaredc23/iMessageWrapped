import React, { useRef, useEffect } from 'react';
import './BackupSelect.css';

const BackupSelect = ({ onCreate, backupLocation, setBackupLocation }) => {
  const fileInputRef = useRef(null);

  // Do not auto-load from localStorage on mount; require explicit user selection.

  const chooseWrappedFile = async () => {
    try {
      if (window.__TAURI__ && window.__TAURI__.dialog && typeof window.__TAURI__.dialog.open === 'function') {
        const opts = { multiple: false, filters: [{ name: '.imsgwrp', extensions: ['imsgwrp'] }] };
        if (backupLocation) opts.defaultPath = backupLocation;
        const selected = await window.__TAURI__.dialog.open(opts);
        if (selected) {
          const path = Array.isArray(selected) ? selected[0] : selected;
          // enforce .imsgwrp extension even if dialog allows other files
          const isValid = String(path).toLowerCase().endsWith('.imsgwrp');
          if (!isValid) {
            try { window.alert('Please select a file with the .imsgwrp extension'); } catch (e) {}
            return;
          }
          // record selection globally for fetcher and persist for future sessions
          try { window.__SELECTED_WRAPPED__ = path; } catch (e) {}
          setBackupLocation(path);
          try { localStorage.setItem('wrappedJsonPath', path); } catch (e) {}
          if (typeof onCreate === 'function') onCreate(path);
          return;
        }
      }
    } catch (e) {
      // fall back to web file input
    }
    if (fileInputRef.current) fileInputRef.current.click();
  };

  const onFallbackChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      // Validate extension client-side — browsers may still allow all files
      if (!(file.name || '').toLowerCase().endsWith('.imsgwrp')) {
        try { window.alert('Please choose a .imsgwrp file'); } catch (e) {}
        // clear the input so the user can try again
        e.target.value = '';
        return;
      }
      // create a blob URL so the app can fetch it via HTTP APIs
      try {
        const url = URL.createObjectURL(file);
        try { window.__SELECTED_WRAPPED__ = url; } catch (e) {}
        setBackupLocation(url);
        try { localStorage.setItem('wrappedJsonPath', url); } catch (e) {}
        if (typeof onCreate === 'function') onCreate(url);
      } catch (e) {
        // fallback to filename only (less reliable)
        const name = file.name || 'wrapped.json';
        try { window.__SELECTED_WRAPPED__ = name; } catch (e) {}
        setBackupLocation(name);
        try { localStorage.setItem('wrappedJsonPath', name); } catch (e) {}
        if (typeof onCreate === 'function') onCreate(name);
      }
    }
  };

  return (
    <div className="slide backup-select">
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: 12}}>
        <h2>Select Your iMessage Wrapped File</h2>

        <div style={{marginBottom: 12}}>
          <button className="get-started" onClick={chooseWrappedFile}>Choose .imsgwrp file</button>
        </div>

        <input ref={fileInputRef} type="file" style={{display: 'none'}} accept=".imsgwrp" onChange={onFallbackChange} />

        <div style={{marginTop: 12}} />
      </div>
    </div>
  );
};

export default BackupSelect;
