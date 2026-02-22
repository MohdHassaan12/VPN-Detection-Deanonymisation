import os
import argparse
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score, f1_score
from sklearn.preprocessing import LabelEncoder
import joblib

def load_data(data_path):
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path, low_memory=False)
    print(f"Dataset shape: {df.shape}")
    return df

def preprocess_data(df):
    print("Preprocessing data...")
    
    # 1. Handle missing values
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(0, inplace=True)
    
    # Target variable for Intent classification
    target_col = 'intent_label'
    
    if target_col not in df.columns:
        print(f"Error: {target_col} not found in columns!")
        exit(1)
        
    print(f"Intent Label Distribution:\n{df[target_col].value_counts()}")
    
    # Convert text target to numeric (Benign -> 0, Malicious/Attack -> 1)
    # We map 'Benign' to 0 and everything else to 1 for binary intent classifier
    df['target'] = df[target_col].apply(lambda x: 0 if str(x).lower() == 'benign' else 1)
    
    # Select feature columns (excluding identifiers, targets, IPs, timestamps)
    exclude_cols = ['src_ip', 'dst_ip', 'timestamp', 'source_file', 'dataset_source', 
                    'Protocol', 'protocol_hint', 'app_label', 'intent_label', 'target', 
                    'service_name', 'user', 'group', 'src_country', 'dst_country', 'policy_name']
    
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    # Keep only numeric columns
    numeric_df = df[feature_cols].select_dtypes(include=[np.number])
    feature_cols = numeric_df.columns.tolist()
    
    print(f"Selected {len(feature_cols)} numeric features for training.")
    
    X = numeric_df[feature_cols]
    y = df['target']
    
    return X, y, feature_cols

def main():
    parser = argparse.ArgumentParser(description="Train Stage-2 XGBoost Intent Classifier")
    parser.add_argument("--input", type=str, required=True, help="Path to aggregated features CSV")
    parser.add_argument("--n-estimators", type=int, default=200, help="Number of trees")
    parser.add_argument("--max-depth", type=int, default=6, help="Max depth of trees")
    parser.add_argument("--model-out", type=str, default="../../inference/models/stage2/model.xgb", help="Output model path")
    parser.add_argument("--features-out", type=str, default="../../inference/models/stage2/feature_names.txt", help="Output features list")
    
    args = parser.parse_args()
    
    df = load_data(args.input)
    X, y, feature_cols = preprocess_data(df)
    
    print("Splitting data -> 80% train, 20% test...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print(f"Training XGBoost classifier with {args.n_estimators} estimators (max_depth={args.max_depth})...")
    
    # Check if we have two classes
    classes_present = len(np.unique(y_train))
    print(f"Classes present in training data: {classes_present}")
    
    if classes_present < 2:
        print("WARNING: Only one class present in training data! Model will not be able to learn distinctions.")
        print("Using dummy base_score to prevent XGBoost error.")
        base_score = 0.5
    else:
        # Default behavior
        base_score = None
        
    model = xgb.XGBClassifier(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=0.1,
        objective='binary:logistic',
        use_label_encoder=False,
        eval_metric='logloss',
        base_score=base_score,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1] if classes_present > 1 else np.zeros(len(X_test))
    
    acc = accuracy_score(y_test, y_pred)
    
    # Handle F1 and AUC carefully if only 1 class is present
    if len(np.unique(y_test)) > 1:
        f1 = f1_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_prob)
    else:
        f1 = 0.0
        auc = 0.0
        print("Note: Test set contains only one class. F1 and AUC are ill-defined.")
        
    print(f"Accuracy: {acc:.4f}")
    print(f"F1-Score: {f1:.4f}")
    print(f"AUC:      {auc:.4f}")
    
    print("\nClassification Report:")
    # Only provide target_names if both classes are in y_test
    unique_classes_test = np.unique(y_test)
    if len(unique_classes_test) == 2:
        print(classification_report(y_test, y_pred, target_names=["Benign", "Malicious"]))
    else:
        target_names = ["Benign"] if unique_classes_test[0] == 0 else ["Malicious"]
        print(classification_report(y_test, y_pred, target_names=target_names))
    
    # Save the model
    os.makedirs(os.path.dirname(args.model_out), exist_ok=True)
    model.save_model(args.model_out)
    print(f"Model saved to {args.model_out}")
    
    # Save feature names so inference API knows exact order
    with open(args.features_out, "w") as f:
        f.write("\n".join(feature_cols))
    print(f"Feature list saved to {args.features_out}")

if __name__ == "__main__":
    main()
