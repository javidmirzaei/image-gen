import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import os
import traceback
import base64
from auth import init_auth, logout
import shutil
import glob
import json

# تابع کمکی برای شکستن متن به چند خط
def wrap_text_to_lines(draw, text, font, max_width):
    """
    متن را فقط بر اساس خطوط جدید (اینتر) جدا می‌کند
    و هیچ شکستن خط خودکاری انجام نمی‌دهد
    """
    # فقط متن را بر اساس خطوط جدید (اینتر) جدا می‌کنیم
    return text.split('\n')

# تنظیمات اولیه صفحه
st.set_page_config(
    page_title="تصویرساز فارسی",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنظیم مسیر فونت‌ها و تمپلیت‌ها
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Vazirmatn-Regular.ttf")
FONT_BOLD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Vazirmatn-Bold.ttf")
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# اطمینان از وجود پوشه تمپلیت‌ها
if not os.path.exists(TEMPLATES_DIR):
    os.makedirs(TEMPLATES_DIR)

# تبدیل مسیر فایل‌ها به URL
FONT_URL = f"data:font/ttf;base64,{base64.b64encode(open(FONT_PATH, 'rb').read()).decode()}"
FONT_BOLD_URL = f"data:font/ttf;base64,{base64.b64encode(open(FONT_BOLD_PATH, 'rb').read()).decode()}"

# تنظیمات استایل
st.markdown(f"""
    <style>
    @font-face {{
        font-family: 'Vazir';
        src: url('{FONT_URL}') format('truetype');
        font-weight: normal;
        font-style: normal;
    }}
    
    @font-face {{
        font-family: 'Vazir';
        src: url('{FONT_BOLD_URL}') format('truetype');
        font-weight: bold;
        font-style: normal;
    }}
    
    html, body, [class*="st-"] {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    input, button, textarea, select {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTextInput > div > div > input {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stButton > button {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stMarkdown {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stAlert {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSelectbox > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSlider > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stColorPicker > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stFileUploader > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSidebar [data-testid="stSidebar"] {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .layer-card {{
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    .layer-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }}
    
    .layer-title {{
        font-size: 1.2rem;
        font-weight: bold;
        color: #1a237e;
    }}
    
    .layer-controls {{
        display: flex;
        gap: 0.5rem;
    }}
    
    .layer-content {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }}
    
    .layer-preview {{
        width: 100%;
        height: 150px;
        object-fit: contain;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }}
    
    .layer-settings {{
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }}
    
    .add-layer-button {{
        width: 100%;
        padding: 1rem;
        background-color: #e3f2fd;
        border: 2px dashed #2196F3;
        border-radius: 10px;
        color: #1976D2;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    
    .add-layer-button:hover {{
        background-color: #bbdefb;
    }}
    
    .header-container {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }}
    
    .settings-button {{
        margin-left: 1rem;
    }}

    /* استایل مخصوص دکمه‌های انتخاب رنگ */
    .color-button > button {{
        position: relative;
        min-height: 60px;
        height: auto !important;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        align-items: center;
        padding: 5px 2px;
        text-align: center;
        color: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        overflow: hidden;
    }}

    .color-button > button::after {{
        content: attr(data-color-name);
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        color: #333;
        font-size: 0.7rem;
        padding: 2px;
        background-color: rgba(255, 255, 255, 0.7);
        border-bottom-left-radius: 4px;
        border-bottom-right-radius: 4px;
    }}

    .color-button > button::before {{
        content: "";
        position: absolute;
        top: 0;
        right: 0;
        bottom: 25px;
        left: 0;
        background-color: attr(data-color);
        border-radius: 4px;
        border: 1px solid #ccc;
    }}
    </style>
""", unsafe_allow_html=True)

# بررسی احراز هویت
if not init_auth():
    st.stop()

# مسیر فایل دیتابیس رنگ‌ها
COLORS_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "colors.json")

# اطمینان از وجود پوشه data
if not os.path.exists(os.path.dirname(COLORS_DB_PATH)):
    os.makedirs(os.path.dirname(COLORS_DB_PATH))

# تابع بارگذاری رنگ‌ها از فایل
def load_colors():
    if os.path.exists(COLORS_DB_PATH):
        try:
            with open(COLORS_DB_PATH, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"خطا در بارگذاری رنگ‌ها: {str(e)}")
    return []

# تابع ذخیره رنگ‌ها در فایل
def save_colors(colors):
    try:
        with open(COLORS_DB_PATH, 'w', encoding='utf-8') as file:
            json.dump(colors, file, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"خطا در ذخیره رنگ‌ها: {str(e)}")
        return False

# کلاس برای مدیریت لایه‌ها
class Layer:
    def __init__(self, name, image=None):
        self.name = name
        self.image = image
        self.x_percent = 50
        self.y_percent = 50
        self.size_percent = 30
        self.opacity = 100
        self.visible = True
        self.image_key = None  # کلید یکتا برای هر تصویر

# مدیریت لایه‌ها در session state
if 'layers' not in st.session_state:
    st.session_state.layers = []

# برای ذخیره نام تمپلیت انتخاب شده
if 'selected_template_name' not in st.session_state:
    st.session_state.selected_template_name = None

# برای ذخیره مسیر تمپلیت انتخاب شده
if 'selected_template_path' not in st.session_state:
    st.session_state.selected_template_path = None

# برای ذخیره تمپلیت آپلود شده
if 'template_file' not in st.session_state:
    st.session_state.template_file = None

# برای ذخیره متن
if 'text' not in st.session_state:
    st.session_state.text = ""

# برای ذخیره تنظیمات متن
if 'font_size_percent' not in st.session_state:
    st.session_state.font_size_percent = 5
if 'text_color' not in st.session_state:
    st.session_state.text_color = "#000000"
if 'is_bold' not in st.session_state:
    st.session_state.is_bold = False
if 'text_x_percent' not in st.session_state:
    st.session_state.text_x_percent = 50
if 'text_y_percent' not in st.session_state:
    st.session_state.text_y_percent = 98
if 'max_text_width_percent' not in st.session_state:
    st.session_state.max_text_width_percent = 80
if 'line_spacing_percent' not in st.session_state:
    st.session_state.line_spacing_percent = 120

# برای ذخیره وضعیت صفحه‌ای که کاربر در آن قرار دارد
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'main'  # صفحه اصلی به عنوان پیش‌فرض

# برای ذخیره رنگ‌های پیش‌فرض
if 'default_colors' not in st.session_state:
    st.session_state.default_colors = load_colors()

# برای ذخیره نام رنگ جدید
if 'new_color_name' not in st.session_state:
    st.session_state.new_color_name = ""

# برای ذخیره مقدار رنگ جدید
if 'new_color_value' not in st.session_state:
    st.session_state.new_color_value = "#000000"

# نمایش صفحه متناسب با وضعیت
if st.session_state.current_page == 'settings':
    # صفحه تنظیمات
    
    # ایجاد هدر با دکمه بازگشت
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("⚙️ تنظیمات")
    with col2:
        if st.button("🔙 بازگشت", key="header_back_button"):
            st.session_state.current_page = 'main'
            st.rerun()
    
    st.markdown("---")
    
    # بخش مدیریت تمپلیت‌ها
    st.markdown("### 📁 مدیریت تمپلیت‌ها")
    
    # نمایش تب‌های مدیریت تمپلیت
    template_tab1, template_tab2 = st.tabs(["📂 تمپلیت‌های موجود", "⬆️ آپلود تمپلیت جدید"])
    
    with template_tab1:
        # دریافت لیست تمپلیت‌های موجود
        template_files = glob.glob(os.path.join(TEMPLATES_DIR, "*.png")) + glob.glob(os.path.join(TEMPLATES_DIR, "*.jpg"))
        template_files.sort(key=os.path.getmtime, reverse=True)  # مرتب‌سازی بر اساس زمان ایجاد
        
        if template_files:
            # ساخت لیست نمایشی از تمپلیت‌ها
            template_names = [os.path.basename(f) for f in template_files]
            
            # نمایش لیست تمپلیت‌ها
            st.markdown("تمپلیت‌های ذخیره شده:")
            for i, template in enumerate(template_names):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{i+1}. {template}")
                with col2:
                    if st.button("🗑️", key=f"delete_{i}"):
                        try:
                            os.remove(os.path.join(TEMPLATES_DIR, template))
                            # اگر تمپلیت حذف شده با تمپلیت انتخاب شده یکسان است، انتخاب را پاک کن
                            if st.session_state.selected_template_name == template:
                                st.session_state.selected_template_name = None
                                st.session_state.selected_template_path = None
                            st.success(f"تمپلیت {template} با موفقیت حذف شد!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"خطا در حذف تمپلیت: {str(e)}")
        else:
            st.info("🔍 هنوز تمپلیتی ذخیره نشده است. لطفاً از تب آپلود، یک تمپلیت جدید اضافه کنید.")
    
    with template_tab2:
        template_file = st.file_uploader("تمپلیت جدید را انتخاب کنید", type=["png", "jpg", "jpeg"], help="یک تصویر تمپلیت با فرمت PNG یا JPEG آپلود کنید")
        template_name = st.text_input("نام تمپلیت (اختیاری)", help="اگر خالی بماند، از نام فایل استفاده می‌شود")
        
        if template_file:
            try:
                # نمایش پیش‌نمایش
                template_preview = Image.open(template_file)
                st.image(template_preview, caption="پیش‌نمایش تمپلیت جدید", width=300)
                
                # دکمه ذخیره تمپلیت
                if st.button("💾 ذخیره این تمپلیت"):
                    # تعیین نام فایل برای ذخیره
                    if template_name:
                        # اطمینان از داشتن پسوند مناسب
                        if not (template_name.endswith('.png') or template_name.endswith('.jpg') or template_name.endswith('.jpeg')):
                            template_name += '.' + template_file.name.split('.')[-1]
                    else:
                        template_name = template_file.name
                    
                    # مسیر ذخیره تمپلیت
                    save_path = os.path.join(TEMPLATES_DIR, template_name)
                    
                    # ذخیره فایل
                    with open(save_path, "wb") as f:
                        f.write(template_file.getbuffer())
                    
                    st.success(f"✅ تمپلیت با موفقیت ذخیره شد! ({template_name})")
                    st.info("تمپلیت جدید به لیست تمپلیت‌های موجود اضافه شد.")
            except Exception as e:
                st.error(f"خطا در بارگذاری تمپلیت: {str(e)}")
    
    # بخش جداکننده
    st.markdown("---")
    
    # بخش مدیریت رنگ‌های پیش‌فرض
    st.markdown("### 🎨 مدیریت رنگ‌های پیش‌فرض")
    
    # کارت رنگ‌های موجود
    with st.container():
        st.subheader("📋 رنگ‌های ذخیره شده")
        
        if st.session_state.default_colors:
            # تعداد ستون‌ها برای نمایش رنگ‌ها
            num_cols = 3
            color_rows = [st.session_state.default_colors[i:i+num_cols] for i in range(0, len(st.session_state.default_colors), num_cols)]
            
            for row_idx, row in enumerate(color_rows):
                cols = st.columns(num_cols)
                for col_idx, color_item in enumerate(row):
                    idx = row_idx * num_cols + col_idx
                    with cols[col_idx]:
                        # نمایش نام و مقدار رنگ
                        st.markdown(f"<div style='display: flex; align-items: center; margin-bottom: 10px;'>"
                                    f"<div style='width: 30px; height: 30px; background-color: {color_item['value']}; margin-right: 10px; border: 1px solid #ccc;'></div>"
                                    f"<span>{color_item['name']} ({color_item['value']})</span>"
                                    f"</div>", unsafe_allow_html=True)
                        
                        # دکمه حذف رنگ
                        if st.button("🗑️ حذف", key=f"delete_color_{idx}"):
                            st.session_state.default_colors.pop(idx)
                            
                            # ذخیره تغییرات در فایل دیتابیس
                            if save_colors(st.session_state.default_colors):
                                st.success(f"رنگ با موفقیت حذف شد!")
                            else:
                                st.error("خطا در ذخیره‌سازی تغییرات. تغییرات موقت اعمال شد.")
                            
                            st.rerun()
        else:
            st.info("🔍 هنوز رنگی ذخیره نشده است. لطفاً از فرم زیر، رنگ مورد نظر خود را اضافه کنید.")
    
    # کارت افزودن رنگ جدید
    with st.container():
        st.subheader("➕ افزودن رنگ جدید")
        
        # فرم افزودن رنگ جدید
        col1, col2 = st.columns(2)
        
        with col1:
            new_color_name = st.text_input("نام رنگ", value=st.session_state.new_color_name, key="new_color_name_input", 
                                          help="یک نام معنادار برای رنگ خود وارد کنید (مثلا: آبی آسمانی، قرمز لوگو، و...)")
            
            # بروزرسانی مقدار در session state
            if st.session_state.new_color_name != new_color_name:
                st.session_state.new_color_name = new_color_name
        
        with col2:
            new_color_value = st.color_picker("انتخاب رنگ", value=st.session_state.new_color_value, key="new_color_value_picker")
            
            # بروزرسانی مقدار در session state
            if st.session_state.new_color_value != new_color_value:
                st.session_state.new_color_value = new_color_value
        
        # نمایش پیش‌نمایش رنگ
        st.markdown(f"<div style='display: flex; align-items: center; margin: 15px 0;'>"
                   f"<div style='width: 50px; height: 30px; background-color: {new_color_value}; margin-right: 10px; border: 1px solid #ccc;'></div>"
                   f"<span>پیش‌نمایش رنگ انتخاب شده: {new_color_value}</span>"
                   f"</div>", unsafe_allow_html=True)
        
        # دکمه ذخیره رنگ
        if st.button("💾 ذخیره این رنگ"):
            if new_color_name.strip() == "":
                st.error("❌ لطفاً یک نام برای رنگ وارد کنید.")
            else:
                # بررسی تکراری نبودن نام
                existing_names = [color["name"] for color in st.session_state.default_colors]
                if new_color_name in existing_names:
                    st.warning(f"⚠️ رنگی با نام '{new_color_name}' قبلاً ذخیره شده است. لطفاً نام دیگری انتخاب کنید.")
                else:
                    # افزودن رنگ جدید به لیست
                    st.session_state.default_colors.append({
                        "name": new_color_name,
                        "value": new_color_value
                    })
                    
                    # ذخیره رنگ‌ها در فایل
                    if save_colors(st.session_state.default_colors):
                        # پاک کردن مقادیر فرم برای رنگ بعدی
                        st.session_state.new_color_name = ""
                        st.session_state.new_color_value = "#000000"
                        
                        st.success(f"✅ رنگ '{new_color_name}' با موفقیت ذخیره شد!")
                    else:
                        st.error("❌ خطا در ذخیره‌سازی رنگ. لطفاً دوباره تلاش کنید.")
                    
                    st.rerun()
    
    # فضای خالی برای تنظیمات بیشتر در آینده
    st.markdown("---")
    st.markdown("### تنظیمات بیشتر")
    # در اینجا می‌توانید تنظیمات بیشتری اضافه کنید

else:
    # صفحه اصلی
    # عنوان اصلی
    
    # ایجاد هدر با دکمه تنظیمات
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("🎨 تصویرساز فارسی")
    with col2:
        if st.button("⚙️ تنظیمات", key="header_settings_button"):
            st.session_state.current_page = 'settings'
            st.rerun()
    
    st.markdown("---")
    
    # سایدبار
    with st.sidebar:
        # تب‌های سایدبار
        tab1, tab2 = st.tabs(["📝 راهنما", "👁️ پیش‌نمایش"])
        
        with tab1:
            st.header("راهنمای استفاده")
            st.markdown("""
            ### نحوه استفاده:
            1. یک تمپلیت آپلود یا انتخاب کنید
            2. لایه‌های مورد نظر را اضافه کنید
            3. برای هر لایه:
               - تصویر را آپلود کنید
               - موقعیت و اندازه را تنظیم کنید
               - شفافیت را تنظیم کنید
            4. متن فارسی را وارد کنید
            5. دکمه ساخت تصویر را بزنید
            
            ### نکات مهم:
            - از فونت وزیر برای نمایش متن فارسی استفاده می‌شود
            - می‌توانید ترتیب لایه‌ها را تغییر دهید
            - هر لایه را می‌توانید فعال یا غیرفعال کنید
            - تصویر نهایی در فایل output.png ذخیره می‌شود
            """)
        
        with tab2:
            st.header("پیش‌نمایش")
            # بررسی وجود تمپلیت (از فایل آپلود شده یا انتخاب شده)
            template_path = None
            if st.session_state.selected_template_path:
                template_path = st.session_state.selected_template_path
            
            if template_path and (st.session_state.layers or st.session_state.text):
                try:
                    # باز کردن تمپلیت
                    template = Image.open(template_path)
                    
                    # محاسبه ابعاد تصویر
                    template_width, template_height = template.size
                    min_dimension = min(template_width, template_height)
                    
                    # ایجاد یک تصویر پایه خالی (سفید)
                    preview_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 255))
                    draw = ImageDraw.Draw(preview_image)
                    
                    # اضافه کردن لایه‌ها به زمینه سفید
                    for layer in st.session_state.layers:
                        if layer.visible and layer.image:
                            # محاسبه سایز تصویر بر اساس درصد کوچکترین بعد تمپلیت
                            # مقادیر بزرگتر از 100% باعث می‌شود تصویر بزرگتر از حالت اصلی شود
                            max_dimension = int(min_dimension * (layer.size_percent / 100))
                            
                            # تغییر سایز تصویر لایه با حفظ نسبت تصویر
                            original_width, original_height = layer.image.size
                            aspect_ratio = original_width / original_height
                            
                            if aspect_ratio >= 1:  # عرض بزرگتر یا مساوی ارتفاع است
                                new_width = max_dimension
                                new_height = int(max_dimension / aspect_ratio)
                            else:  # ارتفاع بزرگتر از عرض است
                                new_height = max_dimension
                                new_width = int(max_dimension * aspect_ratio)
                            
                            # حتی اگر مقیاس بزرگتر از 100% باشد، تغییر سایز انجام می‌شود (بزرگنمایی)
                            layer_image = layer.image.resize((new_width, new_height), Image.LANCZOS)
                            
                            # تبدیل به RGBA اگر PNG است
                            if layer_image.mode != 'RGBA':
                                layer_image = layer_image.convert('RGBA')
                            
                            # اعمال شفافیت
                            if layer.opacity < 100:
                                layer_image.putalpha(int(255 * layer.opacity / 100))
                            
                            # محاسبه موقعیت مرکز تصویر
                            img_x = int((template_width - new_width) * (layer.x_percent / 100))
                            img_y = int((template_height - new_height) * (layer.y_percent / 100))
                            
                            # اضافه کردن تصویر به پیش‌نمایش
                            preview_image.paste(layer_image, (img_x, img_y), layer_image)
                    
                    # اضافه کردن تمپلیت به عنوان لایه بالایی (بالاتر از لایه‌های تصویر)
                    if template.mode == 'RGBA':
                        # اگر تمپلیت شفافیت داشته باشد، با حفظ شفافیت روی تصویر قرار می‌گیرد
                        preview_image = Image.alpha_composite(preview_image, template)
                    else:
                        # تبدیل تمپلیت به RGBA
                        template_rgba = template.convert('RGBA')
                        preview_image = Image.alpha_composite(preview_image, template_rgba)
                    
                    # اضافه کردن متن به عنوان بالاترین لایه (روی همه چیز، حتی تمپلیت)
                    if st.session_state.text:
                        # آماده‌سازی متن فارسی
                        reshaped_text = arabic_reshaper.reshape(st.session_state.text)
                        bidi_text = get_display(reshaped_text)
                        
                        # محاسبه سایز فونت بر اساس درصد ارتفاع
                        font_size = int(template_height * (st.session_state.font_size_percent / 100))
                        
                        try:
                            # انتخاب فونت مناسب بر اساس وضعیت بولد
                            font_path = FONT_BOLD_PATH if st.session_state.is_bold else FONT_PATH
                            font = ImageFont.truetype(font_path, font_size)
                            
                            # ایجاد یک تصویر شفاف برای متن
                            text_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 0))
                            text_draw = ImageDraw.Draw(text_image)
                            
                            # محاسبه حداکثر عرض متن
                            max_width = template_width * (st.session_state.max_text_width_percent / 100)
                            
                            # شکستن متن به خطوط
                            lines = wrap_text_to_lines(text_draw, bidi_text, font, max_width)
                            
                            # محاسبه ارتفاع کل متن
                            # فاصله بین خطوط را به درصدی از ارتفاع فونت تنظیم می‌کنیم
                            line_spacing_factor = st.session_state.line_spacing_percent / 100
                            line_height = int(font_size * line_spacing_factor)
                            total_text_height = line_height * len(lines)
                            
                            # محاسبه موقعیت شروع متن - نسبت به ابعاد تمپلیت
                            # برای موقعیت افقی (x): 0% یعنی چپ، 50% یعنی وسط و 100% یعنی راست تمپلیت
                            # برای موقعیت عمودی (y): 0% یعنی بالا، 50% یعنی وسط و 100% یعنی پایین تمپلیت
                            start_y = int((template_height - total_text_height) * (st.session_state.text_y_percent / 100))
                            
                            # رسم هر خط متن روی تصویر شفاف
                            for i, line in enumerate(lines):
                                line_width = text_draw.textlength(line, font=font)
                                # محاسبه موقعیت افقی متن نسبت به عرض تمپلیت
                                line_x = int((template_width - line_width) * (st.session_state.text_x_percent / 100))
                                line_y = start_y + i * line_height
                                text_draw.text((line_x, line_y), line, font=font, fill=st.session_state.text_color)
                            
                            # ترکیب تصویر متن با تصویر اصلی
                            preview_image = Image.alpha_composite(preview_image, text_image)
                        except Exception as e:
                            st.error(f"خطا در بارگذاری فونت: {str(e)}")
                            # استفاده از فونت پیش‌فرض در صورت خطا
                            font = ImageFont.load_default()
                            st.warning("از فونت پیش‌فرض استفاده شد. متن چندخطی با این فونت پشتیبانی نمی‌شود.")
                            draw.text((10, 10), bidi_text, font=font, fill=st.session_state.text_color)
                    
                    # نمایش تصویر با سایز محدود شده
                    st.image(preview_image, caption=f"پیش‌نمایش ({template_width}x{template_height})", use_column_width=True)
                    
                    # ذخیره تصویر با سایز اصلی
                    final_image = preview_image.copy()
                    final_image.save("output.png", quality=100)
                    
                    # ایجاد دکمه دانلود
                    with open("output.png", "rb") as file:
                        btn = st.download_button(
                            label="⬇️ دانلود تصویر",
                            data=file,
                            file_name="output.png",
                            mime="image/png",
                            key="sidebar_download_btn"
                        )
                    
                    st.success(f"✅ تصویر با موفقیت ساخته شد! (سایز: {template_width}x{template_height})")
                    
                except Exception as e:
                    st.error(f"❌ خطا در ساخت تصویر: {str(e)}")
                    st.error("جزئیات خطا:")
                    st.code(traceback.format_exc())
            else:
                st.info("👆 برای مشاهده پیش‌نمایش، ابتدا یک تمپلیت انتخاب کنید و حداقل یک لایه یا متن اضافه کنید.")
        
        # نمایش اطلاعات کاربر و دکمه خروج
        st.markdown("---")
        st.markdown(f"👤 کاربر: {st.session_state.username}")
        if st.button("🚪 خروج"):
            logout()
    
    # آپلود و مدیریت تمپلیت
    st.markdown('<p class="upload-header">1️⃣ انتخاب تمپلیت</p>', unsafe_allow_html=True)
    
    # دریافت لیست تمپلیت‌های موجود
    template_files = glob.glob(os.path.join(TEMPLATES_DIR, "*.png")) + glob.glob(os.path.join(TEMPLATES_DIR, "*.jpg"))
    template_files.sort(key=os.path.getmtime, reverse=True)  # مرتب‌سازی بر اساس زمان ایجاد
    
    if template_files:
        # ساخت لیست نمایشی از تمپلیت‌ها
        template_names = [os.path.basename(f) for f in template_files]
        template_options = ["انتخاب کنید..."] + template_names
        
        # انتخاب تمپلیت
        selected_template = st.selectbox(
            "تمپلیت موردنظر را انتخاب کنید",
            template_options,
            index=0,
            help="یک تمپلیت از لیست انتخاب کنید یا از بخش 'تنظیمات' تمپلیت جدید اضافه کنید"
        )
        
        if selected_template != "انتخاب کنید...":
            selected_template_path = os.path.join(TEMPLATES_DIR, selected_template)
            
            # ذخیره انتخاب کاربر
            st.session_state.selected_template_name = selected_template
            st.session_state.selected_template_path = selected_template_path
            
            # نمایش پیش‌نمایش تمپلیت
            try:
                template_preview = Image.open(selected_template_path)
                st.image(template_preview, caption=f"پیش‌نمایش تمپلیت: {selected_template}", width=300)
                st.success(f"✅ تمپلیت '{selected_template}' انتخاب شد. حالا می‌توانید لایه‌ها و متن را اضافه کنید.")
            except Exception as e:
                st.error(f"خطا در بارگذاری تمپلیت: {str(e)}")
    else:
        st.info("🔍 هنوز تمپلیتی ذخیره نشده است. لطفاً از بخش 'تنظیمات'، تمپلیت جدید اضافه کنید.")
        # دکمه رفتن به بخش تنظیمات
        if st.button("رفتن به بخش تنظیمات"):
            st.session_state.current_page = 'settings'
            st.rerun()
    
    # بررسی وضعیت انتخاب تمپلیت برای نمایش بخش‌های بعدی
    if st.session_state.selected_template_path:
        # نمایش بخش مدیریت لایه‌ها
        st.markdown('<p class="upload-header">2️⃣ مدیریت لایه‌ها</p>', unsafe_allow_html=True)
        
        # دکمه افزودن لایه جدید
        if st.button("➕ افزودن لایه جدید"):
            new_layer = Layer(f"لایه {len(st.session_state.layers) + 1}")
            st.session_state.layers.append(new_layer)
            st.rerun()
        
        # نمایش لایه‌ها
        for i, layer in enumerate(st.session_state.layers):
            with st.container():
                st.markdown(f"### 🖼️ {layer.name}")
                
                # آپلود تصویر برای لایه
                uploaded_file = st.file_uploader(
                    "تصویر را انتخاب کنید",
                    type=["png", "jpg", "jpeg"],
                    key=f"layer_{i}_upload",
                    help="تصویری که می‌خواهید در این لایه قرار دهید را آپلود کنید"
                )
                
                if uploaded_file:
                    try:
                        # ایجاد کلید یکتا برای تصویر
                        if layer.image_key != uploaded_file.name:
                            layer.image_key = uploaded_file.name
                            layer.image = Image.open(uploaded_file)
                            st.rerun()  # بروزرسانی صفحه برای نمایش تصویر جدید
                        
                        st.image(layer.image, caption="پیش‌نمایش تصویر", width=200)
                    except Exception as e:
                        st.error(f"خطا در بارگذاری تصویر: {str(e)}")
                
                # تنظیمات لایه
                col1, col2 = st.columns(2)
                with col1:
                    new_x = st.slider(
                        "موقعیت افقی (%)",
                        0, 100, layer.x_percent,
                        key=f"layer_{i}_x",
                        help="0: چپ، 50: وسط، 100: راست"
                    )
                    new_size = st.slider(
                        "اندازه (%)",
                        10, 300, layer.size_percent,
                        key=f"layer_{i}_size",
                        help="سایز تصویر به صورت درصدی از کوچکترین بعد تمپلیت (مقادیر بزرگتر از 100% تصویر را بزرگتر از حالت اصلی نمایش می‌دهند)"
                    )
                    
                    # بروزرسانی مقادیر و رفرش صفحه
                    if new_x != layer.x_percent or new_size != layer.size_percent:
                        layer.x_percent = new_x
                        layer.size_percent = new_size
                        st.rerun()
                
                with col2:
                    new_y = st.slider(
                        "موقعیت عمودی (%)",
                        0, 100, layer.y_percent,
                        key=f"layer_{i}_y",
                        help="0: بالا، 50: وسط، 100: پایین"
                    )
                    new_opacity = st.slider(
                        "شفافیت (%)",
                        0, 100, layer.opacity,
                        key=f"layer_{i}_opacity",
                        help="شفافیت تصویر (0: کاملاً شفاف، 100: کاملاً مات)"
                    )
                    
                    # بروزرسانی مقادیر و رفرش صفحه
                    if new_y != layer.y_percent or new_opacity != layer.opacity:
                        layer.y_percent = new_y
                        layer.opacity = new_opacity
                        st.rerun()
                
                # کنترل‌های لایه
                col1, col2 = st.columns(2)
                with col1:
                    new_visible = st.checkbox(
                        "نمایش لایه",
                        value=layer.visible,
                        key=f"layer_{i}_visible"
                    )
                    
                    # بروزرسانی وضعیت نمایش و رفرش صفحه
                    if new_visible != layer.visible:
                        layer.visible = new_visible
                        st.rerun()
                    
                with col2:
                    if st.button("🗑️ حذف لایه", key=f"layer_{i}_delete"):
                        st.session_state.layers.pop(i)
                        st.rerun()
                
                st.markdown("---")

        # ورود متن
        st.markdown('<p class="upload-header">3️⃣ وارد کردن متن</p>', unsafe_allow_html=True)
        text_input = st.text_area("متن مورد نظر را وارد کنید", value=st.session_state.text, height=150, key="text_input", help="متن فارسی که می‌خواهید روی تصویر قرار دهید را وارد کنید. هر خط جدید در تصویر نیز به عنوان خط جدید نمایش داده می‌شود.")

        # ذخیره متن در session state
        if 'text_input' in st.session_state and st.session_state.text_input != st.session_state.text:
            st.session_state.text = st.session_state.text_input
            st.rerun()
        
        # تنظیمات متن
        st.markdown('<p class="settings-header">⚙️ تنظیمات متن</p>', unsafe_allow_html=True)
        text_col1, text_col2 = st.columns(2)

        with text_col1:
            font_size = st.slider("سایز فونت (% ارتفاع تصویر)", 1, 20, st.session_state.font_size_percent, key="font_size_slider", help="سایز فونت به صورت درصدی از ارتفاع تصویر", on_change=lambda: st.session_state.update({"font_size_percent": st.session_state.font_size_slider}))
            
            # بخش انتخاب رنگ متن با قابلیت استفاده از رنگ‌های ذخیره شده
            st.markdown("#### رنگ متن")
            
            # نمایش رنگ فعلی
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="width: 30px; height: 30px; background-color: {st.session_state.text_color}; border: 1px solid #ccc; margin-right: 10px; border-radius: 4px;"></div>
                <span>رنگ فعلی: {st.session_state.text_color}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # انتخاب رنگ سفارشی
            st.markdown("##### انتخاب رنگ سفارشی:")
            text_color = st.color_picker("", st.session_state.text_color, key="text_color_picker", help="رنگ متن را انتخاب کنید")
            if 'text_color_picker' in st.session_state and st.session_state.text_color_picker != st.session_state.text_color:
                st.session_state.text_color = st.session_state.text_color_picker
            
            # نمایش رنگ‌های ذخیره شده
            if st.session_state.default_colors:
                st.markdown("##### انتخاب از رنگ‌های ذخیره شده:")
                
                # تعریف تعداد ستون‌ها - افزایش تعداد ستون‌ها برای نمایش فشرده‌تر
                colors_per_row = 6
                
                # ساخت HTML برای نمایش رنگ‌ها
                for i in range(0, len(st.session_state.default_colors), colors_per_row):
                    cols = st.columns(colors_per_row)
                    for j in range(colors_per_row):
                        idx = i + j
                        if idx < len(st.session_state.default_colors):
                            color = st.session_state.default_colors[idx]
                            with cols[j]:
                                # ایجاد یک دکمه که ظاهر آن به صورت مربع رنگی است
                                # افزودن کلاس CSS برای استایل دهی مناسب
                                st_key = f"color_btn_{idx}"
                                
                                # استفاده از HTML مستقیم برای نمایش رنگ
                                st.markdown(f"""
                                <div style="width: 100%; position: relative; margin-bottom: 5px;">
                                    <div style="width: 100%; height: 30px; background-color: {color['value']}; 
                                         border: {('2px solid black' if color['value'] == st.session_state.text_color else '1px solid #ccc')}; 
                                         border-radius: 4px;"></div>
                                    <div style="font-size: 0.8em; margin-top: 2px; text-align: center;">{color['name']}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # دکمه نامرئی که روی رنگ قرار می‌گیرد
                                if st.button("انتخاب", key=st_key, help=f"انتخاب رنگ {color['name']}", use_container_width=True):
                                    st.session_state.text_color = color['value']
                                    st.rerun()
                                
                                # CSS برای پوشاندن دکمه روی رنگ
                                st.markdown(f"""
                                <style>
                                button[data-testid="button-{st_key}"] {{
                                    position: absolute;
                                    top: 0;
                                    left: 0;
                                    width: 100%;
                                    height: calc(100% - 20px);
                                    opacity: 0;
                                    margin-top: -50px;
                                }}
                                </style>
                                """, unsafe_allow_html=True)
            else:
                st.info("هنوز رنگی ذخیره نشده است. از بخش تنظیمات، رنگ‌های مورد نظر خود را اضافه کنید.")
            
            is_bold = st.checkbox("متن بولد", value=st.session_state.is_bold, key="is_bold_checkbox", help="نمایش متن به صورت بولد")
            if 'is_bold_checkbox' in st.session_state and st.session_state.is_bold_checkbox != st.session_state.is_bold:
                st.session_state.is_bold = st.session_state.is_bold_checkbox

        with text_col2:
            text_x = st.slider("موقعیت افقی متن (%)", 0, 100, st.session_state.text_x_percent, key="text_x_slider", help="0: کاملاً چپ تمپلیت، 50: وسط تمپلیت، 100: کاملاً راست تمپلیت", on_change=lambda: st.session_state.update({"text_x_percent": st.session_state.text_x_slider}))
            text_y = st.slider("موقعیت عمودی متن (%)", 0, 100, st.session_state.text_y_percent, key="text_y_slider", help="0: کاملاً بالای تمپلیت، 50: وسط تمپلیت، 100: کاملاً پایین تمپلیت", on_change=lambda: st.session_state.update({"text_y_percent": st.session_state.text_y_slider}))
            max_text_width = st.slider("عرض متن (%)", 10, 100, st.session_state.max_text_width_percent, key="max_text_width_slider", help="حداکثر عرض متن به صورت درصدی از عرض تمپلیت", on_change=lambda: st.session_state.update({"max_text_width_percent": st.session_state.max_text_width_slider}))
            line_spacing = st.slider("فاصله خطوط (%)", 100, 200, st.session_state.line_spacing_percent, key="line_spacing_slider", help="فاصله بین خطوط متن به صورت درصدی از ارتفاع خط", on_change=lambda: st.session_state.update({"line_spacing_percent": st.session_state.line_spacing_slider}))

        # دکمه ساخت تصویر
        st.markdown("---")
        if st.button("🎨 ساخت تصویر"):
            # بررسی وجود تمپلیت (از فایل آپلود شده یا انتخاب شده)
            template_path = None
            if st.session_state.template_file:
                template_path = st.session_state.template_file
            elif st.session_state.selected_template_path:
                template_path = st.session_state.selected_template_path
            
            if template_path and (st.session_state.layers or st.session_state.text):
                try:
                    # باز کردن تمپلیت
                    template = Image.open(template_path)
                    
                    # محاسبه ابعاد تصویر
                    template_width, template_height = template.size
                    min_dimension = min(template_width, template_height)
                    
                    # ایجاد یک تصویر پایه خالی (سفید)
                    preview_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 255))
                    draw = ImageDraw.Draw(preview_image)
                    
                    # اضافه کردن لایه‌ها به زمینه سفید
                    for layer in st.session_state.layers:
                        if layer.visible and layer.image:
                            # محاسبه سایز تصویر بر اساس درصد کوچکترین بعد تمپلیت
                            # مقادیر بزرگتر از 100% باعث می‌شود تصویر بزرگتر از حالت اصلی شود
                            max_dimension = int(min_dimension * (layer.size_percent / 100))
                            
                            # تغییر سایز تصویر لایه با حفظ نسبت تصویر
                            original_width, original_height = layer.image.size
                            aspect_ratio = original_width / original_height
                            
                            if aspect_ratio >= 1:  # عرض بزرگتر یا مساوی ارتفاع است
                                new_width = max_dimension
                                new_height = int(max_dimension / aspect_ratio)
                            else:  # ارتفاع بزرگتر از عرض است
                                new_height = max_dimension
                                new_width = int(max_dimension * aspect_ratio)
                            
                            # حتی اگر مقیاس بزرگتر از 100% باشد، تغییر سایز انجام می‌شود (بزرگنمایی)
                            layer_image = layer.image.resize((new_width, new_height), Image.LANCZOS)
                            
                            # تبدیل به RGBA اگر PNG است
                            if layer_image.mode != 'RGBA':
                                layer_image = layer_image.convert('RGBA')
                            
                            # اعمال شفافیت
                            if layer.opacity < 100:
                                layer_image.putalpha(int(255 * layer.opacity / 100))
                            
                            # محاسبه موقعیت مرکز تصویر
                            img_x = int((template_width - new_width) * (layer.x_percent / 100))
                            img_y = int((template_height - new_height) * (layer.y_percent / 100))
                            
                            # اضافه کردن تصویر به پیش‌نمایش
                            preview_image.paste(layer_image, (img_x, img_y), layer_image)
                    
                    # اضافه کردن تمپلیت به عنوان لایه بالایی (بالاتر از لایه‌های تصویر)
                    if template.mode == 'RGBA':
                        # اگر تمپلیت شفافیت داشته باشد، با حفظ شفافیت روی تصویر قرار می‌گیرد
                        preview_image = Image.alpha_composite(preview_image, template)
                    else:
                        # تبدیل تمپلیت به RGBA
                        template_rgba = template.convert('RGBA')
                        preview_image = Image.alpha_composite(preview_image, template_rgba)
                    
                    # اضافه کردن متن به عنوان بالاترین لایه (روی همه چیز، حتی تمپلیت)
                    if st.session_state.text:
                        # آماده‌سازی متن فارسی
                        reshaped_text = arabic_reshaper.reshape(st.session_state.text)
                        bidi_text = get_display(reshaped_text)
                        
                        # محاسبه سایز فونت بر اساس درصد ارتفاع
                        font_size = int(template_height * (st.session_state.font_size_percent / 100))
                        
                        try:
                            # انتخاب فونت مناسب بر اساس وضعیت بولد
                            font_path = FONT_BOLD_PATH if st.session_state.is_bold else FONT_PATH
                            font = ImageFont.truetype(font_path, font_size)
                            
                            # ایجاد یک تصویر شفاف برای متن
                            text_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 0))
                            text_draw = ImageDraw.Draw(text_image)
                            
                            # محاسبه حداکثر عرض متن
                            max_width = template_width * (st.session_state.max_text_width_percent / 100)
                            
                            # شکستن متن به خطوط
                            lines = wrap_text_to_lines(text_draw, bidi_text, font, max_width)
                            
                            # محاسبه ارتفاع کل متن
                            # فاصله بین خطوط را به درصدی از ارتفاع فونت تنظیم می‌کنیم
                            line_spacing_factor = st.session_state.line_spacing_percent / 100
                            line_height = int(font_size * line_spacing_factor)
                            total_text_height = line_height * len(lines)
                            
                            # محاسبه موقعیت شروع متن - نسبت به ابعاد تمپلیت
                            # برای موقعیت افقی (x): 0% یعنی چپ، 50% یعنی وسط و 100% یعنی راست تمپلیت
                            # برای موقعیت عمودی (y): 0% یعنی بالا، 50% یعنی وسط و 100% یعنی پایین تمپلیت
                            start_y = int((template_height - total_text_height) * (st.session_state.text_y_percent / 100))
                            
                            # رسم هر خط متن روی تصویر شفاف
                            for i, line in enumerate(lines):
                                line_width = text_draw.textlength(line, font=font)
                                # محاسبه موقعیت افقی متن نسبت به عرض تمپلیت
                                line_x = int((template_width - line_width) * (st.session_state.text_x_percent / 100))
                                line_y = start_y + i * line_height
                                text_draw.text((line_x, line_y), line, font=font, fill=st.session_state.text_color)
                            
                            # ترکیب تصویر متن با تصویر اصلی
                            preview_image = Image.alpha_composite(preview_image, text_image)
                        except Exception as e:
                            st.error(f"خطا در بارگذاری فونت: {str(e)}")
                            # استفاده از فونت پیش‌فرض در صورت خطا
                            font = ImageFont.load_default()
                            st.warning("از فونت پیش‌فرض استفاده شد. متن چندخطی با این فونت پشتیبانی نمی‌شود.")
                            draw.text((10, 10), bidi_text, font=font, fill=st.session_state.text_color)
                    
                    # نمایش تصویر با سایز محدود شده
                    st.image(preview_image, caption=f"پیش‌نمایش ({template_width}x{template_height})", width=300)
                    
                    # ذخیره تصویر با سایز اصلی
                    final_image = preview_image.copy()
                    final_image.save("output.png", quality=100)
                    
                    # ایجاد دکمه دانلود
                    with open("output.png", "rb") as file:
                        btn = st.download_button(
                            label="⬇️ دانلود تصویر",
                            data=file,
                            file_name="output.png",
                            mime="image/png",
                            key="main_download_btn"
                        )
                    
                    st.success(f"✅ تصویر با موفقیت ساخته شد! (سایز: {template_width}x{template_height})")
                    
                except Exception as e:
                    st.error(f"❌ خطا در ساخت تصویر: {str(e)}")
                    st.error("جزئیات خطا:")
                    st.code(traceback.format_exc())
            else:
                st.error("❌ لطفاً ابتدا یک تمپلیت انتخاب کنید و حداقل یک لایه یا متن وارد کنید!")
        else:
            st.warning("⚠️ لطفاً ابتدا یک تمپلیت انتخاب کنید یا یک تمپلیت جدید آپلود کنید.") 