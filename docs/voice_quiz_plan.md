# Voice quiz mode (deferred feature idea)

Status: idea only, not scheduled. Assessed 2026-08-04.

Goal: hands-free quizzing (e.g. phone mounted in a car) — the app reads a
quiz question aloud, the user answers verbally, the app speaks the result
and advances.

## Why not Siri / App Intents

- Siri is built for one-shot commands ("Hey Siri, start a type quiz"),
  not a sustained multi-turn dialog. It cannot host the question/answer
  loop.
- App Intents must be written in Swift as an app extension running in a
  separate process with no Python runtime — quiz logic (gamemaster data,
  scoring) would need reimplementing or proxying.
- CarPlay is out: quiz/game apps are not an eligible CarPlay category.
- The one place Siri helps: a tiny App Intent as a hands-free *launcher*
  into voice mode. Polish, not core; defer.

## Recommended approach: in-app voice mode

Use native iOS speech APIs from Python via Rubicon-ObjC — the same
bridge `src/gobattlekit/clipboard.py` already uses for `UIPasteboard`.

- Speaking: `AVSpeechSynthesizer` reads the question and feedback.
- Listening: `SFSpeechRecognizer` + `AVAudioEngine`. The answer
  vocabularies are tiny and closed, which makes recognition reliable:
  - Type quiz: 4 phrases ("super effective", "not very effective",
    "neutral", "double resisted")
  - Move-count quiz (quiz.py): numbers 1-20 / "more", plus 4-number
    sequences ("five, four, four, five")
  - Timing quiz: its small fixed set of timing patterns
  Pass these as `contextualStrings` to bias the recognizer; use
  on-device recognition so it works with no signal.

Flow: question shown -> app speaks it -> mic opens -> spoken answer
parsed ("four" -> 4) -> fed into the existing `_check_answer()` ->
app speaks the result -> existing auto-advance. Voice is a new I/O
channel on top of current quiz logic, toggled by a "voice mode" button;
screen logic barely changes. Suggested shape: a platform `speech.py`
module (speak/listen; iOS via rubicon, no-op fallback in dev).

Start with the **type quiz** — simplest screen (4 fixed answers, no
attempt-retry loop) — to prove out the speak/listen bridge before
extending to the two timing quizzes.

## Requirements and caveats

- Info.plist: `NSMicrophoneUsageDescription` and
  `NSSpeechRecognitionUsageDescription`; `AVAudioSession` setup.
  One-time permission prompts on first use.
- Foreground only for v1: app open, `idleTimerDisabled` so the screen
  stays awake. Screen-locked/background listening (audio background
  mode) is possible but invites App Review scrutiny — defer.
- iOS-only as written; Android would need its own
  `SpeechRecognizer`/`TextToSpeech` path.
- Testing needs a real device — speech recognition doesn't behave on
  the simulator.
- TTS will mangle some Pokemon names; harmless, since accuracy matters
  on the answer side (numbers and stock phrases).
- App Store copy must say "hands-free voice mode", never "use while
  driving" (review risk and honesty).
