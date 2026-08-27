import React from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator } from 'react-native';
import * as WebBrowser from 'expo-web-browser';
import { useSentimentList } from '../../lib/api';
import { ExternalLink } from 'lucide-react-native';

export default function NewsFeed({ ticker }: { ticker: string }) {
  const { data, isPending, error } = useSentimentList(ticker, 5);

  const openUrl = async (url: string) => {
    await WebBrowser.openBrowserAsync(url);
  };

  if (isPending) {
    return (
      <View className="items-center py-8">
        <ActivityIndicator color="#10b981" />
      </View>
    );
  }

  if (error || !data || data.length === 0) {
    return (
      <View className="py-8 items-center">
        <Text className="text-gray-500">No recent news found.</Text>
      </View>
    );
  }

  return (
    <View className="mb-8">
      <Text className="text-white font-semibold mb-4 px-2">Recent News</Text>
      {data.map((item: any, index: number) => {
        let labelColor = 'text-gray-400';
        if (item.sentiment === 'BULLISH') labelColor = 'text-emerald-400';
        if (item.sentiment === 'BEARISH') labelColor = 'text-red-400';

        return (
          <TouchableOpacity
            key={item.id || index}
            onPress={() => openUrl(item.url)}
            className="bg-card p-4 rounded-xl mb-3 border border-gray-800 flex-row items-center"
          >
            <View className="flex-1 mr-3">
              <Text className="text-white font-medium mb-2" numberOfLines={2}>
                {item.headline}
              </Text>
              <View className="flex-row items-center space-x-3">
                <Text className={`text-xs font-bold ${labelColor}`}>
                  {item.sentiment}
                </Text>
                <Text className="text-gray-500 text-xs">Score: {item.score.toFixed(2)}</Text>
              </View>
            </View>
            <ExternalLink size={20} color="#6b7280" />
          </TouchableOpacity>
        );
      })}
    </View>
  );
}
