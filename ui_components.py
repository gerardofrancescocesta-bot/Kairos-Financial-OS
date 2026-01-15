
import streamlit as st

def render_hud(metrics):
    liab_class = "alert" if metrics['liabilities'] > 0 else "success"
    cf_class = "success" if metrics['cashflow'] >= 0 else "alert"
    
    html_content = f"""
<style>
    .hud-container {{ display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }}
    .hud-card {{ flex: 1; min-width: 200px; background: linear-gradient(145deg, #11161d, #0d1116); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 15px; position: relative; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
    .hud-card::before {{ content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: #00f0ff; opacity: 0.8; }}
    .hud-card.alert::before {{ background: #ff0055; }}
    .hud-card.success::before {{ background: #00ff41; }}
    .hud-label {{ font-family: 'Rajdhani', sans-serif; font-size: 0.8rem; color: #8b949e; letter-spacing: 1px; margin-bottom: 5px; }}
    .hud-value {{ font-family: 'JetBrains Mono', monospace; font-size: 1.8rem; font-weight: 700; color: #fff; margin-bottom: 5px; }}
    .hud-delta {{ font-size: 0.75rem; display: flex; align-items: center; gap: 5px; color: #8b949e; font-family: 'Inter', sans-serif; }}
</style>

<div class="hud-container">
    <div class="hud-card">
        <div class="hud-label">NET WORTH</div>
        <div class="hud-value">€ {metrics['net_worth']:,.2f}</div>
        <div class="hud-delta" style="color: #00ff41;">▲ LIVE TRACKING</div>
    </div>
    <div class="hud-card">
        <div class="hud-label">ASSETS DEPLOYED</div>
        <div class="hud-value">€ {metrics['assets']:,.2f}</div>
        <div class="hud-delta" style="color: #00f0ff;">ACTIVE PORTFOLIO</div>
    </div>
    <div class="hud-card {liab_class}">
        <div class="hud-label">LIABILITIES</div>
        <div class="hud-value">€ {metrics['liabilities']:,.2f}</div>
        <div class="hud-delta">DEBT LOAD</div>
    </div>
    <div class="hud-card {cf_class}">
        <div class="hud-label">MONTHLY FLOW</div>
        <div class="hud-value">€ {metrics['cashflow']:,.2f}</div>
        <div class="hud-delta">P&L MONTHLY</div>
    </div>
</div>

<div style="margin-top: 25px; padding: 20px; background: #0d1116; border: 1px solid #30363d; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
    <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-family:'Rajdhani'; color:#bc13fe; font-weight:700; font-size: 1.1rem;">
        <span>RAT RACE ESCAPE PROGRESS</span>
        <span>{metrics['freedom_index']:.1f}%</span>
    </div>
    <div style="width:100%; height:12px; background:#21262d; border-radius:6px; overflow:hidden; border: 1px solid #333;">
        <div style="width:{min(metrics['freedom_index'], 100)}%; height:100%; background:linear-gradient(90deg, #bc13fe, #00f0ff); box-shadow: 0 0 15px #bc13fe;"></div>
    </div>
</div>
"""
    st.markdown(html_content, unsafe_allow_html=True)

def render_skill_card(skill_name, current, target, category):
    html = f"""
    <div class="skill-card">
        <div class="skill-header">
            <span style="color:#e6edf3;">{skill_name}</span>
            <span style="color:#8b949e;">Lvl {current}</span>
        </div>
        <div class="progress-bg">
            <div class="progress-bar" style="width: {current}%;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:5px; font-size:0.7rem; color:#8b949e; font-family:'JetBrains Mono';">
            <span>{category}</span>
            <span>TARGET: {target}</span>
        </div>
    </div>
    """
    return html

def render_portfolio_metrics(tot_a, tot_l, net_worth):
    st.markdown(f"""
    <style>
        .pf-metric-container {{ display: flex; gap: 20px; margin-bottom: 30px; }}
        .pf-card {{ flex: 1; background: linear-gradient(135deg, #0d1116, #161b22); border: 1px solid rgba(0, 240, 255, 0.2); border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 0 20px rgba(0,0,0,0.5); position: relative; overflow: hidden; }}
        .pf-card::after {{ content: ''; position: absolute; bottom: 0; left: 0; width: 100%; height: 3px; background: #00f0ff; box-shadow: 0 0 10px #00f0ff; }}
        .pf-card.liab::after {{ background: #ff0055; box-shadow: 0 0 10px #ff0055; }}
        .pf-card.net::after {{ background: #bc13fe; box-shadow: 0 0 10px #bc13fe; }}
        .pf-label {{ font-family: 'Rajdhani', sans-serif; font-size: 1rem; color: #8b949e; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 5px; }}
        .pf-value {{ font-family: 'JetBrains Mono', monospace; font-size: 2.2rem; font-weight: 700; color: #fff; text-shadow: 0 0 10px rgba(255,255,255,0.3); }}
    </style>
    <div class="pf-metric-container">
        <div class="pf-card">
            <div class="pf-label">GROSS ASSETS</div>
            <div class="pf-value">€ {tot_a:,.2f}</div>
        </div>
        <div class="pf-card liab">
            <div class="pf-label">TOTAL LIABILITIES</div>
            <div class="pf-value">€ {tot_l:,.2f}</div>
        </div>
        <div class="pf-card net">
            <div class="pf-label">LIQUID EQUITY</div>
            <div class="pf-value">€ {net_worth:,.2f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_oracle_terminal(slope, traj_msg, pred_6m, pred_12m, target_nw, monthly_save, freedom_date):
    st.markdown(f"""
    <div style="font-family:'JetBrains Mono'; color:#00ff41; background:#050509; padding:20px; border:1px solid #333; border-radius:8px; margin-bottom:20px; box-shadow:0 0 20px rgba(0, 255, 65, 0.1);">
        <div style="margin-bottom:10px; color:#555;">// NEURAL_LINK_ESTABLISHED :: ACCESSING_CORE_MEMORY</div>
        <div>> ANALYZING HISTORICAL DATAPOINTS... [OK]</div>
        <div>> COMPUTING LINEAR REGRESSION SLOPE... {slope:.2f} / DAY</div>
        <div>> TRAJECTORY STATUS: <span style="color:#fff; font-weight:bold;">{traj_msg}</span></div>
        <br>
        <div style="color:#00f0ff;">>> PREDICTION MATRIX (AI_MODEL_V1):</div>
        <div style="margin-left:20px;">+ 6 MONTHS:  <span style="color:#fff">{pred_6m}</span></div>
        <div style="margin-left:20px;">+ 12 MONTHS: <span style="color:#fff">{pred_12m}</span></div>
        <br>
        <div style="color:#bc13fe;">>> ESCAPE VELOCITY CALCULATION:</div>
        <div style="margin-left:20px;">TARGET: € {target_nw:,.0f} | CURRENT FLOW: € {monthly_save:,.0f}/mo</div>
        <div style="margin-left:20px;">ESTIMATED FREEDOM DATE: <span style="background:#bc13fe; color:#fff; padding:2px 8px;">{freedom_date}</span></div>
        <div style="margin-top:10px; animation: blink 1s infinite;">_</div>
    </div>
    """, unsafe_allow_html=True)
