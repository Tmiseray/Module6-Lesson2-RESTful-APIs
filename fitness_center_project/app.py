from flask import Flask, jsonify, request
from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields, ValidationError
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from db_password import my_password

# ---------------------------------------------------------------------------
app = Flask(__name__)
ma = Marshmallow(app)

def get_db_connection():
    """ Connect to the MySQL database and return the connection object """
    # Database connection parameters
    db_name = "fitness_center_db"
    user = "root"
    password = my_password  # <-- Make sure to update db_password.py
    host = "localhost"      #       with your own password

    try:
    # Attempting to establish a connection
        conn =  mysql.connector.connect(
            database = db_name,
            user = user,
            password = password,
            host = host
        )

        # Check if the connection is successful
        print("Connected to MySQL database successfully")
        return conn

    except Error as e:
        # Handling any connection errors
        print(f"Error: {e}")
        return None
    
# -------------------------------------------------------------------------------
# Schema Classes for Database Tables
# -------------------------------------------------------------------------------

class MemberSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    age = fields.Int(required=True)
    email = fields.Str(required=False)
    phone = fields.Str(required=False)

class WorkoutSessionSchema(ma.Schema):
    session_id = fields.Int(dump_only=True)
    member_id = fields.Int(required=False)
    session_date = fields.Date(required=True)
    session_time = fields.Str(required=False)
    activity = fields.Str(required=False)
    duration_minutes = fields.Int(required=False)
    calories_burned = fields.Int(required=False)

member_schema = MemberSchema()
members_schema = MemberSchema(many=True)
workout_session_schema = WorkoutSessionSchema()
workout_sessions_schema = WorkoutSessionSchema(many=True)

# -------------------------------------------------------------------------------
# CRUD operations for Members table data
# -------------------------------------------------------------------------------
# Add a New Member ['POST']
@app.route('/members', methods=['POST'])
def add_member():
    try:
        member = member_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        query = "INSERT INTO Members (name, age) VALUES (%s, %s)"
        cursor.execute(query, (member['name'], member['age']))

        conn.commit()
        return jsonify({"message": "New Member added successfully"}), 201
    
    except Error as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()

# -------------------------------------------------------------------------------
# Retrieve All Members' data ['GET']
@app.route('/members', methods=['GET'])
def get_members():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM Members"
        cursor.execute(query)
        books = cursor.fetchall()

        return members_schema.jsonify(books)
    
    except Error as e:
        print(f"Error: {e}")
        return jsonify({"Error": "Internal Server Error"}), 500
    
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# -------------------------------------------------------------------------------
# Retrieve a Specific Member's data ['GET']
@app.route('/members/<int:id>', methods=['GET'])
def get_member_by_id(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database Connection failed"}), 500
    
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM Members WHERE id = %s"
    cursor.execute(query, (id,))
    member = cursor.fetchone()
    cursor.close()
    conn.close()

    if member:
        return member_schema.jsonify(member)
    else:
        return jsonify({"error": "Member not found"}), 404

# -------------------------------------------------------------------------------
# Update a Member's data ['PUT']
@app.route('/members/<int:id>', methods=['PUT'])
def update_member(id):
    try:
        member_data = member_schema.load(request.json)
    except ValidationError as e:
        print(f"Error: {e}")
        return jsonify(e.messages), 400
    
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor()

        updated_member = (member_data['name'], member_data['age'], member_data['email'], member_data['phone'], id)

        query = "UPDATE Members SET name = %s, age = %s, email = %s, phone = %s WHERE id = %s"
        cursor.execute(query, updated_member)
        conn.commit()

        return jsonify({"message": "Updated the member successfully"}), 201
    except Error as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# -------------------------------------------------------------------------------
# Delete a Member's data ['DELETE']
# Integrated Cascading Deletes within my fitness_center_db ensuring the associated sessions would be deleted if the member data is being deleted
@app.route('/members/<int:id>', methods=['DELETE'])
def delete_member(id):
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor()

        # Verify the member exists
        cursor.execute("SELECT * FROM Members WHERE id = %s", (id,))
        customer = cursor.fetchone()
        if not customer:
            return jsonify({"error": "Member not found"}), 404
        
        # Delete the member and any associated data/sessions
        query = "DELETE FROM Members WHERE id = %s"
        cursor.execute(query, (id,))
        conn.commit()

        return jsonify({"message": "Member removed successfully"}), 200
    except Error as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# -------------------------------------------------------------------------------
# # CRUD operations for WorkoutSessions table data
# # -------------------------------------------------------------------------------
# Schedule a Workout Session ['POST']
@app.route('/workout_sessions', methods=['POST'])
def schedule_session():
    try:
        session = workout_session_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        query = """
        INSERT INTO WorkoutSessions (member_id, session_date, session_time)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (session['member_id'], session['session_date'], session['session_time']))

        conn.commit()
        return jsonify({"message": "Workout session scheduled successfully"}), 201
    except Error as e:
        return jsonify({"error": str(e)})
    
    finally:
        cursor.close()
        conn.close()

# -------------------------------------------------------------------------------
# # Update a Workout Session's data ['PUT']

@app.route('/workout_sessions_by_member_id/<int:id>/<string:session_date>', methods=['PUT'])
def update_session_by_member_id(id, session_date):
    # Parse session date and validate format
    try:
        session_date_obj = datetime.strptime(session_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    
    # Validate JSON body exists
    if not request.json:
        return jsonify({"error": "Invalid input"}), 400
    
    try:
        session_data = workout_session_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    # Get database connection
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)

        # Check if the member with the given ID has any workout sessions
        cursor.execute("SELECT * FROM WorkoutSessions WHERE member_id = %s AND session_date = %s", (id, session_date_obj))
        session = cursor.fetchone()
        if not session:
            return jsonify({"error": "Workout session for member not found"}), 404

        # Get the values from the request JSON
        new_session_date = session_data.get('session_date', session['session_date'])
        session_time = session_data.get('session_time', session['session_time'])
        activity = session_data.get('activity', session['activity'])
        duration_minutes = session_data.get('duration_minutes', session['duration_minutes'])
        calories_burned = session_data.get('calories_burned', session['calories_burned'])

        # Validate and parse the new session date if provided
        if session_date != session['session_date']:
            try:
                session_date = datetime.strptime(session_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Invalid new session date format. Use YYYY-MM-DD."}), 400

        # Prepare the update query
        update_query = """
        UPDATE WorkoutSessions
        SET session_date = %s, session_time = %s, activity = %s, duration_minutes = %s, calories_burned = %s
        WHERE member_id = %s AND session_date = %s
        """

        # Execute the update query
        cursor.execute(update_query, (new_session_date, session_time, activity, duration_minutes, calories_burned, id, session['session_date']))
        conn.commit()

        return jsonify({"message": "Workout session updated successfully"}), 200
    
    except Error as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# -------------------------------------------------------------------------------
# Retrieve a Specific Member's Workout Sessions & Details ['GET']
@app.route('/workout_sessions_by_member_id', methods=['GET'])
def sessions_for_member():
    member_id = request.args.get('member_id')
    if not member_id:  # Ensure member_id is provided
        return jsonify({"error": "Member ID is required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                session_id, session_date, session_time, activity, duration_minutes, calories_burned
            FROM
                WorkoutSessions
            WHERE
                member_id = %s
        """
        cursor.execute(query, (member_id,))
        sessions = cursor.fetchall()

        return workout_sessions_schema.jsonify(sessions)
    
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# -------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)