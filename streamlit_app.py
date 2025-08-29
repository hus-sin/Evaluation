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

# Define user roles for easy access
ROLES = {
    "admin": "admin",
    "evaluator": "evaluator",
    "viewer": "viewer"
}

# List of errors for the evaluation page
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
# Ensure files exist and handle user setup
# ------------------------------
def ensure_files_exist():
    """
    Creates the necessary CSV files if they don't exist.
    Initializes a new admin and viewer user if the users file is missing.
    """
    # Define columns for the reports file, now without "اسم المقيم"
    reports_cols = ["اسم التقرير", "وقت البداية", "وقت النهاية", "الأخطاء", "ملاحظات", "اسم المستخدم", "رقم المركبة"]
    if not os.path.exists(REPORTS_FILE):
        df = pd.DataFrame(columns=reports_cols)
        df.to_csv(REPORTS_FILE, index=False)
    # New code: clear all reports on app start
    else:
        df = pd.DataFrame(columns=reports_cols)
        df.to_csv(REPORTS_FILE, index=False)
        
    # Define columns for the users file, including name and vehicle number
    users_cols = ["username", "password", "role", "evaluator_access", "name", "vehicle_number"]
    if not os.path.exists(USERS_FILE):
        initial_users = [
            {"username": "hus585", "password": "268450", "role": ROLES["admin"], "evaluator_access": True, "name": "المستخدم الرئيسي", "vehicle_number": "12345"},
            {"username": "qwe", "password": "123123", "role": ROLES["viewer"], "evaluator_access": False, "name": "المشاهد", "vehicle_number": "98765"}
        ]
        df = pd.DataFrame(initial_users)
        df.to_csv(USERS_FILE, index=False)

# ------------------------------
# User Management Functions
# ------------------------------
def login(username, password):
    """Authenticates the user and returns their details."""
    try:
        df = pd.read_csv(USERS_FILE, dtype=str)
        df['username'] = df['username'].str.strip()
        df['password'] = df['password'].str.strip()
        
        # Convert both the input username and the dataframe usernames to lowercase for case-insensitive comparison
        input_username_lower = username.lower()
        df['username_lower'] = df['username'].str.lower()
        
        user = df[(df["username_lower"] == input_username_lower) & (df["password"] == password)]
        
        if not user.empty:
            role = user.iloc[0]["role"]
            evaluator_access = user.iloc[0]["evaluator_access"] == "True"
            name = user.iloc[0]["name"]
            vehicle_number = user.iloc[0]["vehicle_number"]
            return role, evaluator_access, name, vehicle_number
        return None, False, None, None
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة ملف المستخدمين: {e}")
        return None, False, None, None

def register_user(username, password, name, vehicle_number):
    """
    Registers a new user with an 'evaluator' role and no access initially.
    """
    try:
        df = pd.read_csv(USERS_FILE, dtype=str)
        if username in df["username"].values:
            return False, "اسم المستخدم موجود بالفعل."
        
        new_row = pd.DataFrame([{
            "username": username,
            "password": password,
            "role": ROLES["evaluator"],
            "evaluator_access": False,
            "name": name,
            "vehicle_number": vehicle_number
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(USERS_FILE, index=False)
        return True, "تم التسجيل بنجاح. سيتم تفعيل حسابك لاحقًا من قِبل المسؤول."
    except Exception as e:
        return False, f"حدث خطأ أثناء التسجيل: {e}"

def update_user_permissions(username, new_role, new_access):
    """Updates a user's role and evaluator_access in the users.csv file."""
    try:
        df = pd.read_csv(USERS_FILE, dtype=str)
        df.loc[df['username'] == username, 'role'] = new_role
        df.loc[df['username'] == username, 'evaluator_access'] = str(new_access)
        df.to_csv(USERS_FILE, index=False)
        return True, "تم حفظ التعديلات بنجاح."
    except Exception as e:
        return False, f"حدث خطأ أثناء حفظ التعديلات: {e}"

def save_report(report_name, start_time, end_time, errors, notes, username, vehicle_number):
    """Saves a new report to the CSV file, including the user's name and vehicle number."""
    try:
        df = pd.read_csv(REPORTS_FILE)
        new_row = pd.DataFrame([{
            "اسم التقرير": report_name,
            "وقت البداية": start_time,
            "وقت النهاية": end_time,
            "الأخطاء": "; ".join(errors),
            "ملاحظات": notes,
            "اسم المستخدم": username,
            "رقم المركبة": vehicle_number
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(REPORTS_FILE, index=False)
    except Exception as e:
        st.error(f"حدث خطأ أثناء حفظ التقرير: {e}")

def delete_report(report_name):
    """Deletes a report by name from the CSV file."""
    try:
        df = pd.read_csv(REPORTS_FILE)
        df = df[df["اسم التقرير"] != report_name]
        df.to_csv(REPORTS_FILE, index=False)
    except Exception as e:
        st.error(f"حدث خطأ أثناء حذف التقرير: {e}")

# ------------------------------
# Application Interface
# ------------------------------
def main():
    st.set_page_config(page_title="تقييم", layout="centered")
    ensure_files_exist()

    # Session State management
    if "page" not in st.session_state: st.session_state.page = "login"
    if "role" not in st.session_state: st.session_state.role = None
    if "username" not in st.session_state: st.session_state.username = None
    if "evaluator_access" not in st.session_state: st.session_state.evaluator_access = False
    if "evaluator_name" not in st.session_state: st.session_state.evaluator_name = None
    if "vehicle_number" not in st.session_state: st.session_state.vehicle_number = None
    if "errors" not in st.session_state: st.session_state.errors = []
    if "report_name" not in st.session_state: st.session_state.report_name = ""
    if "start_time" not in st.session_state: st.session_state.start_time = None
    if "notes" not in st.session_state: st.session_state.notes = ""

    # -------------------- Login Page --------------------
    if st.session_state.page == "login":
        st.title("🔐 تسجيل الدخول")
        username = st.text_input("اسم المستخدم").strip()
        password = st.text_input("كلمة المرور", type="password").strip()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("دخول"):
                role, access, name, vehicle = login(username, password)
                if role:
                    st.session_state.role = role
                    st.session_state.username = username
                    st.session_state.evaluator_access = access
                    st.session_state.evaluator_name = name
                    st.session_state.vehicle_number = vehicle
                    st.session_state.page = "home"
                    st.success("تم تسجيل الدخول بنجاح")
                    st.rerun()
                else:
                    st.error("اسم المستخدم أو كلمة المرور غير صحيح")
        with col2:
            if st.button("تسجيل مستخدم جديد"):
                st.session_state.page = "register"
                st.rerun()

    # -------------------- Register Page --------------------
    elif st.session_state.page == "register":
        st.title("📝 تسجيل مستخدم جديد")
        new_username = st.text_input("اسم المستخدم الجديد").strip()
        new_password = st.text_input("كلمة المرور الجديدة", type="password").strip()
        new_name = st.text_input("اسم المقيم").strip()
        new_vehicle_number = st.text_input("رقم المركبة").strip()
        
        if st.button("إنشاء حساب"):
            if not new_username or not new_password or not new_name or not new_vehicle_number:
                st.error("يرجى إدخال جميع الحقول.")
            else:
                success, message = register_user(new_username, new_password, new_name, new_vehicle_number)
                if success:
                    st.success(message)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(message)
        
        if st.button("رجوع إلى تسجيل الدخول"):
            st.session_state.page = "login"
            st.rerun()

    # -------------------- Admin Management Page --------------------
    elif st.session_state.page == "admin_management":
        st.title("👨‍💼 إدارة المستخدمين")
        
        df_users = pd.read_csv(USERS_FILE, dtype=str)
        st.write("يمكنك تعديل صلاحيات المستخدمين من هنا:")
        
        form_submitted = False
        with st.form("admin_form"):
            for index, row in df_users.iterrows():
                username = row['username']
                current_role = row['role']
                current_access = row['evaluator_access'] == "True"
                
                st.markdown(f"**المستخدم:** {username}")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_role = st.selectbox(
                        "الدور",
                        options=list(ROLES.values()),
                        index=list(ROLES.values()).index(current_role),
                        key=f"role_{username}"
                    )
                with col2:
                    new_access = st.checkbox(
                        "صلاحية التقييم",
                        value=current_access,
                        key=f"access_{username}"
                    )
                st.markdown("---")
            
            if st.form_submit_button("حفظ التعديلات"):
                form_submitted = True
        
        if form_submitted:
            for index, row in df_users.iterrows():
                username = row['username']
                new_role = st.session_state[f"role_{username}"]
                new_access = st.session_state[f"access_{username}"]
                
                if new_role != row['role'] or new_access != (row['evaluator_access'] == "True"):
                    update_user_permissions(username, new_role, new_access)
                    st.success(f"تم تحديث صلاحيات المستخدم {username} بنجاح.")
            st.rerun()
            
        if st.button("🔙 رجوع إلى الرئيسية"):
            st.session_state.page = "home"
            st.rerun()

    # -------------------- Home Page --------------------
    elif st.session_state.page == "home":
        st.title("📊 صفحة الرئيسية")
        st.write(f"مرحباً، {st.session_state.evaluator_name}!")
        now = datetime.now(tz)
        st.write(f"📅 التاريخ: {now.strftime('%Y-%m-%d')}")
        st.write(f"⏰ الوقت: {now.strftime('%H:%M')}")
        st.markdown("---")
        
        is_admin = st.session_state.role == ROLES["admin"]
        has_evaluator_access = st.session_state.evaluator_access
        
        if is_admin or has_evaluator_access:
            st.subheader("بدء تقييم جديد")
            st.session_state.report_name = st.text_input("اسم التقرير", st.session_state.report_name)
            if st.button("ابدأ التقييم"):
                if not st.session_state.report_name.strip():
                    st.error("أدخل اسم التقرير أولاً")
                else:
                    st.session_state.start_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
                    st.session_state.errors = []
                    st.session_state.notes = ""
                    st.session_state.page = "errors"
                    st.rerun()
        else:
            st.info("ليس لديك صلاحية لإجراء تقييمات.")

        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📑 عرض السجلات"):
                st.session_state.page = "reports"
                st.rerun()
        with col2:
            if is_admin:
                if st.button("👨‍💼 إدارة المستخدمين"):
                    st.session_state.page = "admin_management"
                    st.rerun()

        st.markdown("---")
        if st.button("🚪 خروج"):
            st.session_state.page = "login"
            st.session_state.role = None
            st.session_state.username = None
            st.session_state.evaluator_access = False
            st.session_state.evaluator_name = None
            st.session_state.vehicle_number = None
            st.rerun()

    # -------------------- Errors Page --------------------
    elif st.session_state.page == "errors":
        st.title("🚦 الأخطاء")
        st.write("اختر الأخطاء التي وقع فيها السائق:")
        
        # Display the recorded errors
        if st.session_state.errors:
            st.write("الأخطاء المسجلة:")
            for i, err in enumerate(st.session_state.errors):
                st.info(f"{i + 1}. {err}")
            
            # Button to undo the last error
            if st.button("إلغاء آخر خطأ"):
                st.session_state.errors.pop()
                st.rerun()

        # Inject CSS to make buttons fill the column
        st.markdown("""
        <style>
        div.stButton > button {
            width: 100%;
        }
        </style>
        """, unsafe_allow_html=True)

        cols = st.columns(3)
        for i, err in enumerate(ERRORS_LIST):
            button_disabled = err in st.session_state.errors
            with cols[i % 3]:
                if st.button(err, disabled=button_disabled, key=f"err_btn_{i}"):
                    st.session_state.errors.append(err)
                    st.success(f"تم تسجيل: {err}")
                    st.rerun()
        
        st.session_state.notes = st.text_area("ملاحظات إضافية", st.session_state.notes)
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("إنهاء التقييم"):
                end_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
                save_report(st.session_state.report_name, st.session_state.start_time, end_time, st.session_state.errors, st.session_state.notes, st.session_state.username, st.session_state.vehicle_number)
                st.success("✅ تم حفظ التقرير")
                st.session_state.page = "home"
                st.rerun()

        with col2:
            if st.button("إلغاء التقييم"):
                st.session_state.page = "home"
                st.rerun()

    # -------------------- Reports Page --------------------
    elif st.session_state.page == "reports":
        st.title("📑 السجلات")
        try:
            df = pd.read_csv(REPORTS_FILE)
            
            # Filter reports based on user role
            if st.session_state.role == ROLES["evaluator"]:
                df = df[df["اسم المستخدم"] == st.session_state.username]
                st.info("أنت تشاهد تقاريرك الخاصة فقط.")
            
            if not df.empty:
                st.dataframe(df)
                
                # Admin can delete reports
                if st.session_state.role == ROLES["admin"]:
                    report_name_to_delete = st.selectbox("اختر تقرير لحذفه", df["اسم التقرير"].unique())
                    if st.button("🗑️ حذف التقرير"):
                        delete_report(report_name_to_delete)
                        st.success("تم حذف التقرير")
                        st.rerun()
                else:
                    st.warning("ليس لديك صلاحية لحذف التقارير.")

            else:
                st.info("لا توجد تقارير متاحة.")
        except pd.errors.EmptyDataError:
            st.info("ملف التقارير فارغ. ابدأ بإضافة تقرير جديد.")
        except Exception as e:
            st.error(f"حدث خطأ أثناء قراءة ملف التقارير: {e}")

        if st.button("🔙 رجوع"):
            st.session_state.page = "home"
            st.rerun()

# ------------------------------
# Run the application
# ------------------------------
if __name__ == "__main__":
    main()
