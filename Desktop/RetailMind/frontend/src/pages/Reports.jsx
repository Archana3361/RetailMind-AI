import { useState } from 'react';
import { reportsApi } from '../services/api';
import PageHeader from '../components/PageHeader';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import AlertMessage from '../components/AlertMessage';
import { formatCurrency, formatNumber } from '../utils/format';

const REPORTS = [
  { id: 'sales', label: 'Sales Report', icon: 'receipt', desc: 'All sales transactions with revenue and profit', hasDate: true },
  { id: 'purchases', label: 'Purchase Report', icon: 'truck', desc: 'All purchase orders and costs', hasDate: true },
  { id: 'inventory', label: 'Inventory Report', icon: 'archive', desc: 'Current stock levels and values', hasDate: false },
  { id: 'product-performance', label: 'Product Performance', icon: 'bar-chart-line', desc: 'Top and slow-moving products by revenue', hasDate: false },
];

const Reports = () => {
  const [activeReport, setActiveReport] = useState('sales');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [generated, setGenerated] = useState(false);

  const current = REPORTS.find(r => r.id === activeReport);

  const generate = async () => {
    setLoading(true); setError(''); setData([]);
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    try {
      let res;
      if (activeReport === 'sales') res = await reportsApi.sales(params);
      else if (activeReport === 'purchases') res = await reportsApi.purchases(params);
      else if (activeReport === 'inventory') res = await reportsApi.inventory(params);
      else res = await reportsApi.productPerformance(params);
      setData(res.data.data); setGenerated(true);
    } catch { setError('Failed to generate report.'); }
    finally { setLoading(false); }
  };

  const downloadCSV = async () => {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    params.format = 'csv';
    try {
      let res;
      if (activeReport === 'sales') res = await reportsApi.sales(params);
      else if (activeReport === 'purchases') res = await reportsApi.purchases(params);
      else if (activeReport === 'inventory') res = await reportsApi.inventory(params);
      else res = await reportsApi.productPerformance(params);
      const blob = new Blob([res.data], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `${activeReport}_report.csv`; a.click();
      URL.revokeObjectURL(url);
    } catch { setError('Failed to download report.'); }
  };

  const switchReport = (id) => {
    setActiveReport(id); setData([]); setGenerated(false); setError('');
    setStartDate(''); setEndDate('');
  };

  return (
    <div className="page-container">
      <PageHeader title="Reports" subtitle="Generate and export business reports" />

      <AlertMessage type="danger" message={error} onClose={() => setError('')} />

      <div className="reports-layout">
        {/* Report Selector */}
        <div className="reports-sidebar">
          {REPORTS.map(r => (
            <button key={r.id}
              className={`report-selector-btn ${activeReport === r.id ? 'active' : ''}`}
              onClick={() => switchReport(r.id)}>
              <i className={`bi bi-${r.icon}`}></i>
              <div>
                <p className="rsb-title">{r.label}</p>
                <p className="rsb-desc">{r.desc}</p>
              </div>
            </button>
          ))}
        </div>

        {/* Report Content */}
        <div className="reports-content">
          <div className="report-controls">
            <div className="report-controls-left">
              <h4 className="report-title">{current?.label}</h4>
              <p className="report-desc text-muted small">{current?.desc}</p>
            </div>
            <div className="report-controls-right">
              {current?.hasDate && (
                <>
                  <div>
                    <label className="form-label mb-1 small">From</label>
                    <input type="date" className="form-control form-control-sm" value={startDate} onChange={e => setStartDate(e.target.value)} />
                  </div>
                  <div>
                    <label className="form-label mb-1 small">To</label>
                    <input type="date" className="form-control form-control-sm" value={endDate} onChange={e => setEndDate(e.target.value)} />
                  </div>
                </>
              )}
              <button className="btn btn-primary btn-sm" onClick={generate} disabled={loading}>
                {loading ? <span className="spinner-border spinner-border-sm me-1" /> : <i className="bi bi-play-fill me-1"></i>}
                Generate
              </button>
              {generated && data.length > 0 && (
                <button className="btn btn-outline-secondary btn-sm" onClick={downloadCSV}>
                  <i className="bi bi-download me-1"></i>CSV
                </button>
              )}
            </div>
          </div>

          {loading ? <LoadingSpinner text="Generating report..." /> :
            !generated ? (
              <div className="report-prompt">
                <i className="bi bi-file-earmark-text"></i>
                <p>Configure your filters and click <strong>Generate</strong> to run the report.</p>
              </div>
            ) :
            data.length === 0 ? (
              <EmptyState icon="file-earmark" title="No data for this period" message="Try adjusting the date range or filters." />
            ) : (
              <>
                <p className="text-muted small mb-2">{data.length} record{data.length !== 1 ? 's' : ''}</p>
                <div className="table-responsive">
                  <table className="rm-table rm-table-sm">
                    <thead>
                      <tr>{Object.keys(data[0]).map(k => <th key={k}>{k}</th>)}</tr>
                    </thead>
                    <tbody>
                      {data.map((row, i) => (
                        <tr key={i}>
                          {Object.values(row).map((v, j) => (
                            <td key={j}>{typeof v === 'number' && Object.keys(data[0])[j].toLowerCase().includes('revenue') || Object.keys(data[0])[j].toLowerCase().includes('profit') || Object.keys(data[0])[j].toLowerCase().includes('cost') || Object.keys(data[0])[j].toLowerCase().includes('total') || Object.keys(data[0])[j].toLowerCase().includes('value') ? formatCurrency(v) : String(v ?? '—')}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )
          }
        </div>
      </div>
    </div>
  );
};

export default Reports;
