import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  Dimensions,
} from 'react-native';
import { useApp } from '../context/AppContext';

const { width } = Dimensions.get('window');
const COLS = 3;
const ITEM_SIZE = (width - 40) / COLS;

const TableGridScreen = ({ navigation }) => {
  const { tables, selectTable, loadTables } = useApp();

  const getStatusColor = (status) => {
    switch (status) {
      case 'free':
        return '#4CAF50'; // Vert - libre
      case 'occupied':
        return '#FF9800'; // Orange - occupée
      case 'sent':
        return '#2196F3'; // Bleu - commande envoyée
      default:
        return '#9E9E9E'; // Gris
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'free':
        return 'Libre';
      case 'occupied':
        return 'Occupée';
      case 'sent':
        return 'Envoyée';
      default:
        return status;
    }
  };

  const handleTablePress = (table) => {
    selectTable(table);
    navigation.navigate('Menu', { table });
  };

  const renderTable = ({ item }) => (
    <TouchableOpacity
      style={[
        styles.tableCard,
        { backgroundColor: getStatusColor(item.status) },
      ]}
      onPress={() => handleTablePress(item)}
      activeOpacity={0.7}
    >
      <Text style={styles.tableNumber}>Table {item.table_number}</Text>
      <Text style={styles.tableStatus}>{getStatusText(item.status)}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>🍽️ Restaurant</Text>
        <Text style={styles.headerSubtitle}>Sélectionnez une table</Text>
      </View>

      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#4CAF50' }]} />
          <Text style={styles.legendText}>Libre</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#FF9800' }]} />
          <Text style={styles.legendText}>Occupée</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#2196F3' }]} />
          <Text style={styles.legendText}>Envoyée</Text>
        </View>
      </View>

      <FlatList
        data={tables}
        renderItem={renderTable}
        keyExtractor={(item) => item.id.toString()}
        numColumns={COLS}
        contentContainerStyle={styles.grid}
        columnWrapperStyle={styles.row}
        onRefresh={() => loadTables()}
        refreshing={false}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    padding: 20,
    paddingTop: 40,
    backgroundColor: '#1a237e',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#b3c7f5',
    marginTop: 4,
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 6,
  },
  legendText: {
    fontSize: 12,
    color: '#666',
  },
  grid: {
    padding: 10,
  },
  row: {
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  tableCard: {
    width: ITEM_SIZE - 10,
    height: ITEM_SIZE - 10,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  tableNumber: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
  },
  tableStatus: {
    fontSize: 12,
    color: '#fff',
    opacity: 0.9,
    marginTop: 4,
  },
});

export default TableGridScreen;