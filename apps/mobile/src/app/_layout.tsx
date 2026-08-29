import { Stack } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StatusBar } from 'expo-status-bar';
import { Platform } from 'react-native';
import '../global.css';

if (Platform.OS === 'web') {
  const originalConsoleError = console.error;
  console.error = (...args: any[]) => {
    if (typeof args[0] === 'string' && (
      args[0].includes('Unknown event handler property') ||
      args[0].includes('props.pointerEvents is deprecated') ||
      args[0].includes('TouchableMixin is deprecated') ||
      args[0].includes('defaultProps will be removed')
    )) {
      return;
    }
    originalConsoleError(...args);
  };
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 60_000,
      refetchOnWindowFocus: false,
    },
  },
});

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: '#0b0f19' },
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      </Stack>
    </QueryClientProvider>
  );
}
