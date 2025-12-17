"""
PDF Generator Module
Generates PDFs for labels and exports images
"""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from PIL import Image
import os
import zipfile
from datetime import datetime


class PDFGenerator:
    def __init__(self):
        self.export_dir = 'static/exports'
        os.makedirs(self.export_dir, exist_ok=True)
    
    def generate_labels_pdf(self, inventory_ids):
        """
        Generate labels PDF
        A4 layout: 3 columns × 10 rows = 30 labels per page
        Each label contains: Barcode, Inventory ID, Description
        """
        try:
            from database import Database
            db = Database()
            
            pdf_filename = f"{self.export_dir}/labels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            c = canvas.Canvas(pdf_filename, pagesize=A4)
            
            page_width, page_height = A4
            
            # Layout configuration
            cols = 3
            rows = 10
            labels_per_page = cols * rows
            
            # Calculate cell dimensions
            margin = 10 * mm
            cell_width = (page_width - 2 * margin) / cols
            cell_height = (page_height - 2 * margin) / rows
            
            label_count = 0
            
            for inventory_id in inventory_ids:
                # Get item details
                item = db.get_item_by_inventory_id(inventory_id)
                if not item:
                    continue
                
                # Calculate position on page
                page_index = label_count % labels_per_page
                col = page_index % cols
                row = page_index // cols
                
                # Calculate x, y position (from bottom-left)
                x = margin + col * cell_width
                y = page_height - margin - (row + 1) * cell_height
                
                # Draw border
                c.rect(x, y, cell_width, cell_height)
                
                # Draw barcode if exists
                barcode_path = f"static/barcodes/{inventory_id}.png"
                if os.path.exists(barcode_path):
                    try:
                        c.drawImage(
                            barcode_path,
                            x + 5,
                            y + cell_height - 35,
                            width=cell_width - 10,
                            height=25,
                            preserveAspectRatio=True
                        )
                    except:
                        pass
                
                # Draw text information
                c.setFont("Helvetica-Bold", 10)
                c.drawString(x + 5, y + cell_height - 45, inventory_id)
                
                c.setFont("Helvetica", 8)
                # Truncate description if too long
                description = item.get('description', '')[:30]
                c.drawString(x + 5, y + cell_height - 55, description)
                
                # Draw additional info
                c.setFont("Helvetica", 7)
                info_y = y + cell_height - 65
                
                if item.get('article_code'):
                    c.drawString(x + 5, info_y, f"Art: {item['article_code']}")
                    info_y -= 8
                
                if item.get('location_code'):
                    c.drawString(x + 5, info_y, f"Loc: {item['location_code']}")
                    info_y -= 8
                
                if item.get('price'):
                    c.drawString(x + 5, info_y, f"Price: {item['price']} SEK")
                
                label_count += 1
                
                # New page if needed
                if label_count % labels_per_page == 0 and label_count < len(inventory_ids):
                    c.showPage()
            
            c.save()
            return pdf_filename
            
        except Exception as e:
            print(f"Error generating labels PDF: {e}")
            return None
    
    def export_images_zip(self, item_ids, db):
        """Export images for items as ZIP file"""
        try:
            zip_filename = f"{self.export_dir}/images_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for item_id in item_ids:
                    # Get item details
                    item = db.get_item_by_id(item_id)
                    if not item:
                        continue
                    
                    inventory_id = item['inventory_id']
                    
                    # Get images for item
                    images = db.get_item_images(item_id)
                    
                    for idx, img in enumerate(images):
                        # Add cropped image if available, otherwise original
                        if img.get('filename_cropped'):
                            img_path = f"static/uploads/{img['filename_cropped']}"
                            if os.path.exists(img_path):
                                # Add to ZIP with structured name
                                arcname = f"{inventory_id}/image_{idx+1}.jpg"
                                zipf.write(img_path, arcname)
                        elif img.get('filename_original'):
                            img_path = f"static/uploads/{img['filename_original']}"
                            if os.path.exists(img_path):
                                arcname = f"{inventory_id}/image_{idx+1}.jpg"
                                zipf.write(img_path, arcname)
            
            return zip_filename
            
        except Exception as e:
            print(f"Error creating images ZIP: {e}")
            return None
    
    def generate_location_labels_pdf(self, barcode_values):
        """
        Generate location labels PDF
        A4 layout: 3 columns × 10 rows = 30 labels per page
        Each label contains: Barcode and Location Code
        """
        try:
            pdf_filename = f"{self.export_dir}/location_labels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            c = canvas.Canvas(pdf_filename, pagesize=A4)
            
            page_width, page_height = A4
            
            # Layout configuration
            cols = 3
            rows = 10
            labels_per_page = cols * rows
            
            # Calculate cell dimensions
            margin = 10 * mm
            cell_width = (page_width - 2 * margin) / cols
            cell_height = (page_height - 2 * margin) / rows
            
            label_count = 0
            
            for barcode_value in barcode_values:
                # Calculate position on page
                page_index = label_count % labels_per_page
                col = page_index % cols
                row = page_index // cols
                
                # Calculate x, y position (from bottom-left)
                x = margin + col * cell_width
                y = page_height - margin - (row + 1) * cell_height
                
                # Draw border
                c.rect(x, y, cell_width, cell_height)
                
                # Draw barcode if exists
                barcode_path = f"static/barcodes/{barcode_value}.png"
                if os.path.exists(barcode_path):
                    try:
                        c.drawImage(
                            barcode_path,
                            x + 5,
                            y + cell_height / 2 - 15,
                            width=cell_width - 10,
                            height=30,
                            preserveAspectRatio=True
                        )
                    except:
                        pass
                
                # Draw location code (large and bold)
                c.setFont("Helvetica-Bold", 16)
                # Extract location code from barcode (e.g., LOC-A1-001 -> A1)
                location_code = barcode_value.replace('LOC-', '').split('-')[0] if 'LOC-' in barcode_value else barcode_value
                text_width = c.stringWidth(location_code, "Helvetica-Bold", 16)
                c.drawString(x + (cell_width - text_width) / 2, y + 10, location_code)
                
                # Draw full barcode value
                c.setFont("Helvetica", 8)
                text_width = c.stringWidth(barcode_value, "Helvetica", 8)
                c.drawString(x + (cell_width - text_width) / 2, y + cell_height - 15, barcode_value)
                
                label_count += 1
                
                # New page if needed
                if label_count % labels_per_page == 0 and label_count < len(barcode_values):
                    c.showPage()
            
            c.save()
            return pdf_filename
            
        except Exception as e:
            print(f"Error generating location labels PDF: {e}")
            return None
    
    def generate_packing_slip_pdf(self, order):
        """Generate packing slip PDF for an order"""
        try:
            from database import Database
            db = Database()
            
            pdf_filename = f"{self.export_dir}/packing_slip_{order['order_number']}.pdf"
            c = canvas.Canvas(pdf_filename, pagesize=A4)
            
            page_width, page_height = A4
            margin = 20 * mm
            
            # Header
            c.setFont("Helvetica-Bold", 16)
            c.drawString(margin, page_height - margin, "PACKING SLIP")
            
            c.setFont("Helvetica", 10)
            y = page_height - margin - 20
            
            # Order details
            c.drawString(margin, y, f"Order Number: {order['order_number']}")
            y -= 15
            c.drawString(margin, y, f"Date: {order['created_at']}")
            y -= 15
            c.drawString(margin, y, f"Buyer: {order.get('buyer_info', 'N/A')}")
            y -= 30
            
            # Items header
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margin, y, "Items:")
            y -= 20
            
            # Get order items
            items = db.get_order_items(order['id'])
            
            c.setFont("Helvetica", 9)
            for item in items:
                c.drawString(margin + 10, y, f"• {item['inventory_id']}")
                y -= 12
                c.drawString(margin + 20, y, f"{item.get('description', 'N/A')}")
                y -= 12
                c.drawString(margin + 20, y, 
                           f"Location: {item.get('location_code', 'N/A')} | " + 
                           f"Size: {item.get('length', 0)}x{item.get('width', 0)}x{item.get('height', 0)} cm")
                y -= 20
                
                if y < margin + 50:
                    c.showPage()
                    y = page_height - margin
            
            c.save()
            return pdf_filename
            
        except Exception as e:
            print(f"Error generating packing slip: {e}")
            return None
