"""
Image Processor Module
Handles image processing including auto-cropping using OpenCV
"""
import cv2
import numpy as np
import os


class ImageProcessor:
    def __init__(self):
        pass
    
    def auto_crop_image(self, input_path, output_path, padding=10, min_area=1000, max_area_ratio=0.95):
        """
        Automatically crop an image to the main object
        
        Args:
            input_path: Path to input image
            output_path: Path to save cropped image
            padding: Padding around detected object (pixels)
            min_area: Minimum contour area to consider (pixels²)
            max_area_ratio: Maximum ratio of contour to image area (to avoid selecting entire image)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Read image
            img = cv2.imread(input_path)
            if img is None:
                print(f"Error: Could not read image from {input_path}")
                return False
            
            height, width = img.shape[:2]
            total_area = height * width
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Dilate edges to close gaps
            kernel = np.ones((5, 5), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                print("No contours found, saving original image")
                cv2.imwrite(output_path, img)
                return True
            
            # Find the largest valid contour
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                area_ratio = area / total_area
                
                # Filter by area constraints
                if area > min_area and area_ratio < max_area_ratio:
                    valid_contours.append(contour)
            
            if not valid_contours:
                print("No valid contours found, saving original image")
                cv2.imwrite(output_path, img)
                return True
            
            # Get bounding box of largest valid contour
            largest_contour = max(valid_contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # Add padding
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(width - x, w + 2 * padding)
            h = min(height - y, h + 2 * padding)
            
            # Crop image
            cropped = img[y:y+h, x:x+w]
            
            # Save cropped image
            cv2.imwrite(output_path, cropped)
            print(f"✓ Image cropped successfully: {output_path}")
            
            return True
            
        except Exception as e:
            print(f"Error cropping image: {e}")
            return False
    
    def resize_image(self, input_path, output_path, max_width=800, max_height=800):
        """
        Resize image maintaining aspect ratio
        
        Args:
            input_path: Path to input image
            output_path: Path to save resized image
            max_width: Maximum width
            max_height: Maximum height
        """
        try:
            img = cv2.imread(input_path)
            if img is None:
                return False
            
            height, width = img.shape[:2]
            
            # Calculate scaling factor
            scale = min(max_width / width, max_height / height)
            
            if scale < 1:
                new_width = int(width * scale)
                new_height = int(height * scale)
                resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
                cv2.imwrite(output_path, resized)
            else:
                # Image is already smaller than max dimensions
                cv2.imwrite(output_path, img)
            
            return True
            
        except Exception as e:
            print(f"Error resizing image: {e}")
            return False
    
    def enhance_image(self, input_path, output_path):
        """
        Enhance image (brightness, contrast, sharpness)
        """
        try:
            img = cv2.imread(input_path)
            if img is None:
                return False
            
            # Convert to LAB color space
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge channels
            enhanced_lab = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
            
            # Sharpen
            kernel = np.array([[-1, -1, -1],
                             [-1,  9, -1],
                             [-1, -1, -1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)
            
            cv2.imwrite(output_path, sharpened)
            return True
            
        except Exception as e:
            print(f"Error enhancing image: {e}")
            return False
    
    def remove_background(self, input_path, output_path):
        """
        Simple background removal (white background)
        """
        try:
            img = cv2.imread(input_path)
            if img is None:
                return False
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Threshold
            _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
            
            # Create white background
            background = np.full(img.shape, 255, dtype=np.uint8)
            
            # Apply mask
            mask_3channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            foreground = cv2.bitwise_and(img, mask_3channel)
            background_masked = cv2.bitwise_and(background, cv2.bitwise_not(mask_3channel))
            
            result = cv2.add(foreground, background_masked)
            
            cv2.imwrite(output_path, result)
            return True
            
        except Exception as e:
            print(f"Error removing background: {e}")
            return False
    
    def detect_barcode(self, image_path):
        """
        Detect and decode barcodes in an image using pyzbar
        """
        try:
            from pyzbar.pyzbar import decode
            
            img = cv2.imread(image_path)
            if img is None:
                return None
            
            # Decode barcodes
            barcodes = decode(img)
            
            if barcodes:
                # Return first barcode found
                barcode = barcodes[0]
                return {
                    'data': barcode.data.decode('utf-8'),
                    'type': barcode.type,
                    'rect': barcode.rect
                }
            
            return None
            
        except ImportError:
            print("pyzbar not installed. Install with: pip install pyzbar")
            return None
        except Exception as e:
            print(f"Error detecting barcode: {e}")
            return None
