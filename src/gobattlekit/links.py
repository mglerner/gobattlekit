#!/usr/bin/env python
"""Open external URLs with platform handling.

Shared by the About / Help / IV Credits screens (it was triplicated).
"""
import asyncio
import logging

from .platform import ON_ANDROID

logger = logging.getLogger(__name__)

# Hold strong references to fire-and-forget dialog tasks: the event loop only
# keeps a weak reference, so without this a task can be GC'd before it runs and
# the "Could not open link" dialog silently never appears.
_pending_tasks = set()


def open_url(app, url):
    """Open a URL in the system browser, surfacing failures in a dialog."""
    if ON_ANDROID:
        try:
            from java import jclass
            Intent = jclass('android.content.Intent')
            Uri = jclass('android.net.Uri')
            intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            app._impl.native.startActivity(intent)
        except Exception:
            logger.exception("Could not open URL %s", url)
            # asyncio.create_task needs a real coroutine. The previous code
            # passed window.info_dialog(...)'s return value — an awaitable
            # Dialog, not a coroutine — so every failure raised TypeError
            # on top of the (deprecated) dialog call (SQ1).
            import toga

            async def _show_dialog():
                await app.main_window.dialog(toga.InfoDialog(
                    "Could not open link",
                    f"Try opening this URL manually:\n{url}",
                ))

            task = asyncio.create_task(_show_dialog())
            _pending_tasks.add(task)
            task.add_done_callback(_pending_tasks.discard)
    else:
        import webbrowser
        webbrowser.open(url)
