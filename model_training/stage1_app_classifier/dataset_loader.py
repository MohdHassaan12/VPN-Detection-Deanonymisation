import os
import pandas as pd
import numpy as np
from PIL import Image

class PacketBlockLoader:
    def __init__(self, image_dir, img_size=64):
        self.image_dir = image_dir
        self.img_size = img_size
        self.manifest_path = os.path.join(image_dir, "manifest.csv")
        
    def load_dataset(self):
        if not os.path.exists(self.manifest_path):
            raise FileNotFoundError(f"Manifest not found at {self.manifest_path}")
            
        print(f"Loading manifest from {self.manifest_path}...")
        df = pd.read_csv(self.manifest_path)
        
        # Determine labels
        labels = df['app_label'].unique()
        self.label_map = {label: i for i, label in enumerate(labels)}
        print(f"Found {len(labels)} classes: {self.label_map}")
        
        X = []
        y = []
        
        print(f"Loading {len(df)} images...")
        for _, row in df.iterrows():
            img_path = os.path.join(self.image_dir, row['image_file'])
            if not os.path.exists(img_path):
                continue
                
            try:
                img = Image.open(img_path).convert('RGB')
                img = img.resize((self.img_size, self.img_size))
                img_array = np.array(img) / 255.0  # Normalize to [0,1]
                
                X.append(img_array)
                y.append(self.label_map[row['app_label']])
            except Exception as e:
                print(f"Error loading {img_path}: {e}")
                
        return np.array(X), np.array(y), self.label_map
