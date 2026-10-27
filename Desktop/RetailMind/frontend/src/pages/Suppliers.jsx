import { useState, useEffect, useCallback } from 'react';
import { suppliersApi } from '../services/api';
import PageHeader from '../components/PageHeader';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import AlertMessage from '../components/AlertMessage';
import Pagination from '../components/Pagination';
import ConfirmModal from '../components/ConfirmModal';
import { formatCurrency, formatDate, formatDateTime } from '../utils/format';

const initForm = { name: '', phone: '', email: '', address: '', contact_person: '' };

const Suppliers = () => {
  const [suppliers, setSuppliers] = useState([]);
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
  const [viewSupplier, setViewSupplier] = useState(null);

  const fetch = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const r = await suppliersApi.list({ page: p, per_page: 15, search });
      setSuppliers(r.data.items); setPages(r.data.pages); setTotal(r.data.total);
    } catch { setError('Failed to load suppliers.'); }
    finally { setLoading(false); }
  }, [search]);

  useEffect(() => { fetch(page); }, [page]);
  useEffect(() => { setPage(1); fetch(1); }, [search]);

  const openAdd = () => { setForm(initForm); setEditId(null); setFormError(''); setShowModal(true); };
  const openEdit = (s) => {
    setForm({ name: s.name, phone: s.phone || '', email: s.email || '', address: s.address || '', contact_person: s.contact_person || '' });
    setEditId(s.id); setFormError(''); setShowModal(true);
  };

  const openView = async (id) => {
    try {
      const r = await suppliersApi.get(id);
      setViewSupplier(r.data);
    } catch { setError('Failed to load supplier details.'); }
  };

  const handleField = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const save = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { setFormError('Supplier name is required.'); return; }
    setSaving(true); setFormError('');
    try {
      if (editId) { await suppliersApi.update(editId, form); setSuccess('Supplier updated.'); }
      else { await suppliersApi.create(form); setSuccess('Supplier added.'); }
      setShowModal(false); fetch(page);
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to save supplier.');
    } finally { setSaving(false); }
  };

  const confirmDelete = async () => {
    setDeleting(true);
    try {
      await suppliersApi.delete(deleteId);
      setSuccess('Supplier deleted.'); setDeleteId(null); fetch(page);
    } catch { setError('Failed to delete supplier.'); }
    finally { setDeleting(false); }
  };

  return (
    <div className="page-container">
      <PageHeader
        title="Suppliers"
        subtitle={`${total} supplier${total !== 1 ? 's' : ''}`}
        actions={
          <button className="btn btn-primary" onClick={openAdd}>
            <i className="bi bi-building-add me-2"></i>Add Supplier
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

      {loading ? <LoadingSpinner /> : suppliers.length === 0 ? (
        <EmptyState icon="building" title="No suppliers yet"
          message="Add suppliers to track your purchasing relationships."
          action={<button className="btn btn-primary mt-2" onClick={openAdd}><i className="bi bi-building-add me-2"></i>Add Supplier</button>} />
      ) : (
        <>
          <div className="table-responsive">
            <table className="rm-table">
              <thead>
                <tr><th>Name</th><th>Contact Person</th><th>Phone</th><th>Orders</th><th>Total Purchased</th><th>Last Order</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {suppliers.map(s => (
                  <tr key={s.id}>
                    <td><p className="product-name mb-0">{s.name}</p></td>
                    <td>{s.contact_person || <span className="text-muted">—</span>}</td>
                    <td>{s.phone || <span className="text-muted">—</span>}</td>
                    <td>{s.total_orders}</td>
                    <td>{formatCurrency(s.total_purchase_value)}</td>
                    <td>{s.last_purchase_date ? formatDate(s.last_purchase_date) : <span className="text-muted">—</span>}</td>
                    <td>
                      <div className="action-btns">
                        <button className="btn-icon" title="View" onClick={() => openView(s.id)}><i className="bi bi-eye"></i></button>
                        <button className="btn-icon" title="Edit" onClick={() => openEdit(s)}><i className="bi bi-pencil"></i></button>
                        <button className="btn-icon btn-icon-danger" title="Delete" onClick={() => setDeleteId(s.id)}><i className="bi bi-trash"></i></button>
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
              <h5>{editId ? 'Edit Supplier' : 'Add Supplier'}</h5>
              <button className="btn-close" onClick={() => setShowModal(false)} />
            </div>
            <form onSubmit={save}>
              <div className="modal-body-custom">
                <AlertMessage type="danger" message={formError} onClose={() => setFormError('')} />
                <div className="row g-3">
                  <div className="col-12"><label className="form-label">Supplier Name *</label>
                    <input className="form-control" name="name" value={form.name} onChange={handleField} required /></div>
                  <div className="col-md-6"><label className="form-label">Contact Person</label>
                    <input className="form-control" name="contact_person" value={form.contact_person} onChange={handleField} /></div>
                  <div className="col-md-6"><label className="form-label">Phone</label>
                    <input className="form-control" name="phone" value={form.phone} onChange={handleField} /></div>
                  <div className="col-md-6"><label className="form-label">Email</label>
                    <input type="email" className="form-control" name="email" value={form.email} onChange={handleField} /></div>
                  <div className="col-12"><label className="form-label">Address</label>
                    <input className="form-control" name="address" value={form.address} onChange={handleField} /></div>
                </div>
              </div>
              <div className="modal-footer-custom">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? <span className="spinner-border spinner-border-sm me-1" /> : null}
                  {editId ? 'Save Changes' : 'Add Supplier'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {viewSupplier && (
        <div className="modal-backdrop-custom" onClick={() => setViewSupplier(null)}>
          <div className="modal-dialog-custom modal-lg-custom" onClick={e => e.stopPropagation()}>
            <div className="modal-header-custom">
              <h5>{viewSupplier.name}</h5>
              <button className="btn-close" onClick={() => setViewSupplier(null)} />
            </div>
            <div className="modal-body-custom">
              <div className="row g-3 mb-4">
                <div className="col-md-3"><p className="text-muted small mb-0">Contact</p><p className="mb-0 fw-semibold">{viewSupplier.contact_person || '—'}</p></div>
                <div className="col-md-3"><p className="text-muted small mb-0">Phone</p><p className="mb-0 fw-semibold">{viewSupplier.phone || '—'}</p></div>
                <div className="col-md-3"><p className="text-muted small mb-0">Total Orders</p><p className="mb-0 fw-semibold">{viewSupplier.total_orders}</p></div>
                <div className="col-md-3"><p className="text-muted small mb-0">Total Purchased</p><p className="mb-0 fw-semibold">{formatCurrency(viewSupplier.total_purchase_value)}</p></div>
              </div>
              <h6>Recent Purchases</h6>
              {viewSupplier.recent_purchases?.length === 0 ? <p className="text-muted small">No purchases yet.</p> : (
                <table className="rm-table rm-table-sm">
                  <thead><tr><th>PO #</th><th>Total</th><th>Date</th></tr></thead>
                  <tbody>
                    {viewSupplier.recent_purchases?.map(p => (
                      <tr key={p.id}><td>{p.purchase_number}</td><td>{formatCurrency(p.total)}</td><td>{formatDateTime(p.created_at)}</td></tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}

      <ConfirmModal show={!!deleteId} title="Delete Supplier"
        message="Delete this supplier? Their purchase history will remain."
        onConfirm={confirmDelete} onCancel={() => setDeleteId(null)} loading={deleting} />
    </div>
  );
};

export default Suppliers;
