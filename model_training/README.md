# Model Training

This directory contains the training pipelines for the different stages of the VPN Detection & Deanonymisation project.

## Pipeline Stages

### Stage 1: App Classifier (CNN)
The default Stage 1 model uses a Convolutional Neural Network (CNN) trained on packet payloads converted to images.
Directory: `stage1_app_classifier/`

### Stage 1: App Classifier (ET-BERT)
An alternative Stage 1 model utilizing the pre-trained ET-BERT Transformer model for encrypted traffic classification directly from packet bytes.
Directory: `stage1_etbert_classifier/`
- **Data Preparation**: `python3 data_preparation.py --pcap_dir <directory> --output_tsv <path/to/train.tsv>`
- **Training**: `./train_etbert.sh` (Downloads the pre-trained model automatically if missing)
- **Evaluation**: `./evaluate_etbert.sh <model_path> <test_tsv_path>`

### Stage 2: Intent Classifier (XGBoost)
Provides a binary intent classification (Benign vs Malicious) using XGBoost on aggregated statistical flow features.
Directory: `stage2_intent_classifier/`
