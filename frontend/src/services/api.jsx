import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

export const searchHcps = (query) => api.get(`/api/hcps`, { params: { q: query } });
export const searchMaterials = (query) => api.get(`/api/materials`, { params: { q: query } });
export const searchSamples = (query) => api.get(`/api/samples`, { params: { q: query } });

export default api;