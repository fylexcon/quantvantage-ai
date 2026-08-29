import React from 'react';
import { View, Text, ActivityIndicator, ScrollView } from 'react-native';
import { LineChart } from 'react-native-gifted-charts';
import { usePredict } from '../../lib/api';

interface PredictionChartProps {
  ticker: string;
  daysAhead?: number;
}

export default function PredictionChart({
  ticker,
  daysAhead = 14,
}: PredictionChartProps) {
  const { data, isPending, error } = usePredict(ticker, daysAhead);

  if (isPending) {
    return (
      <View className="bg-card rounded-2xl p-4 border border-gray-800 mb-4">
        <Text className="text-white font-semibold mb-4 px-2">
          {daysAhead}-Day Price Forecast
        </Text>
        <View className="items-center justify-center min-h-[220px]">
          <ActivityIndicator color="#06b6d4" size="large" />
          <Text className="text-gray-400 mt-3 text-sm">
            Running forecast model...
          </Text>
          <Text className="text-amber-400/60 text-xs mt-2">
            May take up to 60s on first load
          </Text>
        </View>
      </View>
    );
  }

  if (error || !data?.forecasted_prices) {
    return (
      <View className="bg-card rounded-2xl p-4 border border-gray-800 mb-4">
        <Text className="text-white font-semibold mb-4 px-2">
          {daysAhead}-Day Price Forecast
        </Text>
        <View className="items-center justify-center min-h-[220px]">
          <Text className="text-gray-500 text-sm">
            Forecast not available for {ticker}.
          </Text>
          <Text className="text-gray-600 text-xs mt-1">
            The model may not be trained for this asset.
          </Text>
        </View>
      </View>
    );
  }

  const chartData = data.forecasted_prices.map((price, i) => ({
    value: price,
    label: `+${i + 1}d`,
    dataPointText: `$${price.toFixed(0)}`,
  }));

  const currentPrice = data.current_price;
  const lastPrice = data.forecasted_prices[data.forecasted_prices.length - 1];
  const priceChange = lastPrice - currentPrice;
  const priceChangePercent = ((priceChange / currentPrice) * 100).toFixed(1);
  const isUp = priceChange >= 0;

  return (
    <View className="bg-card rounded-2xl p-4 border border-gray-800 mb-4">
      {/* Header */}
      <View className="flex-row justify-between items-center mb-4 px-2">
        <Text className="text-white font-semibold">
          {daysAhead}-Day Price Forecast
        </Text>
        <View className="flex-row items-center">
          <View className="bg-emerald-500/10 rounded-lg px-2 py-1 mr-2">
            <Text className="text-emerald-400 text-xs font-medium">
              ${currentPrice.toFixed(2)}
            </Text>
          </View>
          <Text className="text-gray-500 text-xs">{data.model_version}</Text>
        </View>
      </View>

      {/* Chart */}
      <View className="overflow-hidden">
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <LineChart
            data={chartData}
            color={isUp ? '#10b981' : '#ef4444'}
            thickness={3}
            hideDataPoints={false}
            dataPointsColor={isUp ? '#10b981' : '#ef4444'}
            dataPointsRadius={3}
            yAxisTextStyle={{ color: '#9ca3af', fontSize: 10 }}
            xAxisLabelTextStyle={{ color: '#9ca3af', fontSize: 9 }}
            yAxisLabelPrefix="$"
            width={Math.max(300, chartData.length * 45)}
            height={180}
            areaChart
            startFillColor={isUp ? '#10b981' : '#ef4444'}
            startOpacity={0.15}
            endFillColor={isUp ? '#10b981' : '#ef4444'}
            endOpacity={0}
            rulesColor="#1f2937"
            rulesType="solid"
            initialSpacing={15}
            endSpacing={15}
            yAxisColor="transparent"
            xAxisColor="#1f2937"
            pointerConfig={{
              pointerStripHeight: 160,
              pointerStripColor: '#10b981',
              pointerStripWidth: 1,
              pointerColor: '#10b981',
              radius: 5,
              pointerLabelWidth: 110,
              pointerLabelHeight: 70,
              activatePointersOnLongPress: false,
              autoAdjustPointerLabelPosition: true,
              pointerLabelComponent: (items: any) => {
                return (
                  <View className="bg-gray-800 rounded-lg p-2 justify-center -ml-12">
                    <Text className="text-gray-300 text-center text-xs">
                      {items[0].label}
                    </Text>
                    <Text className="text-white font-bold text-center mt-1">
                      ${items[0].value.toFixed(2)}
                    </Text>
                  </View>
                );
              },
            }}
          />
        </ScrollView>
      </View>

      {/* Summary Footer */}
      <View className="flex-row justify-between items-center mt-3 px-2">
        <View className="flex-row items-center">
          <Text className="text-gray-500 text-xs">Projected: </Text>
          <Text className={`font-bold text-sm ${isUp ? 'text-emerald-400' : 'text-red-400'}`}>
            ${lastPrice.toFixed(2)}
          </Text>
        </View>
        <View
          className={`rounded-full px-2 py-1 ${
            isUp ? 'bg-emerald-500/10' : 'bg-red-500/10'
          }`}
        >
          <Text
            className={`text-xs font-bold ${
              isUp ? 'text-emerald-400' : 'text-red-400'
            }`}
          >
            {isUp ? '+' : ''}
            {priceChangePercent}%
          </Text>
        </View>
      </View>
    </View>
  );
}
