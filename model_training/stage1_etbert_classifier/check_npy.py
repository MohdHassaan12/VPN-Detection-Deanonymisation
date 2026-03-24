import numpy as np

print("Loading test NPY file...")
x_train = np.load("/Users/mdhassan/Developer/VPN Detection & Deanoymisation/datasets/Open-Datasets/ISCX-VPN_app_dataset/x_payload_train.npy", allow_pickle=True)
y_train = np.load("/Users/mdhassan/Developer/VPN Detection & Deanoymisation/datasets/Open-Datasets/ISCX-VPN_app_dataset/y_train.npy", allow_pickle=True)

print(f"X train shape: {x_train.shape}")
print(f"Y train shape: {y_train.shape}")
print(f"Sample X type: {type(x_train[0])}")

if len(x_train) > 0:
    sample = x_train[0]
    print(f"Sample X length: {len(sample)}")
    print(f"Sample X data (first 50 chars): {sample[:50]}")
    
unique_classes = np.unique(y_train)
print(f"Classes: {unique_classes}")
