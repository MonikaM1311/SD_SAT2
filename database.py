
import sqlite3

DATABASE = "exam.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            exam_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            duration INTEGER NOT NULL,
            status TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            question_id INTEGER PRIMARY KEY,
            exam_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            marks INTEGER NOT NULL,
            FOREIGN KEY (exam_id) REFERENCES exams(exam_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            candidate_id TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            answer TEXT NOT NULL,
            PRIMARY KEY (candidate_id, question_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            candidate_id TEXT NOT NULL,
            exam_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total_marks INTEGER NOT NULL,
            PRIMARY KEY (candidate_id, exam_id)
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO exams
        VALUES (101, 'Python Examination', 60, 'AVAILABLE')
    """)

    sample_questions = [
        (1, 101, "Which language is used with Flask?", "Python", 1),
        (2, 101, "Which data type stores True or False?", "Boolean", 1),
        (3, 101, "Which HTTP method retrieves data?", "GET", 1)
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO questions
        VALUES (?, ?, ?, ?, ?)
    """, sample_questions)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully!")
