import { useState, useEffect, useCallback } from 'react';
import { purchasesApi, productsApi, suppliersApi } from '../services/api';
import PageHeader from '../components/PageHeader';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import AlertMessage from '../components/AlertMessage';
import Pagination from '../components/Pagination';
import { formatCurrency, formatDateTime } from '../utils/format';

const Purchases = () => {
  const [purchases, setPurchases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [viewPurchase, setViewPurchase] = useState(null);

  // Form state
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [items, setItems] = useState([{ product_id: '', quantity: 1, unit_cost: 0, product_name: '' }]);
  const [supplierId, setSupplierId] = useState('');
  const [purchaseNumber, setPurchaseNumber] = useState('');
  const [purchaseDate, setPurchaseDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [supplierInvoiceNumber, setSupplierInvoiceNumber] = useState('');
  const [discount, setDiscount] = useState(0);
  const [payMethod, setPayMethod] = useState('cash');
  const [paymentStatus, setPaymentStatus] = useState('paid');
  const [amountPaid, setAmountPaid] = useState('');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  const fetchPurchases = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const r = await purchasesApi.list({ page: p, per_page: 15 });
      setPurchases(r.data.items); setPages(r.data.pages); setTotal(r.data.total);
    } catch { setError('Failed to load purchases.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchPurchases(page); }, [page]);

  const openNew = async () => {
    setFormError('');
    setItems([{ product_id: '', quantity: 1, unit_cost: 0, product_name: '' }]);
    setSupplierId(''); setDiscount(0); setPayMethod('cash'); setNotes('');
    setPurchaseDate(new Date().toISOString().split('T')[0]);
    setSupplierInvoiceNumber('');
    setPaymentStatus('paid');
    setAmountPaid('');
    setPurchaseNumber('Generating...');

    try {
      const numRes = await purchasesApi.getNextNumber();
      setPurchaseNumber(numRes.data.purchase_number);
    } catch {
      setPurchaseNumber('PO-AUTO');
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
      const r = await suppliersApi.list({ per_page: 100 }); 
      setSuppliers(r.data.items); 
    } catch (err) {
      console.error('Failed to load suppliers:', err);
      setFormError('Unable to load suppliers. Please try again.');
      success = false;
    }
    
    // Only open modal if both dropdowns loaded successfully
    if (success) {
      setShowModal(true);
    }
  };

  const setItemField = (i, field, value) => {
    setItems(arr => {
      const next = [...arr];
      next[i] = { ...next[i], [field]: value };
      if (field === 'product_id') {
        const p = products.find(x => x.id === value);
        if (p) {
          next[i].unit_cost = p.cost_price;
          next[i].product_name = p.name;
        }
      }
      return next;
    });
  };

  const subtotal = items.reduce((s, i) => s + (parseFloat(i.quantity) || 0) * (parseFloat(i.unit_cost) || 0), 0);
  const total_ = Math.max(0, subtotal - (parseFloat(discount) || 0));

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

  const savePurchase = async (e) => {
    e.preventDefault();
    const valid = items.every(i => i.product_id && parseInt(i.quantity) > 0);
    if (!valid) { setFormError('All items must have a product and quantity of at least 1.'); return; }
    
    for (const item of items) {
      if ((parseFloat(item.unit_cost) || 0) < 0) {
        setFormError('Unit cost cannot be negative.');
        return;
      }
    }

    setSaving(true); setFormError('');
    try {
      await purchasesApi.create({
        purchase_number: purchaseNumber && !purchaseNumber.includes('Generating') && purchaseNumber !== 'PO-AUTO' ? purchaseNumber : null,
        purchase_date: purchaseDate || null,
        supplier_id: supplierId || null,
        supplier_invoice_number: supplierInvoiceNumber.trim() || null,
        items: items.map(i => ({ product_id: i.product_id, quantity: parseInt(i.quantity), unit_cost: parseFloat(i.unit_cost) })),
        discount: parseFloat(discount) || 0,
        payment_method: payMethod,
        payment_status: paymentStatus,
        amount_paid: effectiveAmountPaid,
        balance_due: balanceDue,
        notes,
      });
      setSuccess('Purchase recorded. Inventory updated.');
      setShowModal(false);
      fetchPurchases(1); setPage(1);
    } catch (err) {
      const d = err.response?.data?.detail;
      setFormError(typeof d === 'string' ? d : 'Failed to record purchase.');
    } finally { setSaving(false); }
  };

  return (
    <div className="page-container">
      <PageHeader
        title="Purchases"
        subtitle={`${total} purchase order${total !== 1 ? 's' : ''} recorded`}
        actions={
          <button className="btn btn-primary" onClick={openNew}>
            <i className="bi bi-plus-lg me-2"></i>Record Purchase
          </button>
        }
      />

      <AlertMessage type="success" message={success} onClose={() => setSuccess('')} />
      <AlertMessage type="danger" message={error} onClose={() => setError('')} />

      {loading ? <LoadingSpinner /> : purchases.length === 0 ? (
        <EmptyState icon="truck" title="No purchases recorded"
          message="Record a purchase to update your inventory."
          action={<button className="btn btn-primary mt-2" onClick={openNew}><i className="bi bi-plus-lg me-2"></i>Record Purchase</button>}
        />
      ) : (
        <>
          <div className="table-responsive">
            <table className="rm-table">
              <thead>
                <tr>
                  <th>PO #</th><th>Supplier</th><th>Items</th>
                  <th>Total Cost</th><th>Payment</th><th>Date</th><th></th>
                </tr>
              </thead>
              <tbody>
                {purchases.map(p => (
                  <tr key={p.id}>
                    <td><code className="sku-code">{p.purchase_number}</code></td>
                    <td>{p.supplier_name || <span className="text-muted">—</span>}</td>
                    <td>{p.items?.length}</td>
                    <td><strong>{formatCurrency(p.total)}</strong></td>
                    <td>
                      <span className="badge bg-light text-dark border me-1">{p.payment_method}</span>
                      <span className={`badge ${p.payment_status === 'paid' ? 'bg-success' : p.payment_status === 'partial' ? 'bg-warning text-dark' : 'bg-danger'}`}>
                        {p.payment_status || 'paid'}
                      </span>
                    </td>
                    <td>{formatDateTime(p.purchase_date || p.created_at)}</td>
                    <td>
                      <button className="btn-icon" title="View" onClick={() => setViewPurchase(p)}>
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

      {/* New Purchase Modal */}
      {showModal && (
        <div className="modal-backdrop-custom" onClick={() => setShowModal(false)}>
          <div className="modal-dialog-custom modal-xl-custom" onClick={e => e.stopPropagation()}>
            <div className="modal-header-custom">
              <h5><i className="bi bi-truck me-2"></i>Record Purchase</h5>
              <button className="btn-close" onClick={() => setShowModal(false)} />
            </div>
            <form onSubmit={savePurchase}>
              <div className="modal-body-custom">
                <AlertMessage type="danger" message={formError} onClose={() => setFormError('')} />
                <div className="row g-3 mb-3">
                  <div className="col-md-3">
                    <label className="form-label">Purchase ID (auto-generated)</label>
                    <input type="text" className="form-control" value={purchaseNumber} readOnly disabled />
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Purchase Date</label>
                    <input type="date" className="form-control" value={purchaseDate} onChange={e => setPurchaseDate(e.target.value)} required />
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Supplier (optional)</label>
                    <select className="form-select" value={supplierId} onChange={e => setSupplierId(e.target.value)}>
                      <option value="">Select supplier</option>
                      {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                    </select>
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Payment Method</label>
                    <select className="form-select" value={payMethod} onChange={e => setPayMethod(e.target.value)}>
                      <option value="cash">Cash</option>
                      <option value="card">Card</option>
                      <option value="upi">UPI</option>
                      <option value="credit">Credit</option>
                      <option value="bank_transfer">Bank Transfer</option>
                    </select>
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Supplier Invoice Number (optional)</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="e.g. INV-2026-001"
                      value={supplierInvoiceNumber}
                      onChange={e => setSupplierInvoiceNumber(e.target.value)}
                    />
                  </div>
                </div>

                <div className="sale-items-section">
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <h6 className="mb-0">Items</h6>
                    <button type="button" className="btn btn-outline-primary btn-sm"
                      onClick={() => setItems(a => [...a, { product_id: '', quantity: 1, unit_cost: 0, product_name: '' }])}>
                      <i className="bi bi-plus-lg me-1"></i>Add Item
                    </button>
                  </div>
                  {items.map((item, i) => (
                    <div key={i} className="sale-item-row">
                      <div className="sale-item-product">
                        <select className="form-select form-select-sm" value={item.product_id}
                          onChange={e => setItemField(i, 'product_id', e.target.value)} required>
                          <option value="">Select product</option>
                          {products.map(p => <option key={p.id} value={p.id}>{p.name} (SKU: {p.sku})</option>)}
                        </select>
                      </div>
                      <div className="sale-item-qty">
                        <input type="number" min="1" className="form-control form-control-sm"
                          placeholder="Qty" value={item.quantity}
                          onChange={e => setItemField(i, 'quantity', e.target.value)} required />
                      </div>
                      <div className="sale-item-price">
                        <div className="input-group input-group-sm">
                          <span className="input-group-text">₹</span>
                          <input type="number" step="0.01" min="0" className="form-control"
                            placeholder="Unit cost" value={item.unit_cost}
                            onChange={e => setItemField(i, 'unit_cost', e.target.value)} />
                        </div>
                      </div>
                      <div className="sale-item-total">
                        <span className="fw-semibold">
                          {formatCurrency((parseFloat(item.quantity) || 0) * (parseFloat(item.unit_cost) || 0))}
                        </span>
                      </div>
                      <button type="button" className="btn-icon btn-icon-danger"
                        onClick={() => setItems(a => a.filter((_, idx) => idx !== i))}
                        disabled={items.length === 1}>
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

                <div className="sale-totals">
                  <div className="sale-total-row"><span>Subtotal</span><span>{formatCurrency(subtotal)}</span></div>
                  <div className="sale-total-row">
                    <div className="d-flex align-items-center gap-2">
                      <span>Discount (₹)</span>
                      <input type="number" min="0" step="0.01" className="form-control form-control-sm"
                        style={{ width: '90px' }} value={discount} onChange={e => setDiscount(e.target.value)} />
                    </div>
                    <span className="text-danger">- {formatCurrency(parseFloat(discount) || 0)}</span>
                  </div>
                  <div className="sale-total-row sale-total-final"><span>Total Cost</span><span>{formatCurrency(total_)}</span></div>
                  <div className="sale-total-row"><span>Amount Paid</span><span>{formatCurrency(effectiveAmountPaid)}</span></div>
                  <div className={`sale-total-row ${balanceDue > 0 ? 'text-danger fw-bold' : 'text-success'}`}><span>Balance Due</span><span>{formatCurrency(balanceDue)}</span></div>
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
                  Save Purchase · {formatCurrency(total_)}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Modal */}
      {viewPurchase && (
        <div className="modal-backdrop-custom" onClick={() => setViewPurchase(null)}>
          <div className="modal-dialog-custom" onClick={e => e.stopPropagation()}>
            <div className="modal-header-custom">
              <h5>Purchase — {viewPurchase.purchase_number}</h5>
              <button className="btn-close" onClick={() => setViewPurchase(null)} />
            </div>
            <div className="modal-body-custom">
              <div className="row g-2 mb-3">
                <div className="col-4"><p className="mb-0 text-muted small">Supplier</p><p className="mb-0 fw-semibold">{viewPurchase.supplier_name || '—'}</p></div>
                <div className="col-4"><p className="mb-0 text-muted small">Purchase Date</p><p className="mb-0 fw-semibold">{formatDateTime(viewPurchase.purchase_date || viewPurchase.created_at)}</p></div>
                <div className="col-4"><p className="mb-0 text-muted small">Invoice #</p><p className="mb-0 fw-semibold">{viewPurchase.supplier_invoice_number || '—'}</p></div>
                <div className="col-4"><p className="mb-0 text-muted small">Payment Method</p><p className="mb-0 fw-semibold text-capitalize">{viewPurchase.payment_method}</p></div>
                <div className="col-4"><p className="mb-0 text-muted small">Payment Status</p><p className="mb-0 fw-semibold text-capitalize"><span className={`badge ${viewPurchase.payment_status === 'paid' ? 'bg-success' : viewPurchase.payment_status === 'partial' ? 'bg-warning text-dark' : 'bg-danger'}`}>{viewPurchase.payment_status || 'paid'}</span></p></div>
                <div className="col-4"><p className="mb-0 text-muted small">Amount Paid</p><p className="mb-0 fw-semibold text-success">{formatCurrency(viewPurchase.amount_paid)}</p></div>
                <div className="col-4"><p className="mb-0 text-muted small">Balance Due</p><p className={`mb-0 fw-semibold ${viewPurchase.balance_due > 0 ? 'text-danger' : 'text-muted'}`}>{formatCurrency(viewPurchase.balance_due)}</p></div>
              </div>
              <table className="rm-table rm-table-sm">
                <thead><tr><th>Product</th><th>Qty</th><th>Unit Cost</th><th>Subtotal</th></tr></thead>
                <tbody>
                  {viewPurchase.items?.map((it, i) => (
                    <tr key={i}>
                      <td>{it.product_name}</td><td>{it.quantity}</td>
                      <td>{formatCurrency(it.unit_cost)}</td><td>{formatCurrency(it.subtotal)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="sale-totals mt-3">
                <div className="sale-total-row"><span>Subtotal</span><span>{formatCurrency(viewPurchase.subtotal)}</span></div>
                {viewPurchase.discount > 0 && <div className="sale-total-row text-danger"><span>Discount</span><span>- {formatCurrency(viewPurchase.discount)}</span></div>}
                <div className="sale-total-row sale-total-final"><span>Total Cost</span><span>{formatCurrency(viewPurchase.total)}</span></div>
                <div className="sale-total-row"><span>Amount Paid</span><span>{formatCurrency(viewPurchase.amount_paid)}</span></div>
                <div className={`sale-total-row ${viewPurchase.balance_due > 0 ? 'text-danger fw-bold' : 'text-success'}`}><span>Balance Due</span><span>{formatCurrency(viewPurchase.balance_due)}</span></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Purchases;
