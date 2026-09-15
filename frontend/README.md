# Study Tracker — Frontend (Flutter)

A clean, mobile-first Material 3 Flutter client for the Study Tracker API.

## Tech stack

- Flutter (Dart 3.3+), Material 3
- `provider` for lightweight state management
- `http` for REST communication
- `shared_preferences` for config + offline cache
- `file_picker` for `.xlsx` import
- `flutter_local_notifications` (optional reminders)
- `intl` for date formatting

## Architecture

```
lib/
├── main.dart
├── core/
│   ├── constants/     # AppConfig (API base URL), strings
│   ├── theme/         # Material 3 light/dark
│   └── network/       # ApiClient + ApiException
├── models/            # Plan, StudyDay, Today, Tracker, Progress, ...
├── services/          # PlanApiService, CacheService, NotificationService
├── providers/         # AppState, DayDetailProvider, ThemeProvider
├── screens/
│   ├── dashboard/     # "What do I do today?"
│   ├── plan/          # full plan grouped by week
│   ├── day_detail/    # status + tracker + confidence + reflection
│   ├── progress/      # streaks, weekly, difficulty, stats
│   ├── import_plan/   # pick .xlsx, preview, import
│   └── settings/      # plan, theme, API server, notifications
└── widgets/           # reusable UI (state views, chips, bars)
```

Every API-driven screen handles **loading**, **error** (with retry), and
**empty** states. When the backend is unreachable, cached data is shown with an
offline banner.

## API configuration

The API base URL is configurable and never hard-coded across the app. It is
resolved in this order:

1. A URL saved in **Settings → API Server**.
2. A `--dart-define=API_BASE_URL=...` provided at build/run time.
3. The built-in development default (`http://localhost:8000`).

> **Android emulator:** use `http://10.0.2.2:8000` (a one-tap button exists in
> Settings). **Physical device:** use your machine's LAN IP.

## Setup

```bash
cd frontend
flutter pub get
```

## Running

```bash
# Web (Chrome)
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000

# Android (emulator)
flutter run -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000

# iOS (simulator)
flutter run -d ios --dart-define=API_BASE_URL=http://localhost:8000
```

## Tests

```bash
flutter test
```

## Building releases

```bash
# Android APK
flutter build apk --release --dart-define=API_BASE_URL=https://your-backend.example.com

# Android App Bundle (Play Store)
flutter build appbundle --release --dart-define=API_BASE_URL=https://your-backend.example.com

# iOS (run on macOS, then archive in Xcode)
flutter build ios --release --dart-define=API_BASE_URL=https://your-backend.example.com

# Web
flutter build web --release --dart-define=API_BASE_URL=https://your-backend.example.com
```

## Platform notes

- **Notifications** are optional and toggled in Settings. On web they are
  no-ops. On Android 13+ the OS will prompt for notification permission.
- The Android network layer uses cleartext for `http://` dev URLs. For
  production always use `https://`.
- iOS builds must be produced on macOS with Xcode.

## Importing a plan

1. Open the app → **Home** → **Import Plan** (or **Settings → Import New Plan**).
2. Pick your `.xlsx` file (e.g. `DSA_Recursion_to_Trees_8_Week_Plan.xlsx`).
3. Choose a **start date** (mapped to Day 1).
4. Review the preview (days / weeks / phases / date range, plus any validation
   errors) and tap **Import Plan**.
