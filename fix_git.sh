#!/bin/bash
# Quick fix script for git push issues
# Run with: bash fix_git.sh

echo "=========================================="
echo "Git Push Fix - Removing Large Files"
echo "=========================================="

# Step 1: Remove venv and large files from git tracking
echo ""
echo "Step 1: Removing venv/ from git tracking..."
git rm -r --cached venv/ 2>/dev/null || echo "venv/ already removed or not tracked"

echo ""
echo "Step 2: Removing large model files from git tracking..."
git rm --cached face-recognition-model/face_recognition_model.h5 2>/dev/null || echo "face_recognition_model.h5 already removed"
git rm --cached face-recognition-model/label_encoder.pkl 2>/dev/null || echo "label_encoder.pkl already removed"
git rm --cached face-recognition-model/haarcascade_frontalface_default.xml 2>/dev/null || echo "haarcascade already removed"

# Step 2: Add .gitignore
echo ""
echo "Step 3: Adding updated .gitignore..."
git add .gitignore

# Step 3: Commit changes
echo ""
echo "Step 4: Committing changes..."
git commit -m "Remove venv and large model files from git, update .gitignore"

# Step 4: Show status
echo ""
echo "=========================================="
echo "Done! Now you can push with:"
echo "  git push -u origin user"
echo "=========================================="
echo ""
echo "If this doesn't work, you need to clean git history."
echo "See GIT_PUSH_FIX.md for detailed instructions."
