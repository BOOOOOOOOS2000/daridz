import React from 'react';
import { StatusBar } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AppProvider } from './src/context/AppContext';
import AppNavigator from './src/navigation/AppNavigator';
import { LoadingScreen } from './src/components/LoadingScreen';

const App = () => {
  return (
    <SafeAreaProvider>
      <AppProvider>
        <StatusBar barStyle="light-content" backgroundColor="#1a237e" />
        <AppNavigator />
      </AppProvider>
    </SafeAreaProvider>
  );
};

export default App;