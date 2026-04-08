import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  TextInput,
  Alert,
  Modal,
} from 'react-native';
import { useApp } from '../context/AppContext';

const AdminScreen = () => {
  const {
    getDailySpecials,
    addDailySpecial,
    removeDailySpecial,
    db,
  } = useApp();

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [specials, setSpecials] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newSpecial, setNewSpecial] = useState({ name: '', description: '', price: '' });

  const ADMIN_PASSWORD = 'admin123'; // Mot de passe simple pour la démo

  useEffect(() => {
    if (isAuthenticated) {
      loadSpecials();
    }
  }, [isAuthenticated]);

  const loadSpecials = async () => {
    const data = await getDailySpecials();
    setSpecials(data);
  };

  const handleLogin = () => {
    if (password === ADMIN_PASSWORD) {
      setIsAuthenticated(true);
    } else {
      Alert.alert('Erreur', 'Mot de passe incorrect');
    }
  };

  const handleAddSpecial = async () => {
    if (!newSpecial.name || !newSpecial.price) {
      Alert.alert('Erreur', 'Veuillez remplir le nom et le prix');
      return;
    }

    await addDailySpecial(newSpecial.name, newSpecial.description, parseFloat(newSpecial.price));
    setNewSpecial({ name: '', description: '', price: '' });
    setShowAddModal(false);
    loadSpecials();
    Alert.alert('Succès', 'Plat du jour ajouté');
  };

  const handleRemoveSpecial = (id) => {
    Alert.alert(
      'Supprimer',
      'Voulez-vous vraiment supprimer ce plat du jour?',
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Supprimer',
          style: 'destructive',
          onPress: async () => {
            await removeDailySpecial(id);
            loadSpecials();
          },
        },
      ]
    );
  };

  if (!isAuthenticated) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>🔒 Administration</Text>
          <Text style={styles.headerSubtitle}>Gestion des plats du jour</Text>
        </View>

        <View style={styles.loginContainer}>
          <View style={styles.loginCard}>
            <Text style={styles.loginTitle}>Authentification requise</Text>
            <Text style={styles.loginText}>Entrez le mot de passe administrateur</Text>
            <TextInput
              style={styles.passwordInput}
              placeholder="Mot de passe"
              secureTextEntry
              value={password}
              onChangeText={setPassword}
            />
            <TouchableOpacity style={styles.loginButton} onPress={handleLogin}>
              <Text style={styles.loginButtonText}>Se connecter</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerRow}>
          <View>
            <Text style={styles.headerTitle}>🔧 Administration</Text>
            <Text style={styles.headerSubtitle}>Gestion des plats du jour</Text>
          </View>
          <TouchableOpacity onPress={() => setIsAuthenticated(false)}>
            <Text style={styles.logoutButton}>Déconnexion</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.content}>
        <View style={styles.statsCard}>
          <Text style={styles.statsLabel}>Plats du jour actifs</Text>
          <Text style={styles.statsValue}>{specials.length}</Text>
        </View>

        <TouchableOpacity
          style={styles.addButton}
          onPress={() => setShowAddModal(true)}
        >
          <Text style={styles.addButtonText}>+ Ajouter un plat du jour</Text>
        </TouchableOpacity>

        {specials.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>🍽️</Text>
            <Text style={styles.emptyText}>Aucun plat du jour</Text>
          </View>
        ) : (
          <FlatList
            data={specials}
            renderItem={({ item }) => (
              <View style={styles.specialCard}>
                <View style={styles.specialHeader}>
                  <Text style={styles.specialName}>{item.name}</Text>
                  <Text style={styles.specialPrice}>{item.price.toFixed(2)}€</Text>
                </View>
                {item.description ? (
                  <Text style={styles.specialDesc}>{item.description}</Text>
                ) : null}
                <TouchableOpacity
                  style={styles.deleteButton}
                  onPress={() => handleRemoveSpecial(item.id)}
                >
                  <Text style={styles.deleteButtonText}>Supprimer</Text>
                </TouchableOpacity>
              </View>
            )}
            keyExtractor={(item) => item.id.toString()}
            contentContainerStyle={styles.list}
          />
        )}
      </View>

      <Modal
        visible={showAddModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowAddModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Nouveau plat du jour</Text>

            <TextInput
              style={styles.input}
              placeholder="Nom du plat"
              value={newSpecial.name}
              onChangeText={(text) => setNewSpecial({ ...newSpecial, name: text })}
            />

            <TextInput
              style={[styles.input, { height: 80 }]}
              placeholder="Description (optionnel)"
              value={newSpecial.description}
              onChangeText={(text) => setNewSpecial({ ...newSpecial, description: text })}
              multiline
            />

            <TextInput
              style={styles.input}
              placeholder="Prix (€)"
              value={newSpecial.price}
              onChangeText={(text) => setNewSpecial({ ...newSpecial, price: text })}
              keyboardType="decimal-pad"
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => setShowAddModal(false)}
              >
                <Text style={styles.cancelButtonText}>Annuler</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.confirmButton]}
                onPress={handleAddSpecial}
              >
                <Text style={styles.confirmButtonText}>Ajouter</Text>
              </TouchableOpacity>
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
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
  logoutButton: {
    color: '#fff',
    fontSize: 14,
    padding: 8,
  },
  content: {
    flex: 1,
    padding: 15,
  },
  loginContainer: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
  },
  loginCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 30,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  loginTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
    marginBottom: 8,
  },
  loginText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  passwordInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 16,
  },
  loginButton: {
    backgroundColor: '#1a237e',
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  loginButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  statsCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    marginBottom: 15,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  statsLabel: {
    fontSize: 14,
    color: '#666',
  },
  statsValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1a237e',
    marginTop: 4,
  },
  addButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 15,
  },
  addButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  list: {
    paddingBottom: 20,
  },
  specialCard: {
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
  specialHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  specialName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  specialPrice: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  specialDesc: {
    fontSize: 13,
    color: '#666',
    marginTop: 4,
    marginBottom: 8,
  },
  deleteButton: {
    alignSelf: 'flex-end',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: '#ffebee',
    marginTop: 4,
  },
  deleteButtonText: {
    color: '#f44336',
    fontSize: 13,
    fontWeight: '500',
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
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
    textAlign: 'center',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 12,
  },
  modalButtons: {
    flexDirection: 'row',
    marginTop: 10,
  },
  modalButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    marginHorizontal: 5,
  },
  cancelButton: {
    backgroundColor: '#e0e0e0',
  },
  cancelButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '500',
  },
  confirmButton: {
    backgroundColor: '#4CAF50',
  },
  confirmButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default AdminScreen;