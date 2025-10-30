# Git Push Fix - Remove Large Files

## Problem
You tried to push `venv/` and large model files (>100MB) which GitHub rejects.

## Solution - Run These Commands

### Step 1: Remove venv and large files from git tracking

```bash
# Remove venv from git (but keep it on disk)
git rm -r --cached venv/

# Remove large model files from git tracking
git rm --cached face-recognition-model/face_recognition_model.h5
git rm --cached face-recognition-model/label_encoder.pkl

# Remove any other large files if they exist
git rm --cached face-recognition-model/haarcascade_frontalface_default.xml
```

### Step 2: Commit the changes

```bash
git add .gitignore
git commit -m "Remove venv and large model files from git, update .gitignore"
```

### Step 3: Push to GitHub

```bash
git push -u origin user
```

## If You Already Pushed Before (Clean History)

If the large files are already in your git history, you need to clean them:

```bash
# Install git filter-repo (if not installed)
pip install git-filter-repo

# Remove venv from entire git history
git filter-repo --path venv --invert-paths --force

# Remove large model files from history
git filter-repo --path face-recognition-model/face_recognition_model.h5 --invert-paths --force
git filter-repo --path face-recognition-model/label_encoder.pkl --invert-paths --force

# Add remote back (filter-repo removes it)
git remote add origin https://github.com/chaimanaouali/SmartCourses.git

# Force push (this rewrites history)
git push -u origin user --force
```

⚠️ **WARNING**: `--force` push rewrites history. Only do this if you're the only one working on the branch!

## Alternative: Use Git LFS for Large Model Files

If you want to keep model files in git:

```bash
# Install Git LFS
git lfs install

# Track large model files
git lfs track "*.h5"
git lfs track "*.pkl"

# Add .gitattributes
git add .gitattributes

# Commit and push
git commit -m "Add Git LFS tracking for model files"
git push -u origin user
```

## What Should Be in Git?

✅ **Include**:
- Source code (.py files)
- Templates (.html files)
- Static files (CSS, JS, small images)
- Requirements files
- Documentation
- .gitignore

❌ **DO NOT Include**:
- venv/ (virtual environment)
- db.sqlite3 (database - contains user data)
- Large model files (>50MB)
- __pycache__/
- *.pyc files
- .env files (secrets)

## Setup Instructions for Other Developers

Create a `SETUP.md` file explaining:
1. Clone the repo
2. Create virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Download model files separately (provide link or instructions)
5. Run migrations: `python manage.py migrate`
6. Run server: `python manage.py runserver`
