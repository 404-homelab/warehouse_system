"""
Camera Handler Module
Placeholder for camera operations - WebRTC is handled client-side in browser
"""


class CameraHandler:
    """
    Camera operations are handled client-side using WebRTC
    This class is kept for future server-side camera operations if needed
    """
    
    def __init__(self):
        self.camera_active = False
    
    def is_available(self):
        """Check if camera functionality is available"""
        return True  # WebRTC is browser-based
    
    def get_status(self):
        """Get camera status"""
        return {
            'available': True,
            'type': 'WebRTC Browser-based',
            'note': 'Camera is accessed directly through browser using WebRTC'
        }


# Note: Camera functionality is implemented client-side using JavaScript WebRTC API
# See templates/register.html for the actual camera implementation
