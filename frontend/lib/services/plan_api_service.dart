import 'dart:typed_data';

import 'package:intl/intl.dart';

import '../core/network/api.dart';
import '../core/network/api_client.dart';
import '../models/import_preview.dart';
import '../models/plan.dart';
import '../models/progress.dart';
import '../models/study_day.dart';
import '../models/study_status.dart';
import '../models/today.dart';
import '../models/tracker.dart';

/// All backend calls related to plans, days, progress, and trackers.
class PlanApiService {
  PlanApiService({ApiClient? client}) : _client = client ?? apiClient;

  final ApiClient _client;
  static final _dateFmt = DateFormat('yyyy-MM-dd');

  // -- Plans ---------------------------------------------------------------
  Future<List<Plan>> listPlans() async {
    final data = await _client.get('/plans') as List;
    return data
        .map((e) => Plan.fromJson((e as Map).cast<String, dynamic>()))
        .toList();
  }

  Future<Plan?> getActivePlan() async {
    final plans = await listPlans();
    return plans.isEmpty ? null : plans.first;
  }

  Future<void> deletePlan(int planId) async {
    await _client.delete('/plans/$planId');
  }

  // -- Import --------------------------------------------------------------
  Future<ImportPreview> previewImport({
    required Uint8List bytes,
    required String filename,
    required DateTime startDate,
    String? planName,
  }) async {
    final data = await _client.uploadExcel(
      '/plans/import/preview',
      bytes: bytes,
      filename: filename,
      fields: {
        'start_date': _dateFmt.format(startDate),
        if (planName != null && planName.isNotEmpty) 'plan_name': planName,
      },
    );
    return ImportPreview.fromJson((data as Map).cast<String, dynamic>());
  }

  Future<ImportSummary> importPlan({
    required Uint8List bytes,
    required String filename,
    required DateTime startDate,
    String? planName,
  }) async {
    final data = await _client.uploadExcel(
      '/plans/import',
      bytes: bytes,
      filename: filename,
      fields: {
        'start_date': _dateFmt.format(startDate),
        if (planName != null && planName.isNotEmpty) 'plan_name': planName,
      },
    );
    return ImportSummary.fromJson((data as Map).cast<String, dynamic>());
  }

  // -- Days ----------------------------------------------------------------
  Future<List<StudyDay>> listDays(int planId) async {
    final data = await _client.get('/plans/$planId/days') as List;
    return data
        .map((e) => StudyDay.fromJson((e as Map).cast<String, dynamic>()))
        .toList();
  }

  Future<StudyDay> getDay(int planId, int dayNumber) async {
    final data = await _client.get('/plans/$planId/days/$dayNumber');
    return StudyDay.fromJson((data as Map).cast<String, dynamic>());
  }

  Future<StudyDay> updateDay(
    int planId,
    int dayNumber, {
    StudyStatus? status,
    String? notes,
  }) async {
    final body = <String, dynamic>{};
    if (status != null) body['status'] = status.wire;
    if (notes != null) body['notes'] = notes;
    final data = await _client.patch(
      '/plans/$planId/days/$dayNumber',
      body: body,
    );
    return StudyDay.fromJson((data as Map).cast<String, dynamic>());
  }

  // -- Today ---------------------------------------------------------------
  Future<Today> getToday(int planId) async {
    final data = await _client.get('/plans/$planId/today');
    return Today.fromJson((data as Map).cast<String, dynamic>());
  }

  // -- Progress ------------------------------------------------------------
  Future<Progress> getProgress(int planId) async {
    final data = await _client.get('/plans/$planId/progress');
    return Progress.fromJson((data as Map).cast<String, dynamic>());
  }

  // -- Tracker -------------------------------------------------------------
  Future<Tracker?> getTracker(int studyDayId) async {
    final data = await _client.get('/study-days/$studyDayId/tracker');
    if (data == null) return null; // 204
    return Tracker.fromJson((data as Map).cast<String, dynamic>());
  }

  Future<Tracker> saveTracker(int studyDayId, Tracker tracker) async {
    final data = await _client.put(
      '/study-days/$studyDayId/tracker',
      body: tracker.toRequest(),
    );
    return Tracker.fromJson((data as Map).cast<String, dynamic>());
  }
}
