#!/bin/bash

# Exit on error
set -e

# Configuration
ET_BERT_DIR="../../ET-BERT-2afe5b390619ba382893a0ea7ac64623efe1fdfe"
PRETRAINED_MODEL_URL="https://drive.google.com/uc?export=download&id=1r1yE34dU2W8zSqx1FkB8gCWri4DQWVtE"
MODELS_DIR="${ET_BERT_DIR}/models"
PRETRAINED_MODEL_PATH="${MODELS_DIR}/pretrained_model.bin"
VOCAB_PATH="${MODELS_DIR}/encryptd_vocab.txt"

# Data paths (Modify these arguments when calling the script)
TRAIN_DATA="data/train_dataset.tsv"
DEV_DATA="data/valid_dataset.tsv"
TEST_DATA="data/test_dataset.tsv"

OUTPUT_MODEL="models/finetuned_etbert.bin"

EPOCHS=10
BATCH_SIZE=32
SEQ_LEN=128

echo "=== ET-BERT Stage 1 App Classification Training ==="

# Check for pre-trained model
if [ ! -f "$PRETRAINED_MODEL_PATH" ]; then
    echo "[!] Pre-trained model not found at $PRETRAINED_MODEL_PATH"
    echo "Downloading pre-trained ET-BERT model..."
    
    # Using gdown since Google Drive wget direct link might fail without confirmations for large files
    # Alternatively wget with confirmation cookies if needed. For now using generic wget but might need gdown if it fails.
    wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1r1yE34dU2W8zSqx1FkB8gCWri4DQWVtE' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1r1yE34dU2W8zSqx1FkB8gCWri4DQWVtE" -O "$PRETRAINED_MODEL_PATH" && rm -rf /tmp/cookies.txt
    
    # If standard wget failed, fallback recommendation:
    if [ ! -f "$PRETRAINED_MODEL_PATH" ]; then
        echo "Failed to heavily download via wget. Please install gdown: pip install gdown"
        echo "Then run: gdown 1r1yE34dU2W8zSqx1FkB8gCWri4DQWVtE -O $PRETRAINED_MODEL_PATH"
        exit 1
    fi
    echo "Download complete."
fi

# Ensure output directory exists
mkdir -p $(dirname "$OUTPUT_MODEL")

echo "Starting fine-tuning..."
export PYTHONPATH="${ET_BERT_DIR}:${PYTHONPATH}"
python3 "${ET_BERT_DIR}/fine-tuning/run_classifier.py" \
    --config_path "${ET_BERT_DIR}/models/bert/base_config.json" \
    --pretrained_model_path "$PRETRAINED_MODEL_PATH" \
    --vocab_path "$VOCAB_PATH" \
    --train_path "$TRAIN_DATA" \
    --dev_path "$DEV_DATA" \
    --test_path "$TEST_DATA" \
    --epochs_num "$EPOCHS" \
    --batch_size "$BATCH_SIZE" \
    --embedding word_pos_seg \
    --encoder transformer \
    --mask fully_visible \
    --seq_length "$SEQ_LEN" \
    --learning_rate 2e-5 \
    --output_model_path "$OUTPUT_MODEL"

echo "Training complete! Model saved to $OUTPUT_MODEL"
