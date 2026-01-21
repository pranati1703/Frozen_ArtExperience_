import cv2
import numpy as np

def create_gradient_background(width, height):
    # Create a radial gradient from Deep Blue to Dark
    # Center color: (80, 50, 20) (BGR for Dark Blue)
    # Edge color: (20, 10, 5) (BGR for Almost Black)
    
    # Create coordinate grids
    x = np.arange(width)
    y = np.arange(height)
    xv, yv = np.meshgrid(x, y)
    
    # Calculate distance from center (normalized)
    cx, cy = width // 2, height // 2
    max_dist = np.sqrt(cx**2 + cy**2)
    dist = np.sqrt((xv - cx)**2 + (yv - cy)**2) / max_dist
    
    # Color definitions (BGR)
    center_color = np.array([120, 50, 20])   # Ice Blueish
    edge_color = np.array([20, 10, 5])       # Dark background
    
    # Interpolate
    dist = np.clip(dist, 0, 1)
    dist = dist[..., np.newaxis] # Add channel dim
    
    background = (1 - dist) * center_color + dist * edge_color
    return background.astype(np.uint8)

def draw_sparkle(img, x, y, size, color, thickness=1, style='cross'):
    # Draw a sparkle (star shape)
    # style 'cross': + shape
    # style 'star': * shape
    ix, iy = int(x), int(y)
    
    # Glow/Center
    cv2.circle(img, (ix, iy), max(1, size // 3), color, -1)
    
    # Rays
    # Horizontal
    cv2.line(img, (ix - size, iy), (ix + size, iy), color, thickness)
    # Vertical
    cv2.line(img, (ix, iy - size), (ix, iy + size), color, thickness)
    
    if style == 'star':
        d_size = int(size * 0.7)
        # Diagonal 1
        cv2.line(img, (ix - d_size, iy - d_size), (ix + d_size, iy + d_size), color, thickness)
        # Diagonal 2
        cv2.line(img, (ix - d_size, iy + d_size), (ix + d_size, iy - d_size), color, thickness)

def draw_aurora_effect(shape, t):
    # shape: (h, w, c)
    h, w = shape[0], shape[1]
    
    # Work at lower res for performance & soft look
    low_h, low_w = h // 8, w // 8
    aurora = np.zeros((low_h, low_w, 3), dtype=np.uint8)
    
    # Create x coordinates
    xs = np.arange(low_w)
    
    # Curve 1: Purple/Pink
    # Sine wave that moves over time
    ys1 = (np.sin(xs * 0.02 + t * 0.5) * 20 + 
           np.sin(xs * 0.08 - t * 0.2) * 10 + 
           low_h * 0.4).astype(np.int32)
    
    pts1 = np.column_stack((xs, ys1))
    # Close polygon down to bottom
    pts1 = np.vstack([pts1, [low_w, low_h], [0, low_h]])
    
    # Draw filled polygon (Purple: 200, 50, 150 BGR)
    # We draw on a temp layer to handle transparency if needed, 
    # but here we just draw additive
    cv2.fillPoly(aurora, [pts1], (200, 50, 100)) # Violet/Purple

    # Curve 2: Cyan/Blue
    ys2 = (np.sin(xs * 0.03 - t * 0.3) * 25 + 
           np.sin(xs * 0.1 + t * 0.1) * 15 + 
           low_h * 0.6).astype(np.int32)
    
    pts2 = np.column_stack((xs, ys2))
    pts2 = np.vstack([pts2, [low_w, low_h], [0, low_h]])
    
    # Draw filled (Cyan: 255, 200, 0 BGR)
    curve2_img = np.zeros_like(aurora)
    cv2.fillPoly(curve2_img, [pts2], (255, 200, 20)) # Cyan
    
    # Blend
    cv2.addWeighted(aurora, 1.0, curve2_img, 0.7, 0, aurora)
    
    # Curve 3: Deep Blue (Top layer)
    ys3 = (np.sin(xs * 0.015 + t * 0.2) * 30 + low_h * 0.8).astype(np.int32)
    pts3 = np.column_stack((xs, ys3))
    pts3 = np.vstack([pts3, [low_w, low_h], [0, low_h]])
    
    curve3_img = np.zeros_like(aurora)
    cv2.fillPoly(curve3_img, [pts3], (150, 50, 20)) # Deep Blue
    
    cv2.addWeighted(aurora, 1.0, curve3_img, 0.5, 0, aurora)
    
    # Blur heavily
    aurora = cv2.GaussianBlur(aurora, (51, 51), 0)
    
    # Upscale
    aurora_large = cv2.resize(aurora, (w, h), interpolation=cv2.INTER_LINEAR)
    
    return aurora_large

def apply_frozen_filter(img):
    # Add a cool blue tint
    # BGR format
    # Increase Blue channel slightly, decrease Red
    
    # Simple addition (clipping handled by cv2.add usually or numpy wrap)
    # Better: overlay a solid blue color with transparency
    
    overlay = np.full(img.shape, (255, 50, 0), dtype=np.uint8) # Blue-ish overlay
    
    # Blend: img * 0.8 + overlay * 0.2
    alpha = 0.2
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    
    return img

def draw_text_centered(img, text, y_pos, font_scale=1, color=(255, 255, 255), thickness=2):
    h, w, c = img.shape
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = (w - text_size[0]) // 2
    
    # Shadow
    cv2.putText(img, text, (text_x + 2, y_pos + 2), font, font_scale, (0, 0, 0), thickness)
    # Text
    cv2.putText(img, text, (text_x, y_pos), font, font_scale, color, thickness)


