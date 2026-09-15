import 'package:intl/intl.dart';

import '../core/network/api.dart';
import '../core/network/api_client.dart';
import '../models/ai.dart';
import '../models/import_preview.dart';

/// Backend calls for the AI study-plan feature.
///
/// Two-step flow:
///   1. [chat] — conversational planning (repeat as needed).
///   2. [generatePlan] — convert the agreed plan into a structured preview.
///   3. [confirmImport] — user confirms; the plan is created & auto-selected.
class AiService {
  AiService({ApiClient? client}) : _client = client ?? apiClient;

  final ApiClient _client;
  static final _dateFmt = DateFormat('yyyy-MM-dd');

  // -- Settings ------------------------------------------------------------
  Future<AiSettings> getSettings() async {
    final data = await _client.get('/ai/settings');
    return AiSettings.fromJson((data as Map).cast<String, dynamic>());
  }

  Future<AiSettings> saveApiKey({
    required String apiKey,
    String provider = 'nvidia',
    String? model,
  }) async {
    final data = await _client.put(
      '/ai/settings',
      body: {
        'api_key': apiKey,
        'provider': provider,
        if (model != null && model.isNotEmpty) 'model': model,
      },
    );
    return AiSettings.fromJson((data as Map).cast<String, dynamic>());
  }

  Future<void> deleteApiKey() async {
    await _client.delete('/ai/settings');
  }

  // -- Chat ----------------------------------------------------------------
  /// Send the user's message with prior [history] for context. Returns the
  /// assistant's reply text.
  Future<String> chat({
    required String message,
    required List<ChatMessage> history,
  }) async {
    final data = await _client.post(
      '/ai/chat',
      body: {
        'message': message,
        'history': history.map((m) => m.toJson()).toList(),
      },
    );
    return (data as Map).cast<String, dynamic>()['reply'] as String;
  }

  // -- Structured generation ----------------------------------------------
  /// Ask the AI to turn the agreed conversation into a structured plan.
  Future<GeneratedPlan> generatePlan({
    required List<ChatMessage> conversation,
    String? instruction,
  }) async {
    final data = await _client.post(
      '/ai/generate',
      body: {
        'conversation': conversation.map((m) => m.toJson()).toList(),
        if (instruction != null && instruction.isNotEmpty)
          'instruction': instruction,
      },
    );
    return GeneratedPlan.fromJson((data as Map).cast<String, dynamic>());
  }

  // -- Confirm & import ----------------------------------------------------
  /// Confirm a generated plan and import it (creates a real, selected plan).
  Future<ImportSummary> confirmImport({
    required GeneratedPlan plan,
    required DateTime startDate,
  }) async {
    final data = await _client.post(
      '/ai/confirm',
      body: {
        'plan': plan.toJson(),
        'start_date': _dateFmt.format(startDate),
      },
    );
    final summary = (data as Map).cast<String, dynamic>()['summary'];
    return ImportSummary.fromJson((summary as Map).cast<String, dynamic>());
  }
}
