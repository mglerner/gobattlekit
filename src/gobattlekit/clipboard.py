#!/usr/bin/env python
"""Copy text to the system clipboard with platform handling.

Toga has no clipboard API, so each platform is driven directly (same
pattern as links.open_url, including taking `app` for the Android
activity). Returns True on success; callers should fall back to "select
the text yourself" UI when this returns False — the search-string widget
always shows the text in a selectable field.
"""
import logging

from .platform import ON_ANDROID, ON_IOS

logger = logging.getLogger(__name__)


def copy_text(app, text):
    """Put `text` on the system clipboard. Returns True on success."""
    try:
        if ON_IOS:
            from rubicon.objc import ObjCClass
            UIPasteboard = ObjCClass('UIPasteboard')
            UIPasteboard.generalPasteboard.string = text
            return True
        if ON_ANDROID:
            from java import jclass
            Context = jclass('android.content.Context')
            ClipData = jclass('android.content.ClipData')
            activity = app._impl.native
            manager = activity.getSystemService(Context.CLIPBOARD_SERVICE)
            manager.setPrimaryClip(
                ClipData.newPlainText('GoBattleKit', text))
            return True
        # Desktop (briefcase dev on macOS): NSPasteboard via rubicon.
        from rubicon.objc import ObjCClass
        NSPasteboard = ObjCClass('NSPasteboard')
        pasteboard = NSPasteboard.generalPasteboard
        pasteboard.clearContents()
        return bool(pasteboard.setString(text,
                                         forType='public.utf8-plain-text'))
    except Exception:
        logger.exception("Clipboard copy failed")
        return False
