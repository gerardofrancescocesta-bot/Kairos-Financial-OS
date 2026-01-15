# KAIROS FINANCIAL OS

> "Control your data, control your destiny."

**KAIROS FINANCIAL OS** is a robust, modular Personal ERP designed to manage net worth, cash flow, and career growth. Built on **Python** and **Streamlit**, it leverages **Linear Regression (NumPy)** for wealth forecasting and **Docker** for OS-agnostic deployment. It follows strict security protocols (IP Whitelisting, Bcrypt) and data persistence standards.

![Kairos Banner](docs/images/banner.png)

---

## � Project Structure

```text
KAIROS-OS/
├── app.py                  # Main Entry Point & Orchestrator (Streamlit)
├── auth_manager.py         # Security Layer (Auth, Session, IP filter)
├── database_manager.py     # Data Access Layer (SQLite3, Migrations)
├── forecast_engine.py      # Logic Layer (AI/Math predictions)
├── report_engine.py        # Output Layer (PDF Generation)
├── ui_components.py        # Presentation Layer (HTML/CSS Widgets)
├── templates/
│   └── style.css           # Global Cyberpunk Theme definitions

├── data/                   # Persistent storage for Docker (volume mapped)
├── Dockerfile              # Container definition (Python 3.9-slim)
└── docker-compose.yml      # Orchestration config
```

---

## 🧠 Technical Architecture

The system operates on the **D.O.E. Protocol** (Data, Oracle, Execution), separating concerns into distinct modules.

### 1. `database_manager.py` (DAL)
Handles all interaction with the SQLite database (`kairos.db`).
- **Schema Management**: Uses `init_db()` and `migrate_db()` to ensure the schema allows evolves without data loss.
- **Context Manager**: Implements `db_connection()` context manager to handle thread-safe connections and auto-closing.
- **Data Persistence**: Checks for the existence of the `data/` directory to ensure Docker volume mappings never fail.

### 2. `auth_manager.py` (Security)
Implements a custom Role-Based Access Control (RBAC) system.
- **Hashing**: Uses `bcrypt` + `salt` for secure password storage.
- **IP Whitelisting**: When a user logs in from a new IP, the system blocks access and creates a "Pending Request" in the DB. The Admin must manually approve the IP from the Security Console.
- **Session State**: Manages Streamlit session state resilience.

### 3. `forecast_engine.py` (The Oracle)
The mathematical core of the application.
- **Linear Regression**: Uses `numpy.polyfit` (deg=1) on historical Net Worth snapshots to calculate the `slope` (wealth velocity).
- **Escape Velocity**: Calculates `(Target - Current) / Slope` to predict the exact date of Financial Freedom.
- **Scenario Simulation**: Applies compound interest formulas to project Future Value (FV) under different inflation/yield conditions.

### 4. `report_engine.py` (Output)
A dedicated engine for generating professional financial statements.
- **FPDF**: Uses low-level PDF drawing commands for pixel-perfect layout control.
- **Structure**: Generates a Cover Page, Income Statement (Mini-P&L), Balance Sheet (Assets vs Liabilities), and an AI-driven text analysis page.
- **Stateless**: The engine is purely functional; it takes dataframes as input and returns bytes.

### 5. `app.py` (Orchestrator)
The Streamlit frontend that binds all modules.
- **Navigation**: Manages the sidebar and page routing based on `st.session_state.role`.
- **Reactivity**: Uses extensive session state management to persist User Inputs across reruns.
- **Visuals**: Integrates `Plotly` for interactive Sunburst charts (Asset Allocation) and Area Charts (Net Worth History).

---

## ⚡ Key Features

### 💎 Wealth Dashboard
- **Real-time HUD**: Visualizes total assets, liabilities, and liquid net worth.
- **Asset Maps**: Drill-down visualization of portfolio distribution.

### 🔮 AI Forecasting
- **6/12/24 Month Projections**: Based on your actual earning behavior, not theoretical inputs.
- **Freedom Countdown**: Calculates days remaining until you don't need to work.

### 🛡️ Security Operations Center
- **Admin Panel**: Full control over user accounts and device access.
- **Logs**: Audit trail of system events.

---

## 🚀 Installation & Deployment

### Environment Variables
Configure these in `docker-compose.yml` or your local `.env`.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `KAIROS_ADMIN_USER` | Initial Admin Username | `admin` |
| `KAIROS_ADMIN_PASS` | Initial Admin Password | `admin` |
| `DB_PATH` | Path to SQLite file | `./kairos.db` (Local) / `/app/data/kairos.db` (Docker) |

### 📦 Local Development
1.  **Clone & Setup**:
    ```bash
    git clone https://github.com/your-repo/kairos.git
    cd kairos
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```
2.  **Run**:
    ```bash
    streamlit run app.py
    ```

### 🐳 Docker Production (Recommended)
Kairos is optimized for Docker to ensure data persistence and stability.

1.  **Build & Run**:
    ```bash
    docker-compose up -d --build
    ```
2.  **Access**:
    Open `http://localhost:8501`.
3.  **Data Persistence**:
    The database is mapped to `./data/kairos.db` on your host machine. You can back up this file at any time.

---

## 📖 User Manual

### Monthly Closing Procedure
At the end of every month, perform a **Monthly Closing** to generate your official report:
1.  Ensure all **Cashflow** items (income/expenses) for the month are entered.
2.  Update current market values of **Assets** in the Portfolio tab.
3.  Go to **Dashboard** -> Scroll to bottom -> **Generate Financial Statement**.
4.  Download the **Kairos Intelligence Report** PDF and archive it.

### Setting Up Goals
1.  Navigate to **Dashboard**.
2.  Scroll to **Smart Goals**.
3.  Add a new Goal (e.g., "Emergency Fund", "Tesla Model 3").
4.  Update the `Current Amount` manually as you save towards it. The progress bar will update automatically.

---

> **Security Note**: The default Admin credentials (`admin`/`admin`) are public. Change them immediately upon first login by updating the Environment Variables in your deployment configuration.

*Engineered for Financial Sovereignty.*
