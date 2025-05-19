import torch
import numpy as np
import joblib
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from model import CLIPRegressor

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

checkpoint = torch.load('model_epoch_final.pth', map_location=DEVICE)
from collections import OrderedDict

new_state_dict = OrderedDict()
for k, v in checkpoint.items():
    new_key = k.replace('module.', '')
    new_state_dict[new_key] = v
model = CLIPRegressor()
model.load_state_dict(new_state_dict)
model.to(DEVICE)
model.eval()

clip_model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32').to(DEVICE)
clip_processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')
scaler = joblib.load('price_scaler_1000_final.pkl')

def predict_price(image, title, member_name, group_name):
    image_input = clip_processor(images=image, return_tensors='pt').to(DEVICE)
    title_input = clip_processor(text=[title], return_tensors='pt', padding=True, truncation=True).to(DEVICE)
    member_input = clip_processor(text=[member_name], return_tensors='pt', padding=True, truncation=True).to(DEVICE)
    group_input = clip_processor(text=[group_name], return_tensors='pt', padding=True, truncation=True).to(DEVICE)

    with torch.no_grad():
        image_emb = clip_model.get_image_features(**image_input)
        title_emb = clip_model.get_text_features(**title_input)
        member_emb = clip_model.get_text_features(**member_input)
        group_emb = clip_model.get_text_features(**group_input)

        features = torch.cat([image_emb, title_emb, member_emb, group_emb], dim=1)
        pred_log_scaled = model(features)
        pred_log = scaler.inverse_transform(pred_log_scaled.cpu().numpy())[0][0]
        predicted_price = np.exp(pred_log)
        return predicted_price