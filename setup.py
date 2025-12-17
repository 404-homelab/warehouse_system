#!/usr/bin/env python3
"""
Warehouse Management System - Setup Script
Automatically initializes the database and creates necessary directories
"""
import os
import sys

def setup():
    print("=" * 60)
    print("  WAREHOUSE MANAGEMENT SYSTEM - SETUP")
    print("=" * 60)
    print()
    
    # Create necessary directories
    directories = [
        'static/uploads',
        'static/barcodes',
        'static/exports',
        'static/css',
        'static/js'
    ]
    
    print("📁 Creating directories...")
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✓ {directory}")
    
    print()
    print("🗄️  Initializing database...")
    
    try:
        from database import Database
        db = Database()
        db.init_db()
        print("   ✓ Database initialized successfully!")
        
        # Add some sample data
        print()
        print("📦 Adding sample data...")
        
        # Add sample locations
        sample_locations = [
            ("A1", "LOC-A1-001", "Hylla A, rad 1"),
            ("A2", "LOC-A2-001", "Hylla A, rad 2"),
            ("B1", "LOC-B1-001", "Hylla B, rad 1"),
            ("B2", "LOC-B2-001", "Hylla B, rad 2"),
        ]
        
        for code, barcode, desc in sample_locations:
            try:
                db.create_location(code, barcode, desc)
                print(f"   ✓ Created location: {code}")
            except:
                pass  # Location already exists
        
        # Add sample box sizes
        sample_boxes = [
            ("Liten Kartong", 20, 15, 10, 5),
            ("Mellan Kartong", 40, 30, 20, 15),
            ("Stor Kartong", 60, 40, 40, 25),
        ]
        
        for name, length, width, height, weight in sample_boxes:
            try:
                db.create_box_size(name, length, width, height, weight)
                print(f"   ✓ Created box size: {name}")
            except:
                pass  # Box size already exists
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    print()
    print("=" * 60)
    print("  ✅ SETUP COMPLETE!")
    print("=" * 60)
    print()
    print("To start the application, run:")
    print()
    print("    python app.py")
    print()
    print("Then open your browser to: http://localhost:5000")
    print()
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = setup()
    sys.exit(0 if success else 1)
