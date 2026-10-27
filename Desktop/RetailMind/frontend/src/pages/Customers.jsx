import { useState, useEffect, useCallback } from 'react';
import { customersApi } from '../services/api';
import PageHeader from '../components/PageHeader';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import AlertMessage from '../components/AlertMessage';
import Pagination from '../components/Pagination';
import ConfirmModal from '../components/ConfirmModal';
import { formatCurrency, formatDate, formatDateTime } from '../utils/format';

const initForm = { name: '', phone: '', email: '', address: '' };

const Customers = () => {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editId, setEditId] = useState(null);
  const [form, setForm] = useState(initForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const [deleteId, setDeleteId] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [viewCustomer, setViewCustomer] = useState(null);
  const [viewLoading, setViewLoading] = useState(false);

  const fetch = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const r = await customersApi.list({ page: p, per_page: 15, search });
      setCustomers(r.data.items); setPages(r.data.pages); setTotal(r.data.total);
    } catch { setError('Failed to load customers.'); }
    finally { setLoading(false); }
  }, [search]);

  useEffect(() => { fetch(page); }, [page]);
  useEffect(() => { setPage(1); fetch(1); }, [search]);

  const openAdd = () => { setForm(initForm); setEditId(null); setFormError(''); setShowModal(true); };
  const openEdit = (c) => {
    setForm({ name: c.name, phone: c.phone || '', email: c.email || '', address: c.address || '' });
    setEditId(c.id); setFormError(''); setShowModal(true);
  };

  const openView = async (id) => {
    setViewLoading(true);
    try {
      const r = await customersApi.get(id);
      setViewCustomer(r.data);
    } catch { setError('Failed to load customer details.'); }
    finally { setViewLoading(false); }
  };

  const handleField = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const save = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { setFormError('Customer name is required.'); return; }
    setSaving(true); setFormError('');
    try {
      if (editId) {
        await customersApi.update(editId, form);
        setSuccess('Customer updated.');
      } else {
        await customersApi.create(form);
        setSuccess('Customer added.');
      }
      setShowModal(false); fetch(page);
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to save customer.');
    } finally { setSaving(false); }
  };

  const confirmDelete = async () => {
    setDeleting(true);
    try {
      await customersApi.delete(deleteId);
      setSuccess('Customer deleted.'); setDeleteId(null); fetch(page);
    } catch { setError('Failed to delete customer.'); }
    finally { setDeleting(false); }
  };

  return (
    <div className="page-container">
      <PageHeader
        title="Customers"
        subtitle={`${total} customer${total !== 1 ? 's' : ''}`}
        actions={
          <button className="btn btn-primary" onClick={openAdd}>
            <i className="bi bi-person-plus me-2"></i>Add Customer
          </button>
        }
      />
      <AlertMessage type="success" message={success} onClose={() => setSuccess('')} />
      <AlertMessage type="danger" message={error} onClose={() => setError('')} />

      <div className="filter-bar">
        <div className="search-input-wrap">
          <i className="bi bi-search search-icon"></i>
          <input className="form-control search-input" placeholder="Search by name, phone, email..."
            value={search} onChange={e => setSearch(e.target.value)} />
        </div>
      </div>

      {loading ? <LoadingSpinner /> : customers.length === 0 ? (
        <EmptyState icon="people" title="No customers yet"
          message="Add your first customer to start tracking their purchases."
          action={<button className="btn btn-primary mt-2" onClick={openAdd}><i className="bi bi-person-plus me-2"></i>Add Customer</button>} />
      ) : (
        <>
          <div className="table-responsive">
            <table className="rm-table">
              <thead>
                <tr><th>Name</th><th>Phone</th><th>Email</th><th>Orders</th><th>Total Spent</th><th>Last Purchase</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {customers.map(c => (
                  <tr key={c.id}>
                    <td><p className="product-name mb-0">{c.name}</p></td>
                    <td>{c.phone || <span className="text-muted">—</span>}</td>
                    <td>{c.email || <span className="text-muted">—</span>}</td>
                    <td>{c.total_orders}</td>
                    <td>{formatCurrency(c.total_purchases)}</td>
                    <td>{c.last_purchase_date ? formatDate(c.last_purchase_date) : <span className="text-muted">—</span>}</td>
                    <td>
                      <div className="action-btns">
                        <button className="btn-icon" title="View" onClick={() => openView(c.id)}><i className="bi bi-eye"></i></button>
                        <button className="btn-icon" title="Edit" onClick={() => openEdit(c)}><i className="bi bi-pencil"></i></button>
                        <button className="btn-icon btn-icon-danger" title="Delete" onClick={() => setDeleteId(c.id)}><i className="bi bi-trash"></i></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pages={pages} onPage={p => setPage(p)} />
        </>
      )}

      {showModal && (
        <div className="modal-backdrop-custom" onClick={() => setShowModal(false)}>
          <div className="modal-dialog-custom" onClick={e => e.stopPropagation()}>
            <div className="modal-header-custom">
              <h5>{editId ? 'Edit Customer' : 'Add Customer'}</h5>
              <button className="btn-close" onClick={() => setShowModal(false)} />
            </div>
            <form onSubmit={save}>
              <div className="modal-body-custom">
                <AlertMessage type="danger" message={formError} onClose={() => setFormError('')} />
                <div className="row g-3">
                  <div className="col-12">
                    <label className="form-label">Full Name *</label>
                    <input className="form-control" name="name" value={form.name} onChange={handleField} required />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Phone</label>
                    <input className="form-control" name="phone" value={form.phone} onChange={handleField} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Email</label>
                    <input type="email" className="form-control" name="email" value={form.email} onChange={handleField} />
                  </div>
                  <div className="col-12">
                    <label className="form-label">Address</label>
                    <input className="form-control" name="address" value={form.address} onChange={handleField} />
                  </div>
                </div>
              </div>
              <div className="modal-footer-custom">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? <span className="spinner-border spinner-border-sm me-1" /> : null}
                  {editId ? 'Save Changes' : 'Add Customer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {viewCustomer && (
        <div className="modal-backdrop-custom" onClick={() => setViewCustomer(null)}>
          <div className="modal-dialog-custom modal-lg-custom" onClick={e => e.stopPropagation()}>
            <div className="modal-header-custom">
              <h5>{viewCustomer.name}</h5>
              <button className="btn-close" onClick={() => setViewCustomer(null)} />
            </div>
            <div className="modal-body-custom">
              <div className="row g-3 mb-4">
                <div className="col-md-3"><p className="text-muted small mb-0">Phone</p><p className="mb-0 fw-semibold">{viewCustomer.phone || '—'}</p></div>
                <div className="col-md-3"><p className="text-muted small mb-0">Email</p><p className="mb-0 fw-semibold">{viewCustomer.email || '—'}</p></div>
                <div className="col-md-3"><p className="text-muted small mb-0">Total Orders</p><p className="mb-0 fw-semibold">{viewCustomer.total_orders}</p></div>
                <div className="col-md-3"><p className="text-muted small mb-0">Total Spent</p><p className="mb-0 fw-semibold">{formatCurrency(viewCustomer.total_purchases)}</p></div>
              </div>
              <h6>Recent Purchases</h6>
              {viewCustomer.recent_sales?.length === 0 ? (
                <p className="text-muted small">No purchases yet.</p>
              ) : (
                <table className="rm-table rm-table-sm">
                  <thead><tr><th>Sale #</th><th>Total</th><th>Date</th></tr></thead>
                  <tbody>
                    {viewCustomer.recent_sales?.map(s => (
                      <tr key={s.id}><td>{s.sale_number}</td><td>{formatCurrency(s.total)}</td><td>{formatDateTime(s.created_at)}</td></tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}

      <ConfirmModal show={!!deleteId} title="Delete Customer"
        message="Delete this customer? Their purchase history will remain."
        onConfirm={confirmDelete} onCancel={() => setDeleteId(null)} loading={deleting} />
    </div>
  );
};

export default Customers;
