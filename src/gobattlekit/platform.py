#!/usr/bin/env python
"""
Platform detection utilities.
"""
import sys

ON_ANDROID = sys.platform == 'android'
ON_IOS = sys.platform == 'ios'
ON_MOBILE = ON_ANDROID or ON_IOS
