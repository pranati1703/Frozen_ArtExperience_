import cv2
import numpy as np
import random
import math

class Snowflake:
    def __init__(self, x, y, direction_bias=0, scale=1.0):
        self.x = x
        self.y = y
        self.scale = scale
        
        # Spread velocity - scaled by hand size? Maybe bigger burst if closer?
        self.vx = (random.uniform(-2, 2) + direction_bias) * (0.8 + 0.2 * scale)
        self.vy = random.uniform(-4, -1) * scale # Faster upward burst if closer
        
        self.gravity = 0.05
        self.friction = 0.98 # Drag for fluidity
        
        self.life = 255
        self.decay = random.uniform(2, 5)
        
        # Base size scaled by hand distance
        base_size = random.randint(2, 6)
        self.size = max(1, int(base_size * scale))
        
        # Oscillation for "fluid" movement
        self.oscillation_freq = random.uniform(0.1, 0.3)
        self.oscillation_offset = random.uniform(0, 2 * math.pi)
        
        # Twinkle
        self.twinkle_speed = random.uniform(0.1, 0.3)
        self.twinkle_phase = random.uniform(0, 6.28)
        
        # Aurora Colors Palette
        # (Blue, Green, Red)
        palettes = [
            ((255, 255, 255), (255, 200, 50)),   # White core, Cyan Aura
            ((255, 200, 255), (200, 50, 150)),   # Pinkish core, Purple Aura
            ((200, 255, 255), (255, 100, 50)),   # Cyan core, Deep Blue Aura
            ((255, 220, 220), (180, 20, 100)),   # Pale Purple, Magenta Aura
        ]
        chosen = random.choice(palettes)
        self.core_color = chosen[0]
        self.aura_color = chosen[1]

    def update(self):
        # Fluid movement: Sine wave on X axis + Drag
        self.x += (self.vx + math.sin(self.y * 0.05 + self.oscillation_offset) * 0.5 * self.scale)
        self.y += self.vy
        
        self.vy += self.gravity
        self.vx *= self.friction # Drag
        
        self.life -= self.decay
        self.twinkle_phase += self.twinkle_speed

    def draw(self, img, overlay):
        if self.life > 0:
            # Twinkle effect: oscillate alpha slightly
            twinkle = (math.sin(self.twinkle_phase) + 1) / 2 # 0 to 1
            alpha_base = self.life / 255.0
            
            # Combine fade out with twinkle
            # Keep alpha at least 50% of base so it doesn't disappear
            current_alpha = alpha_base * (0.7 + 0.3 * twinkle)
            current_alpha = max(0, min(current_alpha, 1.0))
            
            ix, iy = int(self.x), int(self.y)
            
            # 1. Draw "Sparkle" Aura (No more round bubbles!)
            # Draw a large, faint cross shape for the glow
            aura_size = int(self.size * (2 + twinkle))
            
            # Draw Aura rays on overlay (faint)
            cv2.line(overlay, (ix - aura_size, iy), (ix + aura_size, iy), self.aura_color, 1)
            cv2.line(overlay, (ix, iy - aura_size), (ix, iy + aura_size), self.aura_color, 1)
            
            # 2. Draw Snowflake (Star/Asterisk shape)
            arm_length = self.size
            if arm_length < 2: arm_length = 2
            
            # Core color faded
            core = (
                int(self.core_color[0] * current_alpha),
                int(self.core_color[1] * current_alpha),
                int(self.core_color[2] * current_alpha)
            )
            
            # Draw 3 lines crossing for a 6-point star
            # Horizontal
            cv2.line(img, (ix - arm_length, iy), (ix + arm_length, iy), core, 1)
            # Diagonal 1 (60 deg approx) - simple coord offset
            # (dx, dy) = (0.5 * len, 0.86 * len)
            dx = int(arm_length * 0.5)
            dy = int(arm_length * 0.86)
            cv2.line(img, (ix - dx, iy - dy), (ix + dx, iy + dy), core, 1)
            # Diagonal 2
            cv2.line(img, (ix - dx, iy + dy), (ix + dx, iy - dy), core, 1)

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, direction_bias=0, scale=1.0, count=7):
        # count defaults to 7, but can be overridden
        for _ in range(count):
            self.particles.append(Snowflake(x, y, direction_bias, scale))

    def update_and_draw(self, img):
        # Create an overlay for the glows
        overlay = np.zeros_like(img)
        
        # Update
        for p in self.particles:
            p.update()
        
        # Remove dead
        self.particles = [p for p in self.particles if p.life > 0]
        
        # Draw
        for p in self.particles:
            p.draw(img, overlay)
            
        # Combine overlay (aura) with additive blending
        cv2.add(img, overlay, img)
