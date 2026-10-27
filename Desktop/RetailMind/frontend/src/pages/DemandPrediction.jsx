import { useState, useEffect } from 'react';
import { mlApi } from '../services/api';
import PageHeader from '../components/PageHeader';
import AlertMessage from '../components/AlertMessage';
import LoadingSpinner from '../components/LoadingSpinner';
import { formatNumber } from '../utils/format';

const CATEGORIES = ['Grocery', 'Dairy', 'Beverages', 'Snacks', 'Household', 'Personal Care', 'Electronics', 'Clothing', 'Medicine', 'Other'];
const REGIONS = ['North', 'South', 'East', 'West', 'Central'];
const WEATHER = ['Sunny', 'Cloudy', 'Rainy', 'Snowy', 'Stormy'];
const SEASONALITY = ['Regular', 'Peak', 'Off-peak', 'Festival', 'Holiday'];

const initForm = {
  category: 'Grocery', region: 'North', weather_condition: 'Sunny', seasonality: 'Regular',
  price: 100, discount: 0, promotion: 0, competitor_pricing: 105,
  inventory_level: 50,
  demand_lag_1: 30, demand_lag_7: 28, demand_lag_14: 29, demand_lag_28: 27,
  demand_rolling_mean_7: 29, demand_rolling_mean_14: 28.5, demand_rolling_mean_28: 28,
};

const DemandPrediction = () => {
  const [modelInfo, setModelInfo] = useState(null);
  const [form, setForm] = useState(initForm);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [infoLoading, setInfoLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    mlApi.modelInfo()
      .then(r => setModelInfo(r.data))
      .catch((err) => {
        console.error('Failed to load model info:', err);
        // Silent catch acceptable here - model info is optional UI enhancement
      })
      .finally(() => setInfoLoading(false));
  }, []);

  const handle = e => {
    const { name, value, type } = e.target;
    setForm(f => ({ ...f, [name]: type === 'number' ? parseFloat(value) || 0 : value }));
  };

  const predict = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true); setResult(null);
    try {
      const r = await mlApi.predictDemand(form);
      setResult(r.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Prediction failed. Check that the ML model is loaded.');
    } finally { setLoading(false); }
  };

  const reset = () => { setForm(initForm); setResult(null); setError(''); };

  return (
    <div className="page-container">
      <PageHeader
        title="Demand Prediction"
        subtitle="Use the trained ML model to forecast product demand"
      />

      {/* Model Info Banner */}
      {!infoLoading && modelInfo && (
        <div className={`model-info-banner ${modelInfo.loaded ? 'model-loaded' : 'model-error'}`}>
          <div className="model-info-left">
            <i className={`bi bi-${modelInfo.loaded ? 'cpu-fill' : 'exclamation-triangle'}`}></i>
            <div>
              <p className="model-name">{modelInfo.model_name}</p>
              <p className="model-status">{modelInfo.loaded ? 'Model loaded and ready' : `Model not loaded: ${modelInfo.load_error}`}</p>
            </div>
          </div>
          {modelInfo.loaded && modelInfo.metrics && (
            <div className="model-metrics">
              <div className="model-metric"><span>MAE</span><strong>{modelInfo.metrics.test_mae?.toFixed(2)}</strong></div>
              <div className="model-metric"><span>RMSE</span><strong>{modelInfo.metrics.test_rmse?.toFixed(2)}</strong></div>
              <div className="model-metric"><span>R²</span><strong>{modelInfo.metrics.test_r2?.toFixed(4)}</strong></div>
            </div>
          )}
        </div>
      )}

      <div className="prediction-disclaimer">
        <i className="bi bi-info-circle me-2"></i>
        <span>This model was trained on a public retail demand forecasting dataset. Predictions represent expected demand units based on historical demand patterns, not your shop's specific sales history.</span>
      </div>

      <AlertMessage type="danger" message={error} onClose={() => setError('')} />

      <div className="prediction-layout">
        {/* Form */}
        <div className="prediction-form-card">
          <h4 className="prediction-form-title">Prediction Parameters</h4>
          <form onSubmit={predict}>
            <div className="prediction-section">
              <p className="prediction-section-label">Product Context</p>
              <div className="row g-3">
                <div className="col-md-6">
                  <label className="form-label">Category</label>
                  <select className="form-select" name="category" value={form.category} onChange={handle}>
                    {CATEGORIES.map(c => <option key={c}>{c}</option>)}
                  </select>
                </div>
                <div className="col-md-6">
                  <label className="form-label">Region</label>
                  <select className="form-select" name="region" value={form.region} onChange={handle}>
                    {REGIONS.map(r => <option key={r}>{r}</option>)}
                  </select>
                </div>
                <div className="col-md-4">
                  <label className="form-label">Selling Price (₹)</label>
                  <input type="number" name="price" min="0" step="0.01" className="form-control" value={form.price} onChange={handle} />
                </div>
                <div className="col-md-4">
                  <label className="form-label">Discount (%)</label>
                  <input type="number" name="discount" min="0" max="100" step="0.1" className="form-control" value={form.discount} onChange={handle} />
                </div>
                <div className="col-md-4">
                  <label className="form-label">Competitor Price (₹)</label>
                  <input type="number" name="competitor_pricing" min="0" step="0.01" className="form-control" value={form.competitor_pricing} onChange={handle} />
                </div>
                <div className="col-md-4">
                  <label className="form-label">Current Inventory</label>
                  <input type="number" name="inventory_level" min="0" className="form-control" value={form.inventory_level} onChange={handle} />
                </div>
                <div className="col-md-4">
                  <label className="form-label">Promotion Active</label>
                  <select className="form-select" name="promotion" value={form.promotion} onChange={e => setForm(f => ({ ...f, promotion: parseInt(e.target.value) }))}>
                    <option value={0}>No</option>
                    <option value={1}>Yes</option>
                  </select>
                </div>
                <div className="col-md-4">
                  <label className="form-label">Seasonality</label>
                  <select className="form-select" name="seasonality" value={form.seasonality} onChange={handle}>
                    {SEASONALITY.map(s => <option key={s}>{s}</option>)}
                  </select>
                </div>
                <div className="col-md-6">
                  <label className="form-label">Weather</label>
                  <select className="form-select" name="weather_condition" value={form.weather_condition} onChange={handle}>
                    {WEATHER.map(w => <option key={w}>{w}</option>)}
                  </select>
                </div>
              </div>
            </div>

            <div className="prediction-section">
              <p className="prediction-section-label">Historical Demand</p>
              <div className="row g-3">
                {[
                  { name: 'demand_lag_1', label: 'Yesterday' },
                  { name: 'demand_lag_7', label: '7 Days Ago' },
                  { name: 'demand_lag_14', label: '14 Days Ago' },
                  { name: 'demand_lag_28', label: '28 Days Ago' },
                  { name: 'demand_rolling_mean_7', label: '7-Day Avg' },
                  { name: 'demand_rolling_mean_14', label: '14-Day Avg' },
                  { name: 'demand_rolling_mean_28', label: '28-Day Avg' },
                ].map(f => (
                  <div key={f.name} className="col-md-4 col-6">
                    <label className="form-label">{f.label}</label>
                    <input type="number" name={f.name} min="0" step="0.1" className="form-control"
                      value={form[f.name]} onChange={handle} />
                  </div>
                ))}
              </div>
            </div>

            <div className="d-flex gap-2 mt-3">
              <button type="submit" className="btn btn-primary flex-grow-1" disabled={loading || !modelInfo?.loaded}>
                {loading ? <><span className="spinner-border spinner-border-sm me-2" />Predicting...</>
                  : <><i className="bi bi-cpu me-2"></i>Predict Demand</>}
              </button>
              <button type="button" className="btn btn-outline-secondary" onClick={reset}>Reset</button>
            </div>
          </form>
        </div>

        {/* Result Panel */}
        <div className="prediction-result-panel">
          {!result && !loading && (
            <div className="prediction-result-empty">
              <i className="bi bi-graph-up-arrow"></i>
              <h5>Prediction Result</h5>
              <p>Fill in the parameters and click "Predict Demand" to see the ML model's output.</p>
            </div>
          )}

          {loading && (
            <div className="prediction-result-empty">
              <div className="spinner-border text-primary mb-3"></div>
              <p>Running prediction model...</p>
            </div>
          )}

          {result && !loading && (
            <div className="prediction-result">
              <div className="prediction-result-header">
                <i className="bi bi-cpu-fill"></i>
                <h4>Prediction Result</h4>
              </div>

              <div className="prediction-demand-display">
                <p className="pred-label">Predicted Demand</p>
                <p className="pred-number">{Math.round(result.predicted_demand)}</p>
                <p className="pred-unit">units</p>
              </div>

              <div className="prediction-details">
                <div className="pred-detail-row">
                  <span>Category</span><span>{result.input?.Category}</span>
                </div>
                <div className="pred-detail-row">
                  <span>Region</span><span>{result.input?.Region}</span>
                </div>
                <div className="pred-detail-row">
                  <span>Seasonality</span><span>{result.input?.Seasonality}</span>
                </div>
                <div className="pred-detail-row">
                  <span>Promotion Active</span><span>{result.input?.Promotion ? 'Yes' : 'No'}</span>
                </div>
                <div className="pred-detail-row">
                  <span>Price</span><span>₹{result.input?.Price}</span>
                </div>
                <div className="pred-detail-row">
                  <span>Inventory Level</span><span>{result.input?.Inventory_Level} units</span>
                </div>
              </div>

              <div className="prediction-note">
                <i className="bi bi-info-circle me-1"></i>
                Prediction from HistGradientBoosting model (R² = {modelInfo?.metrics?.test_r2?.toFixed(4)}).
                Use alongside your business judgment.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DemandPrediction;
