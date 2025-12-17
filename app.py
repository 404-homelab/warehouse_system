"""
Warehouse Management System
Main Flask Application
"""
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import os
from database import Database
from camera_handler import CameraHandler
from barcode_generator import BarcodeGenerator
from pdf_generator import PDFGenerator
from image_processor import ImageProcessor
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialize components
db = Database()
camera = CameraHandler()
barcode_gen = BarcodeGenerator()
pdf_gen = PDFGenerator()
img_processor = ImageProcessor()

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/barcodes', exist_ok=True)
os.makedirs('static/exports', exist_ok=True)


# ==================== WEB ROUTES ====================

@app.route('/')
def index():
    """Dashboard"""
    return render_template('dashboard.html')


@app.route('/register')
def register():
    """Product registration page"""
    return render_template('register.html')


@app.route('/orders')
def orders():
    """Orders list page"""
    return render_template('orders_list.html')


@app.route('/orders/new')
def orders_new():
    """Create new order page"""
    return render_template('orders_new.html')


@app.route('/orders/<int:order_id>/edit')
def orders_edit(order_id):
    """Edit order page"""
    return render_template('orders_edit.html', order_id=order_id)


@app.route('/packing')
def packing():
    """Packing page"""
    return render_template('packing.html')


@app.route('/search')
def search():
    """Search page"""
    return render_template('search.html')


@app.route('/marketplace')
def marketplace():
    """Marketplace management page"""
    return render_template('marketplace.html')


@app.route('/admin')
def admin():
    """Admin page"""
    return render_template('admin.html')


@app.route('/reports')
def reports():
    """Reports and analytics page"""
    return render_template('reports.html')


# ==================== API: ITEMS ====================

@app.route('/api/items', methods=['POST'])
def create_item():
    """Create a new item"""
    try:
        data = request.json
        
        # Generate inventory ID
        inventory_id = db.generate_inventory_id()
        
        # Create item
        item_data = {
            'inventory_id': inventory_id,
            'article_code': data.get('article_code'),
            'description': data.get('description'),
            'condition': data.get('condition'),
            'length': data.get('length'),
            'width': data.get('width'),
            'height': data.get('height'),
            'weight': data.get('weight'),
            'price': data.get('price'),
            'location_id': data.get('location_id'),
            'notes': data.get('notes')
        }
        
        item_id = db.create_item(item_data)
        
        # Save images if provided
        images = data.get('images', [])
        print(f"DEBUG: Received {len(images) if images else 0} images")
        
        if images and len(images) > 0:
            import base64
            import os
            from datetime import datetime
            
            for idx, img_data in enumerate(images):
                print(f"DEBUG: Processing image {idx}, type: {type(img_data)}")
                
                # Images come as {data: "data:image/jpeg;base64,...", cropped: "filename or null"}
                img_base64_str = None
                cropped_filename = None
                
                if isinstance(img_data, dict):
                    # Get the image data
                    img_base64_str = img_data.get('data')
                    cropped_filename = img_data.get('cropped')
                    print(f"DEBUG: Dict image - has data: {bool(img_base64_str)}, cropped: {cropped_filename}")
                    
                    # If already cropped and saved, just reference the existing file
                    if cropped_filename and cropped_filename != 'null':
                        # Extract just the filename from path if it's a full path
                        filename_only = os.path.basename(cropped_filename)
                        print(f"DEBUG: Using cropped file: {filename_only}")
                        db.add_image_to_item(item_id, filename_only, filename_only)
                        continue
                elif isinstance(img_data, str):
                    # Direct base64 string
                    img_base64_str = img_data
                    print(f"DEBUG: String image, starts with data:image: {img_base64_str[:20] if img_base64_str else 'None'}")
                
                # Save the image from base64 data
                if img_base64_str and img_base64_str.startswith('data:image'):
                    try:
                        # Extract base64 data
                        img_base64 = img_base64_str.split(',')[1]
                        img_bytes = base64.b64decode(img_base64)
                        
                        # Generate filename
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename_original = f"{inventory_id}_{idx}_{timestamp}.png"
                        filepath = os.path.join('static/uploads', filename_original)
                        
                        print(f"DEBUG: Saving image to: {filepath}, size: {len(img_bytes)} bytes")
                        
                        # Save original image
                        with open(filepath, 'wb') as f:
                            f.write(img_bytes)
                        
                        # Save to database
                        db.add_image_to_item(item_id, filename_original, None)
                        print(f"DEBUG: Image saved to database: {filename_original}")
                    except Exception as img_error:
                        print(f"ERROR saving image {idx}: {img_error}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"DEBUG: Skipping image {idx} - no valid data")
        
        # Generate barcode
        barcode_path = barcode_gen.generate_item_barcode(inventory_id)
        
        # Log action
        db.log_action('CREATE_ITEM', inventory_id, data.get('operator', 'System'), 
                     f"Created item: {data.get('description')}")
        
        return jsonify({
            'success': True,
            'item_id': item_id,
            'inventory_id': inventory_id,
            'barcode_path': barcode_path,
            'images_saved': len(images) if images else 0
        }), 201
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/items/bulk', methods=['POST'])
def create_items_bulk():
    """Create single item with quantity tracking"""
    try:
        data = request.json
        quantity = int(data.get('quantity', 1))
        images = data.get('images', [])
        
        # Generate ONE inventory ID for all units
        inventory_id = db.generate_inventory_id()
        
        item_data = {
            'inventory_id': inventory_id,
            'article_code': data.get('article_code'),
            'description': data.get('description'),
            'condition': data.get('condition'),
            'length': data.get('length'),
            'width': data.get('width'),
            'height': data.get('height'),
            'weight': data.get('weight'),
            'price': data.get('price'),
            'location_id': data.get('location_id'),
            'notes': data.get('notes'),
            'quantity': quantity  # Store total quantity
        }
        
        item_id = db.create_item(item_data)
        
        # Save images for this item
        if images and len(images) > 0:
            import base64
            import os
            from datetime import datetime
            
            for idx, img_data in enumerate(images):
                img_base64_str = None
                cropped_filename = None
                
                if isinstance(img_data, dict):
                    img_base64_str = img_data.get('data')
                    cropped_filename = img_data.get('cropped')
                    
                    if cropped_filename and cropped_filename != 'null':
                        filename_only = os.path.basename(cropped_filename)
                        db.add_image_to_item(item_id, filename_only, filename_only)
                        continue
                elif isinstance(img_data, str):
                    img_base64_str = img_data
                
                if img_base64_str and img_base64_str.startswith('data:image'):
                    try:
                        img_base64 = img_base64_str.split(',')[1]
                        img_bytes = base64.b64decode(img_base64)
                        
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename_original = f"{inventory_id}_{idx}_{timestamp}.png"
                        filepath = os.path.join('static/uploads', filename_original)
                        
                        with open(filepath, 'wb') as f:
                            f.write(img_bytes)
                        
                        db.add_image_to_item(item_id, filename_original, None)
                    except Exception as img_error:
                        print(f"Error saving image for {inventory_id}: {img_error}")
        
        # Generate ONE barcode for the shared INV ID
        barcode_path = barcode_gen.generate_item_barcode(inventory_id)
        
        db.log_action('CREATE_ITEM', inventory_id, data.get('operator', 'System'),
                     f"Bulk created: {quantity}x {data.get('description')}")
        
        return jsonify({
            'success': True,
            'item_id': item_id,
            'inventory_id': inventory_id,
            'quantity': quantity,
            'barcode_path': barcode_path
        }), 201
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400
        
        return jsonify({
            'success': True,
            'items': created_items,
            'count': len(created_items)
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/items/<inventory_id>', methods=['GET'])
def get_item(inventory_id):
    """Get item by inventory ID"""
    try:
        item = db.get_item_by_inventory_id(inventory_id)
        if item:
            return jsonify({'success': True, 'item': item})
        else:
            return jsonify({'success': False, 'error': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/items/<int:item_id>/location', methods=['PUT'])
def update_item_location(item_id):
    """Update item location"""
    try:
        data = request.json
        location_id = data.get('location_id')
        
        db.update_item_location(item_id, location_id)
        db.log_action('UPDATE_LOCATION', None, data.get('operator', 'System'),
                     f"Updated location for item ID {item_id}")
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/items/<int:item_id>/status', methods=['PUT'])
def update_item_status(item_id):
    """Update item status"""
    try:
        data = request.json
        status = data.get('status')
        
        db.update_item_status(item_id, status)
        db.log_action('UPDATE_STATUS', None, data.get('operator', 'System'),
                     f"Updated status to {status} for item ID {item_id}")
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== API: LOCATIONS ====================

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Get all locations"""
    try:
        locations = db.get_all_locations()
        return jsonify({'success': True, 'locations': locations})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/locations', methods=['POST'])
def create_location():
    """Create new location"""
    try:
        data = request.json
        location_code = data.get('location_code')
        barcode_value = data.get('barcode_value')  # Now user-provided
        description = data.get('description', '')
        
        if not location_code or not barcode_value:
            return jsonify({'success': False, 'error': 'Location code and barcode are required'}), 400
        
        location_id = db.create_location(location_code, barcode_value, description)
        
        # Generate physical barcode image
        barcode_path = barcode_gen.generate_location_barcode(barcode_value)
        
        db.log_action('CREATE_LOCATION', None, data.get('operator', 'System'),
                     f"Created location: {location_code} with barcode {barcode_value}")
        
        return jsonify({
            'success': True,
            'location_id': location_id,
            'barcode_path': barcode_path
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/locations/<int:location_id>', methods=['DELETE'])
def delete_location(location_id):
    """Delete location"""
    try:
        db.delete_location(location_id)
        db.log_action('DELETE_LOCATION', None, request.args.get('operator', 'System'),
                     f"Deleted location ID {location_id}")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/locations/scan', methods=['POST'])
def scan_location():
    """Scan location barcode"""
    try:
        data = request.json
        barcode_value = data.get('barcode_value')
        
        location = db.get_location_by_barcode(barcode_value)
        if location:
            return jsonify({'success': True, 'location': location})
        else:
            return jsonify({'success': False, 'error': 'Location not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== API: ORDERS ====================

# ==================== API: CUSTOMERS ====================


@app.route('/api/orders/next', methods=['GET'])
def get_next_order():
    """Get next order to pack"""
    try:
        order = db.get_next_order_to_pack()
        if order:
            return jsonify({'success': True, 'order': order})
        else:
            return jsonify({'success': False, 'message': 'No pending orders'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/orders/<int:order_id>/ship', methods=['POST'])
def ship_order(order_id):
    """Mark order as shipped"""
    try:
        data = request.json
        
        db.ship_order(order_id)
        
        # Update all items in order to shipped status
        items = db.get_order_items(order_id)
        for item in items:
            db.update_item_status(item['id'], 'shipped')
        
        db.log_action('SHIP_ORDER', None, data.get('operator', 'System'),
                     f"Shipped order ID {order_id}")
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """Delete order"""
    try:
        # Get items first to reset their status
        items = db.get_order_items(order_id)
        
        db.delete_order(order_id)
        
        # Reset item statuses
        for item in items:
            db.update_item_status(item['id'], 'in_stock')
        
        db.log_action('DELETE_ORDER', None, request.args.get('operator', 'System'),
                     f"Deleted order ID {order_id}")
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/orders/<int:order_id>/items', methods=['GET'])
def get_order_items(order_id):
    """Get items in an order"""
    try:
        items = db.get_order_items(order_id)
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/orders/<int:order_id>/box-suggestion', methods=['GET'])
def get_box_suggestion(order_id):
    """Get box size suggestion for order"""
    try:
        items = db.get_order_items(order_id)
        suggestion = db.suggest_box_size(items)
        return jsonify({'success': True, 'suggestion': suggestion})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== API: CAMERA & IMAGES ====================

@app.route('/api/image/upload', methods=['POST'])
def upload_image():
    """Upload and process image"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        file = request.files['image']
        item_id = request.form.get('item_id')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Save original
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Auto-crop
        cropped_filename = f"cropped_{filename}"
        cropped_filepath = os.path.join(app.config['UPLOAD_FOLDER'], cropped_filename)
        
        success = img_processor.auto_crop_image(filepath, cropped_filepath)
        
        if success and item_id:
            db.add_image(item_id, filename, cropped_filename)
        
        return jsonify({
            'success': True,
            'original': f'/static/uploads/{filename}',
            'cropped': f'/static/uploads/{cropped_filename}' if success else None
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/image/crop', methods=['POST'])
def crop_image():
    """Auto-crop an image"""
    try:
        data = request.json
        image_path = data.get('image_path')
        padding = data.get('padding', 10)
        min_area = data.get('min_area', 1000)
        
        # Remove leading slash if present
        if image_path.startswith('/'):
            image_path = image_path[1:]
        
        output_path = image_path.replace('uploads/', 'uploads/cropped_')
        
        success = img_processor.auto_crop_image(
            image_path, 
            output_path,
            padding=padding,
            min_area=min_area
        )
        
        if success:
            return jsonify({
                'success': True,
                'cropped_path': f'/{output_path}'
            })
        else:
            return jsonify({'success': False, 'error': 'Cropping failed'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== API: BOX SIZES ====================

@app.route('/api/box-sizes', methods=['GET'])
def get_box_sizes():
    """Get all box sizes"""
    try:
        boxes = db.get_all_box_sizes()
        return jsonify({'success': True, 'boxes': boxes})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/box-sizes', methods=['POST'])
def create_box_size():
    """Create new box size"""
    try:
        data = request.json
        
        box_id = db.create_box_size(
            data.get('name'),
            data.get('inner_length'),
            data.get('inner_width'),
            data.get('inner_height'),
            data.get('max_weight')
        )
        
        return jsonify({'success': True, 'box_id': box_id}), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/box-sizes/<int:box_id>', methods=['DELETE'])
def delete_box_size(box_id):
    """Delete box size"""
    try:
        db.delete_box_size(box_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== API: MARKETPLACE ====================

@app.route('/api/marketplace/listings', methods=['GET'])
def get_marketplace_listings():
    """Get marketplace listings"""
    try:
        status = request.args.get('status')
        marketplace = request.args.get('marketplace')
        listings = db.get_marketplace_listings(status, marketplace)
        return jsonify({'success': True, 'listings': listings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/marketplace/listings', methods=['POST'])
def create_marketplace_listing():
    """Create marketplace listing"""
    try:
        data = request.json
        
        listing_id = db.create_marketplace_listing(
            data.get('item_id'),
            data.get('marketplace'),
            data.get('status', 'active')  # Changed from 'pending' to 'active'
        )
        
        # Update item status
        db.update_item_status(data.get('item_id'), 'uploaded')
        
        db.log_action('CREATE_LISTING', None, data.get('operator', 'System'),
                     f"Created {data.get('marketplace')} listing for item {data.get('item_id')}")
        
        return jsonify({'success': True, 'listing_id': listing_id}), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/marketplace/listings/<int:listing_id>/status', methods=['PUT'])
def update_listing_status(listing_id):
    """Update listing status"""
    try:
        data = request.json
        status = data.get('status')
        
        db.update_marketplace_listing_status(listing_id, status)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/marketplace/listings/<int:listing_id>/mark-sold', methods=['POST'])
def mark_listing_sold(listing_id):
    """Mark listing as sold (only if quantity_available = 0 for bulk items)"""
    try:
        # Get listing info
        listing = db.get_marketplace_listing_by_id(listing_id)
        if not listing:
            return jsonify({'success': False, 'error': 'Listing not found'}), 404
        
        # Get item info to check quantity_available
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT quantity_available, quantity
                FROM items
                WHERE id = ?
            ''', (listing['item_id'],))
            item = cursor.fetchone()
            
            if not item:
                return jsonify({'success': False, 'error': 'Item not found'}), 404
            
            quantity_available = item[0] or 0
            
            # Only mark as sold if quantity_available is 0
            if quantity_available <= 0:
                # Update listing status to sold
                db.update_marketplace_listing_status(listing_id, 'sold')
                
                # Update item status to sold
                db.update_item_status(listing['item_id'], 'sold')
                
                db.log_action('MARK_SOLD', None, 'User',
                             f"Marked {listing['marketplace']} listing {listing_id} as sold (qty=0)")
            else:
                # Partial sale - listing remains active
                db.log_action('PARTIAL_SALE', None, 'User',
                             f"Listing {listing_id} partially sold ({quantity_available} remaining)")
        
        return jsonify({'success': True, 'quantity_remaining': quantity_available})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/marketplace/not-listed', methods=['GET'])
def get_not_listed_items():
    """Get items that are not listed on any marketplace"""
    try:
        # Get all items that are in_stock or uploaded but not in marketplace_listings
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT i.*, l.location_code,
                       (SELECT filename_original FROM images WHERE item_id = i.id LIMIT 1) as image_original,
                       (SELECT filename_cropped FROM images WHERE item_id = i.id LIMIT 1) as image_cropped
                FROM items i
                LEFT JOIN locations l ON i.location_id = l.id
                WHERE i.status IN ('in_stock', 'uploaded')
                AND i.id NOT IN (
                    SELECT item_id FROM marketplace_listings WHERE status != 'sold'
                )
                ORDER BY i.created_at DESC
            ''')
            
            items = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/marketplace/statistics', methods=['GET'])
def get_marketplace_statistics():
    """Get marketplace statistics"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Not listed items
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM items
                WHERE status IN ('in_stock', 'uploaded')
                AND id NOT IN (
                    SELECT item_id FROM marketplace_listings WHERE status != 'sold'
                )
            ''')
            not_listed = cursor.fetchone()['count']
            
            # Blocket listings
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM marketplace_listings
                WHERE marketplace = 'blocket' AND status = 'active'
            ''')
            blocket = cursor.fetchone()['count']
            
            # Tradera listings
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM marketplace_listings
                WHERE marketplace = 'tradera' AND status = 'active'
            ''')
            tradera = cursor.fetchone()['count']
            
            # Sold through marketplace
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM marketplace_listings
                WHERE status = 'sold'
            ''')
            sold = cursor.fetchone()['count']
        
        stats = {
            'not_listed': not_listed,
            'blocket': blocket,
            'tradera': tradera,
            'sold': sold
        }
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== API: EXPORT ====================

@app.route('/api/export/images', methods=['POST'])
def export_images():
    """Export images as ZIP"""
    try:
        data = request.json
        item_ids = data.get('item_ids', [])
        
        zip_path = pdf_gen.export_images_zip(item_ids, db)
        
        return send_file(zip_path, as_attachment=True, 
                        download_name=f'images_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip')
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/export/pdf/labels', methods=['POST'])
def export_labels_pdf():
    """Export labels as PDF"""
    try:
        data = request.json
        inventory_ids = data.get('inventory_ids', [])
        
        pdf_path = pdf_gen.generate_labels_pdf(inventory_ids)
        
        return send_file(pdf_path, as_attachment=True,
                        download_name=f'labels_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/export/pdf/location-labels', methods=['POST'])
def export_location_labels_pdf():
    """Export location labels as PDF"""
    try:
        data = request.json
        barcode_values = data.get('barcode_values', [])
        
        pdf_path = pdf_gen.generate_location_labels_pdf(barcode_values)
        
        return send_file(pdf_path, as_attachment=True,
                        download_name=f'location_labels_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/barcodes/bulk-generate', methods=['POST'])
def bulk_generate_barcodes():
    """Generate bulk barcodes"""
    try:
        data = request.json
        prefix = data.get('prefix', 'CODE')
        start = int(data.get('start', 1))
        end = int(data.get('end', 10))
        operator = data.get('operator', 'System')
        
        pdf_path = barcode_gen.generate_bulk_barcodes_pdf(prefix, start, end)
        
        # Save to history
        db.save_barcode_generation(prefix, start, end, operator)
        
        return send_file(pdf_path, as_attachment=True,
                        download_name=f'barcodes_{prefix}_{start}-{end}.pdf')
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/barcodes/history', methods=['GET'])
def get_barcode_history():
    """Get barcode generation history"""
    try:
        limit = request.args.get('limit', 20, type=int)
        history = db.get_barcode_history(limit)
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/barcodes/last', methods=['GET'])
def get_last_barcode():
    """Get last barcode generation"""
    try:
        prefix = request.args.get('prefix', None)
        last = db.get_last_barcode_generation(prefix)
        
        return jsonify({
            'success': True,
            'last': last
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== API: SHIPPING METHODS ====================

@app.route('/api/shipping-methods', methods=['GET'])
def get_shipping_methods():
    """Get all shipping methods"""
    try:
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        methods = db.get_shipping_methods(active_only)
        
        return jsonify({
            'success': True,
            'methods': methods
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/shipping-methods', methods=['POST'])
def create_shipping_method():
    """Create new shipping method"""
    try:
        data = request.json
        method_id = db.create_shipping_method(
            data.get('name'),
            data.get('description', '')
        )
        
        return jsonify({
            'success': True,
            'method_id': method_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/shipping-methods/<int:method_id>', methods=['PUT'])
def update_shipping_method(method_id):
    """Update shipping method"""
    try:
        data = request.json
        
        # Get current method first
        methods = db.get_shipping_methods(active_only=False)
        method = next((m for m in methods if m['id'] == method_id), None)
        
        if not method:
            return jsonify({'success': False, 'error': 'Method not found'}), 404
        
        db.update_shipping_method(
            method_id,
            data.get('name', method['name']),
            data.get('description', method['description']),
            data.get('active', method['active'])
        )
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/shipping-methods/<int:method_id>', methods=['DELETE'])
def delete_shipping_method(method_id):
    """Delete shipping method"""
    try:
        db.delete_shipping_method(method_id)
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== API: CUSTOMERS ====================

@app.route('/api/customers/search', methods=['GET'])
def search_customers():
    """Search customers"""
    try:
        query = request.args.get('q', '')
        customers = db.search_customers(query)
        
        return jsonify({
            'success': True,
            'customers': customers
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/customers', methods=['GET'])
def get_all_customers():
    """Get all customers"""
    try:
        customers = db.get_all_customers()
        return jsonify({
            'success': True,
            'customers': customers
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/customers', methods=['POST'])
def create_customer():
    """Create or update customer"""
    try:
        data = request.json
        customer_data = data.get('customer', {})
        
        # Check if updating existing customer
        customer_id = customer_data.get('id')
        
        if customer_id:
            # Update existing
            db.update_customer(customer_id, customer_data)
            return jsonify({
                'success': True,
                'customer_id': customer_id
            })
        else:
            # Create new
            customer_id = db.create_customer(customer_data)
            return jsonify({
                'success': True,
                'customer_id': customer_id
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get customer by ID"""
    try:
        customer = db.get_customer(customer_id)
        
        if not customer:
            return jsonify({'success': False, 'error': 'Customer not found'}), 404
        
        return jsonify({
            'success': True,
            'customer': customer
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== API: ORDERS ====================

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create new order"""
    try:
        data = request.json
        
        # Handle customer
        customer_data = data.get('customer', {})
        customer_id = customer_data.get('id')
        
        if not customer_id:
            # Create new customer
            customer_id = db.create_customer(customer_data)
        else:
            # Update existing customer
            db.update_customer(customer_id, customer_data)
        
        # Handle items - can be either:
        # 1. Simple list: [1, 2, 3] (old format)
        # 2. With quantities: [{id: 1, quantity: 2}, {id: 3, quantity: 1}] (new format)
        items_input = data.get('items') or data.get('item_ids', [])
        item_ids = []
        
        for item in items_input:
            if isinstance(item, dict):
                # New format: {id: X, quantity: Y}
                item_ids.append((item['id'], item.get('quantity', 1)))
            else:
                # Old format: just ID
                item_ids.append((item, 1))
        
        # Create order
        order_id, order_number = db.create_order(
            customer_id=customer_id,
            item_ids=item_ids,  # Now list of (id, qty) tuples
            payment_status=data.get('payment_status', 'unpaid'),
            shipping_method=data.get('shipping_method'),
            tracking_number=data.get('tracking_number'),
            notes=data.get('notes')
        )
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'order_number': order_number
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get all orders"""
    try:
        status = request.args.get('status')
        orders = db.get_all_orders(status)
        
        return jsonify({
            'success': True,
            'orders': orders
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get order details"""
    try:
        order = db.get_order(order_id)
        
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        return jsonify({
            'success': True,
            'order': order
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    """Update order"""
    try:
        data = request.json
        
        # Update order details
        if 'status' in data:
            timestamp_field = None
            if data['status'] == 'confirmed':
                timestamp_field = 'confirmed_at'
            elif data['status'] == 'packed':
                timestamp_field = 'packed_at'
            elif data['status'] == 'shipped':
                timestamp_field = 'shipped_at'
            
            db.update_order_status(order_id, data['status'], timestamp_field)
        
        # Update other fields
        db.update_order(order_id, data)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/items/search', methods=['GET'])
def search_items():
    """Search items by inventory_id or description"""
    try:
        query = request.args.get('q', '')
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            search_term = f"%{query}%"
            
            cursor.execute('''
                SELECT i.*, l.location_code,
                       (SELECT filename_original FROM images WHERE item_id = i.id LIMIT 1) as image_original,
                       (SELECT filename_cropped FROM images WHERE item_id = i.id LIMIT 1) as image_cropped
                FROM items i
                LEFT JOIN locations l ON i.location_id = l.id
                WHERE (i.inventory_id LIKE ? OR i.description LIKE ?)
                ORDER BY i.created_at DESC
                LIMIT 50
            ''', (search_term, search_term))
            
            items = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'items': items
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== API: PDF EXPORTS ====================

@app.route('/api/export/pdf/packing-slip/<int:order_id>')
def export_packing_slip(order_id):
    """Export packing slip PDF for an order"""
    try:
        order = db.get_order(order_id)
        
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        import tempfile
        import os
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_path = temp_file.name
        temp_file.close()
        
        # Create PDF
        c = canvas.Canvas(temp_path, pagesize=A4)
        width, height = A4
        
        # Title
        c.setFont("Helvetica-Bold", 20)
        c.drawString(30*mm, height - 30*mm, "PACKLISTA")
        
        # Order info
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30*mm, height - 45*mm, f"Order: {order['order_number']}")
        
        c.setFont("Helvetica", 10)
        y = height - 55*mm
        c.drawString(30*mm, y, f"Datum: {order['created_at'][:10]}")
        
        # Customer info
        y -= 15*mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30*mm, y, "Mottagare:")
        
        c.setFont("Helvetica", 10)
        y -= 5*mm
        c.drawString(30*mm, y, order['customer_name'] or 'Okänd')
        y -= 4*mm
        c.drawString(30*mm, y, order['address'] or '')
        y -= 4*mm
        c.drawString(30*mm, y, f"{order['postal_code'] or ''} {order['city'] or ''}")
        y -= 4*mm
        c.drawString(30*mm, y, order['country'] or 'Sverige')
        
        # Shipping info
        if order.get('shipping_method'):
            y -= 8*mm
            c.setFont("Helvetica-Bold", 10)
            c.drawString(30*mm, y, f"Fraktmetod: {order['shipping_method']}")
        
        if order.get('tracking_number'):
            y -= 5*mm
            c.setFont("Helvetica", 10)
            c.drawString(30*mm, y, f"Spårningsnr: {order['tracking_number']}")
        
        # Items table
        y -= 15*mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30*mm, y, "Varor att packa:")
        
        y -= 8*mm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(30*mm, y, "Inventory ID")
        c.drawString(80*mm, y, "Beskrivning")
        c.drawString(150*mm, y, "Plats")
        
        y -= 2*mm
        c.line(30*mm, y, width - 30*mm, y)
        
        y -= 5*mm
        c.setFont("Helvetica", 9)
        
        for item in order.get('items', []):
            if y < 30*mm:  # New page if needed
                c.showPage()
                y = height - 30*mm
                c.setFont("Helvetica", 9)
            
            c.drawString(30*mm, y, item.get('inventory_id', ''))
            
            # Wrap description if too long
            desc = item.get('description', '')[:40]
            c.drawString(80*mm, y, desc)
            
            location = item.get('location_code', 'N/A')
            c.drawString(150*mm, y, location)
            
            # Checkbox
            c.rect(170*mm, y - 2*mm, 4*mm, 4*mm)
            
            y -= 6*mm
        
        # Total
        y -= 5*mm
        c.line(30*mm, y, width - 30*mm, y)
        y -= 6*mm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(30*mm, y, f"Totalt antal varor: {len(order.get('items', []))}")
        c.drawString(120*mm, y, f"Totalbelopp: {int(order.get('total_amount', 0))} kr")
        
        # Footer
        c.setFont("Helvetica", 8)
        c.drawString(30*mm, 20*mm, "Packad av: _________________")
        c.drawString(100*mm, 20*mm, "Datum: _________________")
        
        c.save()
        
        # Send file
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=f'packlista_{order["order_number"]}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== API: REPORTS ====================

@app.route('/api/reports/statistics', methods=['GET'])
def get_statistics():
    """Get system statistics"""
    try:
        stats = db.get_statistics()
        return jsonify({'success': True, 'statistics': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/reports/sales', methods=['GET'])
def get_sales_report():
    """Get sales report"""
    try:
        period = request.args.get('period', 'month')  # day, week, month, year
        sales = db.get_sales_report(period)
        return jsonify({'success': True, 'sales': sales})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/reports/inventory-value', methods=['GET'])
def get_inventory_value():
    """Get inventory value report"""
    try:
        value_report = db.get_inventory_value_report()
        return jsonify({'success': True, 'report': value_report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/reports/activity', methods=['GET'])
def get_activity_log():
    """Get recent activity"""
    try:
        limit = int(request.args.get('limit', 50))
        activity = db.get_recent_activity(limit)
        return jsonify({'success': True, 'activity': activity})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/reports/top-items', methods=['GET'])
def get_top_items():
    """Get top selling items"""
    try:
        limit = int(request.args.get('limit', 10))
        top_items = db.get_top_items(limit)
        return jsonify({'success': True, 'items': top_items})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== UPDATE MANAGEMENT ====================

@app.route('/admin/updates')
def admin_updates():
    """Update management page"""
    return render_template('admin_updates.html')


@app.route('/api/update/config', methods=['GET'])
def get_update_config():
    """Get current update configuration"""
    try:
        import subprocess
        
        # Get current version
        version = '1.0.0'
        if os.path.exists('VERSION'):
            with open('VERSION', 'r') as f:
                version = f.read().strip()
        
        # Load config
        config = {}
        if os.path.exists('update_config.json'):
            with open('update_config.json', 'r') as f:
                config = json.load(f)
        
        config['current_version'] = version
        
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/update/config', methods=['POST'])
def save_update_config():
    """Save update configuration"""
    try:
        data = request.json
        
        # Load existing config or create new
        config = {}
        if os.path.exists('update_config.json'):
            with open('update_config.json', 'r') as f:
                config = json.load(f)
        
        # Update config
        config.update(data)
        
        # Save
        with open('update_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        # Log action
        db.log_action('UPDATE_CONFIG', None, 'Admin', 
                     f"Updated configuration: channel={data.get('channel')}, auto_update={data.get('auto_update')}")
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/update/schedule', methods=['POST'])
def save_update_schedule():
    """Save update schedule"""
    try:
        data = request.json
        
        # Load existing config
        config = {}
        if os.path.exists('update_config.json'):
            with open('update_config.json', 'r') as f:
                config = json.load(f)
        
        # Update schedule settings
        config.update(data)
        
        # Save
        with open('update_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        db.log_action('UPDATE_SCHEDULE', None, 'Admin', 
                     f"Updated schedule: time={data.get('preferred_time')}, days={len(data.get('allowed_days', []))}")
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/update/check', methods=['GET'])
def check_for_updates():
    """Check if updates are available"""
    try:
        import subprocess
        import sys
        
        # Run update client check
        result = subprocess.run(
            [sys.executable, 'update_client.py', '--check'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Parse output to determine if update available
        # This is a simplified version - update_client.py should be modified to output JSON
        
        # For now, try to query the update server directly
        config = {}
        if os.path.exists('update_config.json'):
            with open('update_config.json', 'r') as f:
                config = json.load(f)
        
        if not config.get('update_server'):
            return jsonify({'success': False, 'error': 'Update server not configured'})
        
        import requests
        
        channel = config.get('channel', 'stable')
        url = f"{config['update_server']}/api/version/{channel}"
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            version_info = response.json()
            
            # Get current version
            current_version = '1.0.0'
            if os.path.exists('VERSION'):
                with open('VERSION', 'r') as f:
                    current_version = f.read().strip()
            
            # Compare versions
            def compare_versions(v1, v2):
                v1_parts = list(map(int, v1.replace('-beta', '').replace('-alpha', '').split('.')))
                v2_parts = list(map(int, v2.replace('-beta', '').replace('-alpha', '').split('.')))
                return v2_parts > v1_parts
            
            update_available = compare_versions(current_version, version_info.get('version', '0.0.0'))
            
            # Update last check time
            config['last_check'] = datetime.now().isoformat()
            with open('update_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            return jsonify({
                'success': True,
                'update_available': update_available,
                'current_version': current_version,
                'latest_version': version_info if update_available else None
            })
        else:
            return jsonify({'success': False, 'error': 'Could not reach update server'})
            
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'Network error: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/update/install', methods=['POST'])
def install_update():
    """Install available update"""
    try:
        import subprocess
        import sys
        
        # Run update client
        result = subprocess.run(
            [sys.executable, 'update_client.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode == 0:
            db.log_action('UPDATE_INSTALL', None, 'Admin', 'Update installed successfully')
            return jsonify({'success': True, 'message': 'Update installed'})
        else:
            db.log_action('UPDATE_INSTALL_FAIL', None, 'Admin', f'Update failed: {result.stderr}')
            return jsonify({'success': False, 'error': result.stderr})
            
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Update timed out'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/update/test', methods=['GET'])
def test_update_connection():
    """Test connection to update server"""
    try:
        config = {}
        if os.path.exists('update_config.json'):
            with open('update_config.json', 'r') as f:
                config = json.load(f)
        
        if not config.get('update_server'):
            return jsonify({'success': False, 'error': 'Update server not configured'})
        
        import requests
        
        url = f"{config['update_server']}/api/stats"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            return jsonify({'success': True, 'server_url': config['update_server']})
        else:
            return jsonify({'success': False, 'error': f'Server returned {response.status_code}'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/update/rollback', methods=['POST'])
def rollback_update():
    """Rollback to previous version"""
    try:
        # Find most recent backup
        backup_dir = 'backups/updates'
        if not os.path.exists(backup_dir):
            return jsonify({'success': False, 'error': 'No backups found'})
        
        backups = sorted(
            [f for f in os.listdir(backup_dir) if f.endswith('.zip')],
            reverse=True
        )
        
        if not backups:
            return jsonify({'success': False, 'error': 'No backups available'})
        
        latest_backup = os.path.join(backup_dir, backups[0])
        
        # Extract backup
        import zipfile
        with zipfile.ZipFile(latest_backup, 'r') as zip_ref:
            zip_ref.extractall('.')
        
        db.log_action('UPDATE_ROLLBACK', None, 'Admin', f'Rolled back to {backups[0]}')
        
        return jsonify({'success': True, 'backup': backups[0]})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/update/history', methods=['GET'])
def get_update_history():
    """Get update history from activity log"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT action, details, timestamp, operator
                FROM activity_log
                WHERE action LIKE 'UPDATE%'
                ORDER BY timestamp DESC
                LIMIT 20
            ''')
            
            history = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                
                # Parse version from details if possible
                version = 'unknown'
                channel = 'unknown'
                status = 'success' if 'success' in row_dict['action'].lower() else 'unknown'
                
                if 'FAIL' in row_dict['action']:
                    status = 'failed'
                
                history.append({
                    'action': row_dict['action'],
                    'version': version,
                    'channel': channel,
                    'status': status,
                    'timestamp': row_dict['timestamp']
                })
            
            return jsonify({'success': True, 'history': history})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/update/backups', methods=['GET'])
def get_backups():
    """List available backups"""
    try:
        backup_dir = 'backups/updates'
        if not os.path.exists(backup_dir):
            return jsonify({'success': True, 'backups': []})
        
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith('.zip'):
                filepath = os.path.join(backup_dir, filename)
                backups.append({
                    'name': filename,
                    'size': os.path.getsize(filepath),
                    'created': os.path.getctime(filepath)
                })
        
        backups.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({'success': True, 'backups': backups})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/update/backup/<path:name>', methods=['DELETE'])
def delete_backup(name):
    """Delete a backup file"""
    try:
        backup_path = os.path.join('backups/updates', name)
        
        if not os.path.exists(backup_path):
            return jsonify({'success': False, 'error': 'Backup not found'}), 404
        
        os.remove(backup_path)
        
        db.log_action('DELETE_BACKUP', None, 'Admin', f'Deleted backup: {name}')
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    # Initialize database
    db.init_db()
    
    # Run application
    app.run(host='0.0.0.0', port=5000, debug=True, 
        ssl_context=('cert.pem', 'key.pem'))
