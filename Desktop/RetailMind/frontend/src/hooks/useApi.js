import { useState, useCallback } from 'react';

/**
 * Generic hook for API calls with loading/error state.
 * Usage: const { data, loading, error, execute } = useApi(apiFn);
 */
export const useApi = (apiFn, initialData = null) => {
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(async (...args) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFn(...args);
      setData(res.data);
      return res.data;
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Something went wrong';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiFn]);

  return { data, loading, error, execute, setData };
};

export default useApi;
