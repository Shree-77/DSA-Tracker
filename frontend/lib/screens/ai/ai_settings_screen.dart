import 'package:flutter/material.dart';

import '../../core/network/api_exception.dart';
import '../../models/ai.dart';
import '../../services/ai_service.dart';

/// Screen where the user pastes and saves their own LLM (NVIDIA) API key.
///
/// The key is sent to our backend, encrypted at rest, and never returned in
/// plaintext — only a masked preview (e.g. `****a1b2`) is shown afterwards.
class AiSettingsScreen extends StatefulWidget {
  const AiSettingsScreen({super.key, AiService? service})
      : _service = service;

  final AiService? _service;

  @override
  State<AiSettingsScreen> createState() => _AiSettingsScreenState();
}

class _AiSettingsScreenState extends State<AiSettingsScreen> {
  late final AiService _service = widget._service ?? AiService();
  final _keyCtrl = TextEditingController();
  final _modelCtrl = TextEditingController();

  AiSettings? _settings;
  bool _loading = true;
  bool _saving = false;
  bool _obscure = true;
  String? _error;

  static const _defaultModel = 'meta/llama-3.1-70b-instruct';

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _keyCtrl.dispose();
    _modelCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final s = await _service.getSettings();
      if (!mounted) return;
      setState(() {
        _settings = s;
        _modelCtrl.text = s.model ?? _defaultModel;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _loading = false;
      });
    }
  }

  Future<void> _save() async {
    final key = _keyCtrl.text.trim();
    if (key.length < 8) {
      setState(() => _error = 'Enter a valid API key.');
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final s = await _service.saveApiKey(
        apiKey: key,
        model: _modelCtrl.text.trim(),
      );
      if (!mounted) return;
      setState(() {
        _settings = s;
        _keyCtrl.clear();
        _saving = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('API key saved securely')),
      );
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _saving = false;
      });
    }
  }

  Future<void> _remove() async {
    setState(() => _saving = true);
    try {
      await _service.deleteApiKey();
      if (!mounted) return;
      setState(() {
        _settings = const AiSettings(configured: false);
        _saving = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('API key removed')),
      );
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _saving = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final configured = _settings?.configured ?? false;
    return Scaffold(
      appBar: AppBar(title: const Text('AI Settings')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                if (configured)
                  Card(
                    color: Theme.of(context).colorScheme.secondaryContainer,
                    child: ListTile(
                      leading: const Icon(Icons.verified_user_outlined),
                      title: const Text('API key configured'),
                      subtitle: Text(
                        'Key ${_settings?.apiKeyPreview ?? '****'} · '
                        '${_settings?.provider ?? 'nvidia'}',
                      ),
                    ),
                  ),
                const SizedBox(height: 12),
                Text(
                  'Provide your own NVIDIA API key',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 6),
                Text(
                  'Get a free key at build.nvidia.com, then paste it below. '
                  'It is encrypted on our server and never shown again.',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _keyCtrl,
                  obscureText: _obscure,
                  autocorrect: false,
                  enableSuggestions: false,
                  decoration: InputDecoration(
                    labelText: configured ? 'Replace API key' : 'API key',
                    hintText: 'nvapi-...',
                    prefixIcon: const Icon(Icons.key),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscure ? Icons.visibility : Icons.visibility_off,
                      ),
                      onPressed: () => setState(() => _obscure = !_obscure),
                    ),
                    border: const OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _modelCtrl,
                  autocorrect: false,
                  decoration: const InputDecoration(
                    labelText: 'Model',
                    hintText: _defaultModel,
                    prefixIcon: Icon(Icons.model_training),
                    border: OutlineInputBorder(),
                  ),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    _error!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ],
                const SizedBox(height: 20),
                FilledButton.icon(
                  onPressed: _saving ? null : _save,
                  icon: _saving
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.save),
                  label: Text(configured ? 'Update key' : 'Save key'),
                ),
                if (configured) ...[
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Theme.of(context).colorScheme.error,
                      minimumSize: const Size.fromHeight(48),
                    ),
                    onPressed: _saving ? null : _remove,
                    icon: const Icon(Icons.delete_outline),
                    label: const Text('Remove key'),
                  ),
                ],
              ],
            ),
    );
  }
}
