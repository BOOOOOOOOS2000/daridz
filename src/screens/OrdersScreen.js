import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  ScrollView,
  Alert,
  Modal,
} from 'react-native';
import { useApp } from '../context/AppContext';

const OrdersScreen = () => {
  const {
    activeOrders,
    loadActiveOrders,
    getOrderItems,
    updateOrderStatus,
  } = useApp();

  const [selectedOrder, setSelectedOrder] = useState(null);
  const [orderItems, setOrderItems] = useState([]);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    loadActiveOrders();
  }, []);

  const handleOrderPress = async (order) => {
    const items = await getOrderItems(order.id);
    setOrderItems(items);
    setSelectedOrder(order);
    setShowModal(true);
  };

  const handleStatusUpdate = async (orderId, newStatus) => {
    await updateOrderStatus(orderId, newStatus);
    setShowModal(false);
    loadActiveOrders();

    const statusMessages = {
      preparing: 'Commande envoyée en cuisine',
      ready: 'Commande prête à servir',
      served: 'Commande servie - Table libérée',
    };

    Alert.alert('Statut mis à jour', statusMessages[newStatus] || '');
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return '#FF9800';
      case 'preparing':
        return '#2196F3';
      case 'ready':
        return '#4CAF50';
      default:
        return '#9E9E9E';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending':
        return 'En attente';
      case 'preparing':
        return 'En préparation';
      case 'ready':
        return 'Prête';
      default:
        return status;
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  };

  const renderOrder = ({ item }) => (
    <TouchableOpacity
      style={[styles.orderCard, { borderLeftColor: getStatusColor(item.status) }]}
      onPress={() => handleOrderPress(item)}
      activeOpacity={0.7}
    >
      <View style={styles.orderHeader}>
        <Text style={styles.orderTable}>Table {item.table_number}</Text>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(item.status) }]}>
          <Text style={styles.statusText}>{getStatusText(item.status)}</Text>
        </View>
      </View>
      <Text style={styles.orderTime}>{formatDate(item.created_at)}</Text>
      <Text style={styles.orderTotal}>{item.total.toFixed(2)}€</Text>
    </TouchableOpacity>
  );

  const renderOrderItem = ({ item }) => (
    <View style={styles.orderItemCard}>
      <View style={styles.orderItemHeader}>
        <Text style={styles.orderItemName}>{item.name}</Text>
        <Text style={styles.orderItemQty}>{item.quantity}x</Text>
      </View>
      {item.notes && (
        <Text style={styles.orderItemNotes}>📝 {item.notes}</Text>
      )}
      <Text style={styles.orderItemPrice}>{(item.price * item.quantity).toFixed(2)}€</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>📋 Commandes</Text>
        <Text style={styles.headerSubtitle}>
          {activeOrders.length} commande{activeOrders.length !== 1 ? 's' : ''} en cours
        </Text>
      </View>

      {activeOrders.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>🍽️</Text>
          <Text style={styles.emptyText}>Aucune commande en cours</Text>
        </View>
      ) : (
        <FlatList
          data={activeOrders}
          renderItem={renderOrder}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.list}
          onRefresh={loadActiveOrders}
          refreshing={false}
        />
      )}

      <Modal
        visible={showModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <View>
                <Text style={styles.modalTitle}>Table {selectedOrder?.table_number}</Text>
                <Text style={styles.modalSubtitle}>
                  {formatDate(selectedOrder?.created_at)} - {selectedOrder?.total.toFixed(2)}€
                </Text>
              </View>
              <TouchableOpacity onPress={() => setShowModal(false)}>
                <Text style={styles.closeButton}>✕</Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              {orderItems.map((item, index) => (
                <View key={index} style={styles.orderItemCard}>
                  <View style={styles.orderItemHeader}>
                    <Text style={styles.orderItemName}>{item.name}</Text>
                    <Text style={styles.orderItemQty}>{item.quantity}x</Text>
                  </View>
                  {item.notes ? (
                    <Text style={styles.orderItemNotes}>📝 {item.notes}</Text>
                  ) : null}
                  <Text style={styles.orderItemPrice}>{(item.price * item.quantity).toFixed(2)}€</Text>
                </View>
              ))}
            </ScrollView>

            <View style={styles.modalActions}>
              {selectedOrder?.status === 'pending' && (
                <TouchableOpacity
                  style={[styles.actionButton, { backgroundColor: '#2196F3' }]}
                  onPress={() => handleStatusUpdate(selectedOrder.id, 'preparing')}
                >
                  <Text style={styles.actionButtonText}>Envoyer en cuisine</Text>
                </TouchableOpacity>
              )}
              {selectedOrder?.status === 'preparing' && (
                <TouchableOpacity
                  style={[styles.actionButton, { backgroundColor: '#4CAF50' }]}
                  onPress={() => handleStatusUpdate(selectedOrder.id, 'ready')}
                >
                  <Text style={styles.actionButtonText}>Marquer comme prête</Text>
                </TouchableOpacity>
              )}
              {selectedOrder?.status === 'ready' && (
                <TouchableOpacity
                  style={[styles.actionButton, { backgroundColor: '#FF9800' }]}
                  onPress={() => handleStatusUpdate(selectedOrder.id, 'served')}
                >
                  <Text style={styles.actionButtonText}>Servir et libérer la table</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        </View>
      </Modal>
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
  list: {
    padding: 15,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
  },
  orderCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
    borderLeftWidth: 4,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  orderTable: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  orderTime: {
    fontSize: 13,
    color: '#666',
  },
  orderTotal: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a237e',
    marginTop: 8,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  modalSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  closeButton: {
    fontSize: 24,
    color: '#666',
    padding: 8,
  },
  modalBody: {
    padding: 20,
  },
  orderItemCard: {
    backgroundColor: '#f9f9f9',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  orderItemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  orderItemName: {
    fontSize: 15,
    fontWeight: '500',
    color: '#333',
    flex: 1,
  },
  orderItemQty: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1a237e',
  },
  orderItemNotes: {
    fontSize: 13,
    color: '#666',
    fontStyle: 'italic',
    marginTop: 4,
  },
  orderItemPrice: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4CAF50',
    marginTop: 4,
  },
  modalActions: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  actionButton: {
    paddingVertical: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default OrdersScreen;