#!/usr/bin/env python3
"""
Migration: Fix marketplace listings with 'pending' status
Change all 'pending' to 'active' so they show up in the UI
"""

import sqlite3

def migrate():
    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    
    try:
        # Check how many pending listings exist
        c.execute("SELECT COUNT(*) FROM marketplace_listings WHERE status = 'pending'")
        pending_count = c.fetchone()[0]
        
        if pending_count > 0:
            print(f"Found {pending_count} listings with status 'pending'")
            print("Updating to 'active'...")
            
            c.execute("UPDATE marketplace_listings SET status = 'active' WHERE status = 'pending'")
            conn.commit()
            
            print(f"✓ Updated {pending_count} listings to 'active'")
        else:
            print("✓ No pending listings found")
        
        # Show all listings
        c.execute("""
            SELECT ml.id, i.inventory_id, ml.marketplace, ml.status, ml.listed_at
            FROM marketplace_listings ml
            JOIN items i ON ml.item_id = i.id
            ORDER BY ml.listed_at DESC
        """)
        listings = c.fetchall()
        
        if listings:
            print(f"\n=== ALL MARKETPLACE LISTINGS ({len(listings)}) ===")
            for listing in listings:
                print(f"  {listing[1]}: {listing[2]} - {listing[3]} (listed: {listing[4]})")
        else:
            print("\n=== NO MARKETPLACE LISTINGS ===")
        
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
