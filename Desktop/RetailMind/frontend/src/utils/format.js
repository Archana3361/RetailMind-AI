export const formatCurrency = (amount, symbol = '₹') => {
  if (amount === null || amount === undefined) return `${symbol}0.00`;
  return `${symbol}${Number(amount).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
};

export const formatNumber = (n) => {
  if (n === null || n === undefined) return '0';
  return Number(n).toLocaleString('en-IN');
};

export const formatDate = (dateStr) => {
  if (!dateStr) return '—';
  try {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
    });
  } catch { return '—'; }
};

export const formatDateTime = (dateStr) => {
  if (!dateStr) return '—';
  try {
    return new Date(dateStr).toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return '—'; }
};

export const formatPercent = (n) => {
  if (n === null || n === undefined) return '0%';
  return `${Number(n).toFixed(1)}%`;
};

export const stockStatusLabel = (status) => {
  const map = {
    in_stock: 'In Stock',
    low_stock: 'Low Stock',
    out_of_stock: 'Out of Stock',
  };
  return map[status] || status;
};

export const stockStatusClass = (status) => {
  const map = {
    in_stock: 'badge-in-stock',
    low_stock: 'badge-low-stock',
    out_of_stock: 'badge-out-of-stock',
  };
  return map[status] || '';
};

export const restockStatusClass = (status) => {
  const map = {
    'OUT OF STOCK': 'restock-badge-out-of-stock',
    'RESTOCK': 'restock-badge-restock',
    'RESTOCK SOON': 'restock-badge-restock-soon',
    'MONITOR': 'restock-badge-monitor',
    'OVERSTOCK': 'restock-badge-overstock',
    'HEALTHY': 'restock-badge-healthy',
    'NO IMMEDIATE ACTION': 'restock-badge-healthy',
  };
  return map[status] || '';
};
