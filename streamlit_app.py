# -*- coding: utf-8 -*-
# Import necessary libraries
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz

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
        # Read the users file and ensure all columns are treated as strings
        df = pd.read_csv(USERS_FILE, dtype=str)
        # Remove any leading/trailing whitespace
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
        username = st.text_input("اسم المستخدم").strip()
        password = st.text_input("كلمة المرور", type="password").strip()
        
        if st.button("دخول"):
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
            if not st.session_state.report_name.strip():
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

        st.markdown("---")
        if st.button("🚪 خروج"):
            st.session_state.page = "login"
            st.session_state.role = None
            st.experimental_rerun()

    # -------------------- Errors Page --------------------
    elif st.session_state.page == "errors":
        st.title("🚦 الأخطاء")
        st.write("اختر الأخطاء التي وقع فيها السائق:")

        if st.session_state.errors:
            st.write("الأخطاء المسجلة:")
            for i, err in enumerate(st.session_state.errors):
                st.info(f"{i + 1}. {err}")
            
            if st.button("إلغاء آخر خطأ"):
                st.session_state.errors.pop()
                st.experimental_rerun()

        cols = st.columns(2)
        for i, err in enumerate(ERRORS_LIST):
            button_disabled = err in st.session_state.errors
            if cols[i % 2].button(err, disabled=button_disabled):
                st.session_state.errors.append(err)
                st.success(f"تم تسجيل: {err}")
                st.experimental_rerun()
        
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
        try:
            df = pd.read_csv(REPORTS_FILE)
            if not df.empty:
                st.dataframe(df)

                report_name = st.selectbox("اختر تقرير", df["اسم التقرير"].unique())
                
                if st.button("🗑️ حذف التقرير"):
                    df = df[df["اسم التقرير"] != report_name]
                    df.to_csv(REPORTS_FILE, index=False)
                    st.success("تم حذف التقرير")
                    st.experimental_rerun()
            else:
                st.info("لا توجد تقارير حالياً.")
        except pd.errors.EmptyDataError:
            st.info("ملف التقارير فارغ. ابدأ بإضافة تقرير جديد.")
        except Exception as e:
            st.error(f"حدث خطأ أثناء قراءة ملف التقارير: {e}")

        if st.button("🔙 رجوع"):
            st.session_state.page = "home"
            st.experimental_rerun()

# ------------------------------
# Run the application
# ------------------------------
if __name__ == "__main__":
    main()
