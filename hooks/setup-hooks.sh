#!/bin/bash
cp hooks/pre-push.sh .git/hooks/pre-push
chmod +x .git/hooks/pre-push
echo "Pre-push hook installed."