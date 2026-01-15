import sqlite3
import random
from datetime import datetime, timedelta

# CONFIG
DB_FILE = "kairos.db"
USER_ID = 1  # Admin

def get_db():
    return sqlite3.connect(DB_FILE)

def inject_full_demo():
    conn = get_db()
    c = conn.cursor()
    
    print("🚀 AVVIO INIEZIONE DATI AVANZATA...")

    # 1. PULIZIA TOTALE (Per evitare duplicati)
    tables = ['assets', 'liabilities', 'cashflow', 'career_skills', 'career_wins', 'history_snapshots']
    for t in tables:
        try:
            c.execute(f"DELETE FROM {t}")
        except: pass
    
    # 2. ASSETS (Portafoglio Solido)
    # Totale: ~190k
    assets = [
        (USER_ID, 'Tesla Stock', 'Stocks', 'TSLA', 150, 180.00, 245.00), # ~36k
        (USER_ID, 'Bitcoin Cold', 'Crypto', 'BTC-USD', 1.2, 35000.00, 52000.00), # ~62k
        (USER_ID, 'Ethereum Staking', 'Crypto', 'ETH-USD', 15.0, 2000.00, 2800.00), # ~42k (Genera Passive!)
        (USER_ID, 'Appartamento Affitto', 'Real Estate', '', 1, 40000.00, 45000.00), # Downpayment
        (USER_ID, 'Emergency Fund', 'Cash', '', 10000, 1.0, 1.0),
    ]
    c.executemany("INSERT INTO assets (user_id, name, category, ticker, quantity, avg_price, current_price) VALUES (?,?,?,?,?,?,?)", assets)

    # 3. LIABILITIES (Debiti "Buoni" e "Cattivi")
    liabilities = [
        (USER_ID, 'Mutuo Immobiliare', 'Mortgage', 128000.00, 750.00, 3.2),
        (USER_ID, 'Leasing Auto', 'Car Loan', 12000.00, 350.00, 4.5),
    ]
    c.executemany("INSERT INTO liabilities (user_id, name, category, remaining_balance, monthly_payment, interest_rate) VALUES (?,?,?,?,?,?)", liabilities)

    # 4. CASHFLOW (Il segreto della Rat Race)
    # Formula Rat Race = (Passive Income / Expenses) * 100
    # Qui inseriamo Dividendi e Affitti per avere reddito passivo
    cashflow = [
        # ENTRATE ATTIVE (Lavoro)
        (USER_ID, 'Income', 'Salary', 'Tech Lead Salary', 4200.00, 'Monthly'),
        
        # ENTRATE PASSIVE (Fondamentali per la barra viola)
        (USER_ID, 'Income', 'Rent', 'Affitto Appartamento', 650.00, 'Monthly'),
        (USER_ID, 'Income', 'Dividends', 'Dividendi Azionari', 1200.00, 'Yearly'), # 100/mese
        (USER_ID, 'Income', 'Passive', 'Staking Rewards ETH', 150.00, 'Monthly'),
        
        # SPESE
        (USER_ID, 'Expense', 'Housing', 'Mutuo + Spese Casa', 1100.00, 'Monthly'),
        (USER_ID, 'Expense', 'Transport', 'Auto + Benzina', 500.00, 'Monthly'),
        (USER_ID, 'Expense', 'Food', 'Spesa & Ristoranti', 600.00, 'Monthly'),
        (USER_ID, 'Expense', 'Fun', 'Svago & Viaggi', 400.00, 'Monthly'),
    ]
    # Nota: Totale Spese Mensili = 2600. 
    # Totale Passivo Mensile = 650 (Affitto) + 100 (Div) + 150 (Staking) = 900.
    # Rat Race Progress previsto: 900 / 2600 = ~34% !
    
    c.executemany("INSERT INTO cashflow (user_id, type, category, name, amount, frequency) VALUES (?,?,?,?,?,?)", cashflow)

    # 5. CAREER (Gamification)
    skills = [
        (USER_ID, 'Python Architecture', 85, 100, 'Hard Skill'),
        (USER_ID, 'Financial Analysis', 60, 90, 'Hard Skill'),
        (USER_ID, 'Team Leadership', 70, 80, 'Soft Skill'),
        (USER_ID, 'Negotiation', 40, 75, 'Soft Skill'),
    ]
    c.executemany("INSERT INTO career_skills (user_id, skill_name, current_level, target_level, category) VALUES (?,?,?,?,?)", skills)

    wins = [
        (USER_ID, '2025-01-10', 'Deployed Kairos OS v1.0', 'Critical'),
        (USER_ID, '2024-11-20', 'Promosso a Senior Dev', 'High'),
        (USER_ID, '2024-09-15', 'Completato corso AI', 'Medium'),
    ]
    c.executemany("INSERT INTO career_wins (user_id, date, description, impact) VALUES (?,?,?,?)", wins)

    # 6. STORICO (Per l'Oracolo)
    # Generiamo uno storico che mostra una crescita grazie al risparmio mensile
    current_nw = 190000 - 140000 # Assets - Liabs approx = 50k
    history = []
    for i in range(18, -1, -1): # Ultimi 18 mesi
        date = (datetime.now() - timedelta(days=i*30)).strftime("%Y-%m-%d")
        
        # Crescita simulata: partiamo da 25k e saliamo a 50k
        base_val = 25000 + (25000 * ((18-i)/18)) 
        noise = random.uniform(0.98, 1.02)
        val = base_val * noise
        
        history.append((USER_ID, date, val*4, val*3, val)) # Asset e Liab fittizi per supportare il NW
        
    c.executemany("INSERT INTO history_snapshots (user_id, date, total_assets, total_liabilities, net_worth) VALUES (?,?,?,?,?)", history)

    conn.commit()
    conn.close()
    print("✅ DATABASE POPOLATO CON SUCCESSO!")

if __name__ == "__main__":
    inject_full_demo()