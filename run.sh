#!/bin/bash
source /usr/local/anaconda/bin/activate vulture
gunicorn -c /etc/gunicorn/vulture.py vulture:application
