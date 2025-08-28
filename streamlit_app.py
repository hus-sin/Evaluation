# app.py
import streamlit as st
import pandas as pd
import os
import hashlib
import io
from datetime import datetime

# timezone: try zoneinfo (Py3.9+), fallback to pytz if needed
try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Riyadh")
except Exception:
    import pytz
    TZ = pytz.timezone("Asia/Riyadh")

# PDF library
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

# --------- Config ----------
USERS_FILE = "users.csv"
REPORTS_FILE = "reports.csv"
PASSWORD_SALT = "veh_eval_salt_2025"  # salt for hashing (simple)

# Errors list (fixed order you gave)
ERRORS = [
    "باب السائق","حزام","افضلية","سرعة","ضعف مراقبة",
    "عدم التقيد بالمسارات","سرعة اثناء الانعطاف","إشارة للموازي","موقف موازي",
    "صدم بالموازي","مراقبة اثناء الخروج","استخدام كلتا القدمين","ضعف تحكم بالمقود",
    "صدم ثمانية","إشارة ٩٠ خلفي","موقف ٩٠ خلفي","صدم ٩٠ خلفي","عكس سير",
    "فلشر للرجوع","الرجوع للخلف","مراقبة اثناء الرجوع","تسارع عالي","تباطؤ",
    "فرامل","علامةقف","صدم رصيف","خطوط المشاة","تجاوز اشارة","موقف نهائي","صدم نهائي"
]

# --------- Helpers ----------
def hash_pw(password: str) -> str:
    return hashlib.sha256((password + PASSWORD_SALT).encode("utf-8")).hexdigest()

def ensure_files_exist():
    if not os.path.exists(USERS_FILE):
        df = pd.DataFrame(columns=["username","password_hash","role","active"])
        # initial admin (hus585 / 268450) active
        df = df.append({
            "username":"hus585",
            "password_hash": hash_pw("268450"),
            "role":"رئيسي",
            "active": True
        }, ignore_index=True)
        df.to_csv(USERS_FILE, index=False)

    if not os.path.exists(REPORTS_FILE):
        df = pd.DataFrame(columns=[
            "id","user","report_name","start_time","end_time","errors","notes"
        ])
        df.to_csv(REPORTS_FILE, index=False)

def load_users():
    return pd.read_csv(USERS_FILE)

def save_users(df):
    df.to_csv(USERS_FILE, index=False)

def load_reports():
    return pd.read_csv(REPORTS_FILE)

def save_reports(df):
    df.to_csv(REPORTS_FILE, index=False)

def now_local():
    # return timezone-aware datetime in Asia/Riyadh
    return datetime.now(TZ)

def fmt_dt(dt_obj):
    # accept naive string or datetime -> return formatted string "YYYY-MM-DD HH:MM"
    if isinstance(dt_obj, str):
        try:
            # try parse back
            dt = datetime.fromisoformat(dt_obj)
            return dt.astimezone(TZ).strftime("%Y-%m-%d %H:%M")
        except Exception:
            return dt_obj
    if isinstance(dt_obj, datetime):
        return dt_obj.astimezone(TZ).strftime("%Y-%m-%d %H:%M")
    return str(dt_obj)

def generate_pdf_bytes(report_row: pd.Series) -> bytes:
    """
    Generate a simple PDF (A4) with the report's content.
    Uses reportlab if available. Returns bytes.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab not available on the environment.")
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x_margin = 50
    y = height - 60
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x_margin, y, "تقرير تقييم")
    y -= 30
    c.setFont("Helvetica", 11)

    lines = [
        f"اسم التقرير: {report_row['report_name']}",
        f"المستخدم: {report_row.get('user', '')}",
        f"بدء: {fmt_dt(report_row['start_time'])}",
        f"نهاية: {fmt_dt(report_row['end_time'])}",
        f"الأخطاء:",
    ]
    for line in lines:
        c.drawString(x_margin, y, line)
        y -= 20

    # errors list
    errs = str(report_row.get("errors",""))
    for err in errs.split(";"):
        if err.strip():
            c.drawString(x_margin + 10, y, f"- {err.strip()}")
            y -= 16
            if y < 80:
                c.showPage()
                y = height - 60
                c.setFont("Helvetica", 11)

    y -= 10
    c.drawString(x_margin, y, "الملاحظات:")
    y -= 20
    notes = str(report_row.get("notes",""))
    # wrap notes manually
    max_chars = 90
    for i in range(0, len(notes), max_chars):
        c.drawString(x_margin + 5, y, notes[i:i+max_chars])
        y -= 16
        if y < 80:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 11)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

# --------- Initialize ----------
ensure_files_exist()

# Streamlit page config + simple light background and footer
st.set_page_config(page_title="تقييم السائق", layout="wide", page_icon="🚗")
st.markdown("""
    <style>
      .stApp { background-color: #f8fafc; }
      .footer { font-size:10px; color: #666; text-align:center; margin-top:10px; }
      .small { font-size:12px; color:#444; }
    </style>
""", unsafe_allow_html=True)

# --------- Session state defaults ----------
if "page" not in st.session_state:
    st.session_state.page = "login"   # default: login page
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "report_name" not in st.session_state:
    st.session_state.report_name = ""
if "start_dt_iso" not in st.session_state:
    st.session_state.start_dt_iso = None
if "notes" not in st.session_state:
    st.session_state.notes = ""
# ensure checkbox keys exist when starting evaluation

# --------- Pages: Login / Register / Home / Evaluation / History / Admin ----------
def page_login():
    st.markdown("<h2 style='text-align:center;'>تسجيل الدخول</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("اسم المستخدم", key="login_user")
        password = st.text_input("كلمة المرور", type="password", key="login_pass")
        if st.button("دخول"):
            df_users = load_users()
            user_row = df_users[df_users["username"] == username]
            if user_row.empty:
                st.error("اسم المستخدم غير موجود.")
                return
            user_row = user_row.iloc[0]
            if not user_row["active"]:
                st.error("الحساب معطّل. يرجى التواصل مع المسؤول لتفعيله.")
                return
            if hash_pw(password) != user_row["password_hash"]:
                st.error("كلمة المرور غير صحيحة.")
                return
            # success
            st.session_state.username = username
            st.session_state.role = user_row["role"]
            st.session_state.page = "home"
            st.experimental_rerun()
    st.markdown("---")
    st.write("إذا لم تملك حسابًا، سجل هنا:")
    if st.button("تسجيل حساب جديد"):
        st.session_state.page = "register"
        st.experimental_rerun()

def page_register():
    st.markdown("<h2 style='text-align:center;'>تسجيل حساب جديد</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        new_user = st.text_input("اسم مستخدم جديد", key="reg_user")
        new_pass = st.text_input("كلمة المرور", key="reg_pass", type="password")
    with col2:
        role = st.selectbox("نوع الحساب", ["مقيم", "مشاهد فقط"])
        st.markdown("ملاحظة: الحساب سيظهر **معطلاً** وسيحتاج تفعيل من المستخدم الرئيسي.")
    if st.button("سجل الآن"):
        if not new_user or not new_pass:
            st.warning("الرجاء إدخال اسم مستخدم وكلمة مرور.")
        else:
            df = load_users()
            if (df["username"] == new_user).any():
                st.error("اسم المستخدم موجود بالفعل. اختر اسمًا آخر.")
            else:
                df = df.append({
                    "username": new_user,
                    "password_hash": hash_pw(new_pass),
                    "role": role,
                    "active": False
                }, ignore_index=True)
                save_users(df)
                st.success("تم إنشاء الحساب بنجاح. الحساب معطّل حتى يفعّله المستخدم الرئيسي.")
    if st.button("عودة لتسجيل الدخول"):
        st.session_state.page = "login"
        st.experimental_rerun()

def page_home():
    # top row: date/time left, title center, user info right
    left, center, right = st.columns([1,2,1])
    with left:
        dt = now_local()
        st.markdown(f"<div class='small'>{dt.strftime('%Y-%m-%d')}<br>{dt.strftime('%H:%M')}</div>", unsafe_allow_html=True)
    with center:
        st.markdown("<h1 style='text-align:center;'>تقييم</h1>", unsafe_allow_html=True)
    with right:
        if st.session_state.username:
            st.markdown(f"<div style='text-align:right;'>المستخدم: <b>{st.session_state.username}</b><br><span class='small'>{st.session_state.role}</span></div>", unsafe_allow_html=True)
        else:
            st.write("")

    st.markdown("---")
    # report name input
    st.session_state.report_name = st.text_input("اسم التقرير (مثلاً: اسم السائق/رقم السيارة)", value=st.session_state.report_name, key="report_name_input")
    cols = st.columns(3)
    with cols[0]:
        if st.button("ابدأ التقييم"):
            if not st.session_state.report_name.strip():
                st.warning("أدخل اسم التقرير أولاً.")
            else:
                # set start time (ISO)
                st.session_state.start_dt_iso = now_local().isoformat()
                # initialize all checkbox keys to False for fresh evaluation
                for idx in range(len(ERRORS)):
                    st.session_state[f"err_{idx}"] = False
                st.session_state.notes = ""
                st.session_state.page = "evaluation"
                st.experimental_rerun()
    with cols[1]:
        if st.button("عرض السجل السابق"):
            st.session_state.page = "history"
            st.experimental_rerun()
    with cols[2]:
        if st.session_state.username:
            if st.button("تسجيل خروج"):
                st.session_state.username = None
                st.session_state.role = None
                st.session_state.page = "login"
                st.experimental_rerun()
        else:
            if st.button("دخول"):
                st.session_state.page = "login"
                st.experimental_rerun()

    st.markdown("<div class='footer'>تصميم حسين العييري</div>", unsafe_allow_html=True)

def page_evaluation():
    st.markdown(f"### التقييم: {st.session_state.report_name}")
    st.markdown(f"**وقت البداية:** {fmt_dt(st.session_state.start_dt_iso)}    (توقيت السعودية, 24h)")

    # Grid: 3 columns, rows auto
    cols = st.columns(3)
    for idx, err in enumerate(ERRORS):
        col = cols[idx % 3]
        # create checkbox with persistent key; default False if not set
        default_val = st.session_state.get(f"err_{idx}", False)
        checked = col.checkbox(err, key=f"err_{idx}", value=default_val)
        # nothing extra needed — checkbox persists selection

    st.session_state.notes = st.text_area("الملاحظات (تظهر في التقرير)", value=st.session_state.notes, height=120)

    # End evaluation
    if st.button("إنهاء التقييم"):
        # collect selected errors
        selected = []
        for idx, err in enumerate(ERRORS):
            if st.session_state.get(f"err_{idx}", False):
                selected.append(err)
        start_iso = st.session_state.start_dt_iso
        end_iso = now_local().isoformat()
        # load reports and append
        df = load_reports()
        next_id = int(df["id"].max())+1 if (not df.empty) else 1
        user = st.session_state.username if st.session_state.username else "anonymous"
        df = df.append({
            "id": next_id,
            "user": user,
            "report_name": st.session_state.report_name,
            "start_time": start_iso,
            "end_time": end_iso,
            "errors": "; ".join(selected),
            "notes": st.session_state.notes
        }, ignore_index=True)
        save_reports(df)
        st.success("تم حفظ التقرير.")
        # set last viewed report id
        st.session_state.last_report_id = next_id
        # reset local fields for next time but don't clear username
        st.session_state.report_name = ""
        st.session_state.start_dt_iso = None
        st.session_state.notes = ""
        for idx in range(len(ERRORS)):
            st.session_state[f"err_{idx}"] = False
        st.session_state.page = "history"
        st.experimental_rerun()

    if st.button("إلغاء والعودة للرئيسية"):
        st.session_state.page = "home"
        st.experimental_rerun()

def page_history():
    st.markdown("<h2>سجل التقييمات</h2>", unsafe_allow_html=True)
    df = load_reports()
    if df.empty:
        st.info("لا توجد تقارير محفوظة بعد.")
        if st.button("رجوع للصفحة الرئيسية"):
            st.session_state.page = "home"
            st.experimental_rerun()
        return

    # Restrict view for 'مقيم' to only their reports
    if st.session_state.role == "مقيم":
        df_view = df[df["user"] == st.session_state.username].copy()
    else:
        df_view = df.copy()

    # show summary table (id, report_name, user, start, end)
    df_view_display = df_view[["id","report_name","user","start_time","end_time"]].copy()
    df_view_display["start_time"] = df_view_display["start_time"].apply(fmt_dt)
    df_view_display["end_time"] = df_view_display["end_time"].apply(fmt_dt)
    st.dataframe(df_view_display.reset_index(drop=True))

    # select a report by id
    ids = df_view["id"].astype(int).tolist()
    selected_id = st.selectbox("اختر رقم التقرير لعرض التفاصيل", ids)
    if selected_id:
        report_row = df[df["id"] == selected_id].iloc[0]
        st.markdown("**تفاصيل التقرير**")
        st.write(f"اسم التقرير: {report_row['report_name']}")
        st.write(f"المستخدم: {report_row['user']}")
        st.write(f"وقت البداية: {fmt_dt(report_row['start_time'])}")
        st.write(f"وقت النهاية: {fmt_dt(report_row['end_time'])}")
        st.write("الأخطاء:")
        if str(report_row['errors']).strip():
            for e in str(report_row['errors']).split(";"):
                st.write(f"- {e.strip()}")
        else:
            st.write("- لا توجد أخطاء.")
        st.write("الملاحظات:")
        st.write(report_row.get('notes',''))

        # PDF download (if reportlab available)
        if REPORTLAB_AVAILABLE:
            try:
                pdf_bytes = generate_pdf_bytes(report_row)
                st.download_button("تحميل التقرير كـ PDF", data=pdf_bytes,
                                   file_name=f"report_{selected_id}.pdf", mime="application/pdf")
            except Exception as ex:
                st.error(f"حدث خطأ أثناء توليد PDF: {ex}")
        else:
            st.info("ميزة تحميل PDF غير متاحة (تأكد من إضافة reportlab في requirements).")

        # Deletion: permit if admin OR owner
        can_delete = False
        if st.session_state.role == "رئيسي":
            can_delete = True
        if st.session_state.username == report_row['user']:
            can_delete = True
        if can_delete:
            if st.button("حذف هذا التقرير"):
                df_all = load_reports()
                df_all = df_all[df_all["id"] != selected_id]
                save_reports(df_all)
                st.success("تم حذف التقرير.")
                st.experimental_rerun()
        else:
            st.info("لا تملك صلاحية حذف هذا التقرير.")

    if st.button("رجوع للصفحة الرئيسية"):
        st.session_state.page = "home"
        st.experimental_rerun()

def page_admin():
    st.markdown("<h2>لوحة إدارة المستخدمين (للمستخدم الرئيسي)</h2>", unsafe_allow_html=True)
    df = load_users()
    st.dataframe(df.reset_index(drop=True))

    st.markdown("### تفعيل / تعطيل حساب")
    users = df["username"].tolist()
    selected = st.selectbox("اختر مستخدم", users)
    if selected:
        idx = df[df["username"] == selected].index[0]
        current_active = bool(df.at[idx, "active"])
        new_state = st.radio("الحالة:", ("مفعل", "معطل"), index=0 if current_active else 1)
        if st.button("تطبيق الحالة"):
            df.at[idx, "active"] = True if new_state == "مفعل" else False
            save_users(df)
            st.success("تم تحديث الحالة.")
            st.experimental_rerun()

    st.markdown("### تغيير الصلاحية")
    if selected:
        new_role = st.selectbox("اختر الصلاحية الجديدة", ["رئيسي","مقيم","مشاهد فقط"])
        if st.button("تغيير الصلاحية"):
            df.at[idx, "role"] = new_role
            save_users(df)
            st.success("تم تعديل الصلاحية.")
            st.experimental_rerun()

    if st.button("عودة"):
        st.session_state.page = "home"
        st.experimental_rerun()

# --------- Router ----------
page = st.session_state.page

if page == "login":
    page_login()
elif page == "register":
    page_register()
elif page == "home":
    page_home()
elif page == "evaluation":
    page_evaluation()
elif page == "history":
    page_history()
elif page == "admin":
    # only allow admin user
    if st.session_state.role == "رئيسي":
        page_admin()
    else:
        st.error("هذه الصفحة متاحة للمستخدم الرئيسي فقط.")
        if st.button("العودة"):
            st.session_state.page = "home"
            st.experimental_rerun()

st.markdown("<div class='footer'>تصميم حسين العييري</div>", unsafe_allow_html=True)
