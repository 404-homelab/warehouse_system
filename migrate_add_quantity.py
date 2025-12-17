#!/usr/bin/env python3
"""
Migration: Add quantity columns to items and order_items tables
"""

import sqlite3

def migrate():
    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    
    try:
        # Check items table
        c.execute("PRAGMA table_info(items)")
        items_cols = [col[1] for col in c.fetchall()]
        
        if 'quantity' not in items_cols:
            print("Adding 'quantity' column to items...")
            c.execute('ALTER TABLE items ADD COLUMN quantity INTEGER DEFAULT 1')
            print("✓ Added quantity column to items")
        else:
            print("✓ items.quantity already exists")
        
        if 'quantity_available' not in items_cols:
            print("Adding 'quantity_available' column to items...")
            c.execute('ALTER TABLE items ADD COLUMN quantity_available INTEGER DEFAULT 1')
            print("✓ Added quantity_available column to items")
        else:
            print("✓ items.quantity_available already exists")
        
        # Check order_items table
        c.execute("PRAGMA table_info(order_items)")
        order_items_cols = [col[1] for col in c.fetchall()]
        
        if 'quantity' not in order_items_cols:
            print("Adding 'quantity' column to order_items...")
            c.execute('ALTER TABLE order_items ADD COLUMN quantity INTEGER DEFAULT 1')
            print("✓ Added quantity column to order_items")
        else:
            print("✓ order_items.quantity already exists")
        
        # Update existing items to have quantity = 1
        c.execute('UPDATE items SET quantity = 1 WHERE quantity IS NULL')
        c.execute('UPDATE items SET quantity_available = 1 WHERE quantity_available IS NULL')
        c.execute('UPDATE order_items SET quantity = 1 WHERE quantity IS NULL')
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\nYou can now:")
        print("  - Register bulk items with quantity > 1")
        print("  - Add multiple of same item to orders")
        print("  - Track available quantity per item")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
