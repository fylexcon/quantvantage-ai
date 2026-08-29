import React from 'react';
import { ScrollView, TouchableOpacity, Text, View } from 'react-native';

const TICKERS = ['AAPL', 'IONQ', 'BTC-USD', 'ETH-USD', 'SOL-USD'];

interface TickerSelectorProps {
  selected: string;
  onSelect: (ticker: string) => void;
}

export default function TickerSelector({
  selected,
  onSelect,
}: TickerSelectorProps) {
  return (
    <View className="mb-4">
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        className="flex-row"
        contentContainerStyle={{ paddingHorizontal: 2 }}
      >
        {TICKERS.map((ticker) => {
          const isActive = ticker === selected;
          return (
            <TouchableOpacity
              key={ticker}
              onPress={() => onSelect(ticker)}
              activeOpacity={0.7}
              className={`px-4 py-2.5 mr-2 rounded-xl border ${
                isActive
                  ? 'bg-emerald-500/15 border-emerald-500/40'
                  : 'bg-white/[0.03] border-gray-800'
              }`}
            >
              <Text
                className={`font-semibold text-sm ${
                  isActive ? 'text-emerald-400' : 'text-gray-400'
                }`}
              >
                {ticker}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
}
