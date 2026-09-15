import 'package:flutter/material.dart';

import '../../core/network/api_exception.dart';
import '../../models/ai.dart';
import '../../services/ai_service.dart';
import 'ai_settings_screen.dart';

/// AI study-plan creator.
///
/// Flow:
///   1. User chats with the assistant to design a plan.
///   2. Tap "Generate plan" -> AI returns a structured preview.
///   3. Review the preview and pick a start date.
///   4. Tap "Create this plan" -> imports it and pops with `true`.
///
/// Pop result: `true` when a plan was imported (caller should refresh).
class AiPlanScreen extends StatefulWidget {
  const AiPlanScreen({super.key, AiService? service}) : _service = service;

  final AiService? _service;

  @override
  State<AiPlanScreen> createState() => _AiPlanScreenState();
}

class _AiPlanScreenState extends State<AiPlanScreen> {
  late final AiService _service = widget._service ?? AiService();
  final _inputCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();

  final List<ChatMessage> _messages = [];
  bool _sending = false;
  bool _generating = false;
  bool _configured = true;
  bool _checkingConfig = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _checkConfigured();
  }

  @override
  void dispose() {
    _inputCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _checkConfigured() async {
    try {
      final s = await _service.getSettings();
      if (!mounted) return;
      setState(() {
        _configured = s.configured;
        _checkingConfig = false;
      });
    } on ApiException {
      if (!mounted) return;
      setState(() => _checkingConfig = false);
    }
  }

  bool get _canGenerate =>
      _messages.any((m) => m.role == 'assistant') && !_sending && !_generating;

  Future<void> _send() async {
    final text = _inputCtrl.text.trim();
    if (text.isEmpty || _sending) return;
    final history = List<ChatMessage>.from(_messages);
    setState(() {
      _messages.add(ChatMessage(role: 'user', content: text));
      _inputCtrl.clear();
      _sending = true;
      _error = null;
    });
    _scrollToBottom();
    try {
      final reply = await _service.chat(message: text, history: history);
      if (!mounted) return;
      setState(() {
        _messages.add(ChatMessage(role: 'assistant', content: reply));
        _sending = false;
      });
      _scrollToBottom();
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _sending = false;
        _error = e.message;
        if (e.code == 'AI_NOT_CONFIGURED' ||
            e.code == 'AI_KEY_INVALID' ||
            e.code == 'AI_KEY_UNREADABLE') {
          _configured = false;
        }
      });
    }
  }

  Future<void> _generate() async {
    setState(() {
      _generating = true;
      _error = null;
    });
    try {
      final plan = await _service.generatePlan(conversation: _messages);
      if (!mounted) return;
      setState(() => _generating = false);
      await _showPreview(plan);
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _generating = false;
        _error = e.message;
      });
    }
  }

  Future<void> _showPreview(GeneratedPlan plan) async {
    final imported = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => _PlanPreviewSheet(plan: plan, service: _service),
    );
    if (imported == true && mounted) {
      Navigator.of(context).pop(true);
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Create Plan with AI'),
        actions: [
          IconButton(
            tooltip: 'AI settings',
            icon: const Icon(Icons.settings),
            onPressed: () async {
              await Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const AiSettingsScreen()),
              );
              _checkConfigured();
            },
          ),
        ],
      ),
      body: _checkingConfig
          ? const Center(child: CircularProgressIndicator())
          : !_configured
              ? _NotConfigured(onConfigured: _checkConfigured)
              : Column(
                  children: [
                    Expanded(child: _buildMessages(context)),
                    if (_error != null) _errorBanner(context),
                    if (_canGenerate) _generateBar(context),
                    _inputBar(context),
                  ],
                ),
    );
  }

  Widget _buildMessages(BuildContext context) {
    if (_messages.isEmpty) {
      return const _EmptyPrompt();
    }
    return ListView.builder(
      controller: _scrollCtrl,
      padding: const EdgeInsets.all(16),
      itemCount: _messages.length + (_sending ? 1 : 0),
      itemBuilder: (context, i) {
        if (i == _messages.length) return const _TypingBubble();
        return _Bubble(message: _messages[i]);
      },
    );
  }

  Widget _errorBanner(BuildContext context) {
    return Container(
      width: double.infinity,
      color: Theme.of(context).colorScheme.errorContainer,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Text(
        _error!,
        style: TextStyle(
          color: Theme.of(context).colorScheme.onErrorContainer,
        ),
      ),
    );
  }

  Widget _generateBar(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
      child: SizedBox(
        width: double.infinity,
        child: FilledButton.icon(
          onPressed: _generating ? null : _generate,
          icon: _generating
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.auto_awesome),
          label: Text(_generating ? 'Building plan…' : 'Generate plan'),
        ),
      ),
    );
  }

  Widget _inputBar(BuildContext context) {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _inputCtrl,
                minLines: 1,
                maxLines: 4,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _send(),
                decoration: const InputDecoration(
                  hintText: 'Describe the plan you want…',
                  border: OutlineInputBorder(),
                  contentPadding:
                      EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                ),
              ),
            ),
            const SizedBox(width: 8),
            IconButton.filled(
              onPressed: _sending ? null : _send,
              icon: const Icon(Icons.send),
            ),
          ],
        ),
      ),
    );
  }
}

// -- Widgets ----------------------------------------------------------------

class _Bubble extends StatelessWidget {
  const _Bubble({required this.message});
  final ChatMessage message;

  @override
  Widget build(BuildContext context) {
    final isUser = message.isUser;
    final scheme = Theme.of(context).colorScheme;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.8,
        ),
        decoration: BoxDecoration(
          color: isUser ? scheme.primary : scheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Text(
          message.content,
          style: TextStyle(
            color: isUser ? scheme.onPrimary : scheme.onSurface,
          ),
        ),
      ),
    );
  }
}

class _TypingBubble extends StatelessWidget {
  const _TypingBubble();

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(14),
        ),
        child: const SizedBox(
          width: 20,
          height: 20,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
      ),
    );
  }
}

class _EmptyPrompt extends StatelessWidget {
  const _EmptyPrompt();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.auto_awesome,
              size: 56,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(height: 16),
            Text(
              'Describe what you want to learn',
              style: Theme.of(context).textTheme.titleMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              'e.g. "An 8-week plan to learn Python for data science, '
              '1 hour a day, beginner level."',
              style: Theme.of(context).textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _NotConfigured extends StatelessWidget {
  const _NotConfigured({required this.onConfigured});
  final VoidCallback onConfigured;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.key_off, size: 56),
            const SizedBox(height: 16),
            Text(
              'Add your AI API key first',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            const Text(
              'To generate plans with AI, save your own NVIDIA API key.',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            FilledButton.icon(
              icon: const Icon(Icons.settings),
              label: const Text('Open AI settings'),
              onPressed: () async {
                await Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const AiSettingsScreen()),
                );
                onConfigured();
              },
            ),
          ],
        ),
      ),
    );
  }
}

/// Bottom sheet previewing the generated plan; confirms import.
class _PlanPreviewSheet extends StatefulWidget {
  const _PlanPreviewSheet({required this.plan, required this.service});
  final GeneratedPlan plan;
  final AiService service;

  @override
  State<_PlanPreviewSheet> createState() => _PlanPreviewSheetState();
}

class _PlanPreviewSheetState extends State<_PlanPreviewSheet> {
  DateTime _startDate = DateTime.now();
  bool _importing = false;
  String? _error;

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _startDate,
      firstDate: now.subtract(const Duration(days: 30)),
      lastDate: now.add(const Duration(days: 365)),
    );
    if (picked != null) setState(() => _startDate = picked);
  }

  Future<void> _confirm() async {
    setState(() {
      _importing = true;
      _error = null;
    });
    try {
      await widget.service
          .confirmImport(plan: widget.plan, startDate: _startDate);
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _importing = false;
        _error = e.rowErrors.isNotEmpty ? e.rowErrors.join('\n') : e.message;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final plan = widget.plan;
    final dateLabel =
        '${_startDate.year}-${_startDate.month.toString().padLeft(2, '0')}'
        '-${_startDate.day.toString().padLeft(2, '0')}';
    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.75,
      maxChildSize: 0.95,
      builder: (context, controller) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(plan.name, style: Theme.of(context).textTheme.titleLarge),
            if (plan.description != null && plan.description!.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(plan.description!),
              ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: [
                Chip(label: Text('${plan.totalDays} days')),
                if (plan.weekCount > 0)
                  Chip(label: Text('${plan.weekCount} weeks')),
              ],
            ),
            const SizedBox(height: 8),
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.calendar_today),
              title: const Text('Start date (Day 1)'),
              subtitle: Text(dateLabel),
              trailing: TextButton(
                onPressed: _pickDate,
                child: const Text('Change'),
              ),
            ),
            const Divider(),
            Expanded(
              child: ListView.builder(
                controller: controller,
                itemCount: plan.days.length,
                itemBuilder: (context, i) {
                  final d = plan.days[i];
                  return ListTile(
                    dense: true,
                    leading: CircleAvatar(
                      radius: 14,
                      child: Text(
                        '${d.day}',
                        style: const TextStyle(fontSize: 11),
                      ),
                    ),
                    title: Text(d.task ?? d.focus ?? 'Study'),
                    subtitle: Text(
                      [
                        if (d.phase != null) d.phase,
                        if (d.difficulty != null) d.difficulty,
                      ].whereType<String>().join(' · '),
                    ),
                  );
                },
              ),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  _error!,
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.error,
                  ),
                ),
              ),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _importing ? null : _confirm,
                icon: _importing
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.check),
                label: Text(_importing ? 'Creating…' : 'Create this plan'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
