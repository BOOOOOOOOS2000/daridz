import React from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';

export const LoadingScreen = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>🍽️</Text>
      <Text style={styles.appName}>Restaurant App</Text>
      <ActivityIndicator size="large" color="#1a237e" style={styles.loader} />
      <Text style={styles.subtitle}>Chargement...</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1a237e',
  },
  title: {
    fontSize: 64,
    marginBottom: 20,
  },
  appName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 30,
  },
  loader: {
    marginBottom: 20,
  },
  subtitle: {
    fontSize: 16,
    color: '#b3c7f5',
  },
});

export default LoadingScreen;