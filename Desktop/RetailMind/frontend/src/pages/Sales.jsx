import { useState, useEffect, useCallback } from 'react';
import { salesApi, productsApi, customersApi } from '../services/api';
import PageHeader from '../components/PageHeader';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import AlertMessage from '../components/AlertMessage';
import Pagination from '../components/Pagination';
import { formatCurrency, formatDateTime } from '../utils/format';

const Sales = () => {
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showModal, setShowModal] = useState(false);

  // New sale state
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [saleItems, setSaleItems] = useState([{ product_id: '', quantity: 1, unit_price: 0, product_name: '', stock: 0 }]);
  const [customerId, setCustomerId] = useState('');
  const [saleNumber, setSaleNumber] = useState('');
  const [saleDate, setSaleDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [discount, setDiscount] = useState(0);
  const [discountType, setDiscountType] = useState('amount');
  const [payMethod, setPayMethod] = useState('cash');
  const [paymentStatus, setPaymentStatus] = useState('paid');
  const [amountPaid, setAmountPaid] = useState('');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const [viewSale, setViewSale] = useState(null);

  const fetchSales = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const r = await salesApi.list({ page: p, per_page: 15 });
      setSales(r.data.items); setPages(r.data.pages); setTotal(r.data.total);
    } catch { setError('Failed to load sales.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchSales(page); }, [page]);

  const openNew = async () => {
    setFormError('');
    setSaleItems([{ product_id: '', quantity: 1, unit_price: 0, product_name: '', stock: 0 }]);
    setCustomerId(''); setDiscount(0); setDiscountType('amount'); setPayMethod('cash'); setNotes('');
    setSaleDate(new Date().toISOString().split('T')[0]);
    setPaymentStatus('paid');
    setAmountPaid('');
    setSaleNumber('Generating...');

    try {
      const numRes = await salesApi.getNextNumber();
      setSaleNumber(numRes.data.sale_number);
    } catch {
      setSaleNumber('SL-AUTO');
    }
    
    // Always reload fresh data (not cached) - ensures dropdowns show latest options
    let success = true;
    
    try {
      const r = await productsApi.list({ per_page: 100 });
      setProducts(r.data.items);
    } catch (err) {
      console.error('Failed to load products:', err);
      setFormError('Unable to load products. Please try again.');
      success = false;
    }
    
    try {
      const r = await customersApi.list({ per_page: 100 });
      setCustomers(r.data.items);
    } catch (err) {
      console.error('Failed to load customers:', err);
      setFormError('Unable to load customers. Please try again.');
      success = false;
    }
    
    // Only open modal if both dropdowns loaded successfully
    if (success) {
      setShowModal(true);
    }
  };

  const setItem = (i, field, value) => {
    setSaleItems(items => {
      const next = [...items];
      next[i] = { ...next[i], [field]: value };
      if (field === 'product_id') {
        const p = products.find(x => x.id === value);
        if (p) {
          next[i].unit_price = p.selling_price;
          next[i].product_name = p.name;
          next[i].stock = p.current_stock;
        }
      }
      return next;
    });
  };

  const addItem = () => setSaleItems(i => [...i, { product_id: '', quantity: 1, unit_price: 0, product_name: '', stock: 0 }]);
  const removeItem = (i) => setSaleItems(items => items.filter((_, idx) => idx !== i));

  const subtotal = saleItems.reduce((s, i) => s + (parseFloat(i.quantity) || 0) * (parseFloat(i.unit_price) || 0), 0);
  const discountAmount = discountType === 'percent' ? subtotal * (parseFloat(discount) || 0) / 100 : (parseFloat(discount) || 0);
  const total_ = Math.max(0, subtotal - discountAmount);

  // Derive effective amount paid and balance due
  let effectiveAmountPaid = 0;
  if (paymentStatus === 'paid') {
    effectiveAmountPaid = total_;
  } else if (paymentStatus === 'unpaid') {
    effectiveAmountPaid = 0;
  } else {
    const parsed = parseFloat(amountPaid);
    effectiveAmountPaid = isNaN(parsed) ? 0 : Math.min(total_, Math.max(0, parsed));
  }
  const balanceDue = Math.max(0, parseFloat((total_ - effectiveAmountPaid).toFixed(2)));

  const handlePaymentStatusChange = (status) => {
    setPaymentStatus(status);
    if (status === 'paid') {
      setAmountPaid('');
    } else if (status === 'unpaid') {
      setAmountPaid('0');
    } else if (status === 'partial') {
      setAmountPaid(total_ > 0 ? (total_ / 2).toFixed(2) : '0');
    }
  };

  const handleAmountPaidChange = (e) => {
    const valStr = e.target.value;
    setAmountPaid(valStr);
    const val = parseFloat(valStr);
    if (!isNaN(val)) {
      if (val >= total_ && total_ > 0) {
        setPaymentStatus('paid');
      } else if (val <= 0) {
        setPaymentStatus('unpaid');
      } else {
        setPaymentStatus('partial');
      }
    }
  };

  const saveSale = async (e) => {
    e.preventDefault();
    const valid = saleItems.every(i => i.product_id && parseInt(i.quantity) > 0);
    if (!valid) { setFormError('All items must have a product and quantity of at least 1.'); return; }

    // Validate available stock to prevent sales exceeding available stock
    for (const item of saleItems) {
      const p = products.find(x => x.id === item.product_id);
      const available = p ? p.current_stock : (item.stock ?? 0);
      const requested = parseInt(item.quantity);
      if (requested > available) {
        setFormError(`Insufficient stock for "${item.product_name || 'Selected product'}". Available: ${available}, Requested: ${requested}`);
        return;
      }
    }

    setSaving(true); setFormError('');
    try {
      await salesApi.create({
        sale_number: saleNumber && !saleNumber.includes('Generating') && saleNumber !== 'SL-AUTO' ? saleNumber : null,
        sale_date: saleDate || null,
        customer_id: customerId || null,
        items: saleItems.map(i => ({ product_id: i.product_id, quantity: parseInt(i.quantity), unit_price: parseFloat(i.unit_price) })),
        discount: parseFloat(discount) || 0,
        discount_type: discountType,
        tax: 0,
        payment_method: payMethod,
        payment_status: paymentStatus,
        amount_paid: effectiveAmountPaid,
        balance_due: balanceDue,
        notes,
      });
      setSuccess('Sale recorded successfully.');
      setShowModal(false);
      fetchSales(1); setPage(1);
    } catch (err) {
      const d = err.response?.data?.detail;
      setFormError(typeof d === 'string' ? d : 'Failed to create sale.');
    } finally { setSaving(false); }
  };

  return (
    <div className="page-container">
      <PageHeader
        title="Sales"
        subtitle={`${total} sale${total !== 1 ? 's' : ''} recorded`}
        actions={
          <button className="btn btn-primary" onClick={openNew}>
            <i className="bi bi-plus-lg me-2"></i>New Sale
          </button>
        }
      />

      <AlertMessage type="success" message={success} onClose={() => setSuccess('')} />
      <AlertMessage type="danger" message={error} onClose={() => setError('')} />

      {loading ? <LoadingSpinner /> : sales.length === 0 ? (
        <EmptyState icon="receipt" title="No sales yet"
          message="Record your first sale to start tracking revenue."
          action={<button className="btn btn-primary mt-2" onClick={openNew}><i className="bi bi-plus-lg me-2"></i>New Sale</button>}
        />
      ) : (
        <>
          <div className="table-responsive">
            <table className="rm-table">
              <thead>
                <tr>
                  <th>Sale #</th><th>Customer</th><th>Items</th>
                  <th>Total</th><th>Profit</th><th>Payment</th><th>Date</th><th></th>
                </tr>
              </thead>
              <tbody>
                {sales.map(s => (
                  <tr key={s.id}>
                    <td><code className="sku-code">{s.sale_number}</code></td>
                    <td>{s.customer_name}</td>
                    <td>{s.items?.length}</td>
                    <td><strong>{formatCurrency(s.total)}</strong></td>
                    <td className={s.gross_profit >= 0 ? 'text-success' : 'text-danger'}>
                      {formatCurrency(s.gross_profit)}
                    </td>
                    <td>
                      <span className="badge bg-light text-dark border me-1">{s.payment_method}</span>
                      <span className={`badge ${s.payment_status === 'paid' ? 'bg-success' : s.payment_status === 'partial' ? 'bg-warning text-dark' : 'bg-danger'}`}>
                        {s.payment_status || 'paid'}
                      </span>
                    </td>
                    <td>{formatDateTime(s.sale_date || s.created_at)}</td>
                    <td>
                      <button className="btn-icon" title="View" onClick={() => setViewSale(s)}>
                        <i className="bi bi-eye"></i>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pages={pages} onPage={p => setPage(p)} />
        </>
      )}

      {/* New Sale Modal */}
      {showModal && (
        <div className="modal-backdrop-custom" onClick={() => setShowModal(false)}>
          <div className="modal-dialog-custom modal-xl-custom" onClick={e => e.stopPropagation()}>
            <div className="modal-header-custom">
              <h5><i className="bi bi-receipt me-2"></i>New Sale</h5>
              <button className="btn-close" onClick={() => setShowModal(false)} />
            </div>
            <form onSubmit={saveSale}>
              <div className="modal-body-custom">
                <AlertMessage type="danger" message={formError} onClose={() => setFormError('')} />
                <div className="row g-3 mb-3">
                  <div className="col-md-3">
                    <label className="form-label">Sale ID (auto-generated)</label>
                    <input type="text" className="form-control" value={saleNumber} readOnly disabled />
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Sale Date</label>
                    <input type="date" className="form-control" value={saleDate} onChange={e => setSaleDate(e.target.value)} required />
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Customer (optional)</label>
                    <select className="form-select" value={customerId} onChange={e => setCustomerId(e.target.value)}>
                      <option value="">Walk-in Customer</option>
                      {customers.map(c => <option key={c.id} value={c.id}>{c.name} {c.phone ? `· ${c.phone}` : ''}</option>)}
                    </select>
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Payment Method</label>
                    <select className="form-select" value={payMethod} onChange={e => setPayMethod(e.target.value)}>
                      <option value="cash">Cash</option>
                      <option value="card">Card</option>
                      <option value="upi">UPI</option>
                      <option value="credit">Credit</option>
                    </select>
                  </div>
                </div>

                {/* Items */}
                <div className="sale-items-section">
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <h6 className="mb-0">Items</h6>
                    <button type="button" className="btn btn-outline-primary btn-sm" onClick={addItem}>
                      <i className="bi bi-plus-lg me-1"></i>Add Item
                    </button>
                  </div>
                  {saleItems.map((item, i) => (
                    <div key={i} className="sale-item-row">
                      <div className="sale-item-product">
                        <select className="form-select form-select-sm" value={item.product_id}
                          onChange={e => setItem(i, 'product_id', e.target.value)} required>
                          <option value="">Select product</option>
                          {products.map(p => (
                            <option key={p.id} value={p.id}>
                              {p.name} (Stock: {p.current_stock})
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="sale-item-qty">
                        <input type="number" min="1" max={item.stock || undefined}
                          className={`form-control form-control-sm ${item.product_id && parseInt(item.quantity) > item.stock ? 'is-invalid border-danger' : ''}`}
                          placeholder="Qty" value={item.quantity}
                          onChange={e => setItem(i, 'quantity', e.target.value)} required />
                        {item.product_id && parseInt(item.quantity) > item.stock && (
                          <div className="text-danger small mt-1" style={{ fontSize: '0.75rem' }}>
                            Exceeds stock ({item.stock})
                          </div>
                        )}
                      </div>
                      <div className="sale-item-price">
                        <div className="input-group input-group-sm">
                          <span className="input-group-text">₹</span>
                          <input type="number" step="0.01" min="0" className="form-control"
                            value={item.unit_price}
                            onChange={e => setItem(i, 'unit_price', e.target.value)} />
                        </div>
                      </div>
                      <div className="sale-item-total">
                        <span className="fw-semibold">
                          {formatCurrency((parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0))}
                        </span>
                      </div>
                      <button type="button" className="btn-icon btn-icon-danger" onClick={() => removeItem(i)}
                        disabled={saleItems.length === 1}>
                        <i className="bi bi-x-lg"></i>
                      </button>
                    </div>
                  ))}
                </div>

                {/* Payment Status, Amount Paid, Balance Due */}
                <div className="row g-3 mb-3 mt-1">
                  <div className="col-md-4">
                    <label className="form-label">Payment Status</label>
                    <select className="form-select" value={paymentStatus} onChange={e => handlePaymentStatusChange(e.target.value)}>
                      <option value="paid">Paid</option>
                      <option value="partial">Partial</option>
                      <option value="unpaid">Unpaid</option>
                    </select>
                  </div>
                  <div className="col-md-4">
                    <label className="form-label">Amount Paid</label>
                    <div className="input-group">
                      <span className="input-group-text">₹</span>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max={total_}
                        className="form-control"
                        value={paymentStatus === 'paid' ? total_ : paymentStatus === 'unpaid' ? 0 : amountPaid}
                        onChange={handleAmountPaidChange}
                        disabled={paymentStatus === 'unpaid'}
                      />
                    </div>
                  </div>
                  <div className="col-md-4">
                    <label className="form-label">Balance Due</label>
                    <div className="input-group">
                      <span className="input-group-text">₹</span>
                      <input
                        type="text"
                        className={`form-control fw-bold ${balanceDue > 0 ? 'text-danger' : 'text-success'}`}
                        value={formatCurrency(balanceDue)}
                        readOnly
                        disabled
                      />
                    </div>
                  </div>
                </div>

                {/* Totals */}
                <div className="sale-totals">
                  <div className="sale-total-row">
                    <span>Subtotal</span><span>{formatCurrency(subtotal)}</span>
                  </div>
                  <div className="sale-total-row">
                    <div className="d-flex align-items-center gap-2">
                      <span>Discount</span>
                      <select className="form-select form-select-sm" style={{ width: 'auto' }}
                        value={discountType} onChange={e => setDiscountType(e.target.value)}>
                        <option value="amount">₹</option>
                        <option value="percent">%</option>
                      </select>
                      <input type="number" min="0" step="0.01" className="form-control form-control-sm"
                        style={{ width: '90px' }} value={discount}
                        onChange={e => setDiscount(e.target.value)} />
                    </div>
                    <span className="text-danger">- {formatCurrency(discountAmount)}</span>
                  </div>
                  <div className="sale-total-row sale-total-final">
                    <span>Total</span><span>{formatCurrency(total_)}</span>
                  </div>
                  <div className="sale-total-row">
                    <span>Amount Paid</span><span>{formatCurrency(effectiveAmountPaid)}</span>
                  </div>
                  <div className={`sale-total-row ${balanceDue > 0 ? 'text-danger fw-bold' : 'text-success'}`}>
                    <span>Balance Due</span><span>{formatCurrency(balanceDue)}</span>
                  </div>
                </div>

                <div className="mt-3">
                  <label className="form-label">Notes</label>
                  <input className="form-control form-control-sm" placeholder="Optional note..." value={notes} onChange={e => setNotes(e.target.value)} />
                </div>
              </div>
              <div className="modal-footer-custom">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? <span className="spinner-border spinner-border-sm me-1" /> : <i className="bi bi-check2 me-1"></i>}
                  Complete Sale · {formatCurrency(total_)}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Sale Modal */}
      {viewSale && (
        <div className="modal-backdrop-custom" onClick={() => setViewSale(null)}>
          <div className="modal-dialog-custom" onClick={e => e.stopPropagation()}>
            <div className="modal-header-custom">
              <h5>Sale Details — {viewSale.sale_number}</h5>
              <button className="btn-close" onClick={() => setViewSale(null)} />
            </div>
            <div className="modal-body-custom">
              <div className="row g-2 mb-3">
                <div className="col-4"><p className="mb-0 text-muted small">Customer</p><p className="mb-0 fw-semibold">{viewSale.customer_name}</p></div>
                <div className="col-4"><p className="mb-0 text-muted small">Sale Date</p><p className="mb-0 fw-semibold">{formatDateTime(viewSale.sale_date || viewSale.created_at)}</p></div>
                <div className="col-4"><p className="mb-0 text-muted small">Payment Method</p><p className="mb-0 fw-semibold text-capitalize">{viewSale.payment_method}</p></div>
                <div className="col-4"><p className="mb-0 text-muted small">Payment Status</p><p className="mb-0 fw-semibold text-capitalize"><span className={`badge ${viewSale.payment_status === 'paid' ? 'bg-success' : viewSale.payment_status === 'partial' ? 'bg-warning text-dark' : 'bg-danger'}`}>{viewSale.payment_status || 'paid'}</span></p></div>
                <div className="col-4"><p className="mb-0 text-muted small">Amount Paid</p><p className="mb-0 fw-semibold text-success">{formatCurrency(viewSale.amount_paid)}</p></div>
                <div className="col-4"><p className="mb-0 text-muted small">Balance Due</p><p className={`mb-0 fw-semibold ${viewSale.balance_due > 0 ? 'text-danger' : 'text-muted'}`}>{formatCurrency(viewSale.balance_due)}</p></div>
              </div>
              <table className="rm-table rm-table-sm">
                <thead><tr><th>Product</th><th>Qty</th><th>Price</th><th>Subtotal</th></tr></thead>
                <tbody>
                  {viewSale.items?.map((it, i) => (
                    <tr key={i}>
                      <td>{it.product_name}</td>
                      <td>{it.quantity}</td>
                      <td>{formatCurrency(it.unit_price)}</td>
                      <td>{formatCurrency(it.subtotal)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="sale-totals mt-3">
                <div className="sale-total-row"><span>Subtotal</span><span>{formatCurrency(viewSale.subtotal)}</span></div>
                {viewSale.discount > 0 && <div className="sale-total-row text-danger"><span>Discount</span><span>- {formatCurrency(viewSale.discount)}</span></div>}
                <div className="sale-total-row sale-total-final"><span>Total</span><span>{formatCurrency(viewSale.total)}</span></div>
                <div className="sale-total-row"><span>Amount Paid</span><span>{formatCurrency(viewSale.amount_paid)}</span></div>
                <div className={`sale-total-row ${viewSale.balance_due > 0 ? 'text-danger fw-bold' : 'text-success'}`}><span>Balance Due</span><span>{formatCurrency(viewSale.balance_due)}</span></div>
                <div className="sale-total-row text-success"><span>Gross Profit</span><span>{formatCurrency(viewSale.gross_profit)}</span></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sales;
