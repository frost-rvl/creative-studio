#!/bin/bash

pkill -f "npm run prod" 2>/dev/null
pkill -f "gunicorn" 2>/dev/null
pkill -f "pygbag" 2>/dev/null
pkill -f "python.*service" 2>/dev/null
echo "App stopped."