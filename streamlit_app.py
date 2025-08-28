# streamlit_app.py
import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime
import pytz

# PDF
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB = True
except Exception:
    REPORTLAB = False

# -------- CONFIG ----------
TZ = pytz.timezone("Asia/Riyadh")
USERS_FILE = "users.csv"
REPORTS_FILE = "reports.csv"

ERRORS = [
    "باب السائق","حزام","افضلية","سرعة","ضعف مراقبة",
    "عدم التقيد بالمسارات","سرعة اثناء الانعطاف","إشارة للموازي","موقف موازي",
    "صدم بالموازي","مراقبة اثناء الخروج","استخدام كلتا القدمين","ضعف تحكم بالمقود",
    "صدم ثمانية","إشارة ٩٠ خلفي","موقف ٩٠ خلفي","صدم ٩٠ خلفي","عكس سير",
    "فلشر للرجوع","الرجوع للخلف","مراقبة اثناء الرجوع","تسارع عالي","تباطؤ",
    "فرامل","علامةقف","صدم رصيف","خطوط المشاة","تجاوز اشارة","موقف نهائي","صدم نهائي"
]

# -------- Helpers ----------
def now_riyadh():
    return datetime.now(TZ)

def fmt(dt):
    if isinstance(dt, str):
        try:
            d = datetime.fromisoformat(dt)
            return d.astimezone(TZ).strftime("%Y-%m-%d %H:%M")
        except Exception:
            return dt
    if isinstance(dt, datetime):
        return dt.astimezone(TZ).strftime("%Y-%m-%d %H:%M")
    return str(dt)

def ensure_files():
    # create users file if missing (with active admin)
    if not os.path.exists(USERS_FILE):
        df = pd.DataFrame([{
            "username": "hus585",
            "password": "268450",
            "role": "رئيسي",
            "active": True
        }])
        df.to_csv(USERS_FILE, index=False, encoding="utf-8-sig")
    # create reports file if missing
    if not os.path.exists(REPORTS_FILE):
        df = pd.DataFrame(columns=["id","user","report_name","start_time","end_time","errors","notes"])
        df.to_csv(REPORTS_FILE, index=False, encoding="utf-8-sig")

def load_users():
    try:
        return pd.read_csv(USERS_FILE, encoding="utf-8-sig")
    except Exception:
        return pd.DataFrame(columns=["username","password","role","active"])

def save_users(df):
    df.to_csv(USERS_FILE, index=False, encoding="utf-8-sig")

def load_reports():
    try:
        return pd.read_csv(REPORTS_FILE, encoding="utf-8-sig")
    except Exception:
        return pd.DataFrame(columns=["id","user","report_name","start_time","end_time","errors","notes"])

def save_reports(df):
    df.to_csv(REPORTS_FILE, index=False, encoding="utf-8-sig")

def generate_pdf_bytes(report_row):
    """Return PDF as bytes for a report_row (pandas Series). Requires reportlab."""
    if not REPORTLAB:
        raise RuntimeError("reportlab غير مثبت. أضف reportlab إلى requirements.")
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x = 50
    y = height - 60
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "تقرير تقييم")
    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(x, y, f"اسم التقرير: {report_row.get('report_name','')}")
    y -= 20
    c.drawString(x, y, f"المستخدم: {report_row.get('user','')}")
    y -= 20
    c.drawString(x, y, f"وقت البداية: {fmt(report_row.get('start_time',''))}")
    y -= 20
    c.drawString(x, y, f"وقت النهاية: {fmt(report_row.get('end_time',''))}")
    y -= 30
    c.setFont("Helvetica-Bold", 13)
    c.drawString(x, y, "الأخطاء:")
    y -= 20
    c.setFont("Helvetica", 12)
    errs = str(report_row.get("errors",""))
    for line in errs.split(";"):
        if line.strip():
            c.drawString(x+10, y, "- " + line.strip())
            y -= 16
            if y < 80:
                c.showPage()
                y = height - 60
                c.setFont("Helvetica", 12)
    y -= 10
    c.setFont("Helvetica-Bold", 13)
    c.drawString(x, y, "الملاحظات:")
    y -= 20
    c.setFont("Helvetica", 11)
    notes = str(report_row.get("notes",""))
    # wrap notes approx
    max_chars = 90
    for i in range(0, len(notes), max_chars):
        c.drawString(x+5, y, notes[i:i+max_chars])
        y -= 14
        if y < 80:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 11)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

# -------- UI pages ----------
def page_login():
    st.header("تسجيل الدخول")
    u = st.text_input("اسم المستخدم", key="login_user")
    p = st.text_input("كلمة المرور", type="password", key="login_pass")
    if st.button("دخول"):
        users = load_users()
        row = users[(users["username"]==u) & (users["password"]==p)]
        if row.empty:
            st.error("اسم المستخدم أو كلمة المرور خاطئ.")
            return
        if not bool(row.iloc[0].get("active", False)):
            st.error("الحساب معطّل. تواصل مع المستخدم الرئيسي لتفعيله.")
            return
        st.session_state.username = u
        st.session_state.role = row.iloc[0].get("role","")
        st.session_state.page = "home"
        st.experimental_rerun()
    st.markdown("---")
    if st.button("تسجيل حساب جديد"):
        st.session_state.page = "register"
        st.experimental_rerun()

def page_register():
    st.header("تسجيل حساب جديد")
    newu = st.text_input("اسم المستخدم الجديد", key="reg_user")
    newp = st.text_input("كلمة المرور", key="reg_pass", type="password")
    role = st.selectbox("نوع الحساب", ["مقيم","مشاهد فقط"])
    st.write("ملاحظة: الحساب سيُنشأ **معطّلًا** ويتطلب تفعيلًا من المستخدم الرئيسي.")
    if st.button("إنشاء"):
        if not newu or not newp:
            st.warning("أكمل الحقول")
        else:
            users = load_users()
            if (users["username"]==newu).any():
                st.error("اسم المستخدم موجود بالفعل.")
            else:
                new_row = pd.DataFrame([{
                    "username": newu,
                    "password": newp,
                    "role": role,
                    "active": False
                }])
                users = pd.concat([users, new_row], ignore_index=True)
                save_users(users)
                st.success("تم إنشاء الحساب (معطّل). انتظر التفعيل من المسؤول.")
    if st.button("عودة"):
        st.session_state.page = "login"
        st.experimental_rerun()

def page_home():
    left, center, right = st.columns([1,2,1])
    with left:
        dt = now_riyadh()
        st.markdown(f"<div style='font-size:13px'>{dt.strftime('%Y-%m-%d')}<br>{dt.strftime('%H:%M')}</div>", unsafe_allow_html=True)
    with center:
        st.markdown("<h1 style='text-align:center'>تقييم</h1>", unsafe_allow_html=True)
    with right:
        if st.session_state.get("username"):
            st.markdown(f"<div style='text-align:right'>المستخدم: <b>{st.session_state.username}</b><br><span style='font-size:12px'>{st.session_state.get('role','')}</span></div>", unsafe_allow_html=True)
    st.markdown("---")

    # اسم التقرير
    st.session_state.report_name = st.text_input("اسم التقرير (مثال: اسم السائق/رقم السيارة)", value=st.session_state.get("report_name",""), key="report_name_input")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("ابدأ التقييم"):
            if not st.session_state.report_name or not st.session_state.report_name.strip():
                st.warning("أدخل اسم التقرير أولاً.")
            else:
                # set start time and reset checkboxes
                st.session_state.start_time = now_riyadh().isoformat()
                for i in range(len(ERRORS)):
                    st.session_state[f"err_{i}"] = False
                st.session_state.notes = ""
                st.session_state.page = "evaluation"
                st.experimental_rerun()
    with c2:
        if st.button("عرض السجل"):
            st.session_state.page = "history"
            st.experimental_rerun()
    with c3:
        if st.session_state.get("username"):
            if st.button("تسجيل خروج"):
                st.session_state.username = None
                st.session_state.role = None
                st.session_state.page = "login"
                st.experimental_rerun()
        else:
            if st.button("دخول"):
                st.session_state.page = "login"
                st.experimental_rerun()
    st.markdown("<div style='font-size:10px; text-align:center; color:#666'>تصميم حسين العييري</div>", unsafe_allow_html=True)

def page_evaluation():
    st.header(f"التقييم: {st.session_state.get('report_name','')}")
    st.write(f"وقت البداية: {fmt(st.session_state.get('start_time',''))}   (توقيت السعودية)")
    # grid 3 columns, buttons replaced by checkboxes for single-click selection and persistence
    cols = st.columns(3)
    for i, err in enumerate(ERRORS):
        col = cols[i % 3]
        key = f"err_{i}"
        current = st.session_state.get(key, False)
        val = col.checkbox(err, key=key, value=current)
        # using checkbox so single click toggles and persists

    st.session_state.notes = st.text_area("الملاحظات", value=st.session_state.get("notes",""), height=120)
    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("إنهاء التقييم"):
            # collect selected
            selected = [ERRORS[i] for i in range(len(ERRORS)) if st.session_state.get(f"err_{i}", False)]
            start_iso = st.session_state.get("start_time")
            end_iso = now_riyadh().isoformat()
            # save to CSV
            reports = load_reports()
            next_id = int(reports["id"].max())+1 if (not reports.empty) else 1
            user = st.session_state.get("username","anonymous")
            new_row = pd.DataFrame([{
                "id": next_id,
                "user": user,
                "report_name": st.session_state.get("report_name",""),
                "start_time": start_iso,
                "end_time": end_iso,
                "errors": "; ".join(selected),
                "notes": st.session_state.get("notes","")
            }])
            reports = pd.concat([reports, new_row], ignore_index=True)
            save_reports(reports)
            st.success("تم حفظ التقرير.")
            # reset
            st.session_state.report_name = ""
            st.session_state.start_time = None
            st.session_state.notes = ""
            for i in range(len(ERRORS)):
                st.session_state[f"err_{i}"] = False
            st.session_state.page = "history"
            st.experimental_rerun()
    with c2:
        if st.button("إلغاء والعودة"):
            st.session_state.page = "home"
            st.experimental_rerun()

def page_history():
    st.header("سجل التقييمات")
    reports = load_reports()
    if reports.empty:
        st.info("لا توجد تقارير محفوظة.")
        if st.button("رجوع"):
            st.session_state.page = "home"
            st.experimental_rerun()
        return

    # if user role مقيم, show only their reports
    if st.session_state.get("role") == "مقيم":
        df_view = reports[reports["user"] == st.session_state.get("username")]
    else:
        df_view = reports.copy()

    # show summary
    df_display = df_view[["id","report_name","user","start_time","end_time"]].copy()
    df_display["start_time"] = df_display["start_time"].apply(fmt)
    df_display["end_time"] = df_display["end_time"].apply(fmt)
    st.dataframe(df_display.reset_index(drop=True))

    ids = df_view["id"].astype(int).tolist()
    sel = st.selectbox("اختر رقم التقرير لعرض التفاصيل", ids)
    if sel:
        row = reports[reports["id"]==sel].iloc[0]
        st.subheader("تفاصيل التقرير")
        st.write("اسم التقرير:", row["report_name"])
        st.write("المستخدم:", row["user"])
        st.write("وقت البداية:", fmt(row["start_time"]))
        st.write("وقت النهاية:", fmt(row["end_time"]))
        st.write("الأخطاء:")
        if str(row["errors"]).strip():
            for e in str(row["errors"]).split(";"):
                if e.strip():
                    st.write("-", e.strip())
        else:
            st.write("- لا توجد أخطاء")
        st.write("الملاحظات:")
        st.write(row.get("notes",""))
        # download PDF
        if REPORTLAB:
            try:
                pdf_bytes = generate_pdf_bytes(row)
                st.download_button("تحميل التقرير PDF", data=pdf_bytes, file_name=f"report_{sel}.pdf", mime="application/pdf")
            except Exception as ex:
                st.error("خطأ في إنشاء PDF: " + str(ex))
        else:
            st.info("تحميل PDF غير متاح (تأكد من إضافة reportlab إلى requirements).")
        # deletion (admin or owner)
        can_delete = False
        if st.session_state.get("role") == "رئيسي":
            can_delete = True
        if st.session_state.get("username") == row["user"]:
            can_delete = True
        if can_delete:
            if st.button("حذف التقرير"):
                reports_all = load_reports()
                reports_all = reports_all[reports_all["id"] != sel]
                save_reports(reports_all)
                st.success("تم حذف التقرير.")
                st.experimental_rerun()
        else:
            st.info("لا تملك صلاحية حذف هذا التقرير.")
    if st.button("رجوع"):
        st.session_state.page = "home"
        st.experimental_rerun()

def page_admin():
    st.header("إدارة المستخدمين")
    users = load_users()
    st.dataframe(users.reset_index(drop=True))
    st.markdown("---")
    # activate/deactivate
    user_list = users["username"].tolist()
    chosen = st.selectbox("اختر مستخدم", user_list)
    if chosen:
        idx = users[users["username"]==chosen].index[0]
        cur = users.at[idx,"active"]
        st.write(f"الحالة الحالية: {'مفعل' if bool(cur) else 'معطل'}")
        new_state = st.radio("إختر الحالة:", ("مفعل","معطل"), index=0 if bool(cur) else 1)
        if st.button("تطبيق الحالة"):
            users.at[idx,"active"] = True if new_state=="مفعل" else False
            save_users(users)
            st.success("تم حفظ التغيير.")
            st.experimental_rerun()
        st.markdown("### تغيير الصلاحية")
        new_role = st.selectbox("اختر صلاحية جديدة", ["رئيسي","مقيم","مشاهد فقط"])
        if st.button("تغيير الصلاحية"):
            users.at[idx,"role"] = new_role
            save_users(users)
            st.success("تم تغيير الصلاحية.")
            st.experimental_rerun()
    if st.button("رجوع"):
        st.session_state.page = "home"
        st.experimental_rerun()

# -------- Router / init ----------
ensure_files()
if "page" not in st.session_state:
    st.session_state.page = "login"
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None

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
    # restrict admin page
    if st.session_state.get("role") == "رئيسي":
        page_admin()
    else:
        st.error("هذه الصفحة متاحة للمستخدم الرئيسي فقط.")
        if st.button("رجوع"):
            st.session_state.page = "home"
            st.experimental_rerun()

# footer
st.markdown("<div style='font-size:10px; text-align:center; color:#666; margin-top:12px'>تصميم حسين العييري</div>", unsafe_allow_html=True)
    doc.build(story)
    return filename

# -------- واجهة تسجيل الدخول -------- #
def login_page():
    st.title("تسجيل الدخول")
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور", type="password")
    if st.button("تسجيل الدخول"):
        users = pd.read_csv(USERS_FILE, encoding="utf-8-sig")
        user = users[(users["username"] == username) & (users["password"] == password)]
        if not user.empty:
            st.session_state.logged_in = True
            st.session_state.page = "home"
            st.rerun()
        else:
            st.error("اسم المستخدم أو كلمة المرور غير صحيحة")

# -------- الصفحة الرئيسية -------- #
def home_page():
    st.title("📊 تقييم")
    now = datetime.now(TIMEZONE)
    st.write(f"📅 التاريخ: {now.strftime('%Y-%m-%d')}")
    st.write(f"⏰ الوقت: {now.strftime('%H:%M:%S')}")

    report_name = st.text_input("📝 اسم التقرير", key="report_name")
    if st.button("ابدأ التقييم"):
        if report_name.strip() == "":
            st.error("أدخل اسم التقرير أولاً")
        else:
            st.session_state.report_name = report_name
            st.session_state.start_time = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.errors = []
            st.session_state.page = "errors"
            st.rerun()

    if st.button("📑 السجل"):
        st.session_state.page = "reports"
        st.rerun()

# -------- صفحة الأخطاء -------- #
def errors_page():
    st.title("🚦 الأخطاء")
    st.write("اختر الأخطاء التي وقع فيها السائق:")

    cols = st.columns(3)
    for i, error in enumerate(ERRORS_LIST):
        if cols[i % 3].button(error):
            st.session_state.errors.append(error)

    notes = st.text_area("📝 ملاحظات إضافية", key="notes")

    if st.button("إنهاء التقييم"):
        end_time = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
        save_report(
            st.session_state.report_name,
            st.session_state.start_time,
            end_time,
            st.session_state.errors,
            notes
        )
        st.success("✅ تم حفظ التقرير")
        st.session_state.page = "home"
        st.rerun()

# -------- صفحة التقارير -------- #
def reports_page():
    st.title("📑 السجل")
    df = pd.read_csv(REPORTS_FILE, encoding="utf-8-sig")
    st.dataframe(df)

    report_names = df["اسم التقرير"].tolist()
    if len(report_names) > 0:
        selected = st.selectbox("اختر تقرير", report_names)

        col1, col2 = st.columns(2)
        if col1.button("📥 تنزيل PDF"):
            report = df[df["اسم التقرير"] == selected].iloc[0]
            filename = generate_pdf(report)
            with open(filename, "rb") as f:
                st.download_button("تحميل التقرير", f, file_name=filename)

        if col2.button("🗑️ حذف التقرير"):
            df = df[df["اسم التقرير"] != selected]
            df.to_csv(REPORTS_FILE, index=False, encoding="utf-8-sig")
            st.success("تم حذف التقرير")
            st.rerun()

    if st.button("🏠 رجوع"):
        st.session_state.page = "home"
        st.rerun()

# -------- Main -------- #
ensure_files_exist()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"

if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "errors":
        errors_page()
    elif st.session_state.page == "reports":
        reports_page()
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
