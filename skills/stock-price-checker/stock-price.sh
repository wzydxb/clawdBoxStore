#!/bin/bash
# Stock Price Checker - Get current stock prices from Yahoo Finance
#
# Usage: bash stock-price.sh <SYMBOL>
# Example: bash stock-price.sh NVDA

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/stock-price.py" "$@"
