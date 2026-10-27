const LoadingSpinner = ({ text = 'Loading...' }) => (
  <div className="loading-container">
    <div className="spinner-border text-primary" role="status" style={{ width: '2rem', height: '2rem' }}>
      <span className="visually-hidden">{text}</span>
    </div>
    <p className="loading-text">{text}</p>
  </div>
);

export default LoadingSpinner;
