from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import database
import datetime
import random # For varied responses if needed

app = Flask(__name__)
app.secret_key = 'super_secret_key_hostel_hub'

def get_db():
    conn = sqlite3.connect(database.DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ... [PREVIOUS ROUTES REMAIN UNCHANGED] ...

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and user['password'] == password: 
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['name'] = user['name']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('auth.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    name = request.form['name']
    email = request.form['email']
    role = request.form.get('role', 'student')
    
    try:
        conn = get_db()
        conn.execute('INSERT INTO users (username, password, name, email, role) VALUES (?, ?, ?, ?, ?)',
                     (username, password, name, email, role))
        conn.commit()
        conn.close()
        flash('Registration successful! Please login.')
    except sqlite3.IntegrityError:
        flash('Username or Email already exists.')
        
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    conn = get_db()
    if request.method == 'POST':
        phone = request.form.get('phone')
        new_pass = request.form.get('password')
        
        if new_pass:
            conn.execute('UPDATE users SET phone = ?, password = ? WHERE id = ?', (phone, new_pass, session['user_id']))
        else:
            conn.execute('UPDATE users SET phone = ? WHERE id = ?', (phone, session['user_id']))
        conn.commit()
        flash('Profile updated!')
    
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    if session['role'] == 'student':
        complaints = conn.execute('SELECT * FROM complaints WHERE student_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        return render_template('dashboard.html', complaints=complaints, user=user)
    else:
        role = session['role']
        complaints = conn.execute('SELECT * FROM complaints WHERE current_handler_role = ? AND status != "resolved" ORDER BY created_at DESC', (role,)).fetchall()
        conn.close()
        return render_template('dashboard.html', complaints=complaints, role=role)

@app.route('/complaint/create', methods=['POST'])
def create_complaint():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    conn.execute('INSERT INTO complaints (student_id, student_name, title, category, description, current_handler_role) VALUES (?, ?, ?, ?, ?, "warden")', 
                 (session['user_id'], session['name'], request.form['title'], request.form['category'], request.form['description']))
    conn.commit()
    conn.close()
    flash('Complaint submitted successfully!')
    return redirect(url_for('dashboard'))

@app.route('/complaint/<int:id>')
def view_complaint(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    complaint = conn.execute('SELECT * FROM complaints WHERE id = ?', (id,)).fetchone()
    responses = conn.execute('SELECT * FROM complaint_responses WHERE complaint_id = ? ORDER BY timestamp ASC', (id,)).fetchall()
    conn.close()
    return render_template('complaint.html', complaint=complaint, responses=responses)

@app.route('/complaint/<int:id>/escalate', methods=['POST'])
def escalate_complaint(id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    role = session['role']
    next_role = 'hod' if role == 'warden' else 'principal' if role == 'hod' else None
    if next_role:
        conn = get_db()
        conn.execute('UPDATE complaints SET current_handler_role = ?, status = ? WHERE id = ?', (next_role, 'escalated', id))
        conn.execute('INSERT INTO complaint_responses (complaint_id, responder_role, message) VALUES (?, ?, ?)', (id, role, f"Escalated complaint to {next_role.upper()}"))
        conn.commit()
        conn.close()
        flash(f'Complaint escalated to {next_role}')
    return redirect(url_for('dashboard'))

@app.route('/complaint/<int:id>/resolve', methods=['POST'])
def resolve_complaint(id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    conn.execute('UPDATE complaints SET status = ?, resolved_at = CURRENT_TIMESTAMP WHERE id = ?', ('resolved', id))
    conn.execute('INSERT INTO complaint_responses (complaint_id, responder_role, message) VALUES (?, ?, ?)', (id, session['role'], "RESOLVED: Issue addressed."))
    conn.commit()
    conn.close()
    flash('Complaint resolved.')
    return redirect(url_for('dashboard'))

@app.route('/api/stats')
def get_stats():
    if session.get('role') == 'student': return jsonify({})
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM complaints').fetchone()[0]
    resolved = conn.execute('SELECT COUNT(*) FROM complaints WHERE status="resolved"').fetchone()[0]
    pending = conn.execute('SELECT COUNT(*) FROM complaints WHERE status!="resolved"').fetchone()[0]
    cats = conn.execute('SELECT category, COUNT(*) FROM complaints GROUP BY category').fetchall()
    conn.close()
    return jsonify({'total': total, 'resolved': resolved, 'pending': pending, 'categories': {row[0]: row[1] for row in cats}})

# --- Enhanced Chatbot Logic ---
@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    msg = request.json.get('message', '').lower().strip()
    response = ""

    if any(x in msg for x in ['hi', 'hello', 'hey', 'start']):
        response = "<b>Hello! 👋 I am the HostelHub Assistant.</b><br>I can help you with:<br>• Filing a Complaint<br>• Mess Menu & Timings<br>• WiFi & Internet<br>• Cleaning Schedule<br>• Emergency Contacts"

    elif 'complaint' in msg or 'file' in msg or 'report' in msg:
        response = "To file a complaint, go to your <b>Dashboard</b> and click the <b>'File New Complaint'</b> button at the top right. Select a category (WiFi, Mess, etc.) and describe your issue."

    elif 'wifi' in msg or 'internet' in msg or 'net' in msg:
        response = "<b>WiFi Information 📶</b><br>• Network: HostelHub_Student<br>• Limit: 10GB/day per student.<br>• Password resets every month.<br>If speed is slow, please file a complaint under 'Facilities'."

    elif 'food' in msg or 'mess' in msg or 'menu' in msg or 'breakfast' in msg or 'dinner' in msg:
        response = "<b>Mess Timings 🍽️</b><br>• Breakfast: 7:30 AM - 9:00 AM<br>• Lunch: 12:30 PM - 2:00 PM<br>• Snacks: 5:00 PM - 6:00 PM<br>• Dinner: 7:30 PM - 9:00 PM<br><i>Menu is updated every Monday on the notice board.</i>"

    elif 'clean' in msg or 'dust' in msg or 'sweep' in msg:
        response = "<b>Cleaning Schedule 🧹</b><br>• Rooms: Every alternate day (10 AM - 4 PM).<br>• Corridors: Daily (9 AM).<br>• Bathrooms: Twice daily.<br>If your room wasn't cleaned, file a 'Cleanliness' complaint."

    elif 'water' in msg or 'electric' in msg or 'power' in msg or 'light' in msg:
        response = "For power cuts or water shortage 💧, please report it immediately via the complaint system. For major electrical hazards, contact the warden directly."

    elif 'warden' in msg or 'contact' in msg or 'emergency' in msg:
        response = "<b>Emergency Contacts 🚨</b><br>• Warden: +91-9876543210 (Mr. Sharma)<br>• Ambulance: 108<br>• Security Gate: Ext 101<br>For general queries, visit the Warden Office (Ground Floor)."
    
    else:
        response = "I'm not sure about that yet. 🤔<br>Try asking about <b>Mess, WiFi, Cleaning, or Complaints</b>.<br>Or contact the warden for specific queries."
        
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)
