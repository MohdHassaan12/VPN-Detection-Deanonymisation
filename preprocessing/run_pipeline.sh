#!/bin/bash
# Master Preprocessing Script
# Runs the complete pipeline for all datasets

set -e  # Exit on error

echo "=========================================="
echo "VPN Detection - Data Preprocessing Pipeline"
echo "=========================================="
echo ""

# Change to project directory
cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r preprocessing/requirements.txt

echo ""
echo "=========================================="
echo "Step 1: Processing CIC-IDS2017"
echo "=========================================="
if [ -d "CIC-IDS2017" ]; then
    python preprocessing/scripts/process_cicids2017.py \
        --input "CIC-IDS2017/" \
        --output "preprocessing/outputs/cic_ids_2017.csv"
    echo "✅ CIC-IDS2017 processed"
else
    echo "⚠️  CIC-IDS2017 directory not found, skipping..."
fi

echo ""
echo "=========================================="
echo "Step 2: Processing USTC-TFC2016"
echo "=========================================="
if [ -d "USTC-TFC2016-master" ]; then
    python preprocessing/scripts/process_ustc.py \
        --input "USTC-TFC2016-master/" \
        --output "preprocessing/outputs/" \
        --type all
    echo "✅ USTC-TFC2016 processed"
else
    echo "⚠️  USTC-TFC2016 directory not found, skipping..."
fi

echo ""
echo "=========================================="
echo "Step 3: Merging Datasets"
echo "=========================================="
python preprocessing/scripts/merge_datasets.py \
    --config "preprocessing/configs/merge_config.yaml"
echo "✅ Datasets merged"

echo ""
echo "=========================================="
echo "Step 4: Generating Statistics"
echo "=========================================="
if [ -f "preprocessing/outputs/Unified_Dataset.csv" ]; then
    python preprocessing/scripts/dataset_statistics.py \
        --input "preprocessing/outputs/Unified_Dataset.csv" \
        --output-dir "preprocessing/outputs/statistics/"
    echo "✅ Statistics generated"
else
    echo "⚠️  Unified dataset not found, skipping statistics..."
fi

echo ""
echo "=========================================="
echo "✅ PIPELINE COMPLETE!"
echo "=========================================="
echo ""
echo "📁 Output files:"
echo "  - preprocessing/outputs/Unified_Dataset.csv"
echo "  - preprocessing/outputs/Stage1_App_Classification.csv"
echo "  - preprocessing/outputs/Stage2_Intent_Classification.csv"
echo "  - preprocessing/outputs/train.csv"
echo "  - preprocessing/outputs/val.csv"
echo "  - preprocessing/outputs/test.csv"
echo "  - preprocessing/outputs/statistics/"
echo ""
echo "📊 Next steps:"
echo "  1. Review statistics in preprocessing/outputs/statistics/"
echo "  2. Begin Stage-1 model training (Application Classification)"
echo "  3. Begin Stage-2 model training (Intent Classification)"
echo ""
