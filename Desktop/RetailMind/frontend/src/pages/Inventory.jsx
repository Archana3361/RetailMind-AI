import { useState, useEffect, useCallback } from 'react';
import { inventoryApi } from '../services/api';
import PageHeader from '../components/PageHeader';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import AlertMessage from '../components/AlertMessage';
import Pagination from '../components/Pagination';
import StatCard from '../components/StatCard';
import { formatCurrency, formatDateTime, stockStatusLabel, stockStatusClass } from '../utils/format';

const Inventory = () => {
  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [stockFilter, setStockFilter] = useState('');
  const [activeTab, setActiveTab] = useState('inventory');
  const [transactions, setTransactions] = useState([]);
  const [txnLoading, setTxnLoading] = useState(false);
  const [txnPage, setTxnPage] = useState(1);
  const [txnTotal, setTxnTotal] = useState(0);

  const fetchInventory = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const [invRes, sumRes] = await Promise.all([
        inventoryApi.list({ page: p, per_page: 20, search, stock_status: stockFilter }),
        inventoryApi.summary(),
      ]);
      setItems(invRes.data.items); setPages(invRes.data.pages); setTotal(invRes.data.total);
      setSummary(sumRes.data);
    } catch { setError('Failed to load inventory.'); }
    finally { setLoading(false); }
  }, [search, stockFilter]);

  const fetchTransactions = useCallback(async (p = 1) => {
    setTxnLoading(true);
    try {
      const r = await inventoryApi.transactions({ page: p, per_page: 20 });
      setTransactions(r.data.items); setTxnTotal(r.data.total);
    } catch (err) {
      console.error('Failed to load transactions:', err);
      setError('Failed to load transactions.');
    }
    finally { setTxnLoading(false); }
  }, []);

  useEffect(() => { fetchInventory(page); }, [page]);
  useEffect(() => { setPage(1); fetchInventory(1); }, [search, stockFilter]);
  useEffect(() => { if (activeTab === 'movements') fetchTransactions(txnPage); }, [activeTab, txnPage]);

  const txnIcon = (type) => {
    const m = { sale: 'arrow-up-right', purchase: 'arrow-down-left', adjustment: 'sliders', return: 'arrow-return-left' };
    return m[type] || 'arrow-left-right';
  };
  const txnColor = (type) => type === 'sale' ? 'text-danger' : type === 'purchase' ? 'text-success' : 'text-secondary';

  return (
    <div className="page-container">
      <PageHeader title="Inventory" subtitle="Track stock levels, movements, and value" />

      <AlertMessage type="danger" message={error} onClose={() => setError('')} />

      {/* Summary cards */}
      <div className="stats-grid mb-4">
        <StatCard title="Total Products" value={summary.total_products || 0} icon="box-seam" colorClass="stat-blue" />
        <StatCard title="Stock Value" value={formatCurrency(summary.total_stock_value)} icon="currency-rupee" colorClass="stat-teal" />
        <StatCard title="Low Stock" value={summary.low_stock_count || 0} icon="exclamation-triangle" colorClass="stat-orange" />
        <StatCard title="Out of Stock" value={summary.out_of_stock_count || 0} icon="x-circle" colorClass="stat-red" />
      </div>

      {/* Tabs */}
      <div className="rm-tabs mb-3">
        <button className={`rm-tab ${activeTab === 'inventory' ? 'active' : ''}`} onClick={() => setActiveTab('inventory')}>
          <i className="bi bi-archive me-2"></i>Stock Levels
        </button>
        <button className={`rm-tab ${activeTab === 'movements' ? 'active' : ''}`} onClick={() => setActiveTab('movements')}>
          <i className="bi bi-arrow-left-right me-2"></i>Stock Movements
        </button>
      </div>

      {activeTab === 'inventory' && (
        <>
          <div className="filter-bar mb-3">
            <div className="search-input-wrap">
              <i className="bi bi-search search-icon"></i>
              <input className="form-control search-input" placeholder="Search product or SKU..."
                value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <select className="form-select filter-select" value={stockFilter} onChange={e => setStockFilter(e.target.value)}>
              <option value="">All Status</option>
              <option value="in_stock">In Stock</option>
              <option value="low_stock">Low Stock</option>
              <option value="out_of_stock">Out of Stock</option>
            </select>
          </div>

          {loading ? <LoadingSpinner /> : items.length === 0 ? (
            <EmptyState icon="archive" title="No inventory records" message="Add products to track your inventory." />
          ) : (
            <>
              <div className="table-responsive">
                <table className="rm-table">
                  <thead>
                    <tr>
                      <th>Product</th><th>SKU</th><th>Category</th>
                      <th>Current</th><th>Minimum</th><th>Unit</th>
                      <th>Cost</th><th>Stock Value</th><th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map(item => (
                      <tr key={item.product_id}>
                        <td><p className="product-name mb-0">{item.name}</p></td>
                        <td><code className="sku-code">{item.sku}</code></td>
                        <td>{item.category || <span className="text-muted">—</span>}</td>
                        <td>
                          <span className={
                            item.current_stock <= 0 ? 'fw-bold text-danger' :
                            item.current_stock <= item.minimum_stock ? 'fw-bold text-warning' : 'fw-semibold'
                          }>
                            {item.current_stock}
                          </span>
                        </td>
                        <td>{item.minimum_stock}</td>
                        <td>{item.unit}</td>
                        <td>{formatCurrency(item.cost_price)}</td>
                        <td>{formatCurrency(item.stock_value)}</td>
                        <td>
                          <span className={`stock-badge ${stockStatusClass(item.stock_status)}`}>
                            {stockStatusLabel(item.stock_status)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={page} pages={pages} onPage={p => setPage(p)} />
            </>
          )}
        </>
      )}

      {activeTab === 'movements' && (
        <>
          {txnLoading ? <LoadingSpinner /> : transactions.length === 0 ? (
            <EmptyState icon="arrow-left-right" title="No stock movements" message="Movements are recorded when sales or purchases are made." />
          ) : (
            <>
              <div className="table-responsive">
                <table className="rm-table">
                  <thead>
                    <tr><th>Product</th><th>SKU</th><th>Type</th><th>Change</th><th>Before</th><th>After</th><th>Note</th><th>Date</th></tr>
                  </thead>
                  <tbody>
                    {transactions.map(t => (
                      <tr key={t.id}>
                        <td><p className="product-name mb-0">{t.product_name}</p></td>
                        <td><code className="sku-code">{t.sku}</code></td>
                        <td>
                          <span className={`txn-type ${txnColor(t.transaction_type)}`}>
                            <i className={`bi bi-${txnIcon(t.transaction_type)} me-1`}></i>
                            {t.transaction_type}
                          </span>
                        </td>
                        <td>
                          <span className={t.quantity_change > 0 ? 'text-success fw-semibold' : 'text-danger fw-semibold'}>
                            {t.quantity_change > 0 ? '+' : ''}{t.quantity_change}
                          </span>
                        </td>
                        <td>{t.stock_before}</td>
                        <td>{t.stock_after}</td>
                        <td className="text-muted small">{t.notes}</td>
                        <td>{formatDateTime(t.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={txnPage} pages={Math.ceil(txnTotal / 20)} onPage={p => setTxnPage(p)} />
            </>
          )}
        </>
      )}
    </div>
  );
};

export default Inventory;
