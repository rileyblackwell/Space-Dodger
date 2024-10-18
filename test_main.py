import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import random

# Set the environment variable to disable print statements
os.environ['PYTEST_CURRENT_TEST'] = 'yes'

# Mock the entire pygame module
sys.modules['pygame'] = MagicMock()
import pygame

# Now import main after mocking pygame
import main

class TestGameFunctions(unittest.TestCase):
    def setUp(self):
        main.width = 800
        main.height = 600
        main.player_size = 50
        main.enemy_size = 50
        main.power_up_size = 30
        main.enemy_speed = 5
        main.power_up_speed = 3
        main.player_trail = []
        main.particle_list = []
        main.stars = [(random.randint(0, main.width), random.randint(0, main.height), random.random()) for _ in range(100)]
        main.score = 0
        main.UPGRADES = {
            "shield": {"color": main.yellow},
            "speed": {"color": main.blue},
            "shrink": {"color": main.green}
        }

    def test_player_class(self):
        player = main.Player()
        self.assertEqual(player.size, 50)
        self.assertEqual(player.pos, [main.width // 2, main.height - 2 * player.size])
        self.assertEqual(player.speed, 10)
        self.assertEqual(player.health, 3)
        self.assertFalse(player.shield)
        self.assertEqual(player.design, 0)

    def test_hazard_class(self):
        hazard = main.Hazard("asteroid")
        self.assertEqual(hazard.type, "asteroid")
        self.assertEqual(hazard.size, main.HAZARDS["asteroid"]["size"])
        self.assertEqual(hazard.speed, main.HAZARDS["asteroid"]["speed"])
        self.assertEqual(hazard.color, main.HAZARDS["asteroid"]["color"])
        self.assertTrue(0 <= hazard.pos[0] <= main.width - hazard.size)
        self.assertEqual(hazard.pos[1], -hazard.size)

    def test_upgrade_class(self):
        with patch.object(main, 'Upgrade', return_value=MagicMock(type="shield", color=main.yellow, size=30, pos=[0, -30], speed=3)):
            upgrade = main.Upgrade("shield")
            self.assertEqual(upgrade.type, "shield")
            self.assertEqual(upgrade.color, main.UPGRADES["shield"]["color"])
            self.assertEqual(upgrade.size, 30)
            self.assertEqual(upgrade.pos[1], -upgrade.size)
            self.assertEqual(upgrade.speed, 3)

    def test_apply_upgrade(self):
        player = main.Player()
        main.apply_upgrade(player, "shield")
        self.assertTrue(player.shield)

        player = main.Player()
        original_speed = player.speed
        main.apply_upgrade(player, "speed")
        self.assertEqual(player.speed, original_speed * 1.5)

        player = main.Player()
        original_size = player.size
        main.apply_upgrade(player, "shrink")
        self.assertEqual(player.size, original_size * 0.8)

    def test_show_game_over_screen(self):
        with patch('main.draw_text'), \
             patch('main.pygame.display.flip'), \
             patch('main.pygame.event.get', return_value=[MagicMock(type=main.pygame.KEYDOWN, key=main.pygame.K_RETURN)]):
            
            result = main.show_game_over_screen(100)
            self.assertTrue(result)

        with patch('main.draw_text'), \
             patch('main.pygame.display.flip'), \
             patch('main.pygame.event.get', return_value=[MagicMock(type=main.pygame.KEYDOWN, key=main.pygame.K_ESCAPE)]):
            
            result = main.show_game_over_screen(100)
            self.assertFalse(result)

    def test_show_start_screen(self):
        with patch('main.draw_text'), \
             patch('main.pygame.display.flip'), \
             patch('main.pygame.event.get', side_effect=[[], [MagicMock(type=main.pygame.KEYDOWN, key=main.pygame.K_SPACE)]]):
            
            main.show_start_screen()

    def test_create_and_update_particles(self):
        main.particle_list = []
        main.create_particles(100, 100, main.red)
        self.assertEqual(len(main.particle_list), 20)
        
        original_particles = [particle.copy() for particle in main.particle_list]
        main.update_particles()
        
        self.assertNotEqual(original_particles, main.particle_list)
        self.assertTrue(all(0 <= particle[5] <= 40 for particle in main.particle_list))

    def test_move_stars(self):
        original_stars = main.stars.copy()
        main.move_stars()
        self.assertNotEqual(original_stars, main.stars)
        self.assertEqual(len(original_stars), len(main.stars))

    def test_player_reset(self):
        player = main.Player()
        player.pos = [0, 0]
        player.speed = 20
        player.health = 1
        player.shield = True
        player.design = 2
        
        player.reset()
        
        self.assertEqual(player.pos, [main.width // 2, main.height - 2 * player.size])
        self.assertEqual(player.speed, 10)
        self.assertEqual(player.health, 3)
        self.assertFalse(player.shield)
        self.assertEqual(player.design, 0)

if __name__ == '__main__':
    unittest.main()
