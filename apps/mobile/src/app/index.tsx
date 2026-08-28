import React, { useState, useCallback, useEffect } from 'react';
import { ScrollView, RefreshControl, Text, View, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LineChart } from 'react-native-gifted-charts';
import { supabase } from '../../lib/supabase';
import TickerSelector from '../components/TickerSelector';

export default function Dashboard() {
  const [selectedTicker, setSelectedTicker] = useState('AAPL');
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [records, setRecords] = useState<any[]>([]);

  const fetchSentimentData = useCallback(async (ticker: string) => {
    try {
      const { data, error } = await supabase
        .from('sentiment_history')
        .select('*')
        .eq('ticker', ticker)
        .order('created_at', { ascending: true });

      if (error) {
        console.error('Error fetching sentiment data:', error);
      } else {
        setRecords(data || []);
      }
    } catch (err) {
      console.error('Supabase fetch error:', err);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchSentimentData(selectedTicker).finally(() => setLoading(false));
  }, [selectedTicker, fetchSentimentData]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchSentimentData(selectedTicker);
    setRefreshing(false);
  }, [selectedTicker, fetchSentimentData]);

  const chartData = records.map((item) => ({
    value: item.score,
    label: new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    dataPointText: item.score.toFixed(2),
  }));

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
        
        <View className="bg-card rounded-2xl p-4 border border-gray-800 mb-6 mt-4">
          <Text className="text-white font-semibold mb-4 px-2">Sentiment Score (Live)</Text>
          
          {loading ? (
            <View className="items-center justify-center min-h-[250px]">
              <ActivityIndicator color="#06b6d4" size="large" />
              <Text className="text-gray-400 mt-4">Loading sentiment data...</Text>
            </View>
          ) : records.length === 0 ? (
            <View className="items-center justify-center min-h-[250px]">
              <Text className="text-gray-500">No sentiment data available.</Text>
            </View>
          ) : (
            <View className="overflow-hidden">
              <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                <LineChart
                  data={chartData}
                  color="#06b6d4"
                  thickness={3}
                  hideDataPoints={false}
                  dataPointsColor="#06b6d4"
                  yAxisTextStyle={{ color: '#9ca3af' }}
                  xAxisLabelTextStyle={{ color: '#9ca3af', fontSize: 10 }}
                  width={Math.max(300, chartData.length * 60)}
                  height={180}
                  areaChart
                  startFillColor="#06b6d4"
                  startOpacity={0.2}
                  endFillColor="#06b6d4"
                  endOpacity={0}
                  rulesColor="#1f2937"
                  rulesType="solid"
                  initialSpacing={20}
                  yAxisColor="transparent"
                  xAxisColor="#1f2937"
                  pointerConfig={{
                    pointerStripHeight: 160,
                    pointerStripColor: '#10b981',
                    pointerStripWidth: 2,
                    pointerColor: '#10b981',
                    radius: 6,
                    pointerLabelWidth: 100,
                    pointerLabelHeight: 90,
                    activatePointersOnLongPress: false,
                    autoAdjustPointerLabelPosition: true,
                    pointerLabelComponent: (items: any) => {
                      return (
                        <View className="bg-gray-800 rounded-lg p-2 justify-center -ml-10">
                          <Text className="text-white font-bold text-center text-xs">
                            {items[0].label}
                          </Text>
                          <Text className="text-cyan-400 font-bold text-center mt-1">
                            {items[0].value.toFixed(2)}
                          </Text>
                        </View>
                      );
                    },
                  }}
                />
              </ScrollView>
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
