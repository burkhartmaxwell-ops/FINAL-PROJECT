import os
import random
import sqlite3
import requests

class Question: 

    def __init__(self, prompt, options, correct_answer, lore_note=""):
        self.prompt = prompt
        self.options = options
        self.correct_answer = correct_answer
        self.lore_note = lore_note 

    def display(self, q_num):

        print(f"\n[Question {q_num}] {self.prompt}")
        labels = ["A", "B", "C", "D"]
        for idx, option in enumerate(self.options):
            print(f" {labels[idx]}) {option}")
    
    def is_correct(self, user_choice_idx):
        return user_choice_idx == self.correct_answer
    
class DatabaseManager:
    
    def __init__(self, db_name="leaderboard.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):

        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS leaderboard (
                        id INTEGER PRIMARY KEY AUTOINCREMENT
                        player_name TEXT NOT NULL
                        score INTEGER NOT NULL
                        accuracy REAL NOT NULL
                        )
                """
                )
                conn.commit()
        except sqlite3.Error as e:
            print(f"[Database Error] Could not initialize database: {e}")

    def save_score(self, player_name, score, accuracy):

        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO leaderboard (player_name, score, accuracy)
                    VALUES (?, ?, ?)
                """,
                    (player_name, score, accuracy),
                )
                conn.commit()
                print("\n[DB Success] Score saved to local database!")
        except sqlite3.Error as e:
            print(f"[Database Error] Could not save score: {e}")

    def display_top_scores(self, limit=5):

        print("\n=== HIGH SCORE LEADERBOARD ===")
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT player_name, score, accuracy
                    FROM leaderboard
                    ORDER BY score DESC
                    LIMIT ?
                """,
                    (limit,),
                )
                rows = cursor.fetchall()

                if not rows:
                    print("No high scores recorded yet.")
                    return
            
                for idx, (name, score, acc) in enumerate(rows, start=1):
                    print(f"{idx}. {name:<12} | Score: {score:<5} | Accuracy: {acc:.1f}%")
        except sqlite3.Error as e:
            print(f"[Database Error] Failed to read leaderboard: {e}")

def fetch_questions_from_api():
    url = "https://opentdb.com/api.php?amount=5&category=15&type=multiple"
    questions = []

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("response_code") == 0:
            for item in data.get("results", []):
                prompt = (
                    item["question"]
                    .replace("&quot;", '"')
                    .replace("&#039;", "'")
                    .replace("&amp;", "&")
                )
                correct = (
                    item["correct_answer"]
                    .replace("&quot;", '"')
                    .replace("&#039;", "'")
                    .replace("&amp;", "&")
                )
                incorrects = [
                    i.replace("&quot;", '"')
                    .replace("&#039;", "'")
                    .replace("&amp;", "&")
                    for i in item["incorrect_answers"]
                ]

                options = incorrects + [correct]
                random.shuffle(options)
                correct_idx = options.index(correct)

                questions.append(
                    Question(prompt, options, correct_idx, "Web API Data")
                )
        print("[API Success] Downloaded fresh trivia questions from OpenTDB!")
        return questions

    except (requests.RequestException, ValueError) as e:
        print(f"\n[API Warning] Could not reach external server ({e}).")
        print("Falling back to local Kingdom Hearts question vault...")

    fallback_data = [
        {
            "prompt": "What is the name of Sora's iconic default keyblade?",
            "options": [
                "Way to the Dawn",
                "Kingdom Key",
                "Oathkeeper",
                "Oblivion",
            ],
            "correct": 1,
            "lore": "The Kingdom Key is drawn from the Realm of Light.",
        },
        {
            "prompt": "In KH Union X, what title is given to the leaders chosen by the Master of Masters",
            "options": [
                "The Foretellers",
                "The Dandelions",
                "Organization XIII",
                "Real Organization"
            ],
            "correct": 0,
            "lore": "The five Foretellers were assigned Roles by their Master.",

        },
        {
            "prompt": "What is the starting area in Birth By Sleep.",
            "options": [
                "Hollow Bastoin",
                "Castle Oblivion",
                "Radiant Garden",
                "Land of Departure"
            ],
            "correct": 3,
            "lore": "The Land of Departure ends up becoming Castle Oblivion.",

        },
                {
            "prompt": "Who is the hooded man in the secret fight in Kingdom Hearts 1?",
            "options": [
                "Xemnas",
                "Xigbar",
                "Ansem",
                "Jiminy Cricket"
            ],
            "correct": 0,
            "lore": "Xemnas is the leader of Organization 13.",

        },
    ]

    for item in fallback_data:
        questions.append(
            Question(
                item["prompt"], item["options"], item["correct"], item["lore"]
            )
        )
    return questions

def get_user_choice():
    label_map = {"A": 0, "B": 1, "C": 2, "D": 3}
    while True:
        choice = input("Enter your choice (A-D): ").strip().upper()
        if choice in label_map:
            return label_map[choice]
        print("Invalid entry! Please enter A, B, C, or D.")

def run_quiz(db): 
    print("\n--- Starting Trivia Run ---")
    questions = fetch_questions_from_api()

    score = 0 
    correct_count = 0
    total_questions = len(questions)

    for idx, q in enumerate(questions, start=1):
        q.display(idx)
        user_choice = get_user_choice()

        if q.is_correct(user_choice):
            score += 100
            correct_count += 1 
            print(">> Correct! +100 points!")
        else:
            correct_label = ["A", "B", "C", "D"][q.correct_answer]
            print(f">>Wrong! The correct answer was {correct_label}!")

        if q.lore_note:
            print(f"  Lore Note: {q.lore_note}")

    accuracy = (correct_count / total_questions) * 100
    print("\n" + "=" * 40)
    print("QUIZ COMPLETE!")
    print(f"Final Score: {score}")
    print(f"Accuracy:  {accuracy:.1f}% ({correct_count}/{total_questions})")

    name = input("Enter your player name for the database: ").strip()
    if not name:
        name = "Keyblade Wielder"
    db.save_score(name, score, accuracy)

def main():
    db = DatabaseManager()

    while True:
        print("\n=== VIDEO GAME TRIVIA ENGINE ===")
        print("1. Play Quiz")
        print("2. View Leaderboard")
        print("3. Quit")

        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            run_quiz(db)
        elif choice == "2":
            db.display_top_scores()
        elif choice == "3":
            print("Thank you for playing. Goodbye!")
            break
        else:
            print("Invalid Option. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
