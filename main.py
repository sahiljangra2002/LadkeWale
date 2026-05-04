import streamlit as st
import google.generativeai as genai
import base64
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. INITIALIZATION & CONFIG ---
st.set_page_config(
    page_title="LADKEWALE | Haute Couture", 
    layout="wide", 
    page_icon="⚜️"
)

# SECURITY: Fetch API Key from Streamlit Secrets
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    st.error("Missing Gemini API Key. Please add it to your secrets.toml.")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 2. CACHED RESOURCES ---

@st.cache_data(show_spinner=False)
def load_image_as_base64(filename):
    """Encodes local images to base64 for CSS background injection."""
    image_path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(image_path):
        return ""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

@st.cache_resource(show_spinner=False)
def get_gspread_client():
    """Authenticates with Google Sheets API and caches the connection."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"GCP Service Account Error: {e}")
        return None

# --- 3. UI COMPONENTS ---

def render_hero_banner():
    """Renders the top luxury-themed banner."""
    img_data = load_image_as_base64("H.jpg")
    bg_image_url = f', url("data:image/jpeg;base64,{img_data}")' if img_data else ""

    if not img_data:
        st.info("💡 Pro-tip: Add 'H.jpg' to your directory for the full visual experience.")

    st.markdown(
        f"""
    <style>
        .hero-section {{
            background-image: linear-gradient(rgba(4, 59, 44, 0.6), rgba(0, 0, 0, 0.8)){bg_image_url};
            background-size: cover; 
            background-position: center 20%;
            height: 60vh; 
            width: 100vw; 
            position: relative;
            left: 50%; right: 50%; 
            margin-left: -50vw; margin-right: -50vw;
            display: flex; align-items: center; justify-content: center;
            color: white; 
            margin-top: -100px; 
            margin-bottom: 50px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }}
        .hero-brand-title {{
            font-family: 'Playfair Display', serif;
            font-size: clamp(50px, 10vw, 110px); 
            font-weight: 700;
            color: #FFF8E7 !important; 
            text-shadow: 0 10px 30px rgba(0,0,0,0.9);
            letter-spacing: -2px;
        }}
    </style>
    <div class="hero-section">
        <div style="text-align: center;">
            <div class="hero-brand-title">LadkeWale</div>
            <div style="font-family: 'Montserrat'; font-size: 14px; letter-spacing: 10px; color: #FFD700; text-transform: uppercase; margin-top: 10px;">
                Punjab • Delhi • Haryana 
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

def render_design_tab():
    """UI for selecting event types and uploading inspiration."""
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Step 1. The Aesthetic")
        event = st.selectbox(
            "CHOOSE THE CEREMONY", ["HALDI CEREMONY", "SANGEET", "THE WEDDING DAY"]
        )
        up_file = st.file_uploader("UPLOAD INSPIRATION (JPG/PNG)", type=["jpg", "png"])

    with col2:
        st.markdown("### Step 2. The Fabric")
        fabric = st.radio(
            "CHOOSE YOUR TEXTURE",
            [
                "Raw Silk (Premium)",
                "Chanderi (Lightweight)",
                "Banarasi (Classic)",
                "Chikankari (Hand-worked)",
            ],
        )

    if st.button("⚜️ GENERATE COUTURE BLUEPRINT ⚜️", use_container_width=True):
        if up_file:
            with st.spinner("Our Master Tailor is analyzing the aesthetic..."):
                st.success(f"Blueprint logic initialized for {fabric} - {event}!")
        else:
            st.warning("Please upload an inspiration image to begin analysis.")

    return event, fabric

def render_measurement_tab(event, fabric):
    """UI for recording measurements and the AI chat stylist."""
    st.markdown("### Step 3. The Precision Fit")
    c_inputs, c_guide = st.columns([1.5, 1])

    with c_inputs:
        col1, col2 = st.columns(2)
        chest = col1.number_input("CHEST (INCHES)", 30.0, 60.0, 40.0, 0.5)
        shoulder = col1.number_input("SHOULDER (INCHES)", 12.0, 25.0, 18.0, 0.5)
        waist = col2.number_input("WAIST (INCHES)", 24.0, 55.0, 34.0, 0.5)
        length = col2.number_input("LENGTH (INCHES)", 30.0, 60.0, 42.0, 0.5)
        st.caption("Standard precision: +/- 0.5 inch variance allowed.")

    with c_guide:
        st.markdown("#### Master Class: How to Measure")
        st.video("https://youtu.be/oYf8UHjYAvU")

    st.markdown("---")
    st.markdown("<h3 style='text-align: center; color: #043b2c;'>⚜️ VIRTUAL COUTURE STYLIST</h3>", unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about sizing, styling, or color palettes..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            system_context = (
                f"You are the LadkeWale Couture Stylist. "
                f"Client is attending {event} wearing {fabric}. "
                f"Measurements: Chest {chest}\", Shoulder {shoulder}\", Waist {waist}\". "
                "Provide expert fashion advice in an elegant and helpful tone."
            )
            response = model.generate_content(f"{system_context} | User Query: {prompt}")

            with st.chat_message("assistant"):
                st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error("The stylist is currently indisposed. Please check your connection.")

def render_delivery_tab():
    """Form to submit order details to Google Sheets."""
    st.markdown("<h3 style='text-align:center;'>Global Logistics</h3>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("FULL NAME OF CLIENT")
        phone = st.text_input("CONTACT NUMBER")
        address = st.text_area("SHIPPING ADDRESS")
    with col2:
        date = st.date_input("TARGET DELIVERY DATE")
        tier = st.selectbox("SHIPPING TIER", ["Standard (15-20 Days)", "Express (7-10 Days)", "Priority (3-5 Days)"])
        is_gift = st.checkbox("Enclose as Gift with Personalized Note")

    if st.button("CONFIRM ORDER & LOGISTICS", use_container_width=True):
        if not name or not phone:
            st.error("Client Name and Contact Number are required for the ledger.")
            return

        with st.spinner("Updating the Private Ledger..."):
            client = get_gspread_client()
            if client:
                try:
                    sheet = client.open("LadkeWale_Orders").sheet1
                    order_data = [name, phone, address, str(date), tier, "Yes" if is_gift else "No"]
                    sheet.append_row(order_data)
                    st.balloons()
                    st.success("Order Logged. Our concierge will reach out via WhatsApp.")
                except Exception as e:
                    st.error(f"Ledger Access Error: {e}")
            else:
                st.warning("Google Sheets connection is not configured.")

# --- 4. MAIN APP EXECUTION ---

def main():
    render_hero_banner()

    with st.sidebar:
        st.markdown("### ⚜️ PRIVATE CONCIERGE")
        st.link_button("💬 WHATSAPP STYLIST", "https://wa.me/919310104687")
        st.divider()
        st.markdown("**Working Hours:**\n10:00 AM - 8:00 PM (IST)")

    t_design, t_measure, t_delivery = st.tabs([
        "✨ DESIGN GENESIS", 
        "📏 MEASUREMENT VAULT", 
        "🚚 DELIVERY CONCIERGE"
    ])

    with t_design:
        event, fabric = render_design_tab()

    with t_measure:
        render_measurement_tab(event, fabric)

    with t_delivery:
        render_delivery_tab()

    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; color:gray; font-size:10px; letter-spacing: 2px;'>"
        "© 2026 LADKEWALE | THE GENTLEMAN'S ATELIER | PRIVATE CONFIDENTIAL"
        "</p>",
        unsafe_allow_html=True,
    )

if __name__ == "__main__":
    main()
