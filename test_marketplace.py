#!/usr/bin/env python3
"""
Test script: Verify marketplace flow
"""

import sqlite3
import json

def test_marketplace_flow():
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("="*60)
    print("MARKETPLACE FLOW TEST")
    print("="*60)
    
    # Step 1: Check items that should show in "not listed"
    print("\n1. ITEMS THAT SHOULD BE IN 'EJ UPPLAGDA':")
    print("   (status = in_stock/uploaded AND NOT in marketplace_listings)")
    
    c.execute('''
        SELECT i.id, i.inventory_id, i.status
        FROM items i
        WHERE i.status IN ('in_stock', 'uploaded')
        AND i.id NOT IN (
            SELECT item_id FROM marketplace_listings WHERE status != 'sold'
        )
        ORDER BY i.created_at DESC
        LIMIT 5
    ''')
    not_listed = c.fetchall()
    
    if not_listed:
        for item in not_listed:
            print(f"   ✓ {item['inventory_id']} (status: {item['status']})")
    else:
        print("   → No items found (all items either sold or already listed)")
    
    # Step 2: Check active marketplace listings
    print("\n2. ACTIVE MARKETPLACE LISTINGS:")
    print("   (status = active in marketplace_listings)")
    
    c.execute('''
        SELECT ml.id, i.inventory_id, ml.marketplace, ml.status, ml.listed_at
        FROM marketplace_listings ml
        JOIN items i ON ml.item_id = i.id
        WHERE ml.status = 'active'
        ORDER BY ml.listed_at DESC
    ''')
    active = c.fetchall()
    
    if active:
        for listing in active:
            print(f"   ✓ {listing['inventory_id']} on {listing['marketplace']} (listed: {listing['listed_at']})")
    else:
        print("   → No active listings")
    
    # Step 3: Check sold listings
    print("\n3. SOLD MARKETPLACE LISTINGS:")
    
    c.execute('''
        SELECT ml.id, i.inventory_id, ml.marketplace, ml.sold_at
        FROM marketplace_listings ml
        JOIN items i ON ml.item_id = i.id
        WHERE ml.status = 'sold'
        ORDER BY ml.sold_at DESC
        LIMIT 5
    ''')
    sold = c.fetchall()
    
    if sold:
        for listing in sold:
            print(f"   ✓ {listing['inventory_id']} on {listing['marketplace']} (sold: {listing['sold_at']})")
    else:
        print("   → No sold listings")
    
    # Step 4: Check statistics
    print("\n4. STATISTICS:")
    
    c.execute('''
        SELECT COUNT(*) as count
        FROM items
        WHERE status IN ('in_stock', 'uploaded')
        AND id NOT IN (
            SELECT item_id FROM marketplace_listings WHERE status != 'sold'
        )
    ''')
    stat_not_listed = c.fetchone()['count']
    
    c.execute("SELECT COUNT(*) FROM marketplace_listings WHERE marketplace = 'blocket' AND status = 'active'")
    stat_blocket = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM marketplace_listings WHERE marketplace = 'tradera' AND status = 'active'")
    stat_tradera = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM marketplace_listings WHERE status = 'sold'")
    stat_sold = c.fetchone()[0]
    
    print(f"   Ej Upplagda: {stat_not_listed}")
    print(f"   Blocket (active): {stat_blocket}")
    print(f"   Tradera (active): {stat_tradera}")
    print(f"   Sålda: {stat_sold}")
    
    # Step 5: Check for any "pending" listings
    print("\n5. CHECKING FOR 'PENDING' LISTINGS (should be 0):")
    
    c.execute("SELECT COUNT(*) FROM marketplace_listings WHERE status = 'pending'")
    pending = c.fetchone()[0]
    
    if pending > 0:
        print(f"   ❌ Found {pending} pending listings - run migrate_fix_marketplace.py")
        
        c.execute('''
            SELECT ml.id, i.inventory_id, ml.marketplace
            FROM marketplace_listings ml
            JOIN items i ON ml.item_id = i.id
            WHERE ml.status = 'pending'
        ''')
        pending_list = c.fetchall()
        for p in pending_list:
            print(f"      → {p['inventory_id']} on {p['marketplace']}")
    else:
        print("   ✓ No pending listings (good!)")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    
    conn.close()

if __name__ == '__main__':
    test_marketplace_flow()
