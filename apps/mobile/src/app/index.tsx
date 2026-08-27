import React, { useState, useCallback } from 'react';
import { ScrollView, RefreshControl, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQueryClient } from '@tanstack/react-query';

import TickerSelector from '../components/TickerSelector';
import SentimentCard from '../components/SentimentCard';
import PredictionChart from '../components/PredictionChart';
import NewsFeed from '../components/NewsFeed';

export default function Dashboard() {
  const [selectedTicker, setSelectedTicker] = useState('AAPL');
  const [refreshing, setRefreshing] = useState(false);
  const queryClient = useQueryClient();

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await queryClient.invalidateQueries({ queryKey: ['sentiment-summary', selectedTicker] });
    await queryClient.invalidateQueries({ queryKey: ['sentiment-list', selectedTicker] });
    await queryClient.invalidateQueries({ queryKey: ['prediction', selectedTicker] });
    setRefreshing(false);
  }, [queryClient, selectedTicker]);

  return (
    <SafeAreaView className="flex-1 bg-background">
      <View className="px-4 py-3">
        <Text className="text-white text-3xl font-bold">QuantVantage</Text>
        <Text className="text-emerald-400 text-sm font-medium tracking-widest">AI MARKET INTELLIGENCE</Text>
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
        <TickerSelector selected={selectedTicker} onSelect={setSelectedTicker} />
        <SentimentCard ticker={selectedTicker} />
        <PredictionChart ticker={selectedTicker} />
        <NewsFeed ticker={selectedTicker} />
      </ScrollView>
    </SafeAreaView>
  );
}
