def show_sector_drilldown(sector_name: str, companies_df, company_revenue_df):
    # ... existing code ...

@st.cache_data
def load_data():
    # ... existing code ...

with tabs[4]:
    # ── Hero ─────────────────────────────────────────────────────────────────
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1a237e 0%, #283593 60%, #3949ab 100%);
                    padding: 36px 40px; border-radius: 12px; margin-bottom: 28px;">
          <h1 style="color:white; margin:0; font-size:2.2em;">Hey Investment Opportunities</h1>
          <p style="color:#c5cae9; margin:10px 0 0 0; font-size:1.15em;">
            Where should investors look next in the U.S. digital economy?
          </p>
          <p style="color:#9fa8da; margin:6px 0 0 0; font-size:0.95em;">
            Based on technology adoption trends (SO Survey) · R&D intensity (SEC EDGAR) ·
            Revenue growth (SEC EDGAR) · Labor market signals (BLS)
          </p>
    """, unsafe_allow_html=True)

def minmax(s):
    # ... existing code ...
