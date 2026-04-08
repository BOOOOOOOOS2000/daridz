import SQLite from 'react-native-sqlite-storage';

SQLite.enablePromise(true);

const DB_NAME = 'RestaurantDB.db';

export const getDBConnection = async () => {
  return SQLite.openDatabase({ name: DB_NAME, location: 'default' });
};

export const createTables = async (db) => {
  // Table des tables (tables du restaurant)
  await db.executeSql(`
    CREATE TABLE IF NOT EXISTS tables (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      table_number INTEGER UNIQUE NOT NULL,
      status TEXT DEFAULT 'free',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Table des catégories
  await db.executeSql(`
    CREATE TABLE IF NOT EXISTS categories (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      icon TEXT,
      display_order INTEGER DEFAULT 0
    )
  `);

  // Table des articles
  await db.executeSql(`
    CREATE TABLE IF NOT EXISTS items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      description TEXT,
      price REAL NOT NULL,
      category_id INTEGER,
      is_daily_special INTEGER DEFAULT 0,
      FOREIGN KEY (category_id) REFERENCES categories(id)
    )
  `);

  // Table des commandes
  await db.executeSql(`
    CREATE TABLE IF NOT EXISTS orders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      table_id INTEGER NOT NULL,
      status TEXT DEFAULT 'pending',
      total REAL DEFAULT 0,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (table_id) REFERENCES tables(id)
    )
  `);

  // Table des articles de commande
  await db.executeSql(`
    CREATE TABLE IF NOT EXISTS order_items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      order_id INTEGER NOT NULL,
      item_id INTEGER NOT NULL,
      quantity INTEGER DEFAULT 1,
      notes TEXT,
      price REAL NOT NULL,
      FOREIGN KEY (order_id) REFERENCES orders(id),
      FOREIGN KEY (item_id) REFERENCES items(id)
    )
  `);

  // Table des plats du jour
  await db.executeSql(`
    CREATE TABLE IF NOT EXISTS daily_specials (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      description TEXT,
      price REAL NOT NULL,
      is_active INTEGER DEFAULT 1,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);
};

export const insertInitialData = async (db) => {
  // Vérifier si les données existent déjà
  const [tables] = await db.executeSql('SELECT COUNT(*) as count FROM tables');
  if (tables[0].count > 0) return;

  // Insérer les 27 tables
  for (let i = 1; i <= 27; i++) {
    await db.executeSql(
      'INSERT INTO tables (table_number, status) VALUES (?, ?)',
      [i, 'free']
    );
  }

  // Catégories
  const categories = [
    { name: 'Viande', icon: 'local-dining', order: 1 },
    { name: 'Pizza', icon: 'local-pizza', order: 2 },
    { name: 'Burger', icon: 'lunch-dining', order: 3 },
    { name: 'Entrées chaudes', icon: 'whatshot', order: 4 },
    { name: 'Entrées froides', icon: 'icecream', order: 5 },
    { name: 'Plats enfants', icon: 'child-care', order: 6 },
    { name: 'Plats du jour', icon: 'restaurant-menu', order: 7 },
  ];

  for (const cat of categories) {
    await db.executeSql(
      'INSERT INTO categories (name, icon, display_order) VALUES (?, ?, ?)',
      [cat.name, cat.icon, cat.order]
    );
  }

  // Articles par catégorie
  const items = [
    // Viande (category_id: 1)
    { name: 'Entrecôte de bœuf', desc: '300g, grillée à votre convenance', price: 24.90, cat: 1 },
    { name: 'Filet mignon de porc', desc: 'Sauce au poivre vert', price: 18.50, cat: 1 },
    { name: 'Gigot d\'agneau', desc: 'Rôti aux herbes de Provence', price: 22.90, cat: 1 },
    { name: 'Poulet rôti', desc: 'Entier, pommes de terre', price: 16.90, cat: 1 },
    { name: 'Côte de bœuf', desc: '500g pour 2 personnes', price: 45.00, cat: 1 },
    { name: 'Brochette mixte', desc: 'Bœuf, poulet, agneau', price: 21.50, cat: 1 },
    { name: 'Magret de canard', desc: 'Sauce aux figues', price: 23.90, cat: 1 },

    // Pizza (category_id: 2)
    { name: 'Margherita', desc: 'Tomate, mozzarella, basilic', price: 12.50, cat: 2 },
    { name: 'Reine', desc: 'Tomate, mozzarella, jambon, champignons', price: 14.50, cat: 2 },
    { name: '4 Fromages', desc: 'Mozzarella, chèvre, gorgonzola, parmesan', price: 15.50, cat: 2 },
    { name: 'Calzone', desc: 'Tomate, mozzarella, jambon, œuf', price: 14.90, cat: 2 },
    { name: 'Diavola', desc: 'Tomate, mozzarella, pepperoni, piment', price: 15.00, cat: 2 },
    { name: 'Végétarienne', desc: 'Tomate, mozzarella, légumes grillés', price: 14.00, cat: 2 },

    // Burger (category_id: 3)
    { name: 'Classic Burger', desc: 'Bœuf 150g, cheddar, salade, tomate', price: 13.90, cat: 3 },
    { name: 'Double Burger', desc: 'Double bœuf, double cheddar', price: 16.90, cat: 3 },
    { name: 'Chicken Burger', desc: 'Poulet pané, sauce barbecue', price: 12.90, cat: 3 },
    { name: 'Veggie Burger', desc: 'Galette végétale, avocat', price: 14.50, cat: 3 },
    { name: 'Bacon Burger', desc: 'Bœuf, bacon croustillant, oignons', price: 15.50, cat: 3 },
    { name: 'Mushroom Burger', desc: 'Bœuf, champignons sautés, sauce truffe', price: 16.00, cat: 3 },

    // Entrées chaudes (category_id: 4)
    { name: 'Soupe à l\'oignon', desc: 'Gratinée au fromage', price: 8.50, cat: 4 },
    { name: 'Escargots', desc: '6 pièces, beurre persillé', price: 10.90, cat: 4 },
    { name: 'Foie gras', desc: 'Maison, chutney de figues', price: 14.90, cat: 4 },
    { name: 'Gnocchis', desc: 'Maison, sauce tomate basilic', price: 9.50, cat: 4 },
    { name: 'Croque-monsieur', desc: 'Jambon, béchamel, gruyère', price: 8.90, cat: 4 },
    { name: 'Œufs cocotte', desc: 'Crème, jambon, parmesan', price: 7.90, cat: 4 },

    // Entrées froides (category_id: 5)
    { name: 'Salade César', desc: 'Laitue, parmesan, croûtons, poulet', price: 11.90, cat: 5 },
    { name: 'Carpaccio de bœuf', desc: 'Parmesan, roquette, huile d\'olive', price: 13.50, cat: 5 },
    { name: 'Assiette de charcuterie', desc: 'Sélection du chef', price: 14.90, cat: 5 },
    { name: 'Salade composée', desc: 'Tomate, concombre, feta, olives', price: 9.90, cat: 5 },
    { name: 'Terrine de campagne', desc: 'Cornichons, pain toasté', price: 8.50, cat: 5 },
    { name: 'Avocat crevettes', desc: 'Sauce cocktail maison', price: 10.50, cat: 5 },

    // Plats enfants (category_id: 6)
    { name: 'Nuggets (6pcs)', desc: 'Frites, sauce au choix', price: 8.50, cat: 6 },
    { name: 'Hot-dog', desc: 'Frites, ketchup/moutarde', price: 7.90, cat: 6 },
    { name: 'Spaghetti bolognaise', desc: 'Sauce tomate, parmesan', price: 8.90, cat: 6 },
    { name: 'Steak haché', desc: '100g, frites, haricots', price: 9.50, cat: 6 },
    { name: 'Poulet frit', desc: '2 morceaux, frites', price: 9.90, cat: 6 },
    { name: 'Pizza enfant', desc: '8 pouces, garniture au choix', price: 8.50, cat: 6 },
  ];

  for (const item of items) {
    await db.executeSql(
      'INSERT INTO items (name, description, price, category_id) VALUES (?, ?, ?, ?)',
      [item.name, item.desc, item.price, item.cat]
    );
  }

  // Plats du jour
  const dailySpecials = [
    { name: 'Blanquette de veau', desc: 'Riz, carottes glacées', price: 17.90 },
    { name: 'Moules-frites', desc: '1kg de moules, frites maison', price: 16.50 },
    { name: 'Cassoulet', desc: 'Traditionnel du Sud-Ouest', price: 18.90 },
    { name: 'Tartiflette', desc: 'Reblochon, pommes de terre, lardons', price: 15.90 },
  ];

  for (const special of dailySpecials) {
    await db.executeSql(
      'INSERT INTO daily_specials (name, description, price, is_active) VALUES (?, ?, ?, 1)',
      [special.name, special.desc, special.price]
    );
  }
};

export const dropTables = async (db) => {
  await db.executeSql('DROP TABLE IF EXISTS order_items');
  await db.executeSql('DROP TABLE IF EXISTS orders');
  await db.executeSql('DROP TABLE IF EXISTS items');
  await db.executeSql('DROP TABLE IF EXISTS categories');
  await db.executeSql('DROP TABLE IF EXISTS tables');
  await db.executeSql('DROP TABLE IF EXISTS daily_specials');
};

export const resetDatabase = async () => {
  const db = await getDBConnection();
  await dropTables(db);
  await createTables(db);
  await insertInitialData(db);
};

export default {
  getDBConnection,
  createTables,
  insertInitialData,
  resetDatabase,
};