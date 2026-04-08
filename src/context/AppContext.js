import React, { createContext, useState, useContext, useEffect } from 'react';
import { getDBConnection, createTables, insertInitialData } from '../database/database';

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const [db, setDb] = useState(null);
  const [tables, setTables] = useState([]);
  const [categories, setCategories] = useState([]);
  const [currentTable, setCurrentTable] = useState(null);
  const [cart, setCart] = useState([]);
  const [activeOrders, setActiveOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  // Initialiser la base de données
  useEffect(() => {
    const initDB = async () => {
      try {
        const connection = await getDBConnection();
        await createTables(connection);
        await insertInitialData(connection);
        setDb(connection);
        await loadTables(connection);
        await loadCategories(connection);
        await loadActiveOrders(connection);
      } catch (error) {
        console.error('Error initializing database:', error);
      } finally {
        setLoading(false);
      }
    };
    initDB();
  }, []);

  // Charger les tables
  const loadTables = async (dbConnection = db) => {
    if (!dbConnection) return;
    try {
      const [results] = await dbConnection.executeSql(
        'SELECT * FROM tables ORDER BY table_number'
      );
      const tablesData = [];
      for (let i = 0; i < results.rows.length; i++) {
        tablesData.push(results.rows.item(i));
      }
      setTables(tablesData);
    } catch (error) {
      console.error('Error loading tables:', error);
    }
  };

  // Charger les catégories
  const loadCategories = async (dbConnection = db) => {
    if (!dbConnection) return;
    try {
      const [results] = await dbConnection.executeSql(
        'SELECT * FROM categories ORDER BY display_order'
      );
      const categoriesData = [];
      for (let i = 0; i < results.rows.length; i++) {
        categoriesData.push(results.rows.item(i));
      }
      setCategories(categoriesData);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  // Charger les articles d'une catégorie
  const getItemsByCategory = async (categoryId) => {
    if (!db) return [];
    try {
      const [results] = await db.executeSql(
        'SELECT * FROM items WHERE category_id = ? ORDER BY name',
        [categoryId]
      );
      const itemsData = [];
      for (let i = 0; i < results.rows.length; i++) {
        itemsData.push(results.rows.item(i));
      }
      return itemsData;
    } catch (error) {
      console.error('Error loading items:', error);
      return [];
    }
  };

  // Sélectionner une table
  const selectTable = (table) => {
    setCurrentTable(table);
    setCart([]);
  };

  // Ajouter au panier
  const addToCart = (item, quantity = 1, notes = '') => {
    setCart(prevCart => {
      const existingIndex = prevCart.findIndex(i => i.id === item.id && i.notes === notes);
      if (existingIndex >= 0) {
        const newCart = [...prevCart];
        newCart[existingIndex].quantity += quantity;
        return newCart;
      }
      return [...prevCart, { ...item, quantity, notes }];
    });
  };

  // Modifier la quantité dans le panier
  const updateCartQuantity = (itemId, notes, quantity) => {
    if (quantity <= 0) {
      removeFromCart(itemId, notes);
      return;
    }
    setCart(prevCart =>
      prevCart.map(item =>
        item.id === itemId && item.notes === notes
          ? { ...item, quantity }
          : item
      )
    );
  };

  // Supprimer du panier
  const removeFromCart = (itemId, notes) => {
    setCart(prevCart =>
      prevCart.filter(item => !(item.id === itemId && item.notes === notes))
    );
  };

  // Vider le panier
  const clearCart = () => {
    setCart([]);
  };

  // Calculer le total du panier
  const getCartTotal = () => {
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
  };

  // Valider la commande
  const submitOrder = async () => {
    if (!db || !currentTable || cart.length === 0) return null;

    try {
      const total = getCartTotal();

      // Vérifier s'il y a une commande en cours pour cette table
      const [existingOrders] = await db.executeSql(
        'SELECT * FROM orders WHERE table_id = ? AND status IN (?, ?)',
        [currentTable.id, 'pending', 'preparing']
      );

      let orderId;
      if (existingOrders.rows.length > 0) {
        orderId = existingOrders.rows.item(0).id;
        // Mettre à jour le total
        await db.executeSql(
          'UPDATE orders SET total = total + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
          [total, orderId]
        );
      } else {
        // Créer une nouvelle commande
        await db.executeSql(
          'INSERT INTO orders (table_id, status, total) VALUES (?, ?, ?)',
          [currentTable.id, 'pending', total]
        );
        const [result] = await db.executeSql('SELECT last_insert_rowid() as id');
        orderId = result.rows.item(0).id;
      }

      // Ajouter les articles de la commande
      for (const cartItem of cart) {
        await db.executeSql(
          'INSERT INTO order_items (order_id, item_id, quantity, notes, price) VALUES (?, ?, ?, ?, ?)',
          [orderId, cartItem.id, cartItem.quantity, cartItem.notes, cartItem.price]
        );
      }

      // Mettre à jour le statut de la table
      await db.executeSql(
        'UPDATE tables SET status = ? WHERE id = ?',
        ['occupied', currentTable.id]
      );

      // Rafraîchir les données
      await loadTables();
      await loadActiveOrders();
      clearCart();
      setCurrentTable(null);

      return orderId;
    } catch (error) {
      console.error('Error submitting order:', error);
      return null;
    }
  };

  // Charger les commandes actives
  const loadActiveOrders = async (dbConnection = db) => {
    if (!dbConnection) return;
    try {
      const [results] = await dbConnection.executeSql(`
        SELECT o.*, t.table_number 
        FROM orders o 
        JOIN tables t ON o.table_id = t.id 
        WHERE o.status IN ('pending', 'preparing', 'ready')
        ORDER BY o.created_at DESC
      `);
      const ordersData = [];
      for (let i = 0; i < results.rows.length; i++) {
        ordersData.push(results.rows.item(i));
      }
      setActiveOrders(ordersData);
    } catch (error) {
      console.error('Error loading active orders:', error);
    }
  };

  // Obtenir les articles d'une commande
  const getOrderItems = async (orderId) => {
    if (!db) return [];
    try {
      const [results] = await db.executeSql(`
        SELECT oi.*, i.name, i.description 
        FROM order_items oi 
        JOIN items i ON oi.item_id = i.id 
        WHERE oi.order_id = ?
      `, [orderId]);
      const itemsData = [];
      for (let i = 0; i < results.rows.length; i++) {
        itemsData.push(results.rows.item(i));
      }
      return itemsData;
    } catch (error) {
      console.error('Error loading order items:', error);
      return [];
    }
  };

  // Mettre à jour le statut d'une commande
  const updateOrderStatus = async (orderId, status) => {
    if (!db) return;
    try {
      await db.executeSql(
        'UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        [status, orderId]
      );

      // Si la commande est terminée, libérer la table
      if (status === 'served') {
        const [orderResults] = await db.executeSql(
          'SELECT table_id FROM orders WHERE id = ?',
          [orderId]
        );
        if (orderResults.rows.length > 0) {
          const tableId = orderResults.rows.item(0).table_id;
          await db.executeSql(
            'UPDATE tables SET status = ? WHERE id = ?',
            ['free', tableId]
          );
        }
      } else if (status === 'preparing') {
        const [orderResults] = await db.executeSql(
          'SELECT table_id FROM orders WHERE id = ?',
          [orderId]
        );
        if (orderResults.rows.length > 0) {
          const tableId = orderResults.rows.item(0).table_id;
          await db.executeSql(
            'UPDATE tables SET status = ? WHERE id = ?',
            ['sent', tableId]
          );
        }
      }

      await loadTables();
      await loadActiveOrders();
    } catch (error) {
      console.error('Error updating order status:', error);
    }
  };

  // Obtenir les plats du jour
  const getDailySpecials = async () => {
    if (!db) return [];
    try {
      const [results] = await db.executeSql(
        'SELECT * FROM daily_specials WHERE is_active = 1 ORDER BY created_at DESC'
      );
      const specials = [];
      for (let i = 0; i < results.rows.length; i++) {
        specials.push(results.rows.item(i));
      }
      return specials;
    } catch (error) {
      console.error('Error loading daily specials:', error);
      return [];
    }
  };

  // Ajouter un plat du jour
  const addDailySpecial = async (name, description, price) => {
    if (!db) return;
    try {
      await db.executeSql(
        'INSERT INTO daily_specials (name, description, price, is_active) VALUES (?, ?, ?, 1)',
        [name, description, price]
      );
      // Ajouter à la catégorie "Plats du jour"
      const [catResults] = await db.executeSql(
        'SELECT id FROM categories WHERE name = ?',
        ['Plats du jour']
      );
      if (catResults.rows.length > 0) {
        const categoryId = catResults.rows.item(0).id;
        await db.executeSql(
          'INSERT INTO items (name, description, price, category_id, is_daily_special) VALUES (?, ?, ?, ?, 1)',
          [name, description, price, categoryId]
        );
      }
    } catch (error) {
      console.error('Error adding daily special:', error);
    }
  };

  // Supprimer un plat du jour
  const removeDailySpecial = async (id) => {
    if (!db) return;
    try {
      await db.executeSql(
        'UPDATE daily_specials SET is_active = 0 WHERE id = ?',
        [id]
      );
      await db.executeSql(
        'UPDATE items SET is_daily_special = 0 WHERE name IN (SELECT name FROM daily_specials WHERE id = ?)',
        [id]
      );
    } catch (error) {
      console.error('Error removing daily special:', error);
    }
  };

  const value = {
    // État
    tables,
    categories,
    currentTable,
    cart,
    activeOrders,
    loading,
    db,

    // Actions
    selectTable,
    addToCart,
    updateCartQuantity,
    removeFromCart,
    clearCart,
    getCartTotal,
    submitOrder,
    getItemsByCategory,
    loadTables,
    loadCategories,
    loadActiveOrders,
    getOrderItems,
    updateOrderStatus,
    getDailySpecials,
    addDailySpecial,
    removeDailySpecial,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};

export default AppContext;