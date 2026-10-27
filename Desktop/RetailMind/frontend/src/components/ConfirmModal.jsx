const ConfirmModal = ({ show, title, message, onConfirm, onCancel, confirmText = 'Delete', confirmClass = 'btn-danger', loading }) => {
  if (!show) return null;
  return (
    <div className="modal-backdrop-custom" onClick={onCancel}>
      <div className="modal-dialog-custom" onClick={e => e.stopPropagation()}>
        <div className="modal-header-custom">
          <h5>{title || 'Confirm Action'}</h5>
          <button className="btn-close" onClick={onCancel} />
        </div>
        <div className="modal-body-custom">
          <p>{message || 'Are you sure you want to proceed?'}</p>
        </div>
        <div className="modal-footer-custom">
          <button className="btn btn-secondary btn-sm" onClick={onCancel} disabled={loading}>Cancel</button>
          <button className={`btn ${confirmClass} btn-sm`} onClick={onConfirm} disabled={loading}>
            {loading ? <span className="spinner-border spinner-border-sm me-1" /> : null}
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;
