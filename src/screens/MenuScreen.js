import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  ScrollView,
  TextInput,
  Alert,
} from 'react-native';
import { useApp } from '../context/AppContext';

const MenuScreen = ({ navigation, route }) => {
  const { table } = route.params;
  const {
    categories,
    currentTable,
    cart,
    addToCart,
    updateCartQuantity,
    removeFromCart,
    getCartTotal,
    getItemsByCategory,
    submitOrder,
    clearCart,
  } = useApp();

  const [selectedCategory, setSelectedCategory] = useState(categories[0]?.id);
  const [items, setItems] = useState([]);
  const [notes, setNotes] = useState('');
  const [quantities, setQuantities] = useState({});
  const [showNotes, setShowNotes] = useState(null);

  useEffect(() => {
    if (selectedCategory) {
      loadItems(selectedCategory);
    }
  }, [selectedCategory]);

  const loadItems = async (categoryId) => {
    const itemsData = await getItemsByCategory(categoryId);
    setItems(itemsData);
  };

  const handleAddToCart = (item) => {
    const quantity = quantities[item.id] || 1;
    const itemNotes = notes || '';
    addToCart(item, quantity, itemNotes);
    setQuantities({ ...quantities, [item.id]: 1 });
    setNotes('');
    setShowNotes(null);
  };

  const handleSubmitOrder = async () => {
    if (cart.length === 0) {
      Alert.alert('Panier vide', 'Ajoutez des articles au panier.');
      return;
    }

    const orderId = await submitOrder();
    if (orderId) {
      Alert.alert(
        'Commande validée',
        `Votre commande a été enregistrée avec succès!`,
        [{ text: 'OK', onPress: () => navigation.navigate('Tables') }]
      );
    } else {
      Alert.alert('Erreur', 'Une erreur est survenue lors de la commande.');
    }
  };

  const renderCategory = ({ item }) => (
    <TouchableOpacity
      style={[
        styles.categoryButton,
        selectedCategory === item.id && styles.categoryButtonActive,
      ]}
      onPress={() => setSelectedCategory(item.id)}
    >
      <Text
        style={[
          styles.categoryText,
          selectedCategory === item.id && styles.categoryTextActive,
        ]}
      >
        {item.name}
      </Text>
    </TouchableOpacity>
  );

  const renderNoteInput = (itemId) => (
    <View style={styles.noteInputContainer}>
      <TextInput
        style={styles.noteInput}
        placeholder="Notes (ex: sans oignon...)"
        value={notes}
        onChangeText={setNotes}
        multiline
      />
      <View style={styles.noteButtons}>
        <TouchableOpacity
          style={styles.noteCancelButton}
          onPress={() => {
            setShowNotes(null);
            setNotes('');
          }}
        >
          <Text style={styles.noteCancelText}>Annuler</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.noteConfirmButton}
          onPress={() => handleAddToCart(items.find(i => i.id === itemId))}
        >
          <Text style={styles.noteConfirmText}>Ajouter</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderQuantityControl = (item) => (
    <View style={styles.quantityControl}>
      <TouchableOpacity
        style={styles.quantityButton}
        onPress={() => {
          const currentQty = quantities[item.id] || 1;
          if (currentQty > 1) {
            setQuantities({ ...quantities, [item.id]: currentQty - 1 });
          }
        }}
      >
        <Text style={styles.quantityButtonText}>−</Text>
      </TouchableOpacity>
      <Text style={styles.quantityText}>{quantities[item.id] || 1}</Text>
      <TouchableOpacity
        style={styles.quantityButton}
        onPress={() => {
          const currentQty = quantities[item.id] || 1;
          setQuantities({ ...quantities, [item.id]: currentQty + 1 });
        }}
      >
        <Text style={styles.quantityButtonText}>+</Text>
      </TouchableOpacity>
    </View>
  );

  const renderCartItem = ({ item }) => (
    <View style={styles.cartItem}>
      <View style={styles.cartItemInfo}>
        <Text style={styles.cartItemName}>{item.name}</Text>
        <Text style={styles.cartItemDetails}>
          {item.quantity}x - {item.notes || 'Aucune note'}
        </Text>
      </View>
      <View style={styles.cartItemRight}>
        <Text style={styles.cartItemPrice}>{(item.price * item.quantity).toFixed(2)}€</Text>
        <TouchableOpacity
          onPress={() => removeFromCart(item.id, item.notes)}
          style={styles.removeButton}
        >
          <Text style={styles.removeButtonText}>✕</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Table {table?.table_number}</Text>
        <Text style={styles.headerSubtitle}>Choisissez une catégorie</Text>
      </View>

      <FlatList
        data={categories}
        renderItem={renderCategory}
        keyExtractor={(item) => item.id.toString()}
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.categoriesContainer}
      />

      <ScrollView style={styles.content}>
        <View style={styles.itemsList}>
          {items.map((item) => (
            <View key={item.id} style={styles.itemCard}>
              <View style={styles.itemHeader}>
                <Text style={styles.itemName}>{item.name}</Text>
                <Text style={styles.itemPrice}>{item.price.toFixed(2)}€</Text>
              </View>
              {item.description && (
                <Text style={styles.itemDescription}>{item.description}</Text>
              )}
              <View style={styles.itemFooter}>
                {renderQuantityControl(item)}
                <TouchableOpacity
                  style={styles.addButton}
                  onPress={() => setShowNotes(item.id)}
                >
                  <Text style={styles.addButtonText}>Ajouter</Text>
                </TouchableOpacity>
              </View>
              {showNotes === item.id && renderNoteInput(item.id)}
            </View>
          ))}
        </View>

        {cart.length > 0 && (
          <View style={styles.cartSection}>
            <Text style={styles.cartTitle}>🛒 Panier ({cart.length} articles)</Text>
            {cart.map((item, index) => (
              <View key={`${item.id}-${index}`} style={styles.cartItem}>
                <View style={styles.cartItemInfo}>
                  <Text style={styles.cartItemName}>{item.name}</Text>
                  <Text style={styles.cartItemDetails}>
                    {item.quantity}x{item.notes ? ` - ${item.notes}` : ''}
                  </Text>
                </View>
                <View style={styles.cartItemRight}>
                  <Text style={styles.cartItemPrice}>
                    {(item.price * item.quantity).toFixed(2)}€
                  </Text>
                  <TouchableOpacity
                    onPress={() => removeFromCart(item.id, item.notes)}
                    style={styles.removeButton}
                  >
                    <Text style={styles.removeButtonText}>✕</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))}
            <View style={styles.cartTotal}>
              <Text style={styles.cartTotalText}>Total:</Text>
              <Text style={styles.cartTotalAmount}>{getCartTotal().toFixed(2)}€</Text>
            </View>
            <TouchableOpacity
              style={styles.submitButton}
              onPress={handleSubmitOrder}
            >
              <Text style={styles.submitButtonText}>Valider la commande</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    padding: 15,
    backgroundColor: '#1a237e',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 13,
    color: '#b3c7f5',
    marginTop: 2,
  },
  categoriesContainer: {
    paddingVertical: 10,
    paddingHorizontal: 5,
  },
  categoryButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    marginHorizontal: 5,
    borderRadius: 20,
    backgroundColor: '#e0e0e0',
  },
  categoryButtonActive: {
    backgroundColor: '#1a237e',
  },
  categoryText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  categoryTextActive: {
    color: '#fff',
  },
  content: {
    flex: 1,
  },
  itemsList: {
    padding: 15,
  },
  itemCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  itemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  itemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  itemPrice: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a237e',
  },
  itemDescription: {
    fontSize: 13,
    color: '#666',
    marginTop: 4,
  },
  itemFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 10,
  },
  quantityControl: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  quantityButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#1a237e',
    justifyContent: 'center',
    alignItems: 'center',
  },
  quantityButtonText: {
    fontSize: 20,
    color: '#fff',
    fontWeight: 'bold',
  },
  quantityText: {
    fontSize: 16,
    fontWeight: '600',
    marginHorizontal: 12,
    minWidth: 24,
    textAlign: 'center',
  },
  addButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 8,
  },
  addButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  noteInputContainer: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  noteInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 10,
    fontSize: 14,
    minHeight: 60,
    textAlignVertical: 'top',
  },
  noteButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 8,
  },
  noteCancelButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
  },
  noteCancelText: {
    color: '#666',
    fontSize: 14,
  },
  noteConfirmButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
  },
  noteConfirmText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  cartSection: {
    padding: 15,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    backgroundColor: '#fff',
  },
  cartTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  cartItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  cartItemInfo: {
    flex: 1,
  },
  cartItemName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#333',
  },
  cartItemDetails: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  cartItemRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  cartItemPrice: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a237e',
    marginRight: 10,
  },
  removeButton: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#f44336',
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  cartTotal: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 15,
  },
  cartTotalText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  cartTotalAmount: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a237e',
  },
  submitButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default MenuScreen;