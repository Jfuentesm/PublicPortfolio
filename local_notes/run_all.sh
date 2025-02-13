#!/usr/bin/env bash
set -e

#
# 1) Install Python dependencies
#
#echo "Installing Python dependencies..."
#pip install -r requirements.txt

#
# 2) Install Node dependencies in src/frontend
#
echo "Installing Node dependencies..."
cd src/frontend
npm install

#
# 3) Launch both FastAPI & Vite via 'npm run dev'
#
echo "Launching backend & frontend concurrently..."
npm run dev