import streamlit as st
import runpy
import os

st.set_page_config(page_title="My Streamlit App", layout="wide")

# Paths to your scripts
PAGES = {
    "Home": {"path": None, "logo": "🏠"},
    "Save Continuum File": {"path": "pages/save_continuum_file.py", "logo": "💾"},
    "Cloudy Out File": {"path": "pages/cloudy_out_file.py", "logo": "☁️"}
}

if "page" not in st.session_state:
    st.session_state.page = "Home"

cols = st.columns(len(PAGES))
for i, (name, details) in enumerate(PAGES.items()):
    if cols[i].button(f"{details['logo']} {name}"):
        st.session_state.page = name

st.markdown("---")

if st.session_state.page == "Home":
    st.title("Welcome to My Streamlit App")
    st.write("Click the icons above to navigate to different pages.")
else:
    page_path = PAGES[st.session_state.page]["path"]
    if page_path and os.path.exists(page_path):
        # Execute the page script just like running `streamlit run <file>`
        runpy.run_path(page_path, run_name="__main__")
    else:
        st.error(f"Page not found: {page_path}")
