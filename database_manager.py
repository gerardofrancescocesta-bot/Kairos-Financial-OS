
import os
import sqlite3
import pandas as pd
import bcrypt
import yfinance as yf
from datetime import datetime
from contextlib import contextmanager


DB_FILE = os.getenv("DB_PATH", "kairos.db")

# Ensure Database Directory Exists
db_dir = os.path.dirname(DB_FILE)
if db_dir and not os.path.exists(db_dir):
    try:
        os.makedirs(db_dir)
    except OSError:
        pass

@contextmanager
def db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

# --- INITIALIZATION ---
def init_db():
    with db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash BLOB, created_at TIMESTAMP, role TEXT DEFAULT 'USER')''')
        c.execute('''CREATE TABLE IF NOT EXISTS allowed_ips (id INTEGER PRIMARY KEY, user_id INTEGER, ip_address TEXT, device_name TEXT, status TEXT, last_used TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS assets (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, category TEXT, ticker TEXT, quantity REAL, avg_price REAL, current_price REAL, currency TEXT DEFAULT 'EUR')''')
        c.execute('''CREATE TABLE IF NOT EXISTS liabilities (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, category TEXT, remaining_balance REAL, monthly_payment REAL, interest_rate REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS cashflow (id INTEGER PRIMARY KEY, user_id INTEGER, type TEXT, category TEXT, name TEXT, amount REAL, frequency TEXT DEFAULT 'Monthly')''')
        c.execute('''CREATE TABLE IF NOT EXISTS routine (id INTEGER PRIMARY KEY, user_id INTEGER, time_slot TEXT, monday TEXT, tuesday TEXT, wednesday TEXT, thursday TEXT, friday TEXT, saturday TEXT, sunday TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS history_snapshots (id INTEGER PRIMARY KEY, user_id INTEGER, date TEXT, total_assets REAL, total_liabilities REAL, net_worth REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS career_skills (id INTEGER PRIMARY KEY, user_id INTEGER, skill_name TEXT, current_level INTEGER, target_level INTEGER, category TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS career_wins (id INTEGER PRIMARY KEY, user_id INTEGER, date TEXT, description TEXT, impact TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, target_amount REAL, current_amount REAL, deadline TEXT, status TEXT DEFAULT 'ACTIVE')''')
        conn.commit()
    
    # Bootstrap Admin
    bootstrap_admin()

def migrate_db():
    with db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'USER'")
        except:
            pass
        c.execute('''CREATE TABLE IF NOT EXISTS allowed_ips (id INTEGER PRIMARY KEY, user_id INTEGER, ip_address TEXT, device_name TEXT, status TEXT, last_used TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, target_amount REAL, current_amount REAL, deadline TEXT, status TEXT DEFAULT 'ACTIVE')''')
        conn.commit()

def bootstrap_admin():
    """Crea forzatamente l'utente Admin e approva l'IP locale"""
    # [SECURITY NOTICE] Default credentials for GitHub release. Change immediately in production env.
    admin_user = os.getenv("KAIROS_ADMIN_USER", "admin")
    admin_pass = os.getenv("KAIROS_ADMIN_PASS", "admin")
    
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (admin_user,))
        exists = c.fetchone()
        
        user_id = None
        if not exists:
            hashed = bcrypt.hashpw(admin_pass.encode('utf-8'), bcrypt.gensalt())
            c.execute("INSERT INTO users (username, password_hash, created_at, role) VALUES (?, ?, ?, 'ADMIN')", (admin_user, hashed, datetime.now()))
            user_id = c.lastrowid
            conn.commit()
            print(f"ADMIN USER {admin_user} CREATED.")
        else:
            user_id = exists[0]
            # Assicura che sia Admin e Resetta Password
            hashed = bcrypt.hashpw(admin_pass.encode('utf-8'), bcrypt.gensalt())
            c.execute("UPDATE users SET role='ADMIN', password_hash=? WHERE id=?", (hashed, user_id))
            conn.commit()

        # Whitelist IP Locale
        ips_to_approve = ["127.0.0.1", "::1", "localhost", "0.0.0.0"]
        for ip in ips_to_approve:
            c.execute("SELECT id FROM allowed_ips WHERE user_id = ? AND ip_address = ?", (user_id, ip))
            if not c.fetchone():
                c.execute("INSERT INTO allowed_ips (user_id, ip_address, device_name, status, last_used) VALUES (?, ?, ?, 'APPROVED', ?)", (user_id, ip, "Admin Console", datetime.now()))
                conn.commit()
                print(f"IP {ip} AUTO-APPROVED FOR ADMIN.")

# --- DATA ACCESS ---

def load_data(table, user_id):
    with db_connection() as conn:
        try:
            df = pd.read_sql(f"SELECT * FROM {table} WHERE user_id = ?", conn, params=(user_id,))
        except:
            df = pd.DataFrame()
    return df

def save_editor_changes(df_new, table_name, user_id):
    if df_new.empty:
        return
    df_new['user_id'] = user_id
    try:
        with db_connection() as conn:
            conn.execute("BEGIN TRANSACTION")
            conn.execute(f"DELETE FROM {table_name} WHERE user_id = ?", (user_id,))
            df_new.to_sql(table_name, conn, if_exists='append', index=False)
            conn.execute("COMMIT")
    except Exception as e:
        print(f"Error saving changes: {e}")

def update_asset_prices(user_id):
    with db_connection() as conn:
        df = pd.read_sql("SELECT * FROM assets WHERE user_id = ?", conn, params=(user_id,))
    
    if df.empty or 'ticker' not in df.columns:
        return 0
    valid_tkr = df[df['ticker'].notna() & (df['ticker'].astype(str).str.strip() != "")]
    if valid_tkr.empty:
        return 0
    
    tkrs = " ".join(valid_tkr['ticker'].unique())
    updates = []
    try:
        data = yf.download(tkrs, period="1d", group_by='ticker', threads=True)
        for _, row in valid_tkr.iterrows():
            t = row['ticker']
            p = None
            try:
                if len(valid_tkr['ticker'].unique()) == 1:
                    if 'Close' in data.columns:
                        p = data['Close'].iloc[-1]
                else:
                    if t in data.columns.levels[0]:
                        p = data['Close'][t].iloc[-1]
                
                if p is not None and pd.notna(p):
                    if isinstance(p, pd.Series):
                        p = p.iloc[0]
                    updates.append((float(p), row['id'], user_id))
            except:
                continue
            
        if updates:
            with db_connection() as conn:
                conn.executemany("UPDATE assets SET current_price = ? WHERE id = ? AND user_id = ?", updates)
                conn.commit()
        return len(updates)
    except:
        return 0

# --- USER MANAGEMENT HELPERS ---
def get_user_credentials(username):
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, password_hash, role FROM users WHERE username = ?", (username,))
        row = c.fetchone()
    return row

def register_user(username, hashed_password):
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)", (username, hashed_password, datetime.now()))
        uid = c.lastrowid
        conn.commit()
    return uid

def register_ip(user_id, ip_address, status='PENDING'):
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO allowed_ips (user_id, ip_address, device_name, status, last_used) VALUES (?, ?, ?, ?, ?)", 
                  (user_id, ip_address, "Unknown Device", status, datetime.now()))
        conn.commit()

def check_ip_status(user_id, ip_address):
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT status FROM allowed_ips WHERE user_id = ? AND ip_address = ?", (user_id, ip_address))
        row = c.fetchone()
    return row

def update_ip_last_used(user_id, ip_address):
    with db_connection() as conn:
        conn.execute("UPDATE allowed_ips SET last_used = ? WHERE user_id = ? AND ip_address = ?", (datetime.now(), user_id, ip_address))
        conn.commit()

def count_ips(user_id):
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT count(*) FROM allowed_ips WHERE user_id = ?", (user_id,))
        count = c.fetchone()[0]
    return count

def log_victory(user_id, description, impact):
     with db_connection() as conn:
        conn.execute("INSERT INTO career_wins (user_id, date, description, impact) VALUES (?, ?, ?, ?)", (user_id, datetime.now().strftime("%Y-%m-%d"), description, impact))
        conn.commit()

def get_pending_ips():
    with db_connection() as conn:
        return pd.read_sql("""
            SELECT allowed_ips.id, users.username, allowed_ips.ip_address, allowed_ips.device_name, allowed_ips.last_used
            FROM allowed_ips
            JOIN users ON allowed_ips.user_id = users.id
            WHERE allowed_ips.status = 'PENDING'
        """, conn)

def update_ip_approval(ip_id, status):
    with db_connection() as conn:
        conn.execute("UPDATE allowed_ips SET status=? WHERE id=?", (status, ip_id))
        conn.commit()

def approve_all_pending_ips():
    with db_connection() as conn:
        conn.execute("UPDATE allowed_ips SET status='APPROVED' WHERE status='PENDING'")
        conn.commit()

def get_all_users_view():
    with db_connection() as conn:
        return pd.read_sql("SELECT id, username, role, created_at FROM users ORDER BY id ASC", conn)

def admin_reset_password(user_id, hashed):
    with db_connection() as conn:
        conn.execute("UPDATE users SET password_hash=? WHERE id=?", (hashed, user_id))
        conn.commit()

def admin_delete_user(user_id):
    with db_connection() as conn:
         conn.execute("DELETE FROM users WHERE id=?", (user_id,))
         conn.execute("DELETE FROM allowed_ips WHERE user_id=?", (user_id,))
         conn.execute("DELETE FROM assets WHERE user_id=?", (user_id,))
         conn.execute("DELETE FROM liabilities WHERE user_id=?", (user_id,))
         conn.execute("DELETE FROM cashflow WHERE user_id=?", (user_id,))
         conn.commit()
