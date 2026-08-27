import React from 'react';
import { ScrollView, TouchableOpacity, Text, View } from 'react-native';

const TICKERS = ['AAPL', 'IONQ', 'BTC-USD', 'ETH-USD', 'SOL-USD'];

export default function TickerSelector({ 
  selected, 
  onSelect 
}: { 
  selected: string, 
  onSelect: (t: string) => void 
}) {
  return (
    <View className="mb-4">
      <ScrollView horizontal showsHorizontalScrollIndicator={false} className="flex-row">
        {TICKERS.map((ticker) => {
          const isActive = ticker === selected;
          return (
            <TouchableOpacity
              key={ticker}
              onPress={() => onSelect(ticker)}
              className={`px-4 py-2 mr-3 rounded-full border ${
                isActive 
                  ? 'bg-emerald-500/20 border-emerald-500/50' 
                  : 'bg-card border-gray-800'
              }`}
            >
              <Text className={`font-semibold ${isActive ? 'text-emerald-400' : 'text-gray-400'}`}>
                {ticker}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
}
