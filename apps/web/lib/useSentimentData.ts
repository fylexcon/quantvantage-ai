import { useState, useEffect } from 'react';
import { supabase } from './supabase';

export interface SentimentRecord {
  id?: string;
  ticker: string;
  score: number;
  sentiment_label: string;
  model_prediction: number;
  created_at: string;
}

export function useSentimentData(ticker: string) {
  const [data, setData] = useState<SentimentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let mounted = true;

    async function fetchData() {
      setLoading(true);
      try {
        const { data: records, error } = await supabase
          .from('sentiment_history')
          .select('*')
          .eq('ticker', ticker)
          .order('created_at', { ascending: true });

        if (error) {
          throw error;
        }

        if (mounted) {
          const mappedRecords = records.map((r: any) => ({
            ...r,
            score: r.score ?? r.analysis?.score ?? 0,
            sentiment_label: r.sentiment_label ?? r.analysis?.sentiment ?? "neutral",
          }));
          setData(mappedRecords as SentimentRecord[]);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err : new Error('Unknown error fetching data'));
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    if (ticker) {
      fetchData();
    }

    return () => {
      mounted = false;
    };
  }, [ticker]);

  return { data, loading, error };
}
