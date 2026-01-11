import { useState, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://127.0.0.1:8000/api';

function App() {
  const [activeTab, setActiveTab] = useState('bg-remove'); // 'bg-remove' | 'resize'
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  // Resize State
  const [resizeUnit, setResizeUnit] = useState('percent');
  const [resizeWidth, setResizeWidth] = useState(0);
  const [resizeHeight, setResizeHeight] = useState(0);
  const [originalDimensions, setOriginalDimensions] = useState({ w: 0, h: 0 });
  const [resizeScale, setResizeScale] = useState(50);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    handleReset();
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      processFile(selectedFile);
    }
  };

  const processFile = (selectedFile) => {
    if (!selectedFile.type.startsWith('image/')) {
      setError('Please upload an image file (JPG, PNG, etc)');
      return;
    }

    setFile(selectedFile);
    const objectUrl = URL.createObjectURL(selectedFile);
    setPreview(objectUrl);
    setResult(null);
    setError(null);

    const img = new Image();
    img.onload = () => {
      setOriginalDimensions({ w: img.width, h: img.height });
      setResizeWidth(img.width);
      setResizeHeight(img.height);
    };
    img.src = objectUrl;
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('dragging');
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragging');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragging');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('image', file);

    try {
      let endpoint = '';
      if (activeTab === 'bg-remove') {
        endpoint = `${API_URL}/remove-background/`;
        formData.append('confidence', 0.25);
      } else {
        endpoint = `${API_URL}/resize-image/`;
        if (resizeUnit === 'px') {
          formData.append('width', resizeWidth);
          formData.append('height', resizeHeight);
        } else {
          formData.append('scale', resizeScale);
        }
      }

      const response = await axios.post(endpoint, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.data.success) {
        setResult(response.data.processed_image_url);
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || 'Failed to process image.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDownload = async () => {
    if (result) {
      try {
        setLoading(true);
        const response = await fetch(result);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        const prefix = activeTab === 'bg-remove' ? 'nobg' : 'resized';
        link.download = `${prefix}_${file.name.split('.')[0]}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } catch (err) {
        console.error('Download failed:', err);
        setError('Failed to download image');
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="app-container">
      {/* Sticky Navbar */}
      <nav className="navbar">
        <div className="nav-content">
          <a href="#" className="brand">Image Studio Pro</a>
          <div className="nav-links">
            <button
              className={`nav-btn ${activeTab === 'bg-remove' ? 'active' : ''}`}
              onClick={() => handleTabChange('bg-remove')}
            >
              ✨ Background Remover
            </button>
            <button
              className={`nav-btn ${activeTab === 'resize' ? 'active' : ''}`}
              onClick={() => handleTabChange('resize')}
            >
              📏 Image Resizer
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="main-content">
        <div className="header-section">
          <h1>
            {activeTab === 'bg-remove' ? 'Remove Backgrounds Instantly' : 'Resize Images with Precision'}
          </h1>
          <p className="subtitle">
            {activeTab === 'bg-remove'
              ? 'Upload your image and let our AI do the magic in seconds.'
              : 'Scale your images perfectly for any platform or use case.'}
          </p>
        </div>

        <div className="card-container">
          {!preview ? (
            <div
              className="drop-zone"
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current.click()}
            >
              <span className="icon-large">
                {activeTab === 'bg-remove' ? '🖼️' : '📐'}
              </span>
              <h3>Click or Drag Image Here</h3>
              <p style={{ color: 'var(--text-muted)' }}>Supports JPG, PNG, WEBP</p>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="image/*"
                hidden
              />
            </div>
          ) : (
            <div className="preview-area">

              {/* Resize Controls */}
              {activeTab === 'resize' && !result && (
                <div className="resize-controls">
                  <div className="unit-toggle">
                    <button
                      className={`unit-btn ${resizeUnit === 'percent' ? 'active' : ''}`}
                      onClick={() => setResizeUnit('percent')}
                    >
                      Percentage
                    </button>
                    <button
                      className={`unit-btn ${resizeUnit === 'px' ? 'active' : ''}`}
                      onClick={() => setResizeUnit('px')}
                    >
                      Pixels
                    </button>
                  </div>

                  {resizeUnit === 'percent' ? (
                    <div>
                      <div className="slider-container">
                        <span>1%</span>
                        <input
                          type="range"
                          min="1"
                          max="200"
                          value={resizeScale}
                          onChange={(e) => setResizeScale(e.target.value)}
                          className="slider"
                        />
                        <span>200%</span>
                      </div>
                      <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>
                        Scale: <strong>{resizeScale}%</strong> ({Math.round(originalDimensions.w * (resizeScale / 100))} × {Math.round(originalDimensions.h * (resizeScale / 100))} px)
                      </p>
                    </div>
                  ) : (
                    <div className="input-row">
                      <div className="input-wrapper">
                        <label>Width</label>
                        <input
                          type="number"
                          className="input-field"
                          value={resizeWidth}
                          onChange={(e) => setResizeWidth(e.target.value)}
                        />
                      </div>
                      <div className="input-wrapper">
                        <label>Height</label>
                        <input
                          type="number"
                          className="input-field"
                          value={resizeHeight}
                          onChange={(e) => setResizeHeight(e.target.value)}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}

              {error && <div style={{ color: 'var(--error)', margin: '1rem 0' }}>{error}</div>}

              {/* Images Grid */}
              <div className="result-grid">
                <div className="image-card">
                  <h3>Original</h3>
                  <img src={preview} alt="Original" className="img-preview" />
                  <p style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {originalDimensions.w} × {originalDimensions.h} px
                  </p>
                </div>

                <div className="image-card">
                  <h3>Result</h3>
                  <div className={activeTab === 'bg-remove' ? 'transparency-bg' : ''} style={{ width: '100%', borderRadius: '8px', overflow: 'hidden' }}>
                    {loading ? (
                      <div style={{ padding: '3rem 0' }}>
                        <div className="loading-spinner"></div>
                        <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>Processing...</p>
                      </div>
                    ) : result ? (
                      <img src={result} alt="Result" className="img-preview" />
                    ) : (
                      <div style={{ padding: '3rem 1rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        <span style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>✨</span>
                        Ready to process
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="action-buttons">
                {!result && !loading && (
                  <button className="btn-primary" onClick={handleSubmit}>
                    {activeTab === 'bg-remove' ? '✨ Remove Background' : '⚡ Resize Image'}
                  </button>
                )}

                {result && (
                  <button className="btn-primary" onClick={handleDownload} style={{ background: 'var(--success)' }}>
                    ⬇️ Download Result
                  </button>
                )}

                <button
                  className="btn-primary btn-secondary"
                  onClick={handleReset}
                >
                  🔄 Upload New Image
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
