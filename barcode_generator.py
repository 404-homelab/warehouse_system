"""
Barcode Generator Module
Generates Code128 barcodes for items, locations, and bulk operations
"""
import barcode
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import os


# ==========================================
# BARCODE CONFIGURATION - EDIT THESE VALUES
# ==========================================

# Barcode appearance settings
BARCODE_MODULE_WIDTH = 0.3      # Width of each bar in mm (0.2-0.5 recommended)
BARCODE_MODULE_HEIGHT = 15.0    # Height of barcode in mm
BARCODE_QUIET_ZONE = 2.0        # White space around barcode in mm
BARCODE_FONT_SIZE = 10          # Font size for text below barcode
BARCODE_TEXT_DISTANCE = 3.0     # Distance between bars and text in mm

# PDF Layout settings
PDF_BARCODE_WIDTH = 50          # Width of barcode in PDF in mm (CHANGE THIS!)
PDF_BARCODE_HEIGHT = 20         # Height of barcode in PDF in mm
PDF_COLS = 3                    # Number of columns on page
PDF_ROWS = 10                   # Number of rows on page
PDF_MARGIN = 10                 # Page margin in mm

# ==========================================


class BarcodeGenerator:
    def __init__(self):
        self.barcode_dir = 'static/barcodes'
        os.makedirs(self.barcode_dir, exist_ok=True)
    
    def _get_writer_options(self):
        """Get standard barcode writer options"""
        return {
            'module_width': BARCODE_MODULE_WIDTH,
            'module_height': BARCODE_MODULE_HEIGHT,
            'quiet_zone': BARCODE_QUIET_ZONE,
            'font_size': BARCODE_FONT_SIZE,
            'text_distance': BARCODE_TEXT_DISTANCE,
            'write_text': True,
            'background': 'white',
            'foreground': 'black'
        }
    
    def generate_item_barcode(self, inventory_id):
        """Generate barcode for an item (Code128)"""
        try:
            code128 = barcode.get_barcode_class('code128')
            writer = ImageWriter()
            writer.set_options(self._get_writer_options())
            
            barcode_instance = code128(inventory_id, writer=writer)
            
            filename = f"{inventory_id}"
            filepath = os.path.join(self.barcode_dir, filename)
            barcode_instance.save(filepath)
            
            return f"/static/barcodes/{filename}.png"
        except Exception as e:
            print(f"Error generating barcode: {e}")
            return None
    
    def generate_location_barcode(self, barcode_value):
        """Generate barcode for a location"""
        try:
            code128 = barcode.get_barcode_class('code128')
            writer = ImageWriter()
            writer.set_options(self._get_writer_options())
            
            barcode_instance = code128(barcode_value, writer=writer)
            
            filename = f"{barcode_value}"
            filepath = os.path.join(self.barcode_dir, filename)
            barcode_instance.save(filepath)
            
            return f"/static/barcodes/{filename}.png"
        except Exception as e:
            print(f"Error generating location barcode: {e}")
            return None
    
    def generate_special_barcode(self, text):
        """Generate special barcode (e.g., SHIPPED)"""
        try:
            code128 = barcode.get_barcode_class('code128')
            writer = ImageWriter()
            writer.set_options(self._get_writer_options())
            
            barcode_instance = code128(text, writer=writer)
            
            filename = f"SPECIAL_{text}"
            filepath = os.path.join(self.barcode_dir, filename)
            barcode_instance.save(filepath)
            
            return f"/static/barcodes/{filename}.png"
        except Exception as e:
            print(f"Error generating special barcode: {e}")
            return None
    
    def generate_bulk_barcodes_pdf(self, prefix, start, end):
        """
        Generate bulk barcodes as PDF
        Layout configured by PDF_COLS and PDF_ROWS variables at top of file
        Barcode size configured by PDF_BARCODE_WIDTH and PDF_BARCODE_HEIGHT
        """
        try:
            output_dir = 'static/exports'
            os.makedirs(output_dir, exist_ok=True)
            
            pdf_filename = f"{output_dir}/bulk_barcodes_{prefix}_{start}-{end}.pdf"
            c = canvas.Canvas(pdf_filename, pagesize=A4)
            
            page_width, page_height = A4
            
            # Layout configuration from variables
            cols = PDF_COLS
            rows = PDF_ROWS
            barcodes_per_page = cols * rows
            
            # Calculate cell dimensions
            margin = PDF_MARGIN * mm
            cell_width = (page_width - 2 * margin) / cols
            cell_height = (page_height - 2 * margin) / rows
            
            barcode_count = 0
            
            for num in range(start, end + 1):
                barcode_text = f"{prefix}-{num:06d}"
                
                # Calculate position on page
                page_index = barcode_count % barcodes_per_page
                col = page_index % cols
                row = page_index // cols
                
                # Calculate x, y position (from bottom-left)
                x = margin + col * cell_width
                y = page_height - margin - (row + 1) * cell_height
                
                # Generate barcode image
                code128 = barcode.get_barcode_class('code128')
                writer = ImageWriter()
                writer.set_options(self._get_writer_options())
                
                barcode_instance = code128(barcode_text, writer=writer)
                temp_path = f"{self.barcode_dir}/temp_{barcode_text}"
                barcode_instance.save(temp_path)
                
                # Draw on PDF
                try:
                    # Text above barcode
                    c.setFont("Helvetica-Bold", 10)
                    c.drawCentredString(
                        x + cell_width / 2,
                        y + cell_height - 10,
                        barcode_text
                    )
                    
                    # Barcode image with configured size
                    barcode_width = PDF_BARCODE_WIDTH * mm
                    barcode_height = PDF_BARCODE_HEIGHT * mm
                    
                    # Center barcode in cell
                    barcode_x = x + (cell_width - barcode_width) / 2
                    barcode_y = y + (cell_height - barcode_height) / 2
                    
                    # Draw WITHOUT preserveAspectRatio to force exact size
                    c.drawImage(
                        f"{temp_path}.png",
                        barcode_x,
                        barcode_y,
                        width=barcode_width,
                        height=barcode_height,
                        preserveAspectRatio=False  # Force exact dimensions
                    )
                    
                    # Text below barcode
                    c.setFont("Helvetica", 9)
                    c.drawCentredString(
                        x + cell_width / 2,
                        y + 5,
                        barcode_text
                    )
                    
                    # Clean up temp file
                    if os.path.exists(f"{temp_path}.png"):
                        os.remove(f"{temp_path}.png")
                        
                except Exception as e:
                    print(f"Error drawing barcode {barcode_text}: {e}")
                
                barcode_count += 1
                
                # New page if needed
                if barcode_count % barcodes_per_page == 0 and num < end:
                    c.showPage()
            
            c.save()
            return pdf_filename
            
        except Exception as e:
            print(f"Error generating bulk barcodes PDF: {e}")
            return None
