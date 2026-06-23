# App Privacy and Age Rating answers

Prepared answers so you can fill the App Store Connect questionnaires quickly.
Both reflect what the code actually does (verified in the 2026-06-23 review).

## App Privacy (Data Collection)

Answer: **Data Not Collected.**

In App Store Connect > App Privacy, choose "No, we do not collect data from this
app." Rationale you can rely on if asked:

- No account, no sign-in, no user identifiers.
- No analytics or crash-reporting SDK. The only dependencies are BeeWare/Toga
  and certifi.
- The only network traffic is an HTTPS download of public game data and rankings
  from PvPoke. No user data is uploaded.
- The PokeGenie CSV a user imports and the IV targets they save are written to
  the app's local storage and never leave the device.
- The on-device privacy manifest (`resources/PrivacyInfo.xcprivacy`) already
  declares `NSPrivacyTracking=false` and an empty collected-data list, which
  matches this answer.

## Age Rating questionnaire

Answer **None / No** to every content category. There is no violence, no mature
or suggestive themes, no profanity, no gambling, no simulated gambling, and no
in-app purchases. Expected result is 4+.

Two questions to answer carefully:

- Unrestricted web access: the About and Help screens have buttons that open a
  fixed set of specific external links in the system browser — the developer's
  GitHub, PvPoke, a YouTube channel, a Discord invite, a Reddit post (the
  orgodemir webapp the IV badges are credited to), and the support page. This is
  not an in-app web browser, and there is no arbitrary browsing inside the app.
  If the questionnaire asks whether the app can access the open web, the honest
  answer is that it opens specific external links in Safari. The Reddit/YouTube/
  Discord links are the same category as any other outbound link and do not need
  a separate declaration.
- In-app purchases: none. The iOS build has no payment links. (A Venmo tip link
  exists only on the Android build and is gated off for iOS.)

## Export compliance

`ITSAppUsesNonExemptEncryption` is set to `false` in `pyproject.toml`, so the
upload should not prompt. If it does, the app uses only standard HTTPS, which is
exempt encryption.

## Content rights

The app uses Pokémon names referentially and shows game data and rankings sourced
from PvPoke (MIT licensed, credited in-app and in THIRD_PARTY_NOTICES.md). You do
not use third-party content that requires a separate rights grant. Before submit,
confirm the 1024 app icon is your own original art and contains no Niantic or
Nintendo assets.
