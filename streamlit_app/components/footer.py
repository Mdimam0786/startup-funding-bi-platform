import streamlit as st

def render_footer():
    st.markdown(
        """
        <div style="
            text-align:center;
            margin-top:40px;
            padding:14px;
            border-top:1px solid rgba(255,255,255,0.10);
            color:#94A3B8;
            font-size:13px;
            line-height:1.6;">
            🚀 <b style="color:#60A5FA;">Developed by Md Imamuddin</b><br>
            Startup Funding & Business Intelligence Platform<br>
            <span style="font-size:12px;">
                Python • PostgreSQL • Power BI • Machine Learning • Streamlit
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )