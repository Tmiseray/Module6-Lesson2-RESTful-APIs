fitness_center_db = "CREATE DATABASE fitness_center_db;"

MembersTable = """
CREATE TABLE Members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INT NOT NULL
    email VARCHAR(320) UNIQUE,
    phone VARCHAR(15)
);"""

WorkoutSessionsTable = """
CREATE TABLE WorkoutSessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT,
    session_date DATE,
    session_time VARCHAR(50),
    activity VARCHAR(255),
    duration_minutes INT,
    calories_burned INT,
    FOREIGN KEY (member_id) REFERENCES Members(id) ON DELETE CASCADE
);"""