import axios from 'axios';
import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = 'https://quantvantage-ai.onrender.com';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 75000, // 75s for Render cold starts
});

export const useSentimentSummary = (ticker: string) => {
  return useQuery({
    queryKey: ['sentiment-summary', ticker],
    queryFn: async () => {
      const response = await apiClient.get(`/api/sentiment/${ticker}/summary`);
      return response.data;
    },
  });
};

export const useSentimentList = (ticker: string, limit: number = 5) => {
  return useQuery({
    queryKey: ['sentiment-list', ticker, limit],
    queryFn: async () => {
      const response = await apiClient.get(`/api/sentiment/${ticker}?limit=${limit}`);
      return response.data;
    },
  });
};

export const usePredict = (ticker: string) => {
  return useQuery({
    queryKey: ['prediction', ticker],
    queryFn: async () => {
      const response = await apiClient.post(`/api/predict/${ticker}`);
      return response.data;
    },
  });
};
