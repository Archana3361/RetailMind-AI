const Pagination = ({ page, pages, onPage }) => {
  if (!pages || pages <= 1) return null;

  const getPages = () => {
    const items = [];
    const delta = 2;
    const left = Math.max(2, page - delta);
    const right = Math.min(pages - 1, page + delta);
    items.push(1);
    if (left > 2) items.push('...');
    for (let i = left; i <= right; i++) items.push(i);
    if (right < pages - 1) items.push('...');
    if (pages > 1) items.push(pages);
    return items;
  };

  return (
    <nav className="table-pagination">
      <ul className="pagination pagination-sm mb-0">
        <li className={`page-item ${page <= 1 ? 'disabled' : ''}`}>
          <button className="page-link" onClick={() => onPage(page - 1)}>
            <i className="bi bi-chevron-left"></i>
          </button>
        </li>
        {getPages().map((p, i) =>
          p === '...' ? (
            <li key={`e${i}`} className="page-item disabled">
              <span className="page-link">…</span>
            </li>
          ) : (
            <li key={p} className={`page-item ${p === page ? 'active' : ''}`}>
              <button className="page-link" onClick={() => onPage(p)}>{p}</button>
            </li>
          )
        )}
        <li className={`page-item ${page >= pages ? 'disabled' : ''}`}>
          <button className="page-link" onClick={() => onPage(page + 1)}>
            <i className="bi bi-chevron-right"></i>
          </button>
        </li>
      </ul>
    </nav>
  );
};

export default Pagination;
