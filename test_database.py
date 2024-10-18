import unittest
import sqlite3
from database import init_db, insert_score, get_high_score, get_top_scores, get_highest_score, close_db

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Use a new in-memory database for each test
        self.conn = sqlite3.connect(':memory:')
        self.original_conn = sqlite3.connect
        sqlite3.connect = lambda _: self.conn
        init_db(':memory:')

    def tearDown(self):
        close_db()
        sqlite3.connect = self.original_conn
        self.conn.close()

    def test_insert_and_get_high_score(self):
        insert_score(100)
        insert_score(200)
        insert_score(150)
        self.assertEqual(get_high_score(), 200)

    def test_get_top_scores(self):
        scores = [100, 200, 150, 300, 250]
        for score in scores:
            insert_score(score)
        top_scores = get_top_scores()
        self.assertEqual(len(top_scores), 5)
        self.assertEqual(top_scores[0][0], 300)
        self.assertEqual(top_scores[-1][0], 100)

    def test_update_high_score(self):
        insert_score(100)
        self.assertEqual(get_high_score(), 100)
        insert_score(200)
        self.assertEqual(get_high_score(), 200)
        insert_score(150)
        self.assertEqual(get_high_score(), 200)

    def test_get_highest_score(self):
        insert_score(100)
        insert_score(200)
        insert_score(150)
        highest_score, date = get_highest_score()
        self.assertEqual(highest_score, 200)
        self.assertIsNotNone(date)

    def test_get_highest_score_empty_db(self):
        highest_score, date = get_highest_score()
        self.assertEqual(highest_score, 0)
        self.assertEqual(date, "N/A")

if __name__ == '__main__':
    unittest.main()
