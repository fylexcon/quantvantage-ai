import React from 'react';
import { View, Text, ActivityIndicator } from 'react-native';
import { useSentimentSummary } from '../../lib/api';

export default function SentimentCard({ ticker }: { ticker: string }) {
  const { data, isPending, error } = useSentimentSummary(ticker);

  if (isPending) {
    return (
      <View className="bg-card rounded-2xl p-6 border border-gray-800 items-center justify-center min-h-[120px]">
        <ActivityIndicator color="#10b981" />
        <Text className="text-gray-400 mt-2">Analyzing sentiment...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View className="bg-card rounded-2xl p-6 border border-red-900 min-h-[120px]">
        <Text className="text-red-400">Failed to load sentiment data.</Text>
      </View>
    );
  }

  const score = data?.average_score ?? 0;
  const dominant = data?.dominant_sentiment ?? 'NEUTRAL';
  
  let labelColor = 'text-gray-400';
  if (dominant === 'BULLISH') labelColor = 'text-emerald-400';
  if (dominant === 'BEARISH') labelColor = 'text-red-400';

  return (
    <View className="bg-card rounded-2xl p-6 border border-gray-800 flex-row justify-between items-center mb-6">
      <View>
        <Text className="text-gray-400 text-sm font-medium mb-1">AI Sentiment</Text>
        <Text className={`text-2xl font-bold ${labelColor}`}>
          {dominant}
        </Text>
      </View>
      <View className="items-end">
        <Text className="text-gray-400 text-sm font-medium mb-1">Score</Text>
        <Text className="text-white text-xl font-bold">{score.toFixed(2)}</Text>
        <Text className="text-gray-500 text-xs mt-1">Based on {data?.article_count ?? 0} sources</Text>
      </View>
    </View>
  );
}
