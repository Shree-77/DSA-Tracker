# Android configuration notes

The `res/xml/network_security_config.xml` file permits cleartext HTTP **only**
to local development hosts (`localhost`, `10.0.2.2`, `127.0.0.1`).

When Flutter generates the Android project (`flutter create .` in `frontend/`),
reference this config in `AndroidManifest.xml`:

```xml
<application
    ...
    android:networkSecurityConfig="@xml/network_security_config">
```

And add the internet permission (usually already present):

```xml
<uses-permission android:name="android.permission.INTERNET"/>
```

For production, point the app at an `https://` backend via
`--dart-define=API_BASE_URL=https://your-backend.example.com` — no cleartext is
required and this config does not weaken production security.
