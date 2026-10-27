import { useState, useEffect, useCallback } from 'react';
import { productsApi, categoriesApi, suppliersApi } from '../services/api';
import PageHeader from '../components/PageHeader';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import AlertMessage from '../components/AlertMessage';
import Pagination from '../components/Pagination';
import ConfirmModal from '../components/ConfirmModal';
import { formatCurrency, stockStatusLabel, stockStatusClass } from '../utils/format';

const UNITS = ['pcs', 'kg', 'g', 'litre', 'ml', 'pack', 'box', 'dozen', 'pair', 'set'];

const initForm = {
  name: '', sku: '', category_id: '', brand: '', unit: 'pcs',
  cost_price: '', selling_price: '', current_stock: '', minimum_stock: '',
  supplier_id: '', description: '',
};

const initSupplierForm = {
  name: '', phone: '', email: '', address: '',
};

const initCategoryForm = {
  name: '', description: '',
};

const Products = () => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [catFilter, setCatFilter] = useState('');
  const [stockFilter, setStockFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editId, setEditId] = useState(null);
  const [form, setForm] = useState(initForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const [deleteId, setDeleteId] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [showSupplierModal, setShowSupplierModal] = useState(false);
  const [supplierForm, setSupplierForm] = useState(initSupplierForm);
  const [savingSupplier, setSavingSupplier] = useState(false);
  const [supplierError, setSupplierError] = useState('');
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [categoryForm, setCategoryForm] = useState(initCategoryForm);
  const [savingCategory, setSavingCategory] = useState(false);
  const [categoryError, setCategoryError] = useState('');

  const fetchProducts = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const res = await productsApi.list({
        page: p, per_page: 15, search, category_id: catFilter, stock_status: stockFilter
      });
      setProducts(res.data.items);
      setPages(res.data.pages);
      setTotal(res.data.total);
    } catch { setError('Failed to load products.'); }
    finally { setLoading(false); }
  }, [search, catFilter, stockFilter]);

  useEffect(() => { fetchProducts(page); }, [page]);
  useEffect(() => { setPage(1); fetchProducts(1); }, [search, catFilter, stockFilter]);

  useEffect(() => {
    let mounted = true;
    const loadDropdowns = async () => {
      try {
        const r = await categoriesApi.list({ per_page: 100 });
        if (mounted) setCategories(r.data.items);
      } catch (err) {
        console.error('Failed to load categories:', err);
        if (mounted) setError('Failed to load categories. Please refresh the page.');
      }
    };
    
    try {
      suppliersApi.list({ per_page: 100 })
        .then(r => {
          console.log('Suppliers loaded:', r.data.items);
          if (mounted) setSuppliers(r.data.items);
        })
        .catch(err => {
          console.error('Failed to load suppliers:', err);
          if (mounted) setError('Failed to load suppliers. Please refresh the page.');
        });
    } catch (err) {
      console.error('Suppliers load error:', err);
    }
    
    loadDropdowns();
    
    return () => { mounted = false; };
  }, []);

  const openAdd = () => { setForm(initForm); setEditId(null); setFormError(''); setShowModal(true); };
  const openEdit = (p) => {
    setForm({
      name: p.name, sku: p.sku, category_id: p.category_id || '',
      brand: p.brand || '', unit: p.unit || 'pcs',
      cost_price: p.cost_price, selling_price: p.selling_price,
      current_stock: p.current_stock, minimum_stock: p.minimum_stock,
      supplier_id: p.supplier_id || '', description: p.description || '',
    });
    setEditId(p.id); setFormError(''); setShowModal(true);
  };

  const handleField = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const handleSupplierField = (e) => setSupplierForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const handleCategoryField = (e) => setCategoryForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const openAddCategory = () => {
    setCategoryForm(initCategoryForm);
    setCategoryError('');
    setShowCategoryModal(true);
  };

  const saveCategory = async (e) => {
    e.preventDefault();
    if (!categoryForm.name.trim()) {
      setCategoryError('Category name is required.');
      return;
    }
    setSavingCategory(true);
    setCategoryError('');
    try {
      await categoriesApi.create(categoryForm);
      setSuccess('Category added successfully.');
      setShowCategoryModal(false);
      // Refresh categories list and select the new one
      const res = await categoriesApi.list({ per_page: 100 });
      setCategories(res.data.items);
      // Auto-select the newly created category (the last one when sorted)
      const newCategory = res.data.items.find(c => c.name === categoryForm.name);
      if (newCategory) {
        setForm(f => ({ ...f, category_id: newCategory.id }));
      }
    } catch (err) {
      const d = err.response?.data?.detail;
      setCategoryError(typeof d === 'string' ? d : 'Failed to add category.');
    } finally {
      setSavingCategory(false);
    }
  };

  const openAddSupplier = () => {
    setSupplierForm(initSupplierForm);
    setSupplierError('');
    setShowSupplierModal(true);
  };

  const saveSupplier = async (e) => {
    e.preventDefault();
    if (!supplierForm.name.trim()) {
      setSupplierError('Supplier name is required.');
      return;
    }
    setSavingSupplier(true);
    setSupplierError('');
    try {
      const newSupplier = await suppliersApi.create(supplierForm);
      setSuccess('Supplier added successfully.');
      setShowSupplierModal(false);
      // Refresh suppliers list
      const res = await suppliersApi.list({ per_page: 100 });
      setSuppliers(res.data.items);
    } catch (err) {
      const d = err.response?.data?.detail;
      setSupplierError(typeof d === 'string' ? d : 'Failed to add supplier.');
    } finally {
      setSavingSupplier(false);
    }
  };

  const save = async (e) => {
    e.preventDefault();
    if (!form.name.trim() || !form.sku.trim()) { setFormError('Product name and SKU are required.'); return; }
    setSaving(true); setFormError('');
    try {
      const payload = {
        ...form,
        cost_price: parseFloat(form.cost_price) || 0,
        selling_price: parseFloat(form.selling_price) || 0,
        current_stock: parseInt(form.current_stock) || 0,
        minimum_stock: parseInt(form.minimum_stock) || 0,
        category_id: form.category_id || null,
        supplier_id: form.supplier_id || null,
      };
      if (editId) {
        await productsApi.update(editId, payload);
        setSuccess('Product updated successfully.');
      } else {
        await productsApi.create(payload);
        setSuccess('Product added successfully.');
      }
      setShowModal(false);
      fetchProducts(page);
    } catch (err) {
      const d = err.response?.data?.detail;
      setFormError(typeof d === 'string' ? d : 'Failed to save product.');
    } finally { setSaving(false); }
  };

  const confirmDelete = async () => {
    setDeleting(true);
    try {
      await productsApi.delete(deleteId);
      setSuccess('Product deleted.');
      setDeleteId(null);
      fetchProducts(page);
    } catch { setError('Failed to delete product.'); }
    finally { setDeleting(false); }
  };

  return (
    <div className="page-container">
      <PageHeader
        title="Products"
        subtitle={`${total} product${total !== 1 ? 's' : ''} in your catalog`}
        actions={
          <button className="btn btn-primary" onClick={openAdd}>
            <i className="bi bi-plus-lg me-2"></i>Add Product
          </button>
        }
      />

      <AlertMessage type="success" message={success} onClose={() => setSuccess('')} />
      <AlertMessage type="danger" message={error} onClose={() => setError('')} />

      {/* Filters */}
      <div className="filter-bar">
        <div className="search-input-wrap">
          <i className="bi bi-search search-icon"></i>
          <input
            className="form-control search-input" placeholder="Search by name, SKU, brand..."
            value={search} onChange={e => setSearch(e.target.value)}
          />
        </div>
        <select className="form-select filter-select" value={catFilter} onChange={e => setCatFilter(e.target.value)}>
          <option value="">All Categories</option>
          {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select className="form-select filter-select" value={stockFilter} onChange={e => setStockFilter(e.target.value)}>
          <option value="">All Stock Status</option>
          <option value="in_stock">In Stock</option>
          <option value="low_stock">Low Stock</option>
          <option value="out_of_stock">Out of Stock</option>
        </select>
      </div>

      {loading ? <LoadingSpinner /> : products.length === 0 ? (
        <EmptyState icon="box-seam" title="No products found"
          message="Add your first product to get started."
          action={<button className="btn btn-primary mt-2" onClick={openAdd}><i className="bi bi-plus-lg me-2"></i>Add Product</button>}
        />
      ) : (
        <>
          <div className="table-responsive">
            <table className="rm-table">
              <thead>
                <tr>
                  <th>Product</th><th>SKU</th><th>Category</th>
                  <th>Cost</th><th>Price</th><th>Stock</th><th>Status</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map(p => (
                  <tr key={p.id}>
                    <td>
                      <div className="product-cell">
                        <p className="product-name">{p.name}</p>
                        {p.brand && <p className="product-sku">{p.brand}</p>}
                      </div>
                    </td>
                    <td><code className="sku-code">{p.sku}</code></td>
                    <td>{p.category_name || <span className="text-muted">—</span>}</td>
                    <td>{formatCurrency(p.cost_price)}</td>
                    <td>{formatCurrency(p.selling_price)}</td>
                    <td>
                      <span className={p.current_stock <= 0 ? 'text-danger fw-semibold' : p.current_stock <= p.minimum_stock ? 'text-warning fw-semibold' : ''}>
                        {p.current_stock} {p.unit}
                      </span>
                    </td>
                    <td>
                      <span className={`stock-badge ${stockStatusClass(p.stock_status)}`}>
                        {stockStatusLabel(p.stock_status)}
                      </span>
                    </td>
                    <td>
                      <div className="action-btns">
                        <button className="btn-icon" title="Edit" onClick={() => openEdit(p)}>
                          <i className="bi bi-pencil"></i>
                        </button>
                        <button className="btn-icon btn-icon-danger" title="Delete" onClick={() => setDeleteId(p.id)}>
                          <i className="bi bi-trash"></i>
                        </button>
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

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="modal-backdrop-custom" onClick={() => setShowModal(false)}>
          <div className="modal-dialog-custom modal-lg-custom" onClick={e => e.stopPropagation()}>
            <div className="modal-header-custom">
              <h5>{editId ? 'Edit Product' : 'Add Product'}</h5>
              <button className="btn-close" onClick={() => setShowModal(false)} />
            </div>
            <form onSubmit={save}>
              <div className="modal-body-custom">
                <AlertMessage type="danger" message={formError} onClose={() => setFormError('')} />
                <div className="row g-3">
                  <div className="col-md-8">
                    <label className="form-label">Product Name *</label>
                    <input className="form-control" name="name" value={form.name} onChange={handleField} required />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label">SKU *</label>
                    <input className="form-control" name="sku" value={form.sku} onChange={handleField} required />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label">Category</label>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <select className="form-select" name="category_id" value={form.category_id} onChange={handleField} style={{ flex: 1 }}>
                        <option value="">Select category</option>
                        {categories.length === 0 ? (
                          <option disabled>No categories available</option>
                        ) : (
                          categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)
                        )}
                      </select>
                      <button 
                        type="button" 
                        className="btn btn-outline-primary btn-sm" 
                        onClick={openAddCategory}
                        title="Add new category"
                        style={{ whiteSpace: 'nowrap' }}
                      >
                        <i className="bi bi-plus-lg"></i>
                      </button>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <label className="form-label">Brand</label>
                    <input className="form-control" name="brand" value={form.brand} onChange={handleField} />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label">Unit</label>
                    <select className="form-select" name="unit" value={form.unit} onChange={handleField}>
                      {UNITS.map(u => <option key={u} value={u}>{u}</option>)}
                    </select>
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Cost Price (₹)</label>
                    <input type="number" step="0.01" min="0" className="form-control" name="cost_price" value={form.cost_price} onChange={handleField} />
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Selling Price (₹)</label>
                    <input type="number" step="0.01" min="0" className="form-control" name="selling_price" value={form.selling_price} onChange={handleField} />
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Current Stock</label>
                    <input type="number" min="0" className="form-control" name="current_stock" value={form.current_stock} onChange={handleField} />
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Minimum Stock</label>
                    <input type="number" min="0" className="form-control" name="minimum_stock" value={form.minimum_stock} onChange={handleField} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Supplier</label>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <select className="form-select" name="supplier_id" value={form.supplier_id} onChange={handleField} style={{ flex: 1 }}>
                        <option value="">Select supplier</option>
                        {suppliers.length === 0 ? (
                          <option disabled>No suppliers available</option>
                        ) : (
                          suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)
                        )}
                      </select>
                      <button 
                        type="button" 
                        className="btn btn-outline-primary btn-sm" 
                        onClick={openAddSupplier}
                        title="Add new supplier"
                        style={{ whiteSpace: 'nowrap' }}
                      >
                        <i className="bi bi-plus-lg"></i>
                      </button>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Description</label>
                    <input className="form-control" name="description" value={form.description} onChange={handleField} />
                  </div>
                </div>
              </div>
              <div className="modal-footer-custom">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? <span className="spinner-border spinner-border-sm me-1" /> : null}
                  {editId ? 'Save Changes' : 'Add Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ConfirmModal
        show={!!deleteId}
        title="Delete Product"
        message="Are you sure you want to delete this product? This action cannot be undone."
        onConfirm={confirmDelete}
        onCancel={() => setDeleteId(null)}
        loading={deleting}
      />

      {/* Add Supplier Modal */}
      {showSupplierModal && (
        <div className="modal-backdrop-custom" onClick={() => setShowSupplierModal(false)}>
          <div className="modal-dialog-custom" onClick={e => e.stopPropagation()}>
            <div className="modal-header-custom">
              <h5>Add Supplier</h5>
              <button className="btn-close" onClick={() => setShowSupplierModal(false)} />
            </div>
            <form onSubmit={saveSupplier}>
              <div className="modal-body-custom">
                <AlertMessage type="danger" message={supplierError} onClose={() => setSupplierError('')} />
                <div className="row g-3">
                  <div className="col-12">
                    <label className="form-label">Supplier Name *</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      name="name" 
                      value={supplierForm.name} 
                      onChange={handleSupplierField}
                      placeholder="Enter supplier name"
                      required 
                    />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Phone Number</label>
                    <input 
                      type="tel" 
                      className="form-control" 
                      name="phone" 
                      value={supplierForm.phone} 
                      onChange={handleSupplierField}
                      placeholder="+91 98765 43210"
                    />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Email</label>
                    <input 
                      type="email" 
                      className="form-control" 
                      name="email" 
                      value={supplierForm.email} 
                      onChange={handleSupplierField}
                      placeholder="supplier@example.com"
                    />
                  </div>
                  <div className="col-12">
                    <label className="form-label">Address</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      name="address" 
                      value={supplierForm.address} 
                      onChange={handleSupplierField}
                      placeholder="Street address, city, state"
                    />
                  </div>
                </div>
              </div>
              <div className="modal-footer-custom">
                <button type="button" className="btn btn-secondary" onClick={() => setShowSupplierModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={savingSupplier}>
                  {savingSupplier ? <span className="spinner-border spinner-border-sm me-1" /> : null}
                  Save Supplier
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Category Modal */}
      {showCategoryModal && (
        <div className="modal-backdrop-custom" onClick={() => setShowCategoryModal(false)}>
          <div className="modal-dialog-custom" onClick={e => e.stopPropagation()}>
            <div className="modal-header-custom">
              <h5>Add Category</h5>
              <button className="btn-close" onClick={() => setShowCategoryModal(false)} />
            </div>
            <form onSubmit={saveCategory}>
              <div className="modal-body-custom">
                <AlertMessage type="danger" message={categoryError} onClose={() => setCategoryError('')} />
                <div className="row g-3">
                  <div className="col-12">
                    <label className="form-label">Category Name *</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      name="name" 
                      value={categoryForm.name} 
                      onChange={handleCategoryField}
                      placeholder="Enter category name"
                      required 
                    />
                  </div>
                  <div className="col-12">
                    <label className="form-label">Description</label>
                    <textarea 
                      className="form-control" 
                      name="description" 
                      value={categoryForm.description} 
                      onChange={handleCategoryField}
                      placeholder="Optional description"
                      rows="3"
                    />
                  </div>
                </div>
              </div>
              <div className="modal-footer-custom">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCategoryModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={savingCategory}>
                  {savingCategory ? <span className="spinner-border spinner-border-sm me-1" /> : null}
                  Add Category
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Products;
