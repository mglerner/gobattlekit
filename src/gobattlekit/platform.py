#!/usr/bin/env python
"""
Platform detection utilities.
"""
import sys

ON_ANDROID = sys.platform == 'android' or 'android' in sys.platform
ON_IOS = sys.platform == 'ios' or 'ios' in sys.platform
ON_MOBILE = ON_ANDROID or ON_IOS
