import os
import shutil
import sys

def setup_assets():
    """
    Check if the assets directory exists and create it if needed.
    Also creates a default icon file if it doesn't exist.
    """
    # Get the project root directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the assets directory path
    assets_dir = os.path.join(root_dir, 'assets')
    
    # Create assets directory if it doesn't exist
    if not os.path.exists(assets_dir):
        print(f"Creating assets directory at {assets_dir}")
        os.makedirs(assets_dir)
    
    # Define the icon file path
    icon_path = os.path.join(assets_dir, 'quail.ico')
    
    # Check if icon file exists
    if not os.path.exists(icon_path):
        print(f"No icon file found at {icon_path}")
        print("Please place your 'quail.ico' file in the assets directory")
        
        # Create a blank file as placeholder
        with open(icon_path, 'wb') as f:
            # Write a minimal ICO file header (just enough to not crash)
            f.write(bytes.fromhex('00 00 01 00 01 00 10 10 00 00 01 00 04 00 28 01 00 00 16 00 00 00'))
            f.write(bytes(40))  # BITMAPINFOHEADER (all zeros for placeholder)
            f.write(bytes(64))  # Color table (16 colors, 4 bytes each)
            f.write(bytes(256))  # Bitmap data (16x16x1bpp = 32 bytes, padded)
    
    return assets_dir

if __name__ == "__main__":
    assets_dir = setup_assets()
    print(f"Assets directory is ready at: {assets_dir}")
    print("Please ensure your 'quail.ico' file is in this directory.")
