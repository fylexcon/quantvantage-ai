import React, { useState, useCallback } from 'react';
import { ScrollView, RefreshControl, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQueryClient } from '@tanstack/react-query';
import TickerSelector from '../../components/TickerSelector';
import SentimentCard from '../../components/SentimentCard';
import SentimentScoreChart from '../../components/SentimentScoreChart';
import PredictionChart from '../../components/PredictionChart';

export default function Dashboard() {
  const [selectedTicker, setSelectedTicker] = useState('AAPL');
  const [refreshing, setRefreshing] = useState(false);
  const queryClient = useQueryClient();

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await queryClient.invalidateQueries({
      queryKey: ['sentiment-summary', selectedTicker],
    });
    await queryClient.invalidateQueries({
      queryKey: ['prediction', selectedTicker],
    });
    setRefreshing(false);
  }, [selectedTicker, queryClient]);

  return (
    <SafeAreaView className="flex-1 bg-background" edges={['top']}>
      {/* Header */}
      <View className="px-4 pt-3 pb-2">
        <Text className="text-white text-2xl font-bold">QuantVantage</Text>
        <Text className="text-emerald-400 text-xs font-medium tracking-widest mt-0.5">
          AI MARKET INTELLIGENCE
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

        {/* Sentiment Summary Card */}
        <SentimentCard ticker={selectedTicker} />

        {/* Sentiment Score Chart (Supabase real-time) */}
        <SentimentScoreChart ticker={selectedTicker} />

        {/* Price Forecast Chart (API) */}
        <PredictionChart ticker={selectedTicker} daysAhead={14} />

        {/* Bottom spacer for tab bar */}
        <View className="h-4" />
      </ScrollView>
    </SafeAreaView>
  );
}
