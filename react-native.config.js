module.exports = {
  dependencies: {
    // Disable autolinking for problematic packages
    'react-native-sqlite-storage': {
      platforms: {
        android: null,
      },
    },
    'react-native-screens': {
      platforms: {
        android: null,
      },
    },
    'react-native-safe-area-context': {
      platforms: {
        android: null,
      },
    },
    '@react-native-async-storage/async-storage': {
      platforms: {
        android: null,
      },
    },
  },
};