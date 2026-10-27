import { useState, useEffect } from 'react';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { analyticsApi } from '../services/api';
import PageHeader from '../components/PageHeader';
import StatCard from '../components/StatCard';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import AlertMessage from '../components/AlertMessage';
import { formatCurrency, formatPercent, formatNumber, formatDate } from '../utils/format';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316'];

const PERIOD_OPTIONS = [
  { label: '7 days', days: 7 },
  { label: '30 days', days: 30 },
  { label: '90 days', days: 90 },
];

const SectionHeader = ({ title, subtitle }) => (
  <div className="analytics-section-header">
    <h3 className="analytics-section-title">{title}</h3>
    {subtitle && <p className="analytics-section-sub">{subtitle}</p>}
  </div>
);

const Analytics = () => {
  const [salesData, setSalesData] = useState(null);
  const [trend, setTrend] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [customerData, setCustomerData] = useState(null);
  const [inventoryData, setInventoryData] = useState(null);
  const [period, setPeriod] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [segmentsData, setSegmentsData] = useState(null);
  const [segmentsLoading, setSegmentsLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const [s, t, tp, cat, cust, inv] = await Promise.all([
          analyticsApi.sales(),
          analyticsApi.trend({ days: period }),
          analyticsApi.topProducts({ limit: 8 }),
          analyticsApi.categories(),
          analyticsApi.customers(),
          analyticsApi.inventory(),
        ]);
        setSalesData(s.data);
        setTrend(t.data);
        setTopProducts(tp.data);
        setCategories(cat.data);
        setCustomerData(cust.data);
        setInventoryData(inv.data);
      } catch { setError('Failed to load analytics data.'); }
      finally { setLoading(false); }
    };
    load();
  }, [period]);

  useEffect(() => {
    const loadSegments = async () => {
      setSegmentsLoading(true);
      try {
        const res = await analyticsApi.customerSegments();
        setSegmentsData(res.data);
      } catch {
        setSegmentsData(null);
      } finally {
        setSegmentsLoading(false);
      }
    };
    loadSegments();
  }, []);

  if (loading) return <LoadingSpinner text="Loading analytics..." />;

  const hasData = salesData?.total_orders > 0;

  return (
    <div className="page-container">
      <PageHeader
        title="Business Analytics"
        subtitle="Performance insights from your actual business data"
        actions={
          <div className="btn-group" role="group">
            {PERIOD_OPTIONS.map(o => (
              <button key={o.days}
                className={`btn btn-sm ${period === o.days ? 'btn-primary' : 'btn-outline-secondary'}`}
                onClick={() => setPeriod(o.days)}>
                {o.label}
              </button>
            ))}
          </div>
        }
      />

      <AlertMessage type="danger" message={error} onClose={() => setError('')} />

      {/* Sales KPIs */}
      <div className="stats-grid mb-4">
        <StatCard title="Total Revenue" value={formatCurrency(salesData?.total_revenue)} icon="currency-rupee" colorClass="stat-blue" />
        <StatCard title="Total Orders" value={formatNumber(salesData?.total_orders)} icon="receipt" colorClass="stat-teal" />
        <StatCard title="Gross Profit" value={formatCurrency(salesData?.gross_profit)} icon="graph-up" colorClass="stat-green" />
        <StatCard title="Profit Margin" value={formatPercent(salesData?.profit_margin)} icon="percent" colorClass="stat-purple" />
      </div>

      {!hasData ? (
        <EmptyState icon="bar-chart-line" title="No sales data yet"
          message="Start recording sales to see your business analytics." />
      ) : (
        <>
          {/* Sales & Profit Trend */}
          <div className="analytics-card mb-4">
            <SectionHeader title="Revenue & Profit Trend" subtitle={`Last ${period} days`} />
            {trend.length === 0 ? (
              <div className="chart-empty"><i className="bi bi-bar-chart"></i><p>No trend data for this period.</p></div>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={trend} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="aRev" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} /><stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="aProf" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.15} /><stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }} tickFormatter={d => d.slice(5)} />
                  <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} width={60} tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={(v, n) => [formatCurrency(v), n]} />
                  <Legend />
                  <Area type="monotone" dataKey="revenue" name="Revenue" stroke="#3b82f6" strokeWidth={2} fill="url(#aRev)" dot={false} />
                  <Area type="monotone" dataKey="profit" name="Profit" stroke="#10b981" strokeWidth={2} fill="url(#aProf)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="analytics-grid-2 mb-4">
            {/* Top Products */}
            <div className="analytics-card">
              <SectionHeader title="Top Products by Revenue" />
              {topProducts.length === 0 ? (
                <div className="chart-empty"><i className="bi bi-box-seam"></i><p>No product sales data.</p></div>
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={topProducts} layout="vertical" margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 11, fill: '#94a3b8' }} tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`} />
                    <YAxis type="category" dataKey="product_name" tick={{ fontSize: 11, fill: '#475569' }} width={100}
                      tickFormatter={v => v.length > 14 ? v.slice(0, 14) + '…' : v} />
                    <Tooltip formatter={(v) => formatCurrency(v)} />
                    <Bar dataKey="total_revenue" name="Revenue" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Category Performance */}
            <div className="analytics-card">
              <SectionHeader title="Sales by Category" />
              {categories.length === 0 ? (
                <div className="chart-empty"><i className="bi bi-tags"></i><p>No category data.</p></div>
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie data={categories} dataKey="total_revenue" nameKey="category"
                      cx="50%" cy="50%" outerRadius={90} innerRadius={50}
                      paddingAngle={2} label={({ category, percent }) => `${category} ${(percent * 100).toFixed(0)}%`}
                      labelLine={false}>
                      {categories.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip formatter={(v) => formatCurrency(v)} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Profit Summary */}
          <div className="analytics-card mb-4">
            <SectionHeader title="Profit Summary" />
            <div className="profit-summary-grid">
              <div className="profit-item">
                <p className="profit-label">Total Revenue</p>
                <p className="profit-value text-primary">{formatCurrency(salesData?.total_revenue)}</p>
              </div>
              <div className="profit-item">
                <p className="profit-label">Cost of Goods</p>
                <p className="profit-value text-danger">{formatCurrency(salesData?.total_cost)}</p>
              </div>
              <div className="profit-item">
                <p className="profit-label">Gross Profit</p>
                <p className="profit-value text-success">{formatCurrency(salesData?.gross_profit)}</p>
              </div>
              <div className="profit-item">
                <p className="profit-label">Profit Margin</p>
                <p className="profit-value text-info">{formatPercent(salesData?.profit_margin)}</p>
              </div>
              <div className="profit-item">
                <p className="profit-label">Avg Order Value</p>
                <p className="profit-value">{formatCurrency(salesData?.average_order_value)}</p>
              </div>
              <div className="profit-item">
                <p className="profit-label">Total Discounts Given</p>
                <p className="profit-value text-warning">{formatCurrency(salesData?.total_discount)}</p>
              </div>
            </div>
          </div>

          <div className="analytics-grid-2 mb-4">
            {/* Customer Analytics */}
            <div className="analytics-card">
              <SectionHeader title="Customer Insights" />
              {customerData && (
                <div className="customer-analytics-list">
                  <div className="ca-item">
                    <span>Total Customers</span><strong>{customerData.total_customers}</strong>
                  </div>
                  <div className="ca-item">
                    <span>Repeat Customers</span><strong>{customerData.repeat_customers}</strong>
                  </div>
                  <div className="ca-item">
                    <span>New Customers</span><strong>{customerData.new_customers}</strong>
                  </div>
                  {customerData.top_customers?.length > 0 && (
                    <>
                      <p className="ca-subheader">Top Customers</p>
                      {customerData.top_customers.map((c, i) => (
                        <div key={i} className="ca-item ca-top-item">
                          <span>{c.name}</span>
                          <span className="text-primary fw-semibold">{formatCurrency(c.total_purchases)}</span>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              )}
            </div>

            {/* Inventory Analytics */}
            <div className="analytics-card">
              <SectionHeader title="Inventory Overview" />
              {inventoryData && (
                <div className="customer-analytics-list">
                  <div className="ca-item"><span>Total Products</span><strong>{inventoryData.summary?.total_products}</strong></div>
                  <div className="ca-item"><span>Stock Value</span><strong>{formatCurrency(inventoryData.summary?.total_stock_value)}</strong></div>
                  <div className="ca-item text-warning"><span>Low Stock Items</span><strong>{inventoryData.summary?.low_stock_count}</strong></div>
                  <div className="ca-item text-danger"><span>Out of Stock</span><strong>{inventoryData.summary?.out_of_stock_count}</strong></div>
                  {inventoryData.stock_movement?.length > 0 && (
                    <>
                      <p className="ca-subheader">30-Day Stock Movement</p>
                      {inventoryData.stock_movement.map((m, i) => (
                        <div key={i} className="ca-item">
                          <span className="text-capitalize">{m.type}</span>
                          <span>{m.total_qty} units ({m.count} transactions)</span>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
          {/* Customer Segments (RFM K-Means) */}
          <div className="analytics-card mb-4">
            <SectionHeader title="Customer Segments" subtitle="RFM-based K-Means clustering of customers with purchase history" />
            {segmentsLoading ? (
              <div className="chart-empty"><i className="bi bi-arrow-repeat"></i><p>Analyzing customer segments...</p></div>
            ) : segmentsData?.error ? (
              <div className="chart-empty"><i className="bi bi-info-circle"></i><p>{segmentsData.error}</p></div>
            ) : (
              <>
                {/* Summary stats */}
                <div className="customer-analytics-list">
                  <div className="ca-item">
                    <span>Customers Registered</span>
                    <strong>{segmentsData.total_customers_registered ?? 0}</strong>
                  </div>
                  <div className="ca-item">
                    <span>Customers Analyzed (with purchases)</span>
                    <strong>{segmentsData.total_customers_analyzed ?? 0}</strong>
                  </div>
                  <div className="ca-item">
                    <span>Segments Identified</span>
                    <strong>{segmentsData.total_clusters ?? 0}</strong>
                  </div>
                </div>

                {/* Message when clustering is not meaningful */}
                {segmentsData?.message && (
                  <div className="segment-message">
                    <i className="bi bi-info-circle me-1"></i>
                    {segmentsData.message}
                  </div>
                )}

                {/* Segment breakdown */}
                {segmentsData?.segments?.length > 0 && (
                  <>
                    <p className="ca-subheader">Segment Breakdown</p>
                    {segmentsData.segments.map((seg, i) => {
                      const segmentCustomers = segmentsData.customer_details?.filter(c => c.segment === seg.label) || [];
                      return (
                        <details key={i} className="ca-item mb-2">
                          <summary className="fw-semibold">{seg.label}</summary>
                          <div className="segment-summary">
                            <span className="text-primary fw-semibold">
                              {seg.customer_count} customers · {seg.avg_purchases?.toFixed(1)} avg orders · {formatCurrency(seg.avg_total_spent || 0)} avg spent · {Math.round(seg.avg_recency_days || 0)}d since last
                            </span>
                          </div>
                          {segmentCustomers.length > 0 ? (
                            <div className="segment-table-wrap mt-2">
                              <table className="segment-table">
                                <thead>
                                  <tr>
                                    <th>Customer Name</th>
                                    <th>Total Orders</th>
                                    <th>Total Spent</th>
                                    <th>Last Purchase</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {segmentCustomers.map((c, idx) => (
                                    <tr key={idx}>
                                      <td>{c.customer_name || '—'}</td>
                                      <td>{c.frequency ?? 0}</td>
                                      <td>{formatCurrency(c.monetary || 0)}</td>
                                      <td>{formatDate(c.last_purchase)}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          ) : (
                            <p className="mt-2">No customers in this segment.</p>
                          )}
                        </details>
                      );
                    })}
                  </>
                )}

                {/* Per-customer table */}
                {false && (
                  <>
                    <p className="ca-subheader">Customer-Level Details</p>
                    <div className="segment-table-wrap">
                      <table className="segment-table">
                        <thead>
                          <tr>
                            <th>Customer Name</th>
                            <th>Segment</th>
                            <th>Total Orders</th>
                            <th>Total Spent</th>
                            <th>Last Purchase</th>
                          </tr>
                        </thead>
                        <tbody>
                          {segmentsData.customer_details.map((c, i) => (
                            <tr key={i}>
                              <td>{c.customer_name || '—'}</td>
                              <td><span className="segment-tag">{c.segment}</span></td>
                              <td>{c.frequency ?? 0}</td>
                              <td>{formatCurrency(c.monetary || 0)}</td>
                              <td>{formatDate(c.last_purchase)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default Analytics;
