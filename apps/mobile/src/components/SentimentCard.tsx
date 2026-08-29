import React from 'react';
import { View, Text, ActivityIndicator } from 'react-native';
import { useSentimentSummary } from '../../lib/api';

interface SentimentCardProps {
  ticker: string;
}

function getSentimentColor(sentiment: string | null | undefined): string {
  if (!sentiment) return 'text-amber-400';
  const s = sentiment.toLowerCase();
  if (s === 'bullish') return 'text-emerald-400';
  if (s === 'bearish') return 'text-red-400';
  return 'text-amber-400';
}

function getSentimentBg(sentiment: string | null | undefined): string {
  if (!sentiment) return 'bg-amber-500/20 border-amber-500/30';
  const s = sentiment.toLowerCase();
  if (s === 'bullish') return 'bg-emerald-500/20 border-emerald-500/30';
  if (s === 'bearish') return 'bg-red-500/20 border-red-500/30';
  return 'bg-amber-500/20 border-amber-500/30';
}

export default function SentimentCard({ ticker }: SentimentCardProps) {
  const { data, isPending, error } = useSentimentSummary(ticker);

  if (isPending) {
    return (
      <View className="bg-card rounded-2xl p-5 border border-gray-800 mb-4">
        <Text className="text-gray-400 text-xs font-medium mb-3 uppercase tracking-wider">
          24h Sentiment
        </Text>
        <View className="items-center justify-center min-h-[100px]">
          <ActivityIndicator color="#10b981" />
          <Text className="text-gray-400 mt-2 text-sm">
            Analyzing sentiment...
          </Text>
        </View>
      </View>
    );
  }

  if (error) {
    return (
      <View className="bg-card rounded-2xl p-5 border border-red-900/50 mb-4">
        <Text className="text-gray-400 text-xs font-medium mb-3 uppercase tracking-wider">
          24h Sentiment
        </Text>
        <View className="bg-red-500/10 rounded-xl p-3">
          <Text className="text-red-400 text-sm">
            Failed to load sentiment data.
          </Text>
        </View>
      </View>
    );
  }

  if (!data || data.total_articles === 0) {
    return (
      <View className="bg-card rounded-2xl p-5 border border-gray-800 mb-4">
        <Text className="text-gray-400 text-xs font-medium mb-3 uppercase tracking-wider">
          24h Sentiment
        </Text>
        <View className="items-center py-4">
          <Text className="text-gray-500 text-sm">
            No articles processed in the last 24h.
          </Text>
        </View>
      </View>
    );
  }

  const sentiment = data.dominant_sentiment_24h ?? 'Neutral';
  const score = data.avg_score_24h ?? 0;
  const scoreBarWidth = Math.min(100, Math.max(0, (score + 1) * 50));

  return (
    <View className="bg-card rounded-2xl p-5 border border-gray-800 mb-4">
      <Text className="text-gray-400 text-xs font-medium mb-4 uppercase tracking-wider">
        24h Sentiment
      </Text>

      {/* Sentiment Badge */}
      <View className="flex-row items-center mb-4">
        <View
          className={`rounded-full px-4 py-2 border ${getSentimentBg(sentiment)}`}
        >
          <Text className={`font-bold text-sm ${getSentimentColor(sentiment)}`}>
            {sentiment}
          </Text>
        </View>
      </View>

      {/* Metrics Row */}
      <View className="flex-row justify-between">
        {/* Avg Score */}
        <View className="flex-1 mr-4">
          <Text className="text-gray-500 text-xs font-medium uppercase tracking-wider mb-1">
            Avg Score
          </Text>
          <Text className="text-white text-2xl font-bold">
            {score.toFixed(2)}
          </Text>
          {/* Score bar */}
          <View className="h-1.5 w-full rounded-full bg-gray-800 mt-2 overflow-hidden">
            <View
              className="h-full rounded-full bg-emerald-500"
              style={{ width: `${scoreBarWidth}%` }}
            />
          </View>
        </View>

        {/* Articles */}
        <View className="items-end">
          <Text className="text-gray-500 text-xs font-medium uppercase tracking-wider mb-1">
            Articles
          </Text>
          <Text className="text-white text-2xl font-bold">
            {data.total_articles}
          </Text>
          <Text className="text-gray-600 text-xs mt-1">processed (24h)</Text>
        </View>
      </View>
    </View>
  );
}
