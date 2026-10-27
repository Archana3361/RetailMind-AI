const EmptyState = ({ icon = 'inbox', title = 'No data found', message, action }) => (
  <div className="empty-state">
    <i className={`bi bi-${icon}`}></i>
    <h5>{title}</h5>
    {message && <p>{message}</p>}
    {action}
  </div>
);

export default EmptyState;
