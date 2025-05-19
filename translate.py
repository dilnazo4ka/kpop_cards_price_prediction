import os
import hashlib
import unicodedata
import pandas as pd
import json
from sklearn.preprocessing import StandardScaler
from multiprocessing import Pool, Manager
from deep_translator import GoogleTranslator
CACHE_DIR = 'cache_translation'
os.makedirs(CACHE_DIR, exist_ok=True)

translation_cache_path = os.path.join(CACHE_DIR, 'translation_cache.json')

def clean_path(path):
    path = unicodedata.normalize('NFD', path)
    return path.replace('@webp', '')

def hash_string(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()

translation_cache = None

def init_worker(shared_cache):
    global translation_cache
    translation_cache = shared_cache

def translate_text(text):
    global translation_cache
    text = str(text).strip()
    key = hash_string(text)
    if key in translation_cache:
        return translation_cache[key]
    if not text:
        return None
    try:
        translated = GoogleTranslator(source='ja', target='en').translate(text)
        translation_cache[key] = translated
        return translated
    except Exception as e:
        print(f'Translation failed for "{text}": {e}')
        return None

def save_translation_cache(shared_cache):
    with open(translation_cache_path, 'w', encoding='utf-8') as f:
        json.dump(dict(shared_cache), f, ensure_ascii=False, indent=2)

def load_all_csv(csv_dir):
    dfs = []
    for file in os.listdir(csv_dir):
        if file.endswith('.csv'):
            df = pd.read_csv(os.path.join(csv_dir, file))
            dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    df = df.drop_duplicates(subset='product_url', keep='first')
#    df['price'] = df['price'].str.replace(',', '').astype(float)
    df['image_path'] = df['image_path'].apply(clean_path)
    df = df[df['image_path'].apply(os.path.exists)]

    print('Start translation')

    with Manager() as manager:
        shared_cache = manager.dict()
        if os.path.exists(translation_cache_path):
            with open(translation_cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            for k, v in cached.items():
                shared_cache[k] = v

        titles = df['title'].tolist()

        with Pool(initializer=init_worker, initargs=(shared_cache,)) as pool:
            translated_titles = []
            for i, translated in enumerate(pool.imap(translate_text, titles), 1):
                translated_titles.append(translated)
                if i % 100 == 0:
                    print(f'Translated {i} titles')
                    save_translation_cache(shared_cache)
            save_translation_cache(shared_cache)

    df['translated_title'] = translated_titles
    df = df[['translated_title', 'price', 'image_path']].dropna()

    return df.reset_index(drop=True)


if __name__ == "__main__":
    csv_dir = 'mercari_new_csv'
    df_translated = load_all_csv(csv_dir)
    df_translated.to_csv('trans_df.csv')