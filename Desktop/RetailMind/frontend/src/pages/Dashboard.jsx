import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { dashboardApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import PageHeader from '../components/PageHeader';
import StatCard from '../components/StatCard';
import LoadingSpinner from '../components/LoadingSpinner';
import AlertMessage from '../components/AlertMessage';
import { formatCurrency, formatNumber, formatDateTime, restockStatusClass } from '../utils/format';

const RestockBadge = ({ status }) => {
  const cls = restockStatusClass(status);
  return <span className={`restock-badge ${cls}`}>{status}</span>;
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip-label">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>
          {p.name}: {p.name === 'revenue' ? formatCurrency(p.value) : formatNumber(p.value)}
        </p>
      ))}
    </div>
  );
};

const Dashboard = () => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    dashboardApi.get()
      .then(r => setData(r.data))
      .catch(() => setError('Failed to load dashboard data.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner text="Loading dashboard..." />;

  const today = data?.today || {};
  const inventory = data?.inventory || {};
  const trend = data?.sales_trend || [];
  const restock = data?.restock_preview || [];
  const lowStock = data?.low_stock_alerts || [];
  const recentSales = data?.recent_sales || [];

  return (
    <div className="page-container">
      <PageHeader
        title={`Good ${getGreeting()}, ${user?.full_name?.split(' ')[0] || 'there'}`}
        subtitle={`Here's what's happening at ${user?.shop_name || 'your shop'} today.`}
      />

      <AlertMessage type="danger" message={error} onClose={() => setError('')} />

      {/* KPI Cards */}
      <div className="stats-grid">
        <StatCard
          title="Today's Revenue"
          value={formatCurrency(today.today_revenue)}
          icon="currency-rupee"
          colorClass="stat-blue"
          subtitle={`${today.today_orders} order${today.today_orders !== 1 ? 's' : ''} today`}
        />
        <StatCard
          title="Today's Orders"
          value={formatNumber(today.today_orders)}
          icon="receipt"
          colorClass="stat-teal"
          subtitle="Completed sales"
        />
        <StatCard
          title="Today's Profit"
          value={formatCurrency(today.today_profit)}
          icon="graph-up"
          colorClass="stat-green"
          subtitle="Gross profit today"
        />
        <StatCard
          title="Low Stock Items"
          value={formatNumber(inventory.low_stock_count + inventory.out_of_stock_count)}
          icon="exclamation-triangle"
          colorClass="stat-orange"
          subtitle={`${inventory.out_of_stock_count} out of stock`}
        />
      </div>

      {/* Main Grid */}
      <div className="dashboard-grid">
        {/* Sales Trend */}
        <div className="dashboard-card dashboard-card-wide">
          <div className="card-header-row">
            <h3 className="card-section-title">Sales Trend</h3>
            <span className="card-header-meta">Last 14 days</span>
          </div>
          {trend.length === 0 ? (
            <div className="chart-empty">
              <i className="bi bi-bar-chart"></i>
              <p>No sales data yet. Record your first sale to see trends.</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={trend} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.18} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="profGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.18} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }}
                  tickFormatter={d => d.slice(5)} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} width={55}
                  tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="revenue" name="revenue" stroke="#3b82f6"
                  strokeWidth={2} fill="url(#revGrad)" dot={false} />
                <Area type="monotone" dataKey="profit" name="profit" stroke="#10b981"
                  strokeWidth={2} fill="url(#profGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Recent Sales */}
        <div className="dashboard-card">
          <div className="card-header-row">
            <h3 className="card-section-title">Recent Sales</h3>
            <Link to="/sales" className="card-link">View all</Link>
          </div>
          {recentSales.length === 0 ? (
            <div className="mini-empty">
              <i className="bi bi-receipt"></i>
              <p>No sales recorded yet</p>
            </div>
          ) : (
            <div className="mini-list">
              {recentSales.map(s => (
                <div key={s.id} className="mini-list-item">
                  <div className="mini-list-main">
                    <p className="mini-title">{s.sale_number}</p>
                    <p className="mini-sub">{s.customer_name} · {s.items?.length} item{s.items?.length !== 1 ? 's' : ''}</p>
                  </div>
                  <div className="mini-list-right">
                    <p className="mini-amount">{formatCurrency(s.total)}</p>
                    <p className="mini-date">{formatDateTime(s.created_at)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* AI Restock Intelligence */}
      <div className="dashboard-card mt-4">
        <div className="card-header-row">
          <div>
            <h3 className="card-section-title">
              <i className="bi bi-cpu me-2 text-primary"></i>
              AI Stock Intelligence
            </h3>
            <p className="card-header-meta">ML-powered demand prediction & restock recommendations</p>
          </div>
          <Link to="/stock-intelligence" className="card-link">Full analysis</Link>
        </div>

        {restock.length === 0 ? (
          <div className="mini-empty">
            <i className="bi bi-cpu"></i>
            <p>Add products to see AI-powered restock recommendations</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="rm-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Current Stock</th>
                  <th>Predicted Demand</th>
                  <th>Suggested Order</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {restock.map(r => (
                  <tr key={r.product_id}>
                    <td>
                      <div className="product-cell">
                        <p className="product-name">{r.product_name}</p>
                        <p className="product-sku">{r.sku}</p>
                      </div>
                    </td>
                    <td><span className={r.current_stock <= 0 ? 'text-danger fw-semibold' : ''}>{r.current_stock}</span></td>
                    <td>{r.predicted_demand}</td>
                    <td>{r.reorder_quantity > 0 ? <strong>{r.reorder_quantity}</strong> : <span className="text-muted">—</span>}</td>
                    <td><RestockBadge status={r.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Inventory Summary */}
      <div className="dashboard-grid-3 mt-4">
        <div className="dashboard-card">
          <h3 className="card-section-title mb-3">Inventory Overview</h3>
          <div className="inventory-stat-list">
            <div className="inv-stat-row">
              <span>Total Products</span>
              <strong>{formatNumber(inventory.total_products)}</strong>
            </div>
            <div className="inv-stat-row">
              <span>Stock Value</span>
              <strong>{formatCurrency(inventory.total_stock_value)}</strong>
            </div>
            <div className="inv-stat-row text-warning">
              <span>Low Stock</span>
              <strong>{inventory.low_stock_count}</strong>
            </div>
            <div className="inv-stat-row text-danger">
              <span>Out of Stock</span>
              <strong>{inventory.out_of_stock_count}</strong>
            </div>
          </div>
          <Link to="/inventory" className="btn btn-outline-primary btn-sm w-100 mt-3">
            Manage Inventory
          </Link>
        </div>

        <div className="dashboard-card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header-row">
            <h3 className="card-section-title">Stock Alerts</h3>
            <Link to="/inventory" className="card-link">View all</Link>
          </div>
          {lowStock.length === 0 ? (
            <div className="mini-empty">
              <i className="bi bi-check-circle text-success"></i>
              <p>All products are sufficiently stocked</p>
            </div>
          ) : (
            <div className="mini-list">
              {lowStock.map(p => (
                <div key={p.product_id} className="mini-list-item">
                  <div>
                    <p className="mini-title">{p.name}</p>
                    <p className="mini-sub">{p.sku}</p>
                  </div>
                  <div className="mini-list-right">
                    <span className={`badge ${p.current_stock <= 0 ? 'bg-danger' : 'bg-warning text-dark'}`}>
                      {p.current_stock <= 0 ? 'Out of Stock' : `${p.current_stock} left`}
                    </span>
                    <p className="mini-date">Min: {p.minimum_stock}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const getGreeting = () => {
  const h = new Date().getHours();
  if (h < 12) return 'morning';
  if (h < 17) return 'afternoon';
  return 'evening';
};

export default Dashboard;
