
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import numpy as np
import bcrypt # Still needed for admin reset? No, dbm handles that. Wait, Admin Panel UI does manual bcrypt.
# Actually `dbm.admin_reset_password` takes Hashed. So UI needs bcrypt to hash "Reset123!".
# Or I can move that logic to `auth_manager`.
# `auth.hash_password(text)`.
# For now I keep bcrypt here for the admin panel specific manual reset logic, or I should really put `hash_password` in auth.

from datetime import datetime

import database_manager as dbm
import forecast_engine as fe
import report_engine as re
from report_engine import PDFReport
import ui_components as ui
import auth_manager as auth

# --- CONFIGURAZIONE ---
st.set_page_config(
    page_title="KAIROS FINANCIAL OS",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

TEMPLATE_DIR = "templates"

def load_css(file_name):
    try:
        with open(f"{TEMPLATE_DIR}/{file_name}", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass

# --- CALCOLO METRICHE ---
def calculate_metrics_full(user_id):
    df_a = dbm.load_data("assets", user_id)
    df_l = dbm.load_data("liabilities", user_id)
    df_c = dbm.load_data("cashflow", user_id)
    
    tot_a = (df_a['quantity'] * df_a['current_price']).sum() if not df_a.empty else 0.0
    tot_l = df_l['remaining_balance'].sum() if not df_l.empty else 0.0
    nw = tot_a - tot_l
    
    inc, exp, passive = 0.0, 0.0, 0.0
    if not df_c.empty:
        def m(r): return r['amount']/12 if r['frequency']=='Yearly' else r['amount']
        df_c['m'] = df_c.apply(m, axis=1)
        inc = df_c[df_c['type']=='Income']['m'].sum()
        exp = df_c[df_c['type']=='Expense']['m'].sum()
        passive = df_c[(df_c['type']=='Income') & (df_c['category'].isin(['Dividends','Rent','Passive','Interests']))]['m'].sum()
    
    freedom = (passive / exp * 100) if exp > 0 else 0.0
    
    return {"net_worth": nw, "assets": tot_a, "liabilities": tot_l, "cashflow": inc - exp, "freedom_index": freedom}

# --- PAGES ---

def login_page():
    st.markdown('<div class="login-bg"></div>', unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    
    with col:
        with st.container():
            st.markdown("""
                <div class="login-card">
                    <h1 style="color:#00f0ff; text-shadow:0 0 15px #00f0ff; margin-bottom:10px;">KAIROS</h1>
                    <p style="color:#8b949e; font-family:'Rajdhani'; letter-spacing:2px; margin-bottom:30px;">FINANCIAL OS ACCESS</p>
                </div>
            """, unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["IDENTIFY", "INIT_USER"])
            with tab1:
                u = st.text_input("CODENAME", key="l_u")
                p = st.text_input("ACCESS KEY", type="password", key="l_p")
                if st.button("ESTABLISH LINK", type="primary", use_container_width=True):
                    uid, role, msg = auth.authenticate_user(u, p)
                    if uid:
                        if "WAITING" in msg or "BLOCKED" in msg:
                             st.warning(msg)
                             # If we wanted to block, we wouldn't set session state.
                             # But requirements said "Relaxed".
                             # Actually `auth_manager` returns uid only if allowed OR relaxed.
                        elif "GRANTED" in msg:
                             pass
                        
                        # Show Toast for notice
                        if msg != "ACCESS GRANTED":
                             st.toast(f"SECURITY: {msg}", icon="⚠️")
                        
                        st.session_state.user_id = uid
                        st.session_state.username = u
                        st.session_state.role = role
                        st.rerun()
                    else:
                        st.error(msg)
            with tab2:
                nu = st.text_input("NEW CODENAME", key="r_u")
                np = st.text_input("NEW ACCESS KEY", type="password", key="r_p")
                if st.button("CREATE IDENTITY", use_container_width=True):
                    if auth.create_user(nu, np):
                        st.success("IDENTITY CREATED. WAIT FOR ADMIN APPROVAL.")

# --- MAIN APP ---
def main_app(user_id):
    role = st.session_state.get('role', 'USER')
    metrics = calculate_metrics_full(user_id)
    
    with st.sidebar:
        st.markdown(f"<div style='text-align:center; margin-bottom:5px; color:#00f0ff; font-family:Rajdhani; font-weight:700;'>OPERATOR: {st.session_state.username.upper()}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; margin-bottom:20px; color:#8b949e; font-size:0.8em;'>LEVEL: {role}</div>", unsafe_allow_html=True)
        
        nav_options = ["DASHBOARD", "CAREER PATH", "THE ORACLE", "PORTFOLIO", "CASHFLOW"]
        if role == 'ADMIN':
            nav_options.append("ADMIN PANEL")
            
        mode = st.radio("NAVIGATION", nav_options, label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("🔒 TERMINATE SESSION"):
            st.session_state.user_id = None
            st.session_state.role = None
            st.rerun()




    if mode == "DASHBOARD":
        st.title("COMMAND CENTER")
        ui.render_hud(metrics)
        
        if metrics['assets'] == 0 and metrics['liabilities'] == 0:
            st.info("⚠️ SYSTEM EMPTY. INITIALIZE ASSETS IN PORTFOLIO TO BEGIN.")

        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("### 🗺️ ASSET MAP")
            df_a = dbm.load_data("assets", user_id)
            if not df_a.empty:
                df_a['total_value'] = df_a['quantity'] * df_a['current_price']
                fig = px.treemap(df_a, path=[px.Constant("PORTFOLIO"), 'category', 'name'], values='total_value',
                                 color='category', color_discrete_sequence=px.colors.sequential.RdBu)
                fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown("<div style='padding:50px; text-align:center; border:1px dashed #333; color:#555;'>NO DATA VISUALIZED</div>", unsafe_allow_html=True)

        with c2:
            st.markdown("### 📈 VELOCITY")
            hist = dbm.load_data("history_snapshots", user_id)
            if not hist.empty:
                st.area_chart(hist.set_index('date')['net_worth'], color="#bc13fe")
            else:
                st.markdown("<div style='padding:50px; text-align:center; border:1px dashed #333; color:#555;'>AWAITING SNAPSHOTS</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🎯 SMART FINANCIAL TARGETS")
        df_goals = dbm.load_data("goals", user_id)
        
        c_g1, c_g2 = st.columns([1, 1])
        with c_g1:
            if not df_goals.empty:
                active_goals = df_goals[df_goals['status'] == 'ACTIVE']
                if not active_goals.empty:
                    for _, row in active_goals.iterrows():
                        prog = row['current_amount'] / row['target_amount'] if row['target_amount'] > 0 else 0
                        prog = min(max(prog, 0.0), 1.0)
                        st.markdown(f"**{row['name']}** (Deadline: {row['deadline']})")
                        st.progress(prog)
                        st.caption(f"€ {row['current_amount']:,.0f} / € {row['target_amount']:,.0f} ({prog*100:.1f}%)")
                else:
                    st.info("NO ACTIVE GOALS.")
            else:
                st.info("NO GOALS SET.")
        
        with c_g2:
            with st.expander("MANAGE GOALS", expanded=False):
                 ed_g = st.data_editor(df_goals, num_rows="dynamic", key="goals_ed", use_container_width=True, column_config={
                     "user_id": None,
                     "status": st.column_config.SelectboxColumn("Status", options=["ACTIVE", "COMPLETED", "ARCHIVED"]),
                     "target_amount": st.column_config.NumberColumn("Target (€)", format="%.0f"),
                     "current_amount": st.column_config.NumberColumn("Current (€)", format="%.0f"),
                     "deadline": st.column_config.DateColumn("Deadline")
                 })
                 if st.button("SAVE GOALS"): dbm.save_editor_changes(ed_g, "goals", user_id); st.rerun()

        st.markdown("---")
        st.subheader("🖨️ MONTHLY CLOSING")
        st.markdown("Generate your official financial statement for the current period.")
        
        if st.button("GENERATE FINANCIAL STATEMENT"):
             with st.spinner('Generating Financial Statement...'):
                 # Load Data for Report
                 r_df_a = dbm.load_data("assets", user_id)
                 r_df_l = dbm.load_data("liabilities", user_id)
                 r_df_c = dbm.load_data("cashflow", user_id)
                 
                 # Generate PDF
                 pdf_bytes = re.generate_report(user_id, st.session_state.username, metrics, r_df_a, r_df_l, r_df_c)
                 st.session_state['last_report_bytes'] = pdf_bytes
             
             st.toast("Report Generated Successfully", icon="🖨️")

        if 'last_report_bytes' in st.session_state:
             st.download_button(
                 "⬇️ DOWNLOAD REPORT", 
                 data=st.session_state['last_report_bytes'], 
                 file_name=f"Kairos_Report_{datetime.now().strftime('%Y-%m')}.pdf", 
                 mime="application/pdf"
             )

    elif mode == "ADMIN PANEL":
        st.title("🛡️ SECURITY OPERATIONS CENTER")
        
        t1, t2 = st.tabs(["SECURITY QUEUE", "USER MANAGEMENT"])
        
        with t1:
            st.markdown("#### 🚨 IP APPROVAL QUEUE")
            pend_df = dbm.get_pending_ips()
            
            if not pend_df.empty:
                if st.button("✅ APPROVE ALL PENDING REQUESTS", type="primary", use_container_width=True):
                    dbm.approve_all_pending_ips()
                    st.success("ALL PENDING CONNECTIONS APPROVED")
                    time.sleep(1)
                    st.rerun()
                
                st.markdown("---")
                col_spec = [2, 2, 2, 1, 1]
                h1, h2, h3, h4, h5 = st.columns(col_spec)
                h1.markdown("**OPERATOR**"); h2.markdown("**IP ADDRESS**"); h3.markdown("**TIMESTAMP**")
                
                for idx, row in pend_df.iterrows():
                    c1, c2, c3, c4, c5 = st.columns(col_spec)
                    c1.write(f"{row['username']}")
                    c2.code(f"{row['ip_address']}")
                    c3.write(f"{row['last_used']}")
                    
                    if c4.button("ALLOW", key=f"ok_{row['id']}"):
                         dbm.update_ip_approval(row['id'], 'APPROVED')
                         st.success(f"AUTHORIZED: {row['username']}")
                         time.sleep(0.5)
                         st.rerun()
                         
                    if c5.button("BLOCK", key=f"no_{row['id']}"):
                         dbm.update_ip_approval(row['id'], 'REJECTED')
                         st.error(f"BLOCKED: {row['username']}")
                         time.sleep(0.5)
                         st.rerun()
                    st.markdown("---")
            else:
                st.success("✅ NO SECURITY THREATS DETECTED. SYSTEM SECURE.")

        with t2:
            st.markdown("#### 👥 OPERATOR DATABASE")
            users_df = dbm.get_all_users_view()
            
            if not users_df.empty:
                uc1, uc2, uc3, uc4, uc5, uc6 = st.columns([0.5, 2, 1, 2, 1.5, 1.5])
                uc1.markdown("**ID**"); uc2.markdown("**CODENAME**"); uc3.markdown("**ROLE**"); uc4.markdown("**CREATED**"); uc5.markdown("**ACTION**"); uc6.markdown("**DANGER**")
                st.markdown("---")
                
                for idx, row in users_df.iterrows():
                    r1, r2, r3, r4, r5, r6 = st.columns([0.5, 2, 1, 2, 1.5, 1.5])
                    r1.write(str(row['id']))
                    r2.write(row['username'])
                    r3.write(row['role'])
                    r4.write(str(row['created_at'])[:19]) 
                    
                    if r5.button("RE-KEY", key=f"rst_{row['id']}"):
                        new_pass = "Reset123!"
                        hashed = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt())
                        dbm.admin_reset_password(row['id'], hashed)
                        st.toast(f"KEY RESET: {row['username']} -> {new_pass}", icon="🔑")
                    
                    if r6.button("PURGE", key=f"del_{row['id']}"):
                         if row['username'] == st.session_state.get('username'):
                             st.error("SAFEGUARD: CANNOT PURGE SELF")
                         else:
                             dbm.admin_delete_user(row['id'])
                             st.toast(f"TERMINATED: {row['username']}", icon="💀")
                             time.sleep(1)
                             st.rerun()
                    st.divider()

    elif mode == "CAREER PATH":
        st.title("🧬 CAREER RPG")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("### ACTIVE SKILL TREE")
            df_s = dbm.load_data("career_skills", user_id)
            if not df_s.empty:
                html_grid = '<div class="skill-grid">'
                for _, row in df_s.iterrows():
                    html_grid += ui.render_skill_card(row['skill_name'], row['current_level'], row['target_level'], row['category'])
                html_grid += '</div>'
                st.markdown(html_grid, unsafe_allow_html=True)
                
                st.markdown("### SKILL RADAR")
                cats = df_s['skill_name'].tolist()
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=df_s['current_level'], theta=cats, fill='toself', name='Current', line_color='#00ff41'))
                fig.add_trace(go.Scatterpolar(r=df_s['target_level'], theta=cats, fill='toself', name='Target', line_color='#bc13fe'))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), paper_bgcolor='rgba(0,0,0,0)', font_color="white", height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("NO SKILLS LOGGED. ADD SKILLS IN THE EDITOR.")

        with c2:
            st.markdown("### 🏆 VICTORY TIMELINE")
            with st.form("win_form"):
                d = st.text_input("Victory Description", placeholder="e.g. Lead Project X")
                i = st.select_slider("Impact", ["Low", "Medium", "High", "Critical"])
                if st.form_submit_button("LOG VICTORY"):
                    dbm.log_victory(user_id, d, i)
                    st.rerun()
            st.markdown("---")
            df_w = dbm.load_data("career_wins", user_id)
            if not df_w.empty:
                df_w = df_w.sort_values('date', ascending=False)
                for _, row in df_w.iterrows():
                    color = "#00ff41" if row['impact'] == "Critical" else "#00f0ff"
                    st.markdown(f"""
                    <div class="timeline-item" style="border-left-color: {color};">
                        <div class="timeline-date">{row['date']}</div>
                        <div class="timeline-content">{row['description']} <span style="font-size:0.7em; color:{color}; border:1px solid {color}; padding:0 4px; border-radius:4px;">{row['impact']}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
            with st.expander("EDIT SKILLS"):
                ed = st.data_editor(df_s, num_rows="dynamic", key="s_ed", use_container_width=True, column_config={"user_id":None, "current_level": st.column_config.NumberColumn(min_value=0, max_value=100)})
                if st.button("SAVE SKILLS"): dbm.save_editor_changes(ed, "career_skills", user_id); st.rerun()

    elif mode == "THE ORACLE":
        st.title("🔮 THE ORACLE 3.0 // AI FORECAST")
        
        # --- AI LAYER ---
        hist_df = dbm.load_data("history_snapshots", user_id)
        preds, slope = fe.predict_future_nw(hist_df)
        
        target_nw = 1000000
        monthly_save = metrics['cashflow'] if metrics['cashflow'] > 0 else 0
        months_to_freedom = fe.calculate_time_to_target(metrics['net_worth'], monthly_save, target_nw)
        traj_msg = fe.analyze_trajectory(hist_df)
        
        pred_6m = f"€ {preds[6]:,.2f}" if preds[6] else "INSUFFICIENT DATA"
        pred_12m = f"€ {preds[12]:,.2f}" if preds[12] else "INSUFFICIENT DATA"
        freedom_date = "NEVER (INCREASE CASHFLOW)"
        if months_to_freedom != float('inf') and months_to_freedom > 0:
            fd = datetime.now() + pd.DateOffset(months=int(months_to_freedom))
            freedom_date = fd.strftime("%B %Y").upper()
        elif months_to_freedom == 0:
            freedom_date = "ACHIEVED"

        ui.render_oracle_terminal(slope, traj_msg, pred_6m, pred_12m, target_nw, monthly_save, freedom_date)
        
        st.subheader("📐 SCENARIO SIMULATOR")
        with st.container():
            st.markdown('<div class="oracle-panel">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                base_rate = st.slider("BASE ANNUAL RETURN (%)", 1.0, 15.0, 7.0, 0.5)
            with c2:
                inflation = st.slider("INFLATION RATE (%)", 0.0, 10.0, 2.5, 0.5)
            with c3:
                years = st.slider("TIMEFRAME (YEARS)", 5, 40, 15)
            st.markdown("---")
            monthly_contrib = st.slider("MONTHLY CONTRIBUTION (€)", 0, 5000, int(metrics['cashflow']) if metrics['cashflow'] > 0 else 500, 100)
            st.markdown('</div>', unsafe_allow_html=True)

        months = years * 12
        start_nw = metrics['net_worth']
        rates = {"PESSIMISTIC (Bear)": base_rate - 3.0, "REALISTIC (Base)": base_rate, "OPTIMISTIC (Bull)": base_rate + 3.0}
        chart_data = pd.DataFrame(index=range(months+1))
        
        for name, r in rates.items():
            real_rate = (r - inflation) / 100
            monthly_rate = real_rate / 12
            values = [start_nw]
            curr = start_nw
            for m in range(months):
                curr = curr * (1 + monthly_rate) + monthly_contrib
                values.append(curr)
            chart_data[name] = values
            
        st.markdown("### WEALTH PROJECTION (INFLATION ADJUSTED)")
        fig = px.line(chart_data, labels={"index": "Months", "value": "Real Wealth (€)"})
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", hovermode="x unified")
        fig.update_traces(line_color='#ff0055', selector=dict(name="PESSIMISTIC (Bear)"))
        fig.update_traces(line_color='#00f0ff', selector=dict(name="REALISTIC (Base)"))
        fig.update_traces(line_color='#00ff41', selector=dict(name="OPTIMISTIC (Bull)"))
        st.plotly_chart(fig, use_container_width=True)
        final_val = chart_data["REALISTIC (Base)"].iloc[-1]
        st.metric("PROJECTED REAL WEALTH (BASE)", f"€ {final_val:,.2f}", f"Target: {years} Years")

    elif mode == "PORTFOLIO":
        st.title("💎 WEALTH DASHBOARD")
        df_a = dbm.load_data("assets", user_id)
        df_l = dbm.load_data("liabilities", user_id)
        
        tot_a = 0.0
        if not df_a.empty:
            if 'current_price' in df_a.columns and 'quantity' in df_a.columns:
                 df_a['total_value'] = df_a['quantity'] * df_a['current_price']
                 tot_a = df_a['total_value'].sum()
        
        tot_l = df_l['remaining_balance'].sum() if not df_l.empty else 0.0
        net_worth = tot_a - tot_l
        
        ui.render_portfolio_metrics(tot_a, tot_l, net_worth)
        
        if not df_a.empty:
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown("### 🪐 ASSET GALAXY")
                fig_sun = px.sunburst(df_a, path=['category', 'name'], values='total_value', color='category', color_discrete_sequence=['#00f0ff', '#bc13fe', '#ff0055', '#00ff41', '#ffffff'], template="plotly_dark")
                fig_sun.update_layout(margin=dict(t=0, l=0, r=0, b=0), paper_bgcolor='rgba(0,0,0,0)', font=dict(family="JetBrains Mono", size=14))
                fig_sun.update_traces(marker=dict(line=dict(color='#000000', width=1)))
                st.plotly_chart(fig_sun, use_container_width=True)
            with c2:
                st.markdown("### 🧬 ALLOCATION")
                fig_don = px.pie(df_a, values='total_value', names='category', hole=0.6, color='category', color_discrete_sequence=['#00f0ff', '#bc13fe', '#ff0055', '#00ff41', '#ffffff'], template="plotly_dark")
                fig_don.update_layout(showlegend=False, margin=dict(t=20, l=20, r=20, b=20), paper_bgcolor='rgba(0,0,0,0)', annotations=[dict(text='MIX', x=0.5, y=0.5, font_size=20, showarrow=False, font_color='white')])
                fig_don.update_traces(textposition='outside', textinfo='percent+label')
                st.plotly_chart(fig_don, use_container_width=True)
        else:
             st.info("⚠️ PORTFOLIO EMPTY. ADD ASSETS BELOW TO VISUALIZE.")

        st.markdown("---")
        c_act, _ = st.columns([1, 4])
        with c_act:
             if st.button("🔄 SYNC MARKET PRICES", use_container_width=True):
                 n = dbm.update_asset_prices(user_id)
                 if n > 0:
                     st.toast(f"UPDATED {n} ASSETS FROM MARKET", icon="🚀")
                     time.sleep(1)
                     st.rerun()
                 else:
                     st.toast("NO UPDATES AVAILABLE OR API LIMIT", icon="💤")
        
        t1, t2 = st.tabs(["📂 ASSET DATA", "📉 LIABILITIES DATA"])
        with t1:
            ed_a = st.data_editor(df_a, num_rows="dynamic", key="ed_a_new", use_container_width=True, column_config={
                    "user_id": None,
                    "currency": st.column_config.SelectboxColumn("Currency", options=["EUR", "USD", "BTC"]),
                    "current_price": st.column_config.NumberColumn("Price (€)", format="%.2f"),
                    "quantity": st.column_config.NumberColumn("Qty", format="%.4f"),
                    "total_value": st.column_config.NumberColumn("Total (€)", format="%.2f", disabled=True)
                })
            if st.button("SAVE ASSETS DB", type="primary"): dbm.save_editor_changes(ed_a, "assets", user_id); st.rerun()
        with t2:
            ed_l = st.data_editor(df_l, num_rows="dynamic", key="ed_l_new", use_container_width=True, column_config={"user_id":None})
            if st.button("SAVE DEBTS DB", type="primary"): dbm.save_editor_changes(ed_l, "liabilities", user_id); st.rerun()

    elif mode == "CASHFLOW":
        st.title("💸 CASHFLOW ANALYTICS")
        df = dbm.load_data("cashflow", user_id)
        
        monthly_inc = 0.0
        monthly_exp = 0.0
        if not df.empty:
            calc_df = df.copy()
            calc_df['monthly_val'] = calc_df.apply(lambda x: x['amount']/12 if x['frequency']=='Yearly' else x['amount'], axis=1)
            monthly_inc = calc_df[calc_df['type']=='Income']['monthly_val'].sum()
            monthly_exp = calc_df[calc_df['type']=='Expense']['monthly_val'].sum()
            net_flow = monthly_inc - monthly_exp
        else:
            net_flow = 0.0
            calc_df = pd.DataFrame()

        c1, c2, c3 = st.columns(3)
        c1.metric("MONTHLY INCOME", f"€ {monthly_inc:,.2f}")
        c2.metric("MONTHLY EXPENSES", f"€ {monthly_exp:,.2f}")
        delta_color = "normal" if net_flow >= 0 else "inverse" 
        c3.metric("NET CASHFLOW", f"€ {net_flow:,.2f}", f"€ {net_flow:,.2f}", delta_color=delta_color)
        
        if not calc_df.empty:
            st.markdown("---")
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("### ⚖️ IN vs OUT")
                summ_data = pd.DataFrame({'Type': ['Income', 'Expense'], 'Amount': [monthly_inc, monthly_exp]})
                fig_io = px.bar(summ_data, x='Amount', y='Type', orientation='h', color='Type', color_discrete_map={'Income': '#00ff41', 'Expense': '#ff0055'}, text='Amount')
                fig_io.update_traces(texttemplate='%{text:.2s}', textposition='auto')
                fig_io.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', showlegend=False, height=300)
                st.plotly_chart(fig_io, use_container_width=True)
            with g2:
                st.markdown("### 📉 SPENDING DRAIN")
                exp_only = calc_df[calc_df['type']=='Expense']
                if not exp_only.empty:
                    exp_cat = exp_only.groupby('category')['monthly_val'].sum().reset_index().sort_values('monthly_val', ascending=True)
                    fig_br = px.bar(exp_cat, x='monthly_val', y='category', orientation='h', title="", color_discrete_sequence=['#ff0055'])
                    fig_br.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', xaxis_title="Monthly €", yaxis_title="", height=300)
                    st.plotly_chart(fig_br, use_container_width=True)
                else:
                    st.info("NO EXPENSES TRACKED.")

        st.markdown("---")
        with st.expander("📝 EDIT CASHFLOW DATABASE", expanded=False):
            ed = st.data_editor(df, num_rows="dynamic", key="ed_c", use_container_width=True, column_config={
                "user_id": None,
                "type": st.column_config.SelectboxColumn("Type", options=["Income", "Expense"]),
                "frequency": st.column_config.SelectboxColumn("Freq", options=["Monthly", "Yearly", "One-Time"]),
                "amount": st.column_config.NumberColumn("Amount (€)", format="%.2f")
            })
            if st.button("SAVE CASHFLOW", type="primary"): dbm.save_editor_changes(ed, "cashflow", user_id); st.rerun()

if __name__ == "__main__":
    dbm.init_db()
    dbm.migrate_db()
    load_css("style.css")
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        login_page()
    else:
        main_app(st.session_state.user_id)