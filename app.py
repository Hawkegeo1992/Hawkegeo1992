
import ee
import geemap
import streamlit as st

# 📌 احراز هویت GEE
try:
    ee.Initialize()
except:
    ee.Authenticate()
    ee.Initialize()

# 📌 عنوان اپلیکیشن
st.title("🌍 اپلیکیشن شاخص‌های پوشش گیاهی با GEE")

# 📌 بارگذاری مرزهای شهرستان‌های ایران
admin_boundaries = ee.FeatureCollection("FAO/GAUL/2015/level2")
khuzestan_boundaries = admin_boundaries.filter(ee.Filter.eq('ADM1_NAME', 'Khuzestan'))

# 📌 لیست شهرستان‌ها
district_names = khuzestan_boundaries.aggregate_array('ADM2_NAME').distinct().getInfo()

# 📌 ویجت‌های انتخابی
district = st.selectbox("📍 شهرستان:", district_names)
year = st.selectbox("📆 سال:", [str(y) for y in range(2015, 2026)])
month = st.selectbox("📅 ماه:", [str(m) for m in range(1, 13)])
period = st.selectbox("📆 بازه ۱۵ روزه:", ['1-15', '16-30'])
index = st.selectbox("📊 شاخص:", ['NDVI', 'SAVI', 'MNDWI', 'RGB'])

# 📌 بارگذاری داده‌ها
if st.button("🔍 بارگذاری داده‌ها"):
    selected_district = khuzestan_boundaries.filter(ee.Filter.eq('ADM2_NAME', district))
    start_day = 1 if period == '1-15' else 16
    end_day = 15 if period == '1-15' else 30

    start_date = ee.Date.fromYMD(int(year), int(month), start_day)
    end_date = ee.Date.fromYMD(int(year), int(month), end_day)

    collection = (ee.ImageCollection("COPERNICUS/S2")
                  .filterBounds(selected_district)
                  .filterDate(start_date, end_date)
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
                  .median())

    image_count = collection.bandNames().size().getInfo()
    if image_count == 0:
        st.error("❌ هیچ تصویری در این بازه زمانی یافت نشد.")
    else:
        st.success(f"📡 تعداد باندهای موجود: {image_count}")
        index_image = collection.normalizedDifference(['B8', 'B4']).rename(index) if index == 'NDVI' else collection

        # نمایش نقشه
        Map = geemap.Map()
        Map.centerObject(selected_district, 9)
        Map.addLayer(selected_district, {'color': 'red'}, 'Selected District')
        Map.addLayer(index_image, {'min': -1, 'max': 1, 'palette': ['blue', 'white', 'green']}, index)
        Map.to_streamlit()

# 📌 دکمه دانلود تصویر
if st.button("📥 دانلود تصویر"):
    task = ee.batch.Export.image.toDrive(
        image=index_image,
        description=f"{index}_{year}_{month}_{period}",
        folder="GEE_Exports",
        scale=10,
        region=selected_district.geometry().bounds(),
        fileFormat='GeoTIFF'
    )
    task.start()
    st.success("✅ تصویر در Google Drive ذخیره شد!")
