import React from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator } from 'react-native';
import * as WebBrowser from 'expo-web-browser';
import { useSentimentList, type SentimentRead } from '../../lib/api';

interface NewsFeedProps {
  ticker: string;
  limit?: number;
}

function getSentimentBadge(sentiment: string | undefined) {
  if (!sentiment) return { color: 'text-gray-400', bg: 'bg-gray-500/15', dot: 'bg-amber-400' };
  const s = sentiment.toLowerCase();
  if (s === 'bullish') return { color: 'text-emerald-400', bg: 'bg-emerald-500/20', dot: 'bg-emerald-400' };
  if (s === 'bearish') return { color: 'text-red-400', bg: 'bg-red-500/20', dot: 'bg-red-400' };
  return { color: 'text-amber-400', bg: 'bg-amber-500/20', dot: 'bg-amber-400' };
}

function timeAgo(iso: string): string {
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60_000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  } catch {
    return '';
  }
}

export default function NewsFeed({ ticker, limit = 10 }: NewsFeedProps) {
  const { data, isPending, error } = useSentimentList(ticker, limit);

  if (isPending) {
    return (
      <View className="items-center py-8">
        <ActivityIndicator color="#10b981" />
        <Text className="text-gray-400 mt-2 text-sm">Loading news...</Text>
      </View>
    );
  }

  if (error || !data || data.length === 0) {
    return (
      <View className="py-8 items-center">
        <Text className="text-gray-500 text-sm">
          No recent news found for {ticker}.
        </Text>
      </View>
    );
  }

  return (
    <View>
      {data.map((item: SentimentRead, index: number) => {
        const sentiment = item.analysis?.sentiment;
        const summary = item.analysis?.summary;
        const score = item.analysis?.score;
        const badge = getSentimentBadge(sentiment);

        return (
          <View
            key={item.id || index}
            className="bg-card p-4 rounded-xl mb-3 border border-gray-800"
          >
            {/* Sentiment dot + Summary */}
            <View className="flex-row items-start">
              <View className={`w-2 h-2 rounded-full mt-1.5 mr-3 ${badge.dot}`} />
              <View className="flex-1">
                <Text
                  className="text-gray-200 text-sm leading-5 mb-2"
                  numberOfLines={3}
                >
                  {summary || 'No summary available.'}
                </Text>

                {/* Meta row */}
                <View className="flex-row flex-wrap items-center">
                  {/* Sentiment badge */}
                  <View className={`rounded-full px-2 py-0.5 mr-2 ${badge.bg}`}>
                    <Text className={`text-xs font-bold ${badge.color}`}>
                      {sentiment ?? 'Unknown'}
                    </Text>
                  </View>

                  {/* Score */}
                  {typeof score === 'number' && (
                    <Text className="text-gray-500 text-xs mr-3">
                      {score.toFixed(2)}
                    </Text>
                  )}

                  {/* Source */}
                  <Text className="text-gray-600 text-xs mr-3">
                    {item.source}
                  </Text>

                  {/* Time */}
                  <Text className="text-gray-600 text-xs">
                    {timeAgo(item.created_at)}
                  </Text>
                </View>
              </View>
            </View>
          </View>
        );
      })}
    </View>
  );
}
