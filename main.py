import pygame
import sys
import random
from datetime import datetime
from database import init_db, insert_score, get_high_score, get_top_scores, get_highest_score
import os
import math

# Disable print statements during testing
if 'PYTEST_CURRENT_TEST' in os.environ:
    def print(*args, **kwargs):
        pass

# Initialize Pygame and the database
pygame.init()
init_db()

# Set up display
width, height = 800, 600
window = pygame.display.set_mode((width, height))
pygame.display.set_caption("Space Dodger")

# Set up colors
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 60, 60)
blue = (0, 100, 255)
green = (0, 255, 100)
yellow = (255, 255, 0)
purple = (200, 0, 200)

# Load and scale background image
try:
    background = pygame.image.load("space_background.png")
    background = pygame.transform.scale(background, (width, height))
except FileNotFoundError:
    print("Warning: space_background.png not found. Using a simple starfield background.")
    background = pygame.Surface((width, height))
    background.fill((0, 0, 0))  # Black background
    for _ in range(200):  # Add 200 stars
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        pygame.draw.circle(background, (255, 255, 255), (x, y), 1)

# New game variables
STAR_SYSTEMS = [
    "Sol", "Alpha Centauri", "Sirius", "Betelgeuse", "Andromeda", 
    "Orion", "Pleiades", "Cygnus", "Cassiopeia", "Galactic Core",
    "Nebula X", "Quasar Y", "Black Hole Z", "Supernova Remnant",
    "Neutron Star Cluster", "Gamma Ray Burst", "Dark Matter Cloud"
]
HAZARDS = {
    "asteroid": {"speed": 5, "size": 50, "color": (139, 69, 19)},
    "comet": {"speed": 7, "size": 40, "color": (100, 149, 237)},
    "alien": {"speed": 6, "size": 60, "color": (50, 205, 50)},
    "homing": {"speed": 4, "size": 45, "color": (255, 0, 0)},
    "splitting": {"speed": 5, "size": 55, "color": (255, 165, 0)},
}

# Add this after the HAZARDS dictionary
UPGRADES = {
    "shield": {"color": yellow},  # Remove duration for shield
    "speed": {"color": blue, "duration": 7},
    "shrink": {"color": green, "duration": 12},
    "invincibility": {"color": white, "duration": 5},
    "magnet": {"color": (128, 128, 128), "duration": 15},
}

# Game variables
player_size = 50
enemy_size = 50
power_up_size = 30
enemy_speed = 5
power_up_speed = 3
player_trail = []
particle_list = []
stars = [(random.randint(0, width), random.randint(0, height), random.random()) for _ in range(100)]
score = 0

# Add this constant near the top of the file, with other game variables
MAX_PLAYER_SPEED = 15  # Reduced from 20
MIN_PLAYER_SIZE = 30  # Minimum size the player can shrink to

class Player:
    def __init__(self):
        self.reset()

    def reset(self):
        self.size = 50
        self.pos = [width // 2, height - 2 * self.size]
        self.speed = 10
        self.health = 3
        self.shield = False
        self.invincible = False
        self.multi_shot = False
        self.magnet = False
        self.special_charge = 0
        self.combo = 0

    def increase_speed(self):
        self.speed = min(self.speed * 1.5, MAX_PLAYER_SPEED)

    def shrink(self):
        self.size = max(self.size * 0.8, MIN_PLAYER_SIZE)

    def draw(self):
        pygame.draw.rect(window, white, (*self.pos, self.size, self.size))

    def take_damage(self):
        if not self.shield:
            self.health = max(0, self.health - 1)
        else:
            self.shield = False

    def heal(self):
        self.health = min(3, self.health + 1)

    def update(self):
        self.special_charge = min(100, self.special_charge + 0.1)

    def activate_special(self):
        if self.special_charge >= 100:
            self.special_charge = 0
            return True
        return False

class Hazard:
    def __init__(self, hazard_type):
        self.type = hazard_type
        self.size = HAZARDS[hazard_type]["size"]
        self.speed = HAZARDS[hazard_type]["speed"]
        self.color = HAZARDS[hazard_type]["color"]
        self.pos = [random.randint(0, width - self.size), -self.size]
        self.homing_cooldown = 0

    def update(self, player_pos):
        if self.type == "homing":
            if self.homing_cooldown <= 0:
                dx = player_pos[0] - self.pos[0]
                dy = player_pos[1] - self.pos[1]
                dist = max(1, (dx**2 + dy**2)**0.5)
                self.pos[0] += dx / dist * self.speed * 0.5  # Reduced homing speed
                self.pos[1] += dy / dist * self.speed * 0.5
                self.homing_cooldown = 60  # Set cooldown to 1 second (assuming 60 FPS)
            else:
                self.pos[1] += self.speed
                self.homing_cooldown -= 1
        else:
            self.pos[1] += self.speed

    def draw(self):
        draw_space_invader(window, self.pos[0], self.pos[1], self.size, self.color)

class Upgrade:
    def __init__(self, upgrade_type):
        self.type = upgrade_type
        self.color = UPGRADES[upgrade_type]["color"]
        self.size = 30
        self.pos = [random.randint(0, width - self.size), -self.size]
        self.speed = 3

    def update(self):
        self.pos[1] += self.speed

    def draw(self):
        if self.type == "shield":
            self.draw_shield()
        elif self.type == "speed":
            self.draw_speed()
        elif self.type == "shrink":
            self.draw_shrink()
        elif self.type == "invincibility":
            self.draw_invincibility()
        elif self.type == "magnet":
            self.draw_magnet()

    def draw_shield(self):
        center_x = self.pos[0] + self.size // 2
        center_y = self.pos[1] + self.size // 2
        radius = self.size // 2

        pygame.draw.circle(window, self.color, (center_x, center_y), radius, 2)
        points = [
            (center_x - radius // 2, center_y + radius // 2),
            (center_x, center_y - radius // 2),
            (center_x + radius // 2, center_y + radius // 2)
        ]
        pygame.draw.polygon(window, self.color, points, 2)
        pygame.draw.line(window, self.color, (center_x, center_y + radius // 2), (center_x, center_y + radius - 2), 2)

    def draw_speed(self):
        center_x = self.pos[0] + self.size // 2
        center_y = self.pos[1] + self.size // 2
        radius = self.size // 2

        pygame.draw.circle(window, self.color, (center_x, center_y), radius, 2)
        points = [
            (center_x - radius // 2, center_y),
            (center_x + radius // 2, center_y - radius // 4),
            (center_x + radius // 2, center_y + radius // 4)
        ]
        pygame.draw.polygon(window, self.color, points)

    def draw_shrink(self):
        center_x = self.pos[0] + self.size // 2
        center_y = self.pos[1] + self.size // 2
        radius = self.size // 2

        pygame.draw.circle(window, self.color, (center_x, center_y), radius, 2)
        pygame.draw.line(window, self.color, (center_x - radius // 2, center_y - radius // 2), (center_x + radius // 2, center_y + radius // 2), 2)
        pygame.draw.line(window, self.color, (center_x + radius // 2, center_y - radius // 2), (center_x - radius // 2, center_y + radius // 2), 2)

    def draw_invincibility(self):
        center_x = self.pos[0] + self.size // 2
        center_y = self.pos[1] + self.size // 2
        radius = self.size // 2

        pygame.draw.circle(window, self.color, (center_x, center_y), radius, 2)
        pygame.draw.circle(window, self.color, (center_x, center_y), radius // 2, 2)
        for i in range(8):
            angle = i * math.pi / 4
            x = center_x + int(radius * 0.8 * math.cos(angle))
            y = center_y + int(radius * 0.8 * math.sin(angle))
            pygame.draw.circle(window, self.color, (x, y), 2)

    def draw_magnet(self):
        center_x = self.pos[0] + self.size // 2
        center_y = self.pos[1] + self.size // 2
        radius = self.size // 2

        pygame.draw.circle(window, self.color, (center_x, center_y), radius, 2)
        pygame.draw.arc(window, self.color, (center_x - radius // 2, center_y - radius // 2, radius, radius), math.pi / 2, 3 * math.pi / 2, 2)
        pygame.draw.arc(window, self.color, (center_x - radius // 2, center_y - radius // 2, radius, radius), -math.pi / 2, math.pi / 2, 2)
        pygame.draw.line(window, self.color, (center_x - radius // 2, center_y - radius // 4), (center_x - radius // 2, center_y + radius // 4), 2)
        pygame.draw.line(window, self.color, (center_x + radius // 2, center_y - radius // 4), (center_x + radius // 2, center_y + radius // 4), 2)

def create_gradient_surface(size, color1, color2):
    surface = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(size[1]):
        ratio = y / size[1]
        color = [int(color1[i] * (1 - ratio) + color2[i] * ratio) for i in range(3)]
        pygame.draw.line(surface, color, (0, y), (size[0], y))
    return surface

def draw_glowing_circle(surface, color, pos, radius):
    glow_radius = int(radius * 1.5)
    radius = int(radius)  # Ensure radius is an integer
    for r in range(glow_radius, radius, -1):
        alpha = int(255 * (1 - (r - radius) / (glow_radius - radius)))
        glow_color = (*color[:3], alpha)  # Use only RGB values and add alpha
        pygame.draw.circle(surface, glow_color, pos, r)
    pygame.draw.circle(surface, color[:3], pos, radius)  # Use only RGB values for the final circle

def draw_text(text, color, x, y, size=36, align="left"):
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    
    if align == "left":
        text_rect.topleft = (x, y)
    elif align == "right":
        text_rect.topright = (x, y)
    else:  # center
        text_rect.midtop = (x, y)
    
    window.blit(text_surface, text_rect)

def show_start_screen():
    window.blit(background, (0, 0))
    
    # Title
    draw_text("Space Dodger", white, width // 2, height // 8, size=72, align="center")
    
    # Instructions
    instructions = [
        "LEFT/RIGHT: Move",
        "Dodge: Red, Yellow, Purple aliens",
        "Collect power-ups:",
        "  Green: Shrink (easier to dodge)",
        "  Blue: Speed boost",
        "  Yellow: Shield (protects from one hit)",
        "  White: Temporary invincibility",
        "  Gray: Magnet (attracts power-ups)",
        "",
        "SPACE to start"
    ]
    
    for i, instruction in enumerate(instructions):
        draw_text(instruction, white, width // 2, height // 4 + i * 30, size=24, align="center")
    
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
        
        pygame.display.flip()
        pygame.time.Clock().tick(30)

def draw_space_invader(surface, x, y, size, color):
    # Draw the main body
    pygame.draw.rect(surface, color, (x, y + size // 4, size, size // 2))
    
    # Draw the head
    pygame.draw.rect(surface, color, (x + size // 4, y, size // 2, size // 4))
    
    # Draw the tentacles
    pygame.draw.rect(surface, color, (x, y + size // 2, size // 4, size // 2))
    pygame.draw.rect(surface, color, (x + size * 3 // 4, y + size // 2, size // 4, size // 2))
    
    # Draw the eyes
    eye_color = (0, 0, 0)  # Black eyes
    pygame.draw.rect(surface, eye_color, (x + size // 4, y + size // 4, size // 8, size // 8))
    pygame.draw.rect(surface, eye_color, (x + size * 5 // 8, y + size // 4, size // 8, size // 8))

def draw_enemies(enemy_list):
    for enemy_pos in enemy_list:
        if enemy_pos[2] == "normal":
            draw_space_invader(window, enemy_pos[0], enemy_pos[1], enemy_size, red)
        elif enemy_pos[2] == "fast":
            draw_space_invader(window, enemy_pos[0], enemy_pos[1], enemy_size, yellow)
        elif enemy_pos[2] == "big":
            draw_space_invader(window, enemy_pos[0], enemy_pos[1], int(enemy_size * 1.5), purple)

def draw_power_ups(power_up_list):
    for power_up in power_up_list:
        if power_up[2] == "size":
            color = green
        elif power_up[2] == "speed":
            color = blue
        elif power_up[2] == "shield":
            color = yellow
        
        pulse = (pygame.time.get_ticks() % 1000) / 1000  # Value between 0 and 1
        size_offset = int(power_up_size * 0.2 * pulse)
        
        draw_glowing_circle(window, color, (power_up[0] + power_up_size // 2, power_up[1] + power_up_size // 2), power_up_size // 2 + size_offset)

def draw_player(player):
    global player_trail
    # Draw trail
    player_trail.insert(0, player.pos.copy())
    if len(player_trail) > 10:
        player_trail.pop()
    
    for i, trail_pos in enumerate(player_trail):
        alpha = 255 - i * 25
        trail_color = (*blue, alpha)
        trail_size = player.size - i * 2
        draw_glowing_circle(window, blue, (int(trail_pos[0] + player.size // 2), int(trail_pos[1] + player.size // 2)), trail_size // 2)
    
    if player.shield:
        draw_glowing_circle(window, yellow, (int(player.pos[0] + player.size // 2), int(player.pos[1] + player.size // 2)), player.size // 2 + 5)
    
    player.draw()

def drop_enemies(enemy_list):
    if len(enemy_list) < 10 and random.random() < 0.1:
        x_pos = random.randint(0, width - enemy_size)
        y_pos = 0
        enemy_type = random.choice(["normal", "fast", "big"])
        enemy_list.append([x_pos, y_pos, enemy_type])

def drop_power_up(power_up_list):
    if len(power_up_list) < 1 and random.random() < 0.02:
        x_pos = random.randint(0, width - power_up_size)
        y_pos = 0
        power_up_type = random.choice(["size", "speed", "shield"])
        power_up_list.append([x_pos, y_pos, power_up_type])

def update_enemy_positions(enemy_list, score):
    for idx, enemy_pos in enumerate(enemy_list):
        if enemy_pos[1] >= 0 and enemy_pos[1] < height:
            if enemy_pos[2] == "normal":
                enemy_pos[1] += enemy_speed
            elif enemy_pos[2] == "fast":
                enemy_pos[1] += enemy_speed * 1.5
            elif enemy_pos[2] == "big":
                enemy_pos[1] += enemy_speed * 0.75
        else:
            enemy_list.pop(idx)
            score += 1
    return score

def update_power_up_positions(power_up_list):
    for idx, power_up in enumerate(power_up_list):
        if power_up[1] >= 0 and power_up[1] < height:
            power_up[1] += power_up_speed
        else:
            power_up_list.pop(idx)

def collision_check(enemy_list, player_pos, player_size):
    player_rect = pygame.Rect(player_pos[0], player_pos[1], player_size, player_size)
    for enemy_pos in enemy_list:
        enemy_size_actual = enemy_size if enemy_pos[2] != "big" else enemy_size * 1.5
        enemy_rect = pygame.Rect(enemy_pos[0], enemy_pos[1], enemy_size_actual, enemy_size_actual)
        if player_rect.colliderect(enemy_rect):
            return True
    return False

def power_up_collision_check(power_up_list, player_pos, player_size):
    for idx, power_up in enumerate(power_up_list):
        if detect_collision(player_pos, power_up[:2], player_size, power_up_size):
            return power_up_list.pop(idx)[2]
    return None

def detect_collision(pos1, pos2, size1, size2):
    p_x, p_y = pos1
    e_x, e_y = pos2

    # Calculate the corners of the player and enemy
    p_left, p_right = p_x, p_x + size1
    p_top, p_bottom = p_y, p_y + size1
    e_left, e_right = e_x, e_x + size2
    e_top, e_bottom = e_y, e_y + size2

    # Check for overlap
    x_collision = (e_left < p_right) and (p_left < e_right)
    y_collision = (e_top < p_bottom) and (p_top < e_bottom)
    
    return x_collision and y_collision

def create_particles(x, y, color):
    num_particles = 20
    for _ in range(num_particles):
        particle_x = x + random.randint(-10, 10)
        particle_y = y + random.randint(-10, 10)
        particle_size = random.randint(2, 5)
        particle_speed = [random.uniform(-2, 2), random.uniform(-2, 2)]
        particle_life = random.randint(20, 40)
        particle_list.append([particle_x, particle_y, particle_size, particle_speed, color, particle_life])

def update_particles():
    for particle in particle_list:
        particle[0] += particle[3][0]
        particle[1] += particle[3][1]
        particle[5] -= 1
        if particle[5] <= 0:
            particle_list.remove(particle)

def draw_particles():
    for particle in particle_list:
        pygame.draw.circle(window, particle[4], (int(particle[0]), int(particle[1])), particle[2])

def draw_stars():
    for star in stars:
        brightness = int(255 * star[2])
        pygame.draw.circle(window, (brightness, brightness, brightness), (int(star[0]), int(star[1])), 1 if star[2] < 0.5 else 2)

def move_stars():
    for i, star in enumerate(stars):
        stars[i] = ((star[0] - 0.5) % width, (star[1] + (1 + star[2])) % height, star[2])

# Add this function
def apply_upgrade(player, upgrade_type):
    if upgrade_type == "shield":
        player.shield = True
    elif upgrade_type == "speed":
        player.increase_speed()
    elif upgrade_type == "shrink":
        player.shrink()
    elif upgrade_type == "invincibility":
        player.invincible = True
    elif upgrade_type == "magnet":
        player.magnet = True

def draw_heart(surface, x, y, width, height):
    color = (255, 0, 0)  # Red color for hearts
    
    # Draw the main circles of the heart
    pygame.draw.circle(surface, color, (x + width // 4, y + height // 4), width // 4)
    pygame.draw.circle(surface, color, (x + width * 3 // 4, y + height // 4), width // 4)
    
    # Draw the bottom triangle of the heart
    points = [
        (x, y + height // 4),
        (x + width // 2, y + height),
        (x + width, y + height // 4)
    ]
    pygame.draw.polygon(surface, color, points)

def draw_hearts(health, x, y, size=30):
    for i in range(health):
        pygame.draw.polygon(window, red, [
            (x + i * (size + 5), y + size // 4),
            (x + i * (size + 5) + size // 2, y),
            (x + i * (size + 5) + size, y + size // 4),
            (x + i * (size + 5) + size // 2, y + size)
        ])
        pygame.draw.circle(window, red, (x + i * (size + 5) + size // 4, y + size // 4), size // 4)
        pygame.draw.circle(window, red, (x + i * (size + 5) + size * 3 // 4, y + size // 4), size // 4)

def game_loop():
    global score, high_score, level, enemy_list, enemy_speed, paused, particle_list, player_trail

    player = Player()
    hazards = []
    upgrades = []
    score = 0
    level = 0
    star_system = STAR_SYSTEMS[level % len(STAR_SYSTEMS)]
    particle_list = []
    player_trail = []

    level_threshold = 50
    spawn_rate = 0.05

    # Power-up timers
    power_up_timers = {upgrade: 0 for upgrade in UPGRADES if "duration" in UPGRADES[upgrade]}

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return score

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.pos[0] > 0:
            player.pos[0] -= player.speed
        if keys[pygame.K_RIGHT] and player.pos[0] < width - player.size:
            player.pos[0] += player.speed

        # Level up check
        if score >= (level + 1) * level_threshold:
            level += 1
            star_system = STAR_SYSTEMS[level % len(STAR_SYSTEMS)]
            for hazard_type in HAZARDS:
                HAZARDS[hazard_type]["speed"] += 0.1
            spawn_rate = min(0.05 * (1 + level * 0.05), 0.3)

        # Spawn hazards and upgrades
        if random.random() < spawn_rate:
            hazards.append(Hazard(random.choice(list(HAZARDS.keys()))))
        if random.random() < 0.01:
            upgrades.append(Upgrade(random.choice(list(UPGRADES.keys()))))

        # Update positions and check for dodged hazards
        for hazard in hazards[:]:
            hazard.update(player.pos)
            if hazard.pos[1] > height:
                hazards.remove(hazard)
                score += 1
                player.combo += 1
                if player.combo % 10 == 0:
                    score += player.combo // 10

        # Update power-ups
        for upgrade in upgrades[:]:
            upgrade.update()
            if upgrade.pos[1] > height:
                upgrades.remove(upgrade)

        # Check collisions
        player_rect = pygame.Rect(player.pos[0], player.pos[1], player.size, player.size)
        for hazard in hazards[:]:
            if player_rect.colliderect(pygame.Rect(hazard.pos[0], hazard.pos[1], hazard.size, hazard.size)):
                if not player.invincible:
                    if player.shield:
                        player.shield = False
                    else:
                        player.health -= 1
                        player.combo = 0
                    create_particles(player.pos[0] + player.size // 2, player.pos[1] + player.size // 2, red)
                    if player.health <= 0:
                        return score
                hazards.remove(hazard)

        for upgrade in upgrades[:]:
            if player_rect.colliderect(pygame.Rect(upgrade.pos[0], upgrade.pos[1], upgrade.size, upgrade.size)):
                if "duration" in UPGRADES[upgrade.type]:
                    power_up_timers[upgrade.type] = UPGRADES[upgrade.type]["duration"] * 60  # 60 FPS
                apply_upgrade(player, upgrade.type)
                create_particles(upgrade.pos[0] + upgrade.size // 2, upgrade.pos[1] + upgrade.size // 2, UPGRADES[upgrade.type]["color"])
                upgrades.remove(upgrade)

        # Handle special ability
        if keys[pygame.K_SPACE] and player.activate_special():
            for hazard in hazards[:]:
                create_particles(hazard.pos[0] + hazard.size // 2, hazard.pos[1] + hazard.size // 2, hazard.color)
                hazards.remove(hazard)
                score += 1

        # Apply power-up effects
        for upgrade, timer in power_up_timers.items():
            if timer > 0:
                power_up_timers[upgrade] -= 1
                if power_up_timers[upgrade] == 0:
                    if upgrade == "speed":
                        player.speed = 10
                    elif upgrade == "shrink":
                        player.size = 50
                    elif upgrade == "invincibility":
                        player.invincible = False
                    elif upgrade == "magnet":
                        player.magnet = False

        if power_up_timers["speed"] > 0:
            player.speed = min(player.speed, MAX_PLAYER_SPEED)
        else:
            player.speed = 10

        if power_up_timers["shrink"] > 0:
            player.size = max(player.size, MIN_PLAYER_SIZE)
        else:
            player.size = 50

        player.invincible = power_up_timers["invincibility"] > 0

        if power_up_timers["magnet"] > 0:
            # Implement magnet logic here
            for upgrade in upgrades:
                dx = player.pos[0] - upgrade.pos[0]
                dy = player.pos[1] - upgrade.pos[1]
                dist = (dx**2 + dy**2)**0.5
                if dist < 200:
                    upgrade.pos[0] += dx / dist * 5
                    upgrade.pos[1] += dy / dist * 5
            power_up_timers["magnet"] -= 1

        # Draw everything
        window.blit(background, (0, 0))
        draw_player(player)
        for hazard in hazards:
            hazard.draw()
        for upgrade in upgrades:
            upgrade.draw()
        draw_particles()
        update_particles()

        # Display score, level, and power-up status
        draw_text(f"Score: {score}", white, 10, 10)
        draw_text(f"Level: {level + 1} - {star_system}", white, 10, 50)
        draw_hearts(player.health, width - 110, 10)
        
        active_power_ups = [upgrade for upgrade, timer in power_up_timers.items() if timer > 0]
        if player.shield:
            active_power_ups.append("shield")
        for i, power_up in enumerate(active_power_ups):
            if power_up == "shield":
                draw_text(f"{power_up.capitalize()}: Active", UPGRADES[power_up]["color"], 10, 90 + i * 30)
            else:
                draw_text(f"{power_up.capitalize()}: {power_up_timers[power_up]//60}s", UPGRADES[power_up]["color"], 10, 90 + i * 30)

        pygame.display.flip()
        pygame.time.Clock().tick(60)

    return score

def show_game_over_screen(final_score):
    window.fill(black)
    draw_text("GAME OVER", red, width // 2, height // 8, size=50, align="center")
    draw_text(f"Your Score: {final_score}", white, width // 2, height // 4, align="center")
    draw_text(f"Final Level: {level + 1} - {STAR_SYSTEMS[level % len(STAR_SYSTEMS)]}", white, width // 2, height // 3, align="center")
    
    top_scores = get_top_scores()
    for i, (top_score, date) in enumerate(top_scores, 1):
        date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
        score_text = f"{i}. {top_score:5d} - {formatted_date}"
        draw_text(score_text, white, width // 2, height // 2 - 40 + i * 30, align="center")
    
    highest_score, highest_date = get_highest_score()
    highest_date_obj = datetime.strptime(highest_date, "%Y-%m-%d %H:%M:%S")
    formatted_highest_date = highest_date_obj.strftime("%Y-%m-%d %H:%M")
    draw_text(f"Highest Score: {highest_score} - {formatted_highest_date}", green, width // 2, height - 100, align="center")
    
    draw_text("Press ENTER to play again or ESC to quit", white, width // 2, height - 50, align="center")
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True
                elif event.key == pygame.K_ESCAPE:
                    return False

    return True

if __name__ == "__main__":
    high_score = get_high_score()
    show_start_screen()
    while True:
        final_score = game_loop()
        insert_score(final_score)  # Always insert the score
        if final_score > high_score:
            high_score = final_score
        if not show_game_over_screen(final_score):
            break

    pygame.quit()
    sys.exit()