import os
import time
import logging
import pandas as pd
import requests
from urllib.parse import quote, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger('mercari_scraper')
logger.setLevel(logging.INFO)

# Удаляем старые хендлеры
if logger.hasHandlers():
    logger.handlers.clear()

console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('mercari_scraper_new_1.log', encoding='utf-8')

formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)


def scrape_mercari_photocards(search_query, price_min=None, price_max=None, price_step=1000):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    safe_query = search_query.replace(' ', '_')
    image_dir = f'images/{safe_query}'
    os.makedirs(image_dir, exist_ok=True)

    if price_min is None:
        price_min = 0
    if price_max is None:
        price_max = 100000

    data = []
        # Custom price ranges
    price_ranges = [
        (300, 800),
        (801, 1500),
        (1501, 5000),
        (5001, 10000),
        (10001, 40000),
        (40001, None) 
    ]

    logging.info(f'Scraping with {len(price_ranges)} custom price ranges')

    for range_idx, (range_min, range_max) in enumerate(price_ranges):
        encoded_query = quote(search_query)
        if range_max:
            search_url = f'https://www.mercari.com/jp/search/?keyword={encoded_query}&price_min={range_min}&price_max={range_max}'
        else:
            search_url = f'https://www.mercari.com/jp/search/?keyword={encoded_query}&price_min={range_min}'
        logger.info(f'Opening price range {range_min}-{range_max} yen: {search_url}')
        driver.get(search_url)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li[data-testid="item-cell"]'))
            )
        except Exception as e:
            logger.warning(f'Could not find item cards for price range {range_min}-{range_max}: {e}')
            continue

        # Scroll to load more items
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        items = driver.find_elements(By.CSS_SELECTOR, 'li[data-testid="item-cell"]')
        logger.info(f'[Price range {range_min}-{range_max}] Found {len(items)} cards.')

        for idx, item in enumerate(items):
            try:
                driver.execute_script("arguments[0].scrollIntoView();", item)
                time.sleep(0.3)

                link_tag = item.find_element(By.CSS_SELECTOR, 'a[data-testid="thumbnail-link"]')
                product_url = link_tag.get_attribute('href')
                if not product_url.startswith('https'):
                    product_url = 'https://www.mercari.com' + product_url

                thumbnail_div = link_tag.find_element(By.CSS_SELECTOR, 'div[role="img"]')
                aria_label = thumbnail_div.get_attribute('aria-label')
                title = aria_label.split('の画像')[0] if aria_label else 'No title'

                price_span = item.find_element(By.CSS_SELECTOR, 'span.number__6b270ca7')
                price = price_span.text.strip()

                img_tag = item.find_element(By.CSS_SELECTOR, 'img')
                image_url = img_tag.get_attribute('src')

                data.append({
                    'title': title,
                    'price': price,
                    'image_url': image_url,
                    'product_url': product_url
                })

            except Exception as e:
                logger.error(f'Error parsing card #{idx + 1} at price range {range_min}-{range_max}: {e}')

    driver.quit()
    logger.info('Browser closed.')

    if not data:
        logger.warning('No data to save.')
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df.drop_duplicates(subset=['title', 'price', 'image_url', 'product_url'], inplace=True)
    logger.info(f'Unique cards after duplicate removal: {len(df)}')

    output_file = f'{safe_query}_mercari.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    logger.info(f'CSV saved: {output_file}')

    # Download images
    for i, row in df.iterrows():
        try:
            response = requests.get(row['image_url'], timeout=10)
            if response.status_code == 200:
                img_ext = os.path.splitext(urlparse(row['image_url']).path)[-1]
                if not img_ext:
                    img_ext = '.jpg'
                image_path = os.path.join(image_dir, f'{i+1}{img_ext}')
                with open(image_path, 'wb') as f:
                    f.write(response.content)
        except Exception as e:
            logger.error(f'Error downloading image {row["image_url"]}: {e}')

    logger.info(f'Image download complete. Folder: {image_dir}')
    return df


from concurrent.futures import ThreadPoolExecutor

def batch_scrape_stage_names_ja(name_dict, ):
    def run_scrape(stage_name, japanese_name):
        query = f'{japanese_name} フォトカード'
        logging.info(f'Поиск для {stage_name} ({query})')
        scrape_mercari_photocards(query, price_min=None, price_max=None, price_step=1000)

    with ThreadPoolExecutor(max_workers=4) as executor:
        for stage_name, japanese_name in name_dict.items():
            executor.submit(run_scrape, stage_name, japanese_name)

kpop_stage_names_ja = {
    # BTS
    'RM': 'ナムジュン',
    'Jin': 'ユンギ',
    'SUGA': 'ソクジン',
    'j-hope': 'ホソク',
    'Jimin': 'ジミン',
    'V': 'テヒョン',
    'Jungkook': 'ジョングク',
    
    # ENHYPEN
    'Jungwon': 'ジョンウォン',
    'Heeseung': 'ヒスン',
    'Jay': 'エンハイプン ジョンソン',
    'Jake': 'エンハイプン ジェユン',
    'Sunghoon': 'ソンフン',
    'Sunoo': 'エンハイプン ソヌ',
    'Ni-ki': 'ニキ',

    # BLACKPINK
    'Jisoo': 'ジス',
    'Jennie': 'ジェニー',
    'Rosé': 'ロゼ',
    'Lisa': 'リサ',

    # TWICE
    'Nayeon': 'ナヨン',
    'Jeongyeon': 'ジョンヨン',
    'Momo': 'モモ',
    'Sana': 'サナ',
    'Jihyo': 'ジヒョ',
    'Mina': 'ミナ',
    'Dahyun': 'ダヒョン',
    'Chaeyoung': 'チェヨン',
    'Tzuyu': 'ツウィ',

    # TXT
    'Soobin': 'スビン',
    'Yeonjun': 'ヨンジュン',
    'Beomgyu': 'ボムギュ',
    'Taehyun': 'テヒョン',
    'Hueningkai': 'ヒュニンカイ',

    # SEVENTEEN
    'S.Coups': 'エスクプス',
    'Jeonghan': 'ジョンハン',
    'Joshua': 'ジョシュア',
    'Jun': 'ジュン',
    'Hoshi': 'ホシ',
    'Wonwoo': 'ウォヌ',
    'Woozi': 'ウジ',
    'DK': 'ドギョム',
    'Mingyu': 'ミンギュ',
    'The8': 'ディエイト',
    'Seungkwan': 'スングァン',
    'Vernon': 'バーノン',
    'Dino': 'ディノ'
}
stray_kids_name_dict = {
    'Bang Chan': 'バンチャン',
    'Lee Know': 'リノ',
    'Changbin': 'チャンビン',
    'Hyunjin': 'ヒョンジン',
    'Han': 'ハン',
    'Felix': 'フィリックス',
    'Seungmin': 'スンミン',
    'I.N': 'アイエン'
}

kpop_stage_names_ja_new = ({
    # IVE
    'Yujin': 'ユジン ive',
    'Gaeul': 'ガウル',
    'Rei': 'レイ',
    'Wonyoung': 'ウォニョン',
    'Liz': 'リズ',
    'Leeseo': 'イソ',

    # ZEROBASEONE
    'Sung Hanbin': 'ソン ハンビン',
    'Kim Jiwoong': 'キム ジウン',
    'Zhang Hao': 'ジャン ハオ',
    'Seok Matthew': 'ソク マシュー',
    'Kim Taerae': 'キム テレ',
    'Ricky': 'リッキー',
    'Kim Gyuvin': 'キム ギュビン',
    'Park Gunwook': 'パク ゴヌク',
    'Han Yujin': 'ハン ユジン',

    # BOYNEXTDOOR
    'Jaehyun': 'ジェヒョン boynextdoor',
    'Sungho': 'ソンホ',
    'Riwoo': 'リウ',
    'Taesan': 'テサン',
    'Leehan': 'リハン',
    'Woonhak': 'ウンハク',

    # aespa
    'Karina': 'カリナ',
    'Giselle': 'ジゼル',
    'Winter': 'ウィンター',
    'Ningning': 'ニンニン',

    # LE SSERAFIM
    'Chaewon': 'チェウォン lesserafim',
    'Sakura': 'サクラ lesserafim',
    'Yunjin': 'ユンジン lesserafim',
    'Kazuha': 'カズハ lesserafim',
    'Eunchae': 'ウンチェ lesserafim',

    # Red Velvet
    'Irene': 'アイリーン',
    'Seulgi': 'スルギ',
    'Wendy': 'ウェンディ',
    'Joy': 'ジョイ',
    'Yeri': 'イェリ',

    # RIIZE
    'Shotaro': 'ショウタロウ',
    'Eunseok': 'ウンソク',
    'Sungchan': 'ソンチャン',
    'Wonbin': 'ウォンビン riize',
    'Seunghan': 'スンハン riize',
    'Sohee': 'ソヒ riize',
    'Anton': 'アントン',

    # NCT 127
    'Taeyong': 'テヨン nct',
    'Taeil': 'テイル nct',
    'Johnny': 'ジョニー nct',
    'Yuta': 'ユウタ nct',
    'Doyoung': 'ドヨン nct',
    'Jaehyun (NCT)': 'ジェヒョン nct',
    'Jungwoo': 'ジョンウ nct',
    'Mark': 'マーク nct',
    'Haechan': 'ヘチャン nct',

    # (G)I-DLE
    'Soyeon': 'ソヨン gidle',
    'Miyeon': 'ミヨン gidle',
    'Minnie': 'ミンニ gidle',
    'Yuqi': 'ウギ gidle',
    'Shuhua': 'シュファ gidle',

    # EXO
    'Xiumin': 'シウミン',
    'Suho': 'スホ',
    'Lay': 'レイ',
    'Baekhyun': 'ベクヒョン',
    'Chen': 'チェン',
    'Chanyeol': 'チャンヨル',
    'D.O.': 'ディオ exo',
    'Kai': 'カイ',
    'Sehun': 'セフン',

    # NMIXX
    'Lily': 'リリー nmixx',
    'Haewon': 'ヘウォン nmixx',
    'Sullyoon': 'ソリュン',
    'Bae': 'ベイ',
    'Jiwoo': 'ジウ nmixx',
    'Kyujin': 'キュジン nmixx',

    # ITZY
    'Yeji': 'イェジ itzy',
    'Lia': 'リア itzy',
    'Ryujin': 'リュジン itzy',
    'Chaeryeong': 'チェリョン itzy',
    'Yuna': 'ユナ itzy',

    # TWS
    'Shinyu': 'シンユ tws',
    'Dohoon': 'ドフン tws',
    'Youngjae': 'ヨンジェ tws',
    'Hanjin': 'ハンジン tws',
    'Jihoon': 'ジフン tws',
    'Kyungmin': 'キョンミン tws',
    'Taehoon': 'テフン tws'
})


batch_scrape_stage_names_ja(kpop_stage_names_ja_new)