const AlertMessage = ({ type = 'danger', message, onClose }) => {
  if (!message) return null;
  return (
    <div className={`alert alert-${type} alert-dismissible d-flex align-items-start gap-2`} role="alert">
      <i className={`bi bi-${type === 'danger' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'} flex-shrink-0 mt-1`}></i>
      <div className="flex-grow-1">{message}</div>
      {onClose && (
        <button type="button" className="btn-close" onClick={onClose} aria-label="Close" />
      )}
    </div>
  );
};

export default AlertMessage;
