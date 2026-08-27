import React from 'react';
import { View, Text, ActivityIndicator } from 'react-native';
import { LineChart } from 'react-native-gifted-charts';
import { usePredict } from '../../lib/api';

export default function PredictionChart({ ticker }: { ticker: string }) {
  const { data, isPending, error } = usePredict(ticker);

  if (isPending) {
    return (
      <View className="bg-card rounded-2xl p-6 border border-gray-800 items-center justify-center min-h-[250px] mb-6">
        <ActivityIndicator color="#06b6d4" />
        <Text className="text-gray-400 mt-2">Generating forecast...</Text>
      </View>
    );
  }

  if (error || !data?.forecast) {
    return (
      <View className="bg-card rounded-2xl p-6 border border-gray-800 items-center justify-center min-h-[250px] mb-6">
        <Text className="text-gray-500">Forecast not available.</Text>
      </View>
    );
  }

  const chartData = data.forecast.map((item: any) => ({
    value: item.predicted_price,
    date: item.date,
  }));

  return (
    <View className="bg-card rounded-2xl p-4 border border-gray-800 mb-6">
      <Text className="text-white font-semibold mb-4 px-2">14-Day Trajectory</Text>
      <View className="overflow-hidden">
        <LineChart
          data={chartData}
          color="#06b6d4"
          thickness={3}
          hideDataPoints
          yAxisTextStyle={{ color: '#9ca3af' }}
          xAxisLabelTextStyle={{ color: '#9ca3af', fontSize: 10 }}
          yAxisLabelPrefix="$"
          width={300}
          height={180}
          areaChart
          startFillColor="#06b6d4"
          startOpacity={0.2}
          endFillColor="#06b6d4"
          endOpacity={0}
          rulesColor="#1f2937"
          rulesType="solid"
          initialSpacing={10}
          yAxisColor="transparent"
          xAxisColor="#1f2937"
        />
      </View>
    </View>
  );
}
