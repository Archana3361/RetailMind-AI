import { useState, useEffect } from 'react';
import { mlApi } from '../services/api';
import PageHeader from '../components/PageHeader';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import AlertMessage from '../components/AlertMessage';
import { restockStatusClass } from '../utils/format';

const STATUS_ORDER = {
  'RESTOCK': 0,
  'MONITOR': 1,
  'NO IMMEDIATE ACTION': 2,
};

const StockIntelligence = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('ALL');

  const load = () => {
    setLoading(true); setError('');
    mlApi.stockIntelligence()
      .then(r => setData(r.data))
      .catch(() => setError('Failed to load stock intelligence. Ensure the ML model is running.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const products = data?.products || [];
  const filtered = filter === 'ALL' ? products : products.filter(p => p.status === filter);
  const summary = data?.summary || {};

  const statusIcon = (s) => {
    if (s === 'RESTOCK') return 'exclamation-triangle-fill';
    if (s === 'MONITOR') return 'eye-fill';
    return 'check-circle-fill';
  };

  return (
    <div className="page-container">
      <PageHeader
        title="Stock Intelligence"
        subtitle="ML-powered restock recommendations for all active products"
        actions={
          <button className="btn btn-outline-primary btn-sm" onClick={load} disabled={loading}>
            <i className="bi bi-arrow-clockwise me-2"></i>Refresh
          </button>
        }
      />

      <AlertMessage type="danger" message={error} onClose={() => setError('')} />

      <div className="prediction-disclaimer mb-3">
        <i className="bi bi-cpu me-2"></i>
        <span>
          Predictions use the HistGradientBoosting model trained on historical retail data.
          The model considers category, pricing, promotions, and demand history to estimate expected demand.
          Results guide restocking decisions alongside your business knowledge.
        </span>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="si-summary-row mb-4">
          <div className="si-summary-card si-restock">
            <i className="bi bi-exclamation-triangle-fill"></i>
            <div>
              <p className="si-count">{summary.restock_count || 0}</p>
              <p className="si-label">Need Restock</p>
            </div>
          </div>
          <div className="si-summary-card si-monitor">
            <i className="bi bi-eye-fill"></i>
            <div>
              <p className="si-count">{summary.monitor_count || 0}</p>
              <p className="si-label">Monitor</p>
            </div>
          </div>
          <div className="si-summary-card si-safe">
            <i className="bi bi-check-circle-fill"></i>
            <div>
              <p className="si-count">{summary.safe_count || 0}</p>
              <p className="si-label">Safe</p>
            </div>
          </div>
          <div className="si-summary-card si-total">
            <i className="bi bi-box-seam-fill"></i>
            <div>
              <p className="si-count">{summary.total_products || 0}</p>
              <p className="si-label">Total Products</p>
            </div>
          </div>
        </div>
      )}

      {/* Filter */}
      <div className="rm-tabs mb-3">
        {['ALL', 'RESTOCK', 'MONITOR', 'NO IMMEDIATE ACTION'].map(f => (
          <button key={f} className={`rm-tab ${filter === f ? 'active' : ''}`} onClick={() => setFilter(f)}>
            {f === 'ALL' ? 'All Products' : f}
            {f !== 'ALL' && (
              <span className={`ms-2 badge ${f === 'RESTOCK' ? 'bg-danger' : f === 'MONITOR' ? 'bg-warning text-dark' : 'bg-success'}`}>
                {f === 'RESTOCK' ? summary.restock_count : f === 'MONITOR' ? summary.monitor_count : summary.safe_count}
              </span>
            )}
          </button>
        ))}
      </div>

      {loading ? <LoadingSpinner text="Running ML predictions..." /> :
        filtered.length === 0 ? (
          products.length === 0 ? (
            <EmptyState icon="box-seam" title="No products found"
              message="Add products to get ML-powered restock recommendations." />
          ) : (
            <EmptyState icon="funnel" title={`No products with status "${filter}"`} />
          )
        ) : (
          <div className="table-responsive">
            <table className="rm-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Category</th>
                  <th>Current Stock</th>
                  <th>Min Stock</th>
                  <th>Predicted Demand</th>
                  <th>Safety Stock</th>
                  <th>Required</th>
                  <th>Suggested Order</th>
                  <th>Coverage</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(p => (
                  <tr key={p.product_id} className={p.status === 'RESTOCK' ? 'tr-highlight-danger' : p.status === 'MONITOR' ? 'tr-highlight-warning' : ''}>
                    <td>
                      <div className="product-cell">
                        <p className="product-name">{p.product_name}</p>
                        <p className="product-sku">{p.sku}</p>
                      </div>
                    </td>
                    <td>{p.category}</td>
                    <td>
                      <span className={p.current_stock <= 0 ? 'text-danger fw-bold' : p.current_stock < p.predicted_demand ? 'text-warning fw-semibold' : ''}>
                        {p.current_stock}
                      </span>
                    </td>
                    <td>{p.minimum_stock}</td>
                    <td className="fw-semibold">{p.predicted_demand}</td>
                    <td>{p.safety_stock}</td>
                    <td>{p.required_stock}</td>
                    <td>
                      {p.reorder_quantity > 0
                        ? <strong className="text-primary">{p.reorder_quantity}</strong>
                        : <span className="text-muted">—</span>}
                    </td>
                    <td>
                      <span className={parseFloat(p.coverage_ratio) < 1 ? 'text-danger' : parseFloat(p.coverage_ratio) < 1.25 ? 'text-warning' : 'text-success'}>
                        {p.coverage_ratio === Infinity || p.coverage_ratio > 999 ? '∞' : `${p.coverage_ratio}x`}
                      </span>
                    </td>
                    <td>
                      <span className={`restock-badge ${restockStatusClass(p.status)}`}>
                        <i className={`bi bi-${statusIcon(p.status)} me-1`}></i>
                        {p.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      }
    </div>
  );
};

export default StockIntelligence;
