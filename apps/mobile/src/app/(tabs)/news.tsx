import React, { useState, useCallback } from 'react';
import { ScrollView, RefreshControl, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQueryClient } from '@tanstack/react-query';
import TickerSelector from '../../components/TickerSelector';
import NewsFeed from '../../components/NewsFeed';

export default function NewsScreen() {
  const [selectedTicker, setSelectedTicker] = useState('AAPL');
  const [refreshing, setRefreshing] = useState(false);
  const queryClient = useQueryClient();

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await queryClient.invalidateQueries({
      queryKey: ['sentiment-list', selectedTicker],
    });
    setRefreshing(false);
  }, [selectedTicker, queryClient]);

  return (
    <SafeAreaView className="flex-1 bg-background" edges={['top']}>
      {/* Header */}
      <View className="px-4 pt-3 pb-2">
        <Text className="text-white text-2xl font-bold">News Feed</Text>
        <Text className="text-gray-400 text-xs font-medium mt-0.5">
          AI-Analyzed Sentiment Headlines
        </Text>
      </View>

      <ScrollView
        className="flex-1 px-4"
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#10b981"
            colors={['#10b981']}
          />
        }
      >
        {/* Ticker Selector */}
        <TickerSelector selected={selectedTicker} onSelect={setSelectedTicker} />

        {/* News Feed — more items on dedicated screen */}
        <NewsFeed ticker={selectedTicker} limit={15} />

        {/* Bottom spacer for tab bar */}
        <View className="h-4" />
      </ScrollView>
    </SafeAreaView>
  );
}
