import pandas as pd
import os

def process_all_csvs(csv_dir, image_root, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]

    for csv_file in csv_files:
        csv_path = os.path.join(csv_dir, csv_file)
        name_prefix = csv_file.replace('_mercari.csv', '') 
        image_folder = os.path.join(image_root, name_prefix)

        if not os.path.isdir(image_folder):
            print(f'Image folder not found for: {csv_file}, expected: {image_folder}')
            continue

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f'Error reading {csv_path}: {e}')
            continue

        df = df.reset_index(drop=True)
        image_paths = []

        for i in range(len(df)):
            base_name_jpg = f'{i+1}.jpg'
            base_name_webp = f'{i+1}@webp'
            path_jpg = os.path.join(image_folder, base_name_jpg)
            path_webp = os.path.join(image_folder, base_name_webp)

            if os.path.exists(path_jpg):
                image_paths.append(path_jpg)
            elif os.path.exists(path_webp):
                image_paths.append(path_webp)
            else:
                image_paths.append(None)

        df['image_path'] = image_paths
        df = df.dropna(subset=['image_path'])

        output_csv_path = os.path.join(output_dir, csv_file)
        df.to_csv(output_csv_path, index=False)
        print(f'Saved: {output_csv_path} ({len(df)} rows)')

process_all_csvs('mercari_csv', 'images', 'mercari_new_csv')