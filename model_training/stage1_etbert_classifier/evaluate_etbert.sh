#!/bin/bash

# Exit on error
set -e

# Configuration
ET_BERT_DIR="../../ET-BERT-2afe5b390619ba382893a0ea7ac64623efe1fdfe"
PRETRAINED_MODEL_URL="https://drive.google.com/uc?export=download&id=1r1yE34dU2W8zSqx1FkB8gCWri4DQWVtE"
MODELS_DIR="${ET_BERT_DIR}/models"
VOCAB_PATH="${MODELS_DIR}/encryptd_vocab.txt"

# Provide these as arguments, or default to constants
MODEL_PATH="${1:-models/finetuned_etbert.bin}"
TEST_DATA="${2:-data/test_dataset.tsv}"
PREDICTION_OUTPUT="${3:-data/prediction_results.tsv}"

# Count number of unique labels from test dataset
# Assuming first line is header: label \t text_a
LABELS_NUM=$(tail -n +2 "$TEST_DATA" | cut -f 1 | sort | uniq | wc -l | tr -d ' ')

# Need to generate a nolabel version for the inference script
NOLABEL_TEST_DATA="data/nolabel_test_dataset.tsv"
echo "Creating nolabel test dataset for inference..."
awk -F'\t' 'NR==1{print "text_a"} NR>1{print $2}' "$TEST_DATA" > "$NOLABEL_TEST_DATA"

echo "=== ET-BERT Stage 1 App Classification Evaluation ==="
echo "Model: $MODEL_PATH"
echo "Test Data: $TEST_DATA -> $NOLABEL_TEST_DATA"
echo "Detected $LABELS_NUM classes."

python3 "${ET_BERT_DIR}/inference/run_classifier_infer.py" \
    --load_model_path "$MODEL_PATH" \
    --vocab_path "$VOCAB_PATH" \
    --test_path "$NOLABEL_TEST_DATA" \
    --prediction_path "$PREDICTION_OUTPUT" \
    --labels_num "$LABELS_NUM" \
    --embedding word_pos_seg \
    --encoder transformer \
    --mask fully_visible

echo "Evaluation complete! Predictions saved to $PREDICTION_OUTPUT"
