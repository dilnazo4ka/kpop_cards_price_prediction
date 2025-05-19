# K-pop Photocard Price Prediction

This project predicts the price of K-pop photocards using both image and text features (title, member, group). It uses CLIP embeddings and a regression head to estimate the photocard value.

---

##  Dataset

The dataset includes:

- Photocard images
- Metadata (title, member, group)
- Actual prices

📂 Available on Kaggle:  
[ K-pop Dataset on Kaggle](https://www.kaggle.com/datasets/dilnazimanbaeva/kpop-dataset/data)

---

##  Data Collection Scripts

These scripts help with collecting and preparing data for training:

| Script | Description |
|--------|-------------|
| `merc_price.py` | Scrapes photocard listings and prices from Mercari Japan |
| `mercari_csv_with_images_merging.py` | Merges CSV metadata with corresponding image paths |
| `translate.py` | Translates Japanese photocard titles and names into English |

---

##  Training & Modeling

The model combines CLIP visual and text embeddings for:

- Photocard image
- Title
- Member name
- Group name

Then, a regression model predicts the price.

Example notebook:  
[🔗 K-pop Price Prediction - Kaggle Notebook](https://www.kaggle.com/code/dilnazimanbaeva/kpop-price-prediciton)
[🔗 K-pop Price Prediction EDA - Kaggle Notebook](https://www.kaggle.com/code/dilnazimanbaeva/kpop-eda)
---

##  Inference 
A Streamlit app for price prediction is available in the `docker/` folder
```bash
# Build the Docker image
docker buildx build --platform=linux/arm64 -t clip-streamlit-app --load .

# Run the app
docker run --platform=linux/arm64 -p 8501:8501 clip-streamlit-app
---

##  Tech Stack

- Python
- PyTorch
- OpenCLIP
- Selenium
- CLIPTokenizer
- Docker (for deployment)

---

## Author
Dilnaz Imanbayeva
Kaggle: [@dilnazimanbaeva](https://www.kaggle.com/dilnazimanbaeva)
