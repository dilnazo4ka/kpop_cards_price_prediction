import streamlit as st
from PIL import Image
from predictor import predict_price
import os
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"
st.set_page_config(page_title='K-pop Photocard Price Predictor')

st.title('K-pop Photocard Price Predictor')

uploaded_file = st.file_uploader("Upload photocard image", type=["jpg", "jpeg"])
title = st.text_input('Photocard title (in English)')
member = st.text_input('Member name (e.g. Anton)')
group = st.text_input('Group name (e.g. RIIZE)')

if st.button('Predict Price'):
    if uploaded_file and title and member and group:
        image = Image.open(uploaded_file).convert('RGB')
        price = predict_price(image, title, member, group)
        st.success(f'Predicted Price: {price:,.0f}')
    else:
        st.warning('Please fill in all fields and upload an image.')