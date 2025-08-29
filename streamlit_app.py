# -*- coding: utf-8 -*-
# Import necessary libraries
import streamlit as st
import pandas as pd
import os
import pytz
from datetime import datetime
import io
import arabic_reshaper
from bidi.algorithm import get_display

# For PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ------------------------------
# General Settings
# ------------------------------
REPORTS_FILE = "reports.csv"
USERS_FILE = "users.csv"
tz = pytz.timezone("Asia/Riyadh")

# List of errors
ERRORS_LIST = [
    "باب السائق", "حزام", "افضلية", "سرعة", "ضعف مراقبة",
    "عدم التقيد بالمسارات", "سرعة اثناء الانعطاف", "إشارة للموازي",
    "موقف موازي", "صدم بالموازي", "مراقبة اثناء الخروج", "استخدام كلتا القدمين",
    "ضعف تحكم بالمقود", "صدم ثمانية", "إشارة ٩٠خلفي", "موقف ٩٠خلفي",
    "صدم ٩٠خلفي", "عكس سير", "فلشر للرجوع", "الرجوع للخلف",
    "مراقبة اثناء الرجوع", "تسارع عالي", "تباطؤ", "فرامل", "علامةقف",
    "صدم رصيف", "خطوط المشاة", "تجاوز اشارة", "موقف نهائي", "صدم نهائي"
]

# ------------------------------
# Ensure files exist
# ------------------------------
def ensure_files_exist():
    """
    Creates the necessary CSV files if they don't exist.
    """
    if not os.path.exists(REPORTS_FILE):
        df = pd.DataFrame(columns=["اسم التقرير", "وقت البداية", "وقت النهاية", "الأخطاء", "ملاحظات"])
        df.to_csv(REPORTS_FILE, index=False)

    if not os.path.exists(USERS_FILE):
        df = pd.DataFrame([{"username": "hus585", "password": "268450", "role": "admin"}])
        df.to_csv(USERS_FILE, index=False)

# ------------------------------
# Login function
# ------------------------------
def login(username, password):
    """
    Authenticates the user based on the provided username and password.
    """
    try:
        df = pd.read_csv(USERS_FILE, dtype=str)  # تعديل: قراءة الملف مع التأكد من أن جميع الأعمدة كنص
        
        # تعديل: التأكد من أن الأعمدة لا تحتوي على مسافات زائدة
        df['username'] = df['username'].str.strip()
        df['password'] = df['password'].str.strip()
        
        user = df[(df["username"] == username) & (df["password"] == password)]
        if not user.empty:
            return user.iloc[0]["role"]
        return None
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة ملف المستخدمين: {e}")
        return None

# ------------------------------
# Save report
# ------------------------------
def save_report(report_name, start_time, end_time, errors, notes):
    """
    Saves a new report to the CSV file.
    """
    try:
        df = pd.read_csv(REPORTS_FILE)
        new_row = pd.DataFrame([{
            "اسم التقرير": report_name,
            "وقت البداية": start_time,
            "وقت النهاية": end_time,
            "الأخطاء": "; ".join(errors),
            "ملاحظات": notes
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(REPORTS_FILE, index=False)
    except Exception as e:
        st.error(f"حدث خطأ أثناء حفظ التقرير: {e}")

# ------------------------------
# Generate PDF
# ------------------------------
def generate_pdf(report):
    """
    Generates a PDF report with proper Arabic text rendering.
    Returns the file path of the generated PDF.
    """
    # NOTE: You need to have a font file that supports Arabic on the machine
    # running this code. For example, 'Amiri-Regular.ttf'.
    # For a simple setup, you can try to find and upload one.
    
    # Register an Arabic font (replace 'DejaVuSans-Bold.ttf' with your font file)
    try:
        # We will use a font that is likely to be available or can be uploaded
        # For this example, we'll assume a font file exists.
        # In a real app, you would need to ensure the font file is present.
        font_path = "DejaVuSans-Bold.ttf" # You may need to change this path
        pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
    except Exception as e:
        st.error(f"خطأ: لم يتم العثور على ملف الخط 'DejaVuSans-Bold.ttf'. يرجى التأكد من وجوده. {e}")
        return None

    # Use a BytesIO object instead of a physical file
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    # Define a style for the Arabic text
    styles['Normal'].fontName = 'ArabicFont'
    styles['Title'].fontName = 'ArabicFont'

    # Helper function to process Arabic text
    def process_arabic(text):
        return get_display(arabic_reshaper.reshape(text))

    story = []

    story.append(Paragraph(process_arabic("تقرير التقييم"), styles['Title']))
    story.append(Spacer(1, 12))
    
    # Process and add all report details
    report_details = {
        "اسم التقرير": report['اسم التقرير'],
        "وقت البداية": report['وقت البداية'],
        "وقت النهاية": report['وقت النهاية'],
        "الأخطاء": report['الأخطاء'],
        "ملاحظات": report['ملاحظات']
    }

    for key, value in report_details.items():
        processed_key = process_arabic(key)
        processed_value = process_arabic(str(value)) # Ensure value is a string
        story.append(Paragraph(f"{processed_key}: {processed_value}", styles['Normal']))
        story.append(Spacer(1, 6))

    doc.build(story)
    
    # Go to the beginning of the buffer
    buffer.seek(0)
    return buffer

# ------------------------------
# Application Interface
# ------------------------------
def main():
    st.set_page_config(page_title="تقييم", layout="centered")
    ensure_files_exist()

    # Session State management
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "role" not in st.session_state:
        st.session_state.role = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "errors" not in st.session_state:
        st.session_state.errors = []
    if "report_name" not in st.session_state:
        st.session_state.report_name = ""
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "notes" not in st.session_state:
        st.session_state.notes = ""


    # -------------------- Login Page --------------------
    if st.session_state.page == "login":
        st.title("🔐 تسجيل الدخول")
        # تعديل: استخدام .strip() لإزالة أي مسافات زائدة من الإدخال
        username = st.text_input("اسم المستخدم").strip()
        password = st.text_input("كلمة المرور", type="password").strip()
        
        if st.button("دخول"):
            # تعديل: تمرير الإدخالات المعدلة للدالة
            role = login(username, password)
            if role:
                st.session_state.role = role
                st.session_state.username = username
                st.session_state.page = "home"
                st.success("تم تسجيل الدخول بنجاح")
                st.experimental_rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيح")

    # -------------------- Home Page --------------------
    elif st.session_state.page == "home":
        st.title("📊 تقييم")
        now = datetime.now(tz)
        st.write(f"📅 التاريخ: {now.strftime('%Y-%m-%d')}")
        st.write(f"⏰ الوقت: {now.strftime('%H:%M')}")

        st.session_state.report_name = st.text_input("اسم التقرير", st.session_state.report_name)

        if st.button("ابدأ التقييم"):
            if st.session_state.report_name.strip() == "":
                st.error("أدخل اسم التقرير أولاً")
            else:
                st.session_state.start_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
                st.session_state.errors = []
                st.session_state.notes = ""
                st.session_state.page = "errors"
                st.experimental_rerun()

        if st.button("📑 عرض السجلات"):
            st.session_state.page = "reports"
            st.experimental_rerun()

        # Added a logout button for convenience
        st.markdown("---")
        if st.button("🚪 خروج"):
            st.session_state.page = "login"
            st.session_state.role = None
            st.experimental_rerun()

    # -------------------- Errors Page --------------------
    elif st.session_state.page == "errors":
        st.title("🚦 الأخطاء")
        st.write("اختر الأخطاء التي وقع فيها السائق:")

        # Display selected errors
        if st.session_state.errors:
            st.write("الأخطاء المسجلة:")
            for i, err in enumerate(st.session_state.errors):
                st.info(f"{i + 1}. {err}")
            
            # Button to remove the last added error
            if st.button("إلغاء آخر خطأ"):
                st.session_state.errors.pop()
                st.experimental_rerun()

        # Use 2 columns for better responsiveness
        cols = st.columns(2)
        for i, err in enumerate(ERRORS_LIST):
            # Check if the error is already selected to disable the button
            button_disabled = err in st.session_state.errors
            if cols[i % 2].button(err, disabled=button_disabled):
                st.session_state.errors.append(err)
                st.success(f"تم تسجيل: {err}")
                st.experimental_rerun()
        
        # Keep the notes in session state to persist it
        st.session_state.notes = st.text_area("ملاحظات إضافية", st.session_state.notes)
        
        st.markdown("---")
        if st.button("إنهاء التقييم"):
            end_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
            save_report(st.session_state.report_name, st.session_state.start_time, end_time, st.session_state.errors, st.session_state.notes)
            st.success("✅ تم حفظ التقرير")
            st.session_state.page = "home"
            st.experimental_rerun()

        if st.button("إلغاء التقييم"):
            st.session_state.page = "home"
            st.experimental_rerun()

    # -------------------- Reports Page --------------------
    elif st.session_state.page == "reports":
        st.title("📑 السجلات")
        df = pd.read_csv(REPORTS_FILE)
        st.dataframe(df)

        if not df.empty:
            report_name = st.selectbox("اختر تقرير", df["اسم التقرير"].unique())
            
            col1, col2 = st.columns(2)

            with col1:
                if st.button("⬇️ تحميل PDF"):
                    report = df[df["اسم التقرير"] == report_name].iloc[0]
                    pdf_buffer = generate_pdf(report)
                    if pdf_buffer:
                        st.download_button(
                            label="تحميل التقرير كملف PDF",
                            data=pdf_buffer,
                            file_name=f"{report_name}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error("تعذر إنشاء ملف PDF. يرجى مراجعة رسالة الخطأ أعلاه.")

            with col2:
                if st.button("🗑️ حذف التقرير"):
                    df = df[df["اسم التقرير"] != report_name]
                    df.to_csv(REPORTS_FILE, index=False)
                    st.success("تم حذف التقرير")
                    st.experimental_rerun()

        if st.button("🔙 رجوع"):
            st.session_state.page = "home"
            st.experimental_rerun()


# ------------------------------
# Run the application
# ------------------------------
if __name__ == "__main__":
    main()
