import streamlit as st
import pickle
import re
import pandas as pd
import os
from datetime import datetime
from PyPDF2 import PdfReader

# ---------------- PAGE SETTINGS ----------------
st.set_page_config(
    page_title="JobShield AI",
    page_icon="🛡️",
    layout="wide"
)

# ---------------- LOAD MODEL ----------------
model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# ---------------- SETTINGS ----------------
history_file = "analysis_history.csv"

scam_keywords = [
    "registration fee",
    "payment required",
    "limited seats",
    "urgent hiring",
    "easy money",
    "earn lakhs",
    "whatsapp",
    "no experience required",
    "work from home",
    "apply immediately"
]

free_email_domains = [
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com"
]

# ---------------- CUSTOM UI ----------------
st.markdown("""
<style>

.title {
    font-size: 48px;
    font-weight: bold;
    color: #38bdf8;
    text-align: center;
}

.subtitle {
    font-size: 20px;
    text-align: center;
    color: #9ca3af;
}

.result-box {
    border-radius: 15px;
    padding: 20px;
    background-color: #111827;
    border: 1px solid #374151;
}

</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown(
    '<p class="title">🛡️ JobShield AI</p>',
    unsafe_allow_html=True
)

st.markdown(
    '<p class="subtitle">AI-Powered Fake Internship & Job Detection System</p>',
    unsafe_allow_html=True
)

st.markdown("---")

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader(
    "📂 Upload Job Offer (.txt or .pdf)",
    type=["txt", "pdf"]
)

job_text = ""

if uploaded_file is not None:

    # TXT file
    if uploaded_file.type == "text/plain":
        job_text = uploaded_file.read().decode("utf-8")

    # PDF file
    elif uploaded_file.type == "application/pdf":

        pdf_reader = PdfReader(uploaded_file)

        for page in pdf_reader.pages:
            text = page.extract_text()

            if text:
                job_text += text

    st.success("✅ File uploaded successfully!")

# ---------------- TEXT AREA ----------------
job_text = st.text_area(
    "📋 Paste Job Description",
    value=job_text,
    height=250,
    placeholder="Paste job or internship description here..."
)

# ---------------- ANALYZE BUTTON ----------------
if st.button("🚀 Analyze Job Posting"):

    if job_text.strip() == "":
        st.warning("Please enter a job description.")

    else:

        # ML Prediction
        text_vectorized = vectorizer.transform(
            [job_text]
        )

        prediction = model.predict(
            text_vectorized
        )[0]

        probability = model.predict_proba(
            text_vectorized
        )[0]

        fraud_score = probability[1] * 100
        confidence_score = probability[0] * 100

        lower_text = job_text.lower()
        reasons = []

        # ---------------- SCAM CHECKS ----------------
        for keyword in scam_keywords:
            if keyword in lower_text:
                reasons.append(keyword)

        if (
            "lakh" in lower_text
            or "100000" in lower_text
            or "₹50000" in lower_text
        ):
            reasons.append("high salary claim")

        if "whatsapp" in lower_text:
            reasons.append("whatsapp hiring")

        if (
            "fee" in lower_text
            or "payment" in lower_text
        ):
            reasons.append("registration/payment request")

        if (
            "urgent" in lower_text
            or "limited seats" in lower_text
        ):
            reasons.append("pressure tactic")

        # Email detection
        email_pattern = r'\S+@\S+'
        emails = re.findall(
            email_pattern,
            lower_text
        )

        suspicious_email = False

        for email in emails:
            for domain in free_email_domains:
                if domain in email:
                    suspicious_email = True
                    reasons.append("free email domain")

        st.markdown("---")

        # ---------------- RESULT ----------------
        if prediction == 1:

            st.error(
                "⚠️ Suspicious / Fake Job Detected"
            )

            risk_level = (
                "HIGH RISK"
                if fraud_score >= 80
                else "MEDIUM RISK"
            )

        else:

            st.success(
                "✅ Legitimate Job Posting"
            )

            if confidence_score >= 80:
                risk_level = "TRUSTED"

            elif confidence_score >= 50:
                risk_level = "VERIFY"

            else:
                risk_level = "SUSPICIOUS"

        # ---------------- DASHBOARD ----------------
        st.subheader(
            "📊 Risk Analytics Dashboard"
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Fraud Risk %",
                f"{fraud_score:.2f}%"
            )

        with col2:
            st.metric(
                "Risk Level",
                risk_level
            )

        # ---------------- AI SUMMARY ----------------
        st.subheader(
            "🧠 AI Risk Summary"
        )

        if reasons:

            summary = (
                "This job posting may be risky because "
            )

            if "registration/payment request" in reasons:
                summary += (
                    "it asks for registration/payment, "
                )

            if "whatsapp hiring" in reasons:
                summary += (
                    "uses WhatsApp recruitment, "
                )

            if "high salary claim" in reasons:
                summary += (
                    "contains unrealistic salary claims, "
                )

            if suspicious_email:
                summary += (
                    "uses a free recruiter email, "
                )

            if "pressure tactic" in reasons:
                summary += (
                    "and applies urgency tactics. "
                )

            summary += (
                "These patterns are commonly found in fake internships and scam job offers."
            )

            st.info(summary)

        else:

            st.success(
                "No major scam indicators were detected."
            )

        # ---------------- SAVE HISTORY ----------------
        history_data = {
            "Time": [
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ],
            "Fraud Risk %": [
                round(fraud_score, 2)
            ],
            "Risk Level": [
                risk_level
            ]
        }

        history_df = pd.DataFrame(
            history_data
        )

        if os.path.exists(
            history_file
        ):

            history_df.to_csv(
                history_file,
                mode="a",
                header=False,
                index=False
            )

        else:

            history_df.to_csv(
                history_file,
                index=False
            )

# ---------------- HISTORY ----------------
if os.path.exists(history_file):

    history_df = pd.read_csv(
        history_file
    )

    # Show only if history exists
    if not history_df.empty:

        st.markdown("---")

        with st.expander(
            "📜 View Analysis History"
        ):

            st.dataframe(
                history_df.tail(10),
                use_container_width=True
            )

# ---------------- FOOTER ----------------
st.markdown("---")

st.caption(
    "🛡️ Powered by JobShield AI | NLP & Machine Learning"
)