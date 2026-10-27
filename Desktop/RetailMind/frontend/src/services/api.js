import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('rm_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle 401 globally
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('rm_token');
      localStorage.removeItem('rm_user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default api;

// ─── Auth ──────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data) => api.post('/auth/register', data),
  verifyOtp: (data) => api.post('/auth/verify-otp', data),
  resendOtp: (data) => api.post('/auth/resend-otp', data),
  login: (data) => api.post('/auth/login', data),
  forgotPassword: (data) => api.post('/auth/forgot-password', data),
  verifyResetOtp: (data) => api.post('/auth/verify-reset-otp', data),
  resetPassword: (data) => api.post('/auth/reset-password', data),
  me: () => api.get('/auth/me'),
};

// ─── Products ──────────────────────────────────────────────────────────────
export const productsApi = {
  list: (params) => api.get('/products/', { params }),
  get: (id) => api.get(`/products/${id}`),
  create: (data) => api.post('/products/', data),
  update: (id, data) => api.put(`/products/${id}`, data),
  delete: (id) => api.delete(`/products/${id}`),
};

// ─── Categories ────────────────────────────────────────────────────────────
export const categoriesApi = {
  list: (params) => api.get('/categories/', { params }),
  create: (data) => api.post('/categories/', data),
  update: (id, data) => api.put(`/categories/${id}`, data),
  delete: (id) => api.delete(`/categories/${id}`),
};

// ─── Customers ─────────────────────────────────────────────────────────────
export const customersApi = {
  list: (params) => api.get('/customers/', { params }),
  get: (id) => api.get(`/customers/${id}`),
  create: (data) => api.post('/customers/', data),
  update: (id, data) => api.put(`/customers/${id}`, data),
  delete: (id) => api.delete(`/customers/${id}`),
};

// ─── Suppliers ─────────────────────────────────────────────────────────────
export const suppliersApi = {
  list: (params) => api.get('/suppliers/', { params }),
  get: (id) => api.get(`/suppliers/${id}`),
  create: (data) => api.post('/suppliers/', data),
  update: (id, data) => api.put(`/suppliers/${id}`, data),
  delete: (id) => api.delete(`/suppliers/${id}`),
};

// ─── Sales ─────────────────────────────────────────────────────────────────
export const salesApi = {
  list: (params) => api.get('/sales/', { params }),
  get: (id) => api.get(`/sales/${id}`),
  getNextNumber: () => api.get('/sales/next-number'),
  create: (data) => api.post('/sales/', data),
};

// ─── Purchases ─────────────────────────────────────────────────────────────
export const purchasesApi = {
  list: (params) => api.get('/purchases/', { params }),
  get: (id) => api.get(`/purchases/${id}`),
  getNextNumber: () => api.get('/purchases/next-number'),
  create: (data) => api.post('/purchases/', data),
};

// ─── Inventory ─────────────────────────────────────────────────────────────
export const inventoryApi = {
  list: (params) => api.get('/inventory/', { params }),
  summary: () => api.get('/inventory/summary'),
  transactions: (params) => api.get('/inventory/transactions', { params }),
};

// ─── Dashboard ─────────────────────────────────────────────────────────────
export const dashboardApi = {
  get: () => api.get('/dashboard/'),
};

// ─── Analytics ─────────────────────────────────────────────────────────────
export const analyticsApi = {
  sales: (params) => api.get('/analytics/sales', { params }),
  trend: (params) => api.get('/analytics/trend', { params }),
  topProducts: (params) => api.get('/analytics/products/top', { params }),
  categories: () => api.get('/analytics/products/categories'),
  customers: () => api.get('/analytics/customers'),
  customerSegments: () => api.get('/analytics/customer-segments'),
  inventory: () => api.get('/analytics/inventory'),
};

// ─── Reports ───────────────────────────────────────────────────────────────
export const reportsApi = {
  sales: (params) => api.get('/reports/sales', { params }),
  purchases: (params) => api.get('/reports/purchases', { params }),
  inventory: (params) => api.get('/reports/inventory', { params }),
  productPerformance: (params) => api.get('/reports/product-performance', { params }),
};

// ─── ML ────────────────────────────────────────────────────────────────────
export const mlApi = {
  modelInfo: () => api.get('/ml/model-info'),
  predictDemand: (data) => api.post('/ml/predict-demand', data),
  restockRecommendation: (data) => api.post('/ml/restock-recommendation', data),
  stockIntelligence: () => api.get('/ml/stock-intelligence'),
};
