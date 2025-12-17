"""
Database Module
Handles all database operations for the Warehouse Management System
"""
import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager
import os


class Database:
    def __init__(self, db_path='warehouse.db'):
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize database with schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inventory_id TEXT UNIQUE NOT NULL,
                    article_code TEXT,
                    description TEXT,
                    condition TEXT,
                    length REAL,
                    width REAL,
                    height REAL,
                    weight REAL,
                    price REAL,
                    location_id INTEGER,
                    status TEXT DEFAULT 'in_stock',
                    quantity INTEGER DEFAULT 1,
                    quantity_available INTEGER DEFAULT 1,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (location_id) REFERENCES locations(id)
                )
            ''')
            
            # Images table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    filename_original TEXT NOT NULL,
                    filename_cropped TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
                )
            ''')
            
            # Locations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_code TEXT UNIQUE NOT NULL,
                    barcode_value TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Box sizes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS box_sizes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    inner_length REAL,
                    inner_width REAL,
                    inner_height REAL,
                    max_weight REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Customers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT,
                    postal_code TEXT,
                    city TEXT,
                    country TEXT DEFAULT 'Sverige',
                    phone TEXT,
                    email TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_number TEXT UNIQUE NOT NULL,
                    customer_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    payment_status TEXT DEFAULT 'unpaid',
                    shipping_method TEXT,
                    tracking_number TEXT,
                    total_amount REAL DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP,
                    packed_at TIMESTAMP,
                    shipped_at TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            ''')
            
            # Drop old orders table if it exists without customer_id
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='orders'")
            result = cursor.fetchone()
            if result and 'customer_id' not in result[0]:
                print("⚠ Migrating orders table...")
                cursor.execute('DROP TABLE IF EXISTS orders')
                cursor.execute('''
                    CREATE TABLE orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_number TEXT UNIQUE NOT NULL,
                        customer_id INTEGER,
                        status TEXT DEFAULT 'pending',
                        payment_status TEXT DEFAULT 'unpaid',
                        shipping_method TEXT,
                        tracking_number TEXT,
                        total_amount REAL DEFAULT 0,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        confirmed_at TIMESTAMP,
                        packed_at TIMESTAMP,
                        shipped_at TIMESTAMP,
                        FOREIGN KEY (customer_id) REFERENCES customers(id)
                    )
                ''')

            
            # Order items (many-to-many)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            ''')
            
            # Audit log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    inventory_id TEXT,
                    operator TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Marketplace listings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS marketplace_listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    marketplace TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    listed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sold_at TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
                )
            ''')
            
            # Barcode history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS barcode_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prefix TEXT NOT NULL,
                    start_number INTEGER NOT NULL,
                    end_number INTEGER NOT NULL,
                    count INTEGER NOT NULL,
                    operator TEXT,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Shipping methods
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shipping_methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert default shipping methods
            cursor.execute("SELECT COUNT(*) FROM shipping_methods")
            if cursor.fetchone()[0] == 0:
                default_methods = [
                    ('PostNord', 'Standard paketleverans'),
                    ('DHL', 'Express leverans'),
                    ('Schenker', 'Palletfrakt'),
                    ('Bring', 'Paket och pall'),
                    ('Budbee', 'Hemleverans'),
                    ('Hämtas på plats', 'Kunden hämtar själv')
                ]
                cursor.executemany(
                    'INSERT INTO shipping_methods (name, description) VALUES (?, ?)',
                    default_methods
                )
            
            conn.commit()
            print("✓ Database initialized successfully")
    
    # ==================== ITEMS ====================
    
    def generate_inventory_id(self):
        """Generate next inventory ID (INV-000001)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(CAST(SUBSTR(inventory_id, 5) AS INTEGER)) FROM items')
            result = cursor.fetchone()[0]
            next_num = (result or 0) + 1
            return f"INV-{next_num:06d}"
    
    def create_item(self, item_data):
        """Create new item"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            quantity = item_data.get('quantity', 1)
            
            cursor.execute('''
                INSERT INTO items (
                    inventory_id, article_code, description, condition,
                    length, width, height, weight, price, location_id, notes,
                    quantity, quantity_available
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_data['inventory_id'],
                item_data.get('article_code'),
                item_data.get('description'),
                item_data.get('condition'),
                item_data.get('length'),
                item_data.get('width'),
                item_data.get('height'),
                item_data.get('weight'),
                item_data.get('price'),
                item_data.get('location_id'),
                item_data.get('notes'),
                quantity,
                quantity  # Initially all units are available
            ))
            return cursor.lastrowid
    
    def add_image_to_item(self, item_id, filename_original, filename_cropped=None):
        """Add image record to item"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO images (item_id, filename_original, filename_cropped)
                VALUES (?, ?, ?)
            ''', (item_id, filename_original, filename_cropped))
            return cursor.lastrowid
    
    def get_item_by_inventory_id(self, inventory_id):
        """Get item by inventory ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT i.*, l.location_code, l.barcode_value as location_barcode
                FROM items i
                LEFT JOIN locations l ON i.location_id = l.id
                WHERE i.inventory_id = ?
            ''', (inventory_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_item_by_id(self, item_id):
        """Get item by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT i.*, l.location_code, l.barcode_value as location_barcode
                FROM items i
                LEFT JOIN locations l ON i.location_id = l.id
                WHERE i.id = ?
            ''', (item_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def search_items(self, query):
        """Search items by inventory_id, article_code, or description"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            search_term = f'%{query}%'
            cursor.execute('''
                SELECT i.*, l.location_code
                FROM items i
                LEFT JOIN locations l ON i.location_id = l.id
                WHERE i.inventory_id LIKE ? 
                   OR i.article_code LIKE ?
                   OR i.description LIKE ?
                ORDER BY i.created_at DESC
                LIMIT 100
            ''', (search_term, search_term, search_term))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_item_location(self, item_id, location_id):
        """Update item location"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE items 
                SET location_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (location_id, item_id))
    
    def update_item_status(self, item_id, status):
        """Update item status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE items 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, item_id))
    
    def get_items_by_status(self, status):
        """Get items by status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT i.*, l.location_code
                FROM items i
                LEFT JOIN locations l ON i.location_id = l.id
                WHERE i.status = ?
                ORDER BY i.created_at DESC
            ''', (status,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== IMAGES ====================
    
    def add_image(self, item_id, filename_original, filename_cropped=None):
        """Add image to item"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO images (item_id, filename_original, filename_cropped)
                VALUES (?, ?, ?)
            ''', (item_id, filename_original, filename_cropped))
            return cursor.lastrowid
    
    def get_item_images(self, item_id):
        """Get all images for an item"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM images WHERE item_id = ?
                ORDER BY created_at
            ''', (item_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== LOCATIONS ====================
    
    def get_all_locations(self):
        """Get all locations"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM locations ORDER BY location_code')
            return [dict(row) for row in cursor.fetchall()]
    
    def create_location(self, location_code, barcode_value, description=''):
        """Create new location"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO locations (location_code, barcode_value, description)
                VALUES (?, ?, ?)
            ''', (location_code, barcode_value, description))
            return cursor.lastrowid
    
    def delete_location(self, location_id):
        """Delete location"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM locations WHERE id = ?', (location_id,))
    
    def get_location_by_barcode(self, barcode_value):
        """Get location by barcode"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM locations WHERE barcode_value = ?', (barcode_value,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_location_by_id(self, location_id):
        """Get location by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM locations WHERE id = ?', (location_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ==================== BOX SIZES ====================
    
    def get_all_box_sizes(self):
        """Get all box sizes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM box_sizes ORDER BY name')
            return [dict(row) for row in cursor.fetchall()]
    
    def create_box_size(self, name, length, width, height, max_weight):
        """Create new box size"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO box_sizes (name, inner_length, inner_width, inner_height, max_weight)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, length, width, height, max_weight))
            return cursor.lastrowid
    
    def delete_box_size(self, box_id):
        """Delete box size"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM box_sizes WHERE id = ?', (box_id,))
    
    def suggest_box_size(self, items):
        """
        Suggest appropriate box size for items using smart 3D bin packing
        
        Strategy:
        1. Calculate total volume needed
        2. Try different orientations and arrangements
        3. Find smallest box that fits (by volume, then by dimensions)
        4. Consider weight limits
        """
        if not items:
            return None
        
        # Collect item dimensions and calculate total volume
        item_dims = []
        total_volume = 0
        total_weight = 0
        
        for item in items:
            length = item.get('length', 0) or 0
            width = item.get('width', 0) or 0
            height = item.get('height', 0) or 0
            weight = item.get('weight', 0) or 0
            quantity = item.get('quantity', 1) or 1  # Handle bulk items
            
            # Add each item (respecting quantity)
            for _ in range(quantity):
                if length > 0 and width > 0 and height > 0:
                    item_dims.append([length, width, height])
                    total_volume += length * width * height
            
            total_weight += weight * quantity
        
        if not item_dims:
            return None
        
        # Try to pack items efficiently
        # Strategy: Try different arrangements and find the tightest bounding box
        
        def get_bounding_box(dims_list):
            """Calculate minimum bounding box for given item arrangement"""
            if not dims_list:
                return (0, 0, 0)
            
            # Simple stacking strategies
            arrangements = []
            
            # Strategy 1: Stack all items vertically (original method)
            max_l = max(d[0] for d in dims_list)
            max_w = max(d[1] for d in dims_list)
            sum_h = sum(d[2] for d in dims_list)
            arrangements.append((max_l, max_w, sum_h))
            
            # Strategy 2: Arrange in 2x1 grid (side by side)
            if len(dims_list) >= 2:
                sum_l = sum(d[0] for d in dims_list)
                max_w = max(d[1] for d in dims_list)
                max_h = max(d[2] for d in dims_list)
                arrangements.append((sum_l, max_w, max_h))
            
            # Strategy 3: Arrange in 1x2 grid (front to back)
            if len(dims_list) >= 2:
                max_l = max(d[0] for d in dims_list)
                sum_w = sum(d[1] for d in dims_list)
                max_h = max(d[2] for d in dims_list)
                arrangements.append((max_l, sum_w, max_h))
            
            # Strategy 4: Try 2x2 grid for 4+ items
            if len(dims_list) >= 4:
                # Split into pairs and arrange
                sum_l = sum(d[0] for d in dims_list[:2])
                sum_w = sum(d[1] for d in dims_list[::2])
                max_h = max(d[2] for d in dims_list)
                arrangements.append((sum_l, sum_w, max_h))
            
            # Strategy 5: All dimensions for single item
            if len(dims_list) == 1:
                d = dims_list[0]
                arrangements.extend([
                    (d[0], d[1], d[2]),
                    (d[0], d[2], d[1]),
                    (d[1], d[0], d[2]),
                    (d[1], d[2], d[0]),
                    (d[2], d[0], d[1]),
                    (d[2], d[1], d[0])
                ])
            
            # Return arrangement with smallest volume
            return min(arrangements, key=lambda x: x[0] * x[1] * x[2])
        
        # Get optimal bounding box
        min_length, min_width, min_height = get_bounding_box(item_dims)
        
        # Find suitable box from database
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all boxes that meet weight requirement
            cursor.execute('''
                SELECT * FROM box_sizes
                WHERE max_weight >= ?
                ORDER BY (inner_length * inner_width * inner_height)
            ''', (total_weight,))
            
            boxes = [dict(row) for row in cursor.fetchall()]
            
            if not boxes:
                return None
            
            # Find boxes that fit the items (considering all rotations)
            valid_boxes = []
            
            for box in boxes:
                box_dims = [
                    box['inner_length'],
                    box['inner_width'],
                    box['inner_height']
                ]
                
                item_dims_to_fit = [min_length, min_width, min_height]
                
                # Check if items fit in any rotation
                # Try all 6 possible orientations of the box
                rotations = [
                    (box_dims[0], box_dims[1], box_dims[2]),
                    (box_dims[0], box_dims[2], box_dims[1]),
                    (box_dims[1], box_dims[0], box_dims[2]),
                    (box_dims[1], box_dims[2], box_dims[0]),
                    (box_dims[2], box_dims[0], box_dims[1]),
                    (box_dims[2], box_dims[1], box_dims[0])
                ]
                
                for rot in rotations:
                    # Check if items fit when both are optimally rotated
                    sorted_box = sorted(rot)
                    sorted_items = sorted(item_dims_to_fit)
                    
                    if all(sorted_box[i] >= sorted_items[i] for i in range(3)):
                        # Calculate wasted space (box volume - items volume)
                        box_volume = rot[0] * rot[1] * rot[2]
                        waste = box_volume - total_volume
                        
                        valid_boxes.append({
                            'box': box,
                            'waste': waste,
                            'volume': box_volume
                        })
                        break  # Found a valid rotation, no need to try others
            
            if not valid_boxes:
                # No perfect fit found, return smallest box anyway
                return boxes[0]
            
            # Return box with least wasted space
            best = min(valid_boxes, key=lambda x: (x['waste'], x['volume']))
            return best['box']
    
    # ==================== ORDERS ====================
    
    def generate_order_number(self):
        """Generate next order number (ORD-000001)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(CAST(SUBSTR(order_number, 5) AS INTEGER)) FROM orders')
            result = cursor.fetchone()[0]
            next_num = (result or 0) + 1
            return f"ORD-{next_num:06d}"
    
    # ==================== ORDERS (OLD - DEPRECATED) ====================
    # Note: These are kept for backward compatibility with old packing page
    # The new order system uses the functions further down
    
    def get_orders(self, status=None):
        """Get orders, optionally filtered by status (OLD VERSION)"""
        return self.get_all_orders(status)
    
    def get_order_by_id(self, order_id):
        """Get order by ID (OLD VERSION)"""
        return self.get_order(order_id)
    
    def get_next_order_to_pack(self):
        """Get next pending order to pack"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM orders 
                WHERE status = 'pending' OR status = 'confirmed'
                ORDER BY created_at
                LIMIT 1
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_order_items(self, order_id):
        """Get all items in an order"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT i.*, 
                       oi.quantity as order_quantity,
                       l.location_code, l.barcode_value as location_barcode,
                       (SELECT filename_original FROM images WHERE item_id = i.id LIMIT 1) as filename_original,
                       (SELECT filename_cropped FROM images WHERE item_id = i.id LIMIT 1) as filename_cropped
                FROM order_items oi
                JOIN items i ON oi.item_id = i.id
                LEFT JOIN locations l ON i.location_id = l.id
                WHERE oi.order_id = ?
                ORDER BY oi.added_at
            ''', (order_id,))
            
            items = []
            for row in cursor.fetchall():
                item = dict(row)
                # IMPORTANT: Use order_quantity from order_items, not item.quantity
                item['quantity'] = item['order_quantity']
                items.append(item)
            
            return items
    
    def ship_order(self, order_id):
        """Mark order as shipped"""
        self.update_order_status(order_id, 'shipped', 'shipped_at')
    
    def delete_order(self, order_id):
        """Delete order"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    
    # ==================== MARKETPLACE ====================
    
    def create_marketplace_listing(self, item_id, marketplace, status='active'):
        """Create marketplace listing"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO marketplace_listings (item_id, marketplace, status)
                VALUES (?, ?, ?)
            ''', (item_id, marketplace, status))
            return cursor.lastrowid
    
    def get_marketplace_listings(self, status=None, marketplace=None):
        """Get marketplace listings with filters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = '''
                SELECT ml.*, i.inventory_id, i.description, i.price, i.article_code,
                       i.quantity, i.quantity_available
                FROM marketplace_listings ml
                JOIN items i ON ml.item_id = i.id
                WHERE 1=1
            '''
            params = []
            
            if status:
                query += ' AND ml.status = ?'
                params.append(status)
            
            if marketplace:
                query += ' AND ml.marketplace = ?'
                params.append(marketplace)
            
            query += ' ORDER BY ml.listed_at DESC'
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_marketplace_listing_by_id(self, listing_id):
        """Get a single marketplace listing by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ml.*, i.inventory_id, i.description, i.price, i.article_code
                FROM marketplace_listings ml
                JOIN items i ON ml.item_id = i.id
                WHERE ml.id = ?
            ''', (listing_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_marketplace_listing_status(self, listing_id, status):
        """Update listing status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status == 'sold':
                cursor.execute('''
                    UPDATE marketplace_listings
                    SET status = ?, sold_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, listing_id))
            else:
                cursor.execute('''
                    UPDATE marketplace_listings
                    SET status = ?
                    WHERE id = ?
                ''', (status, listing_id))
    
    # ==================== AUDIT LOG ====================
    
    def log_action(self, action, inventory_id=None, operator='System', details=''):
        """Log an action"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO audit_log (action, inventory_id, operator, details)
                VALUES (?, ?, ?, ?)
            ''', (action, inventory_id, operator, details))
    
    def get_recent_activity(self, limit=50):
        """Get recent activity log"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM audit_log
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== REPORTS & STATISTICS ====================
    
    def get_statistics(self):
        """Get system statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total items
            cursor.execute('SELECT COUNT(*) FROM items')
            stats['total_items'] = cursor.fetchone()[0]
            
            # Items by status
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM items
                GROUP BY status
            ''')
            stats['items_by_status'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Total orders
            cursor.execute('SELECT COUNT(*) FROM orders')
            stats['total_orders'] = cursor.fetchone()[0]
            
            # Pending orders
            cursor.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"')
            stats['pending_orders'] = cursor.fetchone()[0]
            
            # Shipped orders
            cursor.execute('SELECT COUNT(*) FROM orders WHERE status = "shipped"')
            stats['shipped_orders'] = cursor.fetchone()[0]
            
            # Total inventory value
            cursor.execute('SELECT SUM(price) FROM items WHERE status = "in_stock"')
            result = cursor.fetchone()[0]
            stats['inventory_value'] = result if result else 0
            
            # Marketplace listings
            cursor.execute('''
                SELECT marketplace, COUNT(*) as count
                FROM marketplace_listings
                WHERE status != 'sold'
                GROUP BY marketplace
            ''')
            stats['active_listings'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Items sold this month
            cursor.execute('''
                SELECT COUNT(*)
                FROM items
                WHERE status = 'sold'
                  AND updated_at >= date('now', 'start of month')
            ''')
            stats['sold_this_month'] = cursor.fetchone()[0]
            
            # Revenue this month
            cursor.execute('''
                SELECT SUM(price)
                FROM items
                WHERE status = 'sold'
                  AND updated_at >= date('now', 'start of month')
            ''')
            result = cursor.fetchone()[0]
            stats['revenue_this_month'] = result if result else 0
            
            return stats
    
    def get_sales_report(self, period='month'):
        """Get sales report for specified period (based on actual orders)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Determine date range
            if period == 'day':
                date_filter = "date('now')"
            elif period == 'week':
                date_filter = "date('now', '-7 days')"
            elif period == 'month':
                date_filter = "date('now', 'start of month')"
            elif period == 'year':
                date_filter = "date('now', 'start of year')"
            else:
                date_filter = "date('now', 'start of month')"
            
            # Sales by day (from orders)
            cursor.execute(f'''
                SELECT 
                    DATE(o.created_at) as sale_date,
                    SUM(oi.quantity) as items_sold,
                    SUM(i.price * oi.quantity) as revenue
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN items i ON oi.item_id = i.id
                WHERE DATE(o.created_at) >= {date_filter}
                GROUP BY DATE(o.created_at)
                ORDER BY sale_date DESC
            ''')
            
            daily_sales = [dict(row) for row in cursor.fetchall()]
            
            # Total for period
            cursor.execute(f'''
                SELECT 
                    COUNT(DISTINCT o.id) as total_orders,
                    SUM(oi.quantity) as total_items,
                    SUM(i.price * oi.quantity) as total_revenue,
                    AVG(i.price) as avg_price
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN items i ON oi.item_id = i.id
                WHERE DATE(o.created_at) >= {date_filter}
            ''')
            
            totals = dict(cursor.fetchone())
            
            return {
                'period': period,
                'daily_sales': daily_sales,
                'totals': totals or {'total_orders': 0, 'total_items': 0, 'total_revenue': 0, 'avg_price': 0}
            }
    
    def get_inventory_value_report(self):
        """Get inventory value report"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Value by status
            cursor.execute('''
                SELECT 
                    status,
                    COUNT(*) as item_count,
                    SUM(price) as total_value,
                    AVG(price) as avg_value
                FROM items
                GROUP BY status
            ''')
            
            by_status = [dict(row) for row in cursor.fetchall()]
            
            # Value by location
            cursor.execute('''
                SELECT 
                    l.location_code,
                    COUNT(i.id) as item_count,
                    SUM(i.price) as total_value
                FROM items i
                LEFT JOIN locations l ON i.location_id = l.id
                WHERE i.status = 'in_stock'
                GROUP BY l.location_code
                ORDER BY total_value DESC
            ''')
            
            by_location = [dict(row) for row in cursor.fetchall()]
            
            # Total inventory value
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_items,
                    SUM(price) as total_value
                FROM items
                WHERE status = 'in_stock'
            ''')
            
            totals = dict(cursor.fetchone())
            
            return {
                'by_status': by_status,
                'by_location': by_location,
                'totals': totals
            }
    
    def get_top_items(self, limit=10):
        """Get top selling items (based on actual orders)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    i.article_code,
                    i.description,
                    SUM(oi.quantity) as times_sold,
                    SUM(i.price * oi.quantity) as total_revenue,
                    AVG(i.price) as avg_price
                FROM order_items oi
                JOIN items i ON oi.item_id = i.id
                WHERE i.article_code IS NOT NULL
                GROUP BY i.article_code, i.description
                ORDER BY times_sold DESC, total_revenue DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== BARCODE HISTORY ====================
    
    def save_barcode_generation(self, prefix, start, end, operator='System'):
        """Save barcode generation to history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            count = end - start + 1
            cursor.execute('''
                INSERT INTO barcode_history (prefix, start_number, end_number, count, operator)
                VALUES (?, ?, ?, ?, ?)
            ''', (prefix, start, end, count, operator))
            return cursor.lastrowid
    
    def get_barcode_history(self, limit=20):
        """Get barcode generation history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, prefix, start_number, end_number, count, operator, generated_at
                FROM barcode_history
                ORDER BY generated_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            return [{
                'id': row['id'],
                'prefix': row['prefix'],
                'start': row['start_number'],
                'end': row['end_number'],
                'count': row['count'],
                'operator': row['operator'],
                'timestamp': row['generated_at']
            } for row in rows]
    
    def get_last_barcode_generation(self, prefix=None):
        """Get last barcode generation, optionally filtered by prefix"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if prefix:
                cursor.execute('''
                    SELECT id, prefix, start_number, end_number, count, operator, generated_at
                    FROM barcode_history
                    WHERE prefix = ?
                    ORDER BY generated_at DESC
                    LIMIT 1
                ''', (prefix,))
            else:
                cursor.execute('''
                    SELECT id, prefix, start_number, end_number, count, operator, generated_at
                    FROM barcode_history
                    ORDER BY generated_at DESC
                    LIMIT 1
                ''')
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'prefix': row['prefix'],
                    'start': row['start_number'],
                    'end': row['end_number'],
                    'count': row['count'],
                    'operator': row['operator'],
                    'timestamp': row['generated_at']
                }
            return None
    
    # ==================== CUSTOMERS ====================
    
    def create_customer(self, customer_data):
        """Create new customer"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO customers (name, address, postal_code, city, country, phone, email, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer_data.get('name'),
                customer_data.get('address'),
                customer_data.get('postal_code'),
                customer_data.get('city'),
                customer_data.get('country', 'Sverige'),
                customer_data.get('phone'),
                customer_data.get('email'),
                customer_data.get('notes')
            ))
            return cursor.lastrowid
    
    def get_customer(self, customer_id):
        """Get customer by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def search_customers(self, query):
        """Search customers by name, email, or phone"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            search_term = f"%{query}%"
            cursor.execute('''
                SELECT * FROM customers
                WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
                ORDER BY created_at DESC
                LIMIT 50
            ''', (search_term, search_term, search_term))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_customers(self):
        """Get all customers"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM customers ORDER BY name ASC')
            return [dict(row) for row in cursor.fetchall()]
    
    def update_customer(self, customer_id, customer_data):
        """Update customer"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE customers
                SET name = ?, address = ?, postal_code = ?, city = ?, 
                    country = ?, phone = ?, email = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                customer_data.get('name'),
                customer_data.get('address'),
                customer_data.get('postal_code'),
                customer_data.get('city'),
                customer_data.get('country'),
                customer_data.get('phone'),
                customer_data.get('email'),
                customer_data.get('notes'),
                customer_id
            ))
    
    def get_customer_orders(self, customer_id):
        """Get all orders for a customer"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.*, COUNT(oi.id) as item_count
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                WHERE o.customer_id = ?
                GROUP BY o.id
                ORDER BY o.created_at DESC
            ''', (customer_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== SHIPPING METHODS ====================
    
    def get_shipping_methods(self, active_only=True):
        """Get all shipping methods"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute('SELECT * FROM shipping_methods WHERE active = 1 ORDER BY name ASC')
            else:
                cursor.execute('SELECT * FROM shipping_methods ORDER BY name ASC')
            return [dict(row) for row in cursor.fetchall()]
    
    def create_shipping_method(self, name, description=''):
        """Create new shipping method"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO shipping_methods (name, description)
                VALUES (?, ?)
            ''', (name, description))
            return cursor.lastrowid
    
    def update_shipping_method(self, method_id, name, description, active):
        """Update shipping method"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE shipping_methods
                SET name = ?, description = ?, active = ?
                WHERE id = ?
            ''', (name, description, active, method_id))
    
    def delete_shipping_method(self, method_id):
        """Delete shipping method"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM shipping_methods WHERE id = ?', (method_id,))
    
    # ==================== ORDERS ====================
    
    def generate_order_number(self):
        """Generate next order number (ORD-000001)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(CAST(SUBSTR(order_number, 5) AS INTEGER)) FROM orders')
            result = cursor.fetchone()[0]
            next_num = (result or 0) + 1
            return f"ORD-{next_num:06d}"
    
    def create_order(self, customer_id, item_ids, payment_status='unpaid', 
                     shipping_method=None, tracking_number=None, notes=None):
        """
        Create new order with items
        item_ids can be:
        - List of IDs: [1, 2, 3] (quantity=1 for each)
        - List of tuples: [(1, 2), (3, 1)] (item_id, quantity)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Generate order number
            order_number = self.generate_order_number()
            
            # Normalize item_ids to list of (item_id, quantity) tuples
            normalized_items = []
            for item in item_ids:
                if isinstance(item, tuple):
                    normalized_items.append(item)  # (item_id, qty)
                else:
                    normalized_items.append((item, 1))  # (item_id, 1)
            
            # DEBUG: Print what we received
            print(f"DEBUG: Creating order with items: {normalized_items}")
            
            # Calculate total amount
            total_amount = 0
            for item_id, qty in normalized_items:
                cursor.execute('SELECT price FROM items WHERE id = ?', (item_id,))
                row = cursor.fetchone()
                if row:
                    total_amount += (row[0] or 0) * qty
            
            # Create order
            cursor.execute('''
                INSERT INTO orders (
                    order_number, customer_id, status, payment_status,
                    shipping_method, tracking_number, total_amount, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_number, customer_id, 'pending', payment_status,
                shipping_method, tracking_number, total_amount, notes
            ))
            
            order_id = cursor.lastrowid
            
            # Add items to order with quantities
            for item_id, qty in normalized_items:
                cursor.execute('''
                    INSERT INTO order_items (order_id, item_id, quantity)
                    VALUES (?, ?, ?)
                ''', (order_id, item_id, qty))
                
                # Decrement quantity_available by the ordered quantity
                cursor.execute('''
                    UPDATE items 
                    SET quantity_available = quantity_available - ?,
                        status = CASE 
                            WHEN quantity_available - ? <= 0 THEN 'sold'
                            ELSE 'in_stock'
                        END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (qty, qty, item_id))
                
                # DEBUG: Check what happened
                cursor.execute('SELECT quantity, quantity_available, status FROM items WHERE id = ?', (item_id,))
                item_after = cursor.fetchone()
                print(f"DEBUG: Item {item_id} after update - qty: {item_after[0]}, qty_available: {item_after[1]}, status: {item_after[2]}")
                
                # Update marketplace listings to sold if out of stock
                cursor.execute('''
                    UPDATE marketplace_listings 
                    SET status = 'sold', sold_at = CURRENT_TIMESTAMP
                    WHERE item_id = ? AND status = 'active'
                    AND (SELECT quantity_available FROM items WHERE id = ?) <= 0
                ''', (item_id, item_id))
            
            return order_id, order_number
    
    def get_order(self, order_id):
        """Get order with all details"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get order
            cursor.execute('''
                SELECT o.*, c.name as customer_name, c.address, c.postal_code, 
                       c.city, c.country, c.phone, c.email
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                WHERE o.id = ?
            ''', (order_id,))
            
            order = cursor.fetchone()
            if not order:
                return None
            
            order_dict = dict(order)
            
            # Get items with quantity from order_items
            cursor.execute('''
                SELECT i.*, oi.added_at, oi.quantity as order_quantity
                FROM items i
                JOIN order_items oi ON i.id = oi.item_id
                WHERE oi.order_id = ?
            ''', (order_id,))
            
            items = []
            for row in cursor.fetchall():
                item = dict(row)
                # Use order_quantity instead of item.quantity
                item['quantity'] = item['order_quantity']
                items.append(item)
            
            order_dict['items'] = items
            
            return order_dict
    
    def get_all_orders(self, status=None):
        """Get all orders, optionally filtered by status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT o.*, c.name as customer_name, 
                           COUNT(oi.id) as item_count
                    FROM orders o
                    LEFT JOIN customers c ON o.customer_id = c.id
                    LEFT JOIN order_items oi ON o.id = oi.order_id
                    WHERE o.status = ?
                    GROUP BY o.id
                    ORDER BY o.created_at DESC
                ''', (status,))
            else:
                cursor.execute('''
                    SELECT o.*, c.name as customer_name,
                           COUNT(oi.id) as item_count
                    FROM orders o
                    LEFT JOIN customers c ON o.customer_id = c.id
                    LEFT JOIN order_items oi ON o.id = oi.order_id
                    GROUP BY o.id
                    ORDER BY o.created_at DESC
                ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_order_status(self, order_id, status, timestamp_field=None):
        """Update order status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if timestamp_field:
                cursor.execute(f'''
                    UPDATE orders
                    SET status = ?, {timestamp_field} = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, order_id))
            else:
                cursor.execute('''
                    UPDATE orders SET status = ? WHERE id = ?
                ''', (status, order_id))
            
            # If shipped, update items status
            if status == 'shipped':
                cursor.execute('''
                    UPDATE items
                    SET status = 'shipped'
                    WHERE id IN (
                        SELECT item_id FROM order_items WHERE order_id = ?
                    )
                ''', (order_id,))
    
    def update_order(self, order_id, data):
        """Update order details"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE orders
                SET payment_status = ?, shipping_method = ?, 
                    tracking_number = ?, notes = ?
                WHERE id = ?
            ''', (
                data.get('payment_status'),
                data.get('shipping_method'),
                data.get('tracking_number'),
                data.get('notes'),
                order_id
            ))
