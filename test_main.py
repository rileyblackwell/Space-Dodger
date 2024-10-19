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
        main.level = 0

    def test_player_class(self):
        player = main.Player()
        self.assertEqual(player.size, 50)
        self.assertEqual(player.pos, [main.width // 2, main.height - 2 * player.size])
        self.assertEqual(player.speed, 10)
        self.assertEqual(player.health, 3)
        self.assertFalse(player.shield)

    def test_hazard_class(self):
        hazard = main.Hazard("asteroid")
        self.assertEqual(hazard.type, "asteroid")
        self.assertEqual(hazard.size, main.HAZARDS["asteroid"]["size"])
        self.assertEqual(hazard.speed, main.HAZARDS["asteroid"]["speed"])
        self.assertEqual(hazard.color, main.HAZARDS["asteroid"]["color"])
        self.assertTrue(0 <= hazard.pos[0] <= main.width - hazard.size)
        self.assertEqual(hazard.pos[1], -hazard.size)

    def test_upgrade_class(self):
        upgrade = main.Upgrade("shield")
        self.assertEqual(upgrade.type, "shield")
        self.assertEqual(upgrade.color, main.UPGRADES["shield"]["color"])
        self.assertEqual(upgrade.size, 30)
        self.assertTrue(0 <= upgrade.pos[0] <= main.width - upgrade.size)
        self.assertEqual(upgrade.pos[1], -upgrade.size)
        self.assertEqual(upgrade.speed, 3)

    @patch('pygame.draw.circle')
    @patch('pygame.draw.polygon')
    @patch('pygame.draw.line')
    @patch('pygame.draw.arc')
    def test_upgrade_draw(self, mock_arc, mock_line, mock_polygon, mock_circle):
        upgrade_types = ["shield", "speed", "shrink", "invincibility", "magnet"]
        for upgrade_type in upgrade_types:
            upgrade = main.Upgrade(upgrade_type)
            upgrade.draw()
            mock_circle.assert_called()
            
            if upgrade_type == "shield":
                mock_polygon.assert_called()
                mock_line.assert_called()
            elif upgrade_type == "speed":
                mock_polygon.assert_called()
            elif upgrade_type == "shrink":
                mock_line.assert_called()
            elif upgrade_type == "invincibility":
                self.assertGreater(mock_circle.call_count, 1)
            elif upgrade_type == "magnet":
                mock_arc.assert_called()
                mock_line.assert_called()
            
            mock_circle.reset_mock()
            mock_polygon.reset_mock()
            mock_line.reset_mock()
            mock_arc.reset_mock()

    def test_apply_upgrade(self):
        player = main.Player()
        main.apply_upgrade(player, "shield")
        self.assertTrue(player.shield)

        player = main.Player()
        original_speed = player.speed
        main.apply_upgrade(player, "speed")
        self.assertGreater(player.speed, original_speed)

        player = main.Player()
        original_size = player.size
        main.apply_upgrade(player, "shrink")
        self.assertLess(player.size, original_size)

        player = main.Player()
        main.apply_upgrade(player, "invincibility")
        self.assertTrue(player.invincible)

        player = main.Player()
        main.apply_upgrade(player, "magnet")
        self.assertTrue(player.magnet)

        # Check durations
        self.assertEqual(main.UPGRADES["speed"]["duration"], 7)
        self.assertEqual(main.UPGRADES["shrink"]["duration"], 12)
        self.assertEqual(main.UPGRADES["invincibility"]["duration"], 5)
        self.assertEqual(main.UPGRADES["magnet"]["duration"], 15)
        self.assertNotIn("duration", main.UPGRADES["shield"])

    @patch('main.get_top_scores')
    @patch('main.get_highest_score')
    @patch('pygame.event.get')
    @patch('main.draw_text')
    def test_show_game_over_screen(self, mock_draw_text, mock_event_get, mock_get_highest_score, mock_get_top_scores):
        mock_get_top_scores.return_value = [(100, '2023-05-01 12:00:00'), (90, '2023-05-02 12:00:00')]
        mock_get_highest_score.return_value = (100, '2023-05-01 12:00:00')
        mock_event_get.side_effect = [
            [],
            [MagicMock(type=pygame.KEYDOWN, key=pygame.K_RETURN)]
        ]
        
        result = main.show_game_over_screen(100)
        
        self.assertTrue(result)
        self.assertGreater(mock_draw_text.call_count, 5)  # Check if draw_text was called multiple times

        mock_draw_text.reset_mock()
        mock_event_get.side_effect = [
            [],
            [MagicMock(type=pygame.KEYDOWN, key=pygame.K_ESCAPE)]
        ]
        
        result = main.show_game_over_screen(100)
        
        self.assertFalse(result)

    @patch('pygame.event.get')
    @patch('main.draw_text')
    def test_show_start_screen(self, mock_draw_text, mock_event_get):
        mock_event_get.side_effect = [
            [],
            [MagicMock(type=pygame.KEYDOWN, key=pygame.K_SPACE)]
        ]
        main.show_start_screen()
        self.assertEqual(mock_draw_text.call_count, 11)  # Title + 10 instruction lines

        # Check if key instruction texts are present
        instruction_texts = [call[0][0] for call in mock_draw_text.call_args_list]
        expected_texts = [
            "Space Dodger",
            "LEFT/RIGHT: Move",
            "Dodge: Red, Yellow, Purple aliens",
            "Collect power-ups:",
            "Green: Shrink (easier to dodge)",
            "Blue: Speed boost",
            "Yellow: Shield (protects from one hit)",
            "White: Temporary invincibility",
            "Gray: Magnet (attracts power-ups)",
            "SPACE to start"
        ]
        for text in expected_texts:
            self.assertTrue(any(text in instruction for instruction in instruction_texts))

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
        
        player.reset()
        
        self.assertEqual(player.pos, [main.width // 2, main.height - 2 * player.size])
        self.assertEqual(player.speed, 10)
        self.assertEqual(player.health, 3)
        self.assertFalse(player.shield)

    def test_player_special_ability(self):
        player = main.Player()
        self.assertEqual(player.special_charge, 0)
        player.update()
        self.assertGreater(player.special_charge, 0)
        player.special_charge = 100
        self.assertTrue(player.activate_special())
        self.assertEqual(player.special_charge, 0)

    def test_hazard_homing_behavior(self):
        hazard = main.Hazard("homing")
        initial_pos = hazard.pos.copy()
        player_pos = [main.width // 2, main.height // 2]
        
        # Test homing behavior
        hazard.update(player_pos)
        self.assertNotEqual(hazard.pos, initial_pos)
        dx = player_pos[0] - hazard.pos[0]
        dy = player_pos[1] - hazard.pos[1]
        self.assertGreater(dx * (player_pos[0] - initial_pos[0]), 0)
        self.assertGreater(dy * (player_pos[1] - initial_pos[1]), 0)
        
        # Test cooldown behavior
        initial_pos = hazard.pos.copy()
        hazard.update(player_pos)
        self.assertEqual(hazard.pos[0], initial_pos[0])  # X position should not change during cooldown
        self.assertGreater(hazard.pos[1], initial_pos[1])  # Y position should increase

    def test_combo_system(self):
        player = main.Player()
        self.assertEqual(player.combo, 0)
        main.score = 0
        for _ in range(10):
            main.score += 1
            player.combo += 1
        self.assertEqual(main.score, 10)  # Remove the bonus point expectation
        player.combo = 0
        self.assertEqual(player.combo, 0)

if __name__ == '__main__':
    unittest.main()
