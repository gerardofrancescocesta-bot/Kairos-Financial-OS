
import streamlit as st
import bcrypt
import database_manager as dbm

# --- SECURITY UTILS ---
def get_client_ip():
    try:
        # Use modern Streamlit context headers if available
        headers = st.context.headers
        ip = headers.get("X-Forwarded-For", headers.get("Remote-Addr", "127.0.0.1"))
        if "," in ip:
            ip = ip.split(",")[0]
        return ip
    except:
        # Fallback mechanism
        try:
            from streamlit.web.server.websocket_headers import _get_websocket_headers
            headers = _get_websocket_headers()
            ip = headers.get("X-Forwarded-For", headers.get("Remote-Addr", "127.0.0.1"))
            if "," in ip:
                ip = ip.split(",")[0]
            return ip
        except:
            return "127.0.0.1"

def check_access(user_id):
    current_ip = get_client_ip()
    row = dbm.check_ip_status(user_id, current_ip)
    
    if row:
        status = row[0]
        if status == 'APPROVED':
            dbm.update_ip_last_used(user_id, current_ip)
            return True, "ACCESS GRANTED"
        elif status == 'PENDING':
            return False, "WAITING FOR ADMIN"
        else: # REJECTED
            return False, "DEVICE BLOCKED"
    else:
        # New Device Logic
        count = dbm.count_ips(user_id)
        if count < 5:
            # Limit not reached, add as PENDING
            dbm.register_ip(user_id, current_ip, status='PENDING')
            return False, "DEVICE PENDING APPROVAL"
        else:
            return False, "DEVICE LIMIT REACHED"

def authenticate_user(username, password):
    row = dbm.get_user_credentials(username)
    
    if row and bcrypt.checkpw(password.encode('utf-8'), row[1]):
        user_id = row[0]
        role = row[2]
        # Strict IP Check
        allowed, msg = check_access(user_id)
        if allowed:
            return user_id, role, msg
        else:
            # Login successful even if IP is unknown (RELAXED SECURITY for now, but msg shown)
            # In a strict environment we would return None.
            # But the requirement asks to show the toast and allow if it's "Relaxed" or block?
            # The current app.py behavior was: if allowed: return. else: toast + return (Wait, really?)
            # Let's check app.py original logic.
            # "Login successful even if IP is unknown (RELAXED SECURITY)"
            # So we mimic that.
            return user_id, role, msg
    else:
        # Invalid Credentials
        return None, None, "Invalid Credentials"

def create_user(username, password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        # 1. Register User
        user_id = dbm.register_user(username, hashed)
        
        # 2. Auto-Register IP as PENDING
        current_ip = get_client_ip()
        dbm.register_ip(user_id, current_ip, status='PENDING')
        
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False
