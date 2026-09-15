import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';

import '../../core/constants/app_strings.dart';
import '../../core/network/api_exception.dart';
import '../../models/import_preview.dart';
import '../../services/plan_api_service.dart';

class ImportPlanScreen extends StatefulWidget {
  const ImportPlanScreen({super.key});

  @override
  State<ImportPlanScreen> createState() => _ImportPlanScreenState();
}

class _ImportPlanScreenState extends State<ImportPlanScreen> {
  final _api = PlanApiService();
  final _dateFmt = DateFormat('MMMM d, yyyy');

  Uint8List? _bytes;
  String? _filename;
  DateTime _startDate = DateTime.now();
  final _planNameCtrl = TextEditingController();

  ImportPreview? _preview;
  bool _loadingPreview = false;
  bool _importing = false;
  String? _error;

  @override
  void dispose() {
    _planNameCtrl.dispose();
    super.dispose();
  }

  Future<void> _copyFormat() async {
    await Clipboard.setData(const ClipboardData(text: AppStrings.importFormat));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text(AppStrings.importFormatCopied)),
    );
  }

  Future<void> _pickFile() async {
    final result = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['xlsx', 'xlsm'],
    );
    if (result.isEmpty) return;
    final file = result.first;

    final bytes = await file.readAsBytes();
    if (bytes.isEmpty) {
      setState(() => _error = 'Could not read the selected file.');
      return;
    }

    setState(() {
      _bytes = bytes;
      _filename = file.name;
      _preview = null;
      _error = null;
    });
    await _loadPreview();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _startDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
    );
    if (picked != null) {
      setState(() {
        _startDate = picked;
        _preview = null;
      });
      if (_bytes != null) await _loadPreview();
    }
  }

  Future<void> _loadPreview() async {
    if (_bytes == null) return;
    setState(() {
      _loadingPreview = true;
      _error = null;
    });
    try {
      final preview = await _api.previewImport(
        bytes: _bytes!,
        filename: _filename ?? 'plan.xlsx',
        startDate: _startDate,
        planName: _planNameCtrl.text.trim(),
      );
      setState(() => _preview = preview);
    } on ApiException catch (e) {
      setState(() {
        _error = e.message;
        // Some validation errors come back as a normal 200 preview with
        // errors; others (e.g. bad file) throw. Surface row errors too.
        if (e.rowErrors.isNotEmpty) {
          _preview = ImportPreview(
            valid: false,
            planName: '',
            totalDays: 0,
            totalWeeks: 0,
            totalPhases: 0,
            errors: e.rowErrors,
          );
        }
      });
    } finally {
      if (mounted) setState(() => _loadingPreview = false);
    }
  }

  Future<void> _import() async {
    if (_bytes == null || _preview == null || !_preview!.valid) return;
    setState(() {
      _importing = true;
      _error = null;
    });
    try {
      await _api.importPlan(
        bytes: _bytes!,
        filename: _filename ?? 'plan.xlsx',
        startDate: _startDate,
        planName: _planNameCtrl.text.trim(),
      );
      if (mounted) Navigator.of(context).pop(true);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _importing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Import Study Plan')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          _formatCard(context),
          const SizedBox(height: 24),

          Text('1. Choose your .xlsx file',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: _pickFile,
            icon: const Icon(Icons.upload_file),
            label: Text(_filename ?? 'Select Excel file'),
          ),
          const SizedBox(height: 24),

          Text('2. Choose a start date',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: _pickDate,
            icon: const Icon(Icons.calendar_today),
            label: Text(_dateFmt.format(_startDate)),
          ),
          const SizedBox(height: 24),

          Text('3. Plan name (optional)',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          TextField(
            controller: _planNameCtrl,
            decoration: const InputDecoration(
              hintText: 'Overrides the name from the workbook',
            ),
            onSubmitted: (_) => _loadPreview(),
          ),
          const SizedBox(height: 24),

          if (_loadingPreview)
            const Center(child: Padding(
              padding: EdgeInsets.all(16),
              child: CircularProgressIndicator(),
            )),

          if (_error != null && (_preview == null || _preview!.errors.isEmpty))
            _errorBox(context, [_error!]),

          if (_preview != null) _previewSection(context, _preview!),
        ],
      ),
    );
  }

  Widget _previewSection(BuildContext context, ImportPreview p) {
    if (!p.valid) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Validation errors',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          _errorBox(context, p.errors),
        ],
      );
    }

    final range = (p.startDate != null && p.endDate != null)
        ? '${_dateFmt.format(p.startDate!)} → ${_dateFmt.format(p.endDate!)}'
        : '—';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(p.planName.isEmpty ? 'Imported Plan' : p.planName,
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            _kv('Days', '${p.totalDays}'),
            _kv('Weeks', '${p.totalWeeks}'),
            _kv('Phases', '${p.totalPhases}'),
            if (p.trackersDetected > 0)
              _kv('Tracker rows', '${p.trackersDetected}'),
            const SizedBox(height: 8),
            _kv('Date', range),
            const SizedBox(height: 16),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.warning_amber_rounded,
                    size: 18, color: Theme.of(context).colorScheme.tertiary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    AppStrings.replacesExistingPlan,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: _importing
                        ? null
                        : () => Navigator.of(context).pop(false),
                    child: const Text('Cancel'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton(
                    onPressed: _importing ? null : _import,
                    child: _importing
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator())
                        : const Text('Import Plan'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _formatCard(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final text = Theme.of(context).textTheme;
    return Card(
      color: scheme.secondaryContainer,
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.info_outline,
                    size: 20, color: scheme.onSecondaryContainer),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    AppStrings.importFormatLabel,
                    style: text.titleMedium?.copyWith(
                      color: scheme.onSecondaryContainer,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            // The literal format string, monospaced + copyable.
            Container(
              width: double.infinity,
              padding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                color: scheme.surface,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: scheme.outlineVariant),
              ),
              child: Row(
                children: [
                  const Expanded(
                    child: SelectableText(
                      AppStrings.importFormat,
                      style: TextStyle(
                        fontFamily: 'monospace',
                        fontWeight: FontWeight.w600,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Copy format',
                    visualDensity: VisualDensity.compact,
                    icon: const Icon(Icons.copy, size: 18),
                    onPressed: _copyFormat,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            Text(
              AppStrings.importFormatHelp,
              style: text.bodySmall?.copyWith(
                color: scheme.onSecondaryContainer,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _errorBox(BuildContext context, List<String> errors) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: scheme.errorContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (final e in errors)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 2),
              child: Text('• $e',
                  style: TextStyle(color: scheme.onErrorContainer)),
            ),
        ],
      ),
    );
  }

  Widget _kv(String k, String v) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(k),
          Text(v, style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
