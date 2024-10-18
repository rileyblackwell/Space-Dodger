import sqlite3

# Global connection variable
conn = None

def init_db(db_name='game_data.db'):
    global conn
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS high_scores
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  score INTEGER NOT NULL,
                  date TEXT NOT NULL)''')
    conn.commit()

def insert_score(score):
    global conn
    c = conn.cursor()
    
    # Get the current number of scores
    c.execute("SELECT COUNT(*) FROM high_scores")
    count = c.fetchone()[0]
    
    if count < 5:
        # If we have less than 5 scores, just insert the new score
        c.execute("INSERT INTO high_scores (score, date) VALUES (?, datetime('now'))", (score,))
    else:
        # Get the lowest score
        c.execute("SELECT MIN(score) FROM high_scores")
        lowest_score = c.fetchone()[0]
        
        if score > lowest_score:
            # If the new score is higher than the lowest score, replace it
            c.execute("DELETE FROM high_scores WHERE score = (SELECT MIN(score) FROM high_scores)")
            c.execute("INSERT INTO high_scores (score, date) VALUES (?, datetime('now'))", (score,))
    
    conn.commit()

def get_high_score():
    global conn
    c = conn.cursor()
    c.execute("SELECT MAX(score) FROM high_scores")
    result = c.fetchone()[0]
    return result if result is not None else 0

def get_top_scores(limit=5):
    global conn
    c = conn.cursor()
    c.execute("SELECT score, date FROM high_scores ORDER BY score DESC LIMIT ?", (limit,))
    return c.fetchall()

def get_highest_score():
    global conn
    c = conn.cursor()
    c.execute("SELECT score, date FROM high_scores ORDER BY score DESC LIMIT 1")
    result = c.fetchone()
    return result if result else (0, "N/A")

def close_db():
    global conn
    if conn:
        conn.close()
        conn = None
