from PIL import Image, ImageDraw
import os

def create_bakery_icon():
    # Create a 256x256 image with a white background
    size = 256
    image = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a brown bread loaf
    # Main bread shape
    draw.ellipse([50, 80, 206, 200], fill=(139, 69, 19))  # Brown color
    
    # Bread top
    draw.ellipse([70, 60, 186, 120], fill=(160, 82, 45))  # Slightly lighter brown
    
    # Add some texture (small circles for bread texture)
    for _ in range(20):
        x = 70 + (size - 140) * 0.5
        y = 100 + (size - 140) * 0.5
        radius = 5
        draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=(160, 82, 45))
    
    # Save as ICO file
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bakery_icon.ico")
    image.save(icon_path, format='ICO', sizes=[(256, 256)])
    return icon_path

if __name__ == "__main__":
    create_bakery_icon() 