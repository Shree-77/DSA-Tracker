import 'package:flutter/foundation.dart';

import '../core/network/api_exception.dart';
import '../models/study_day.dart';
import '../models/study_status.dart';
import '../models/tracker.dart';
import '../services/plan_api_service.dart';

enum DayLoad { loading, ready, error }

/// State for a single day-detail screen: the day + its tracker + edits.
class DayDetailProvider extends ChangeNotifier {
  DayDetailProvider({
    required this.planId,
    required this.dayNumber,
    PlanApiService? api,
  }) : _api = api ?? PlanApiService();

  final int planId;
  final int dayNumber;
  final PlanApiService _api;

  DayLoad state = DayLoad.loading;
  String? errorMessage;

  StudyDay? day;
  Tracker tracker = Tracker.empty();
  String notes = '';
  bool saving = false;

  Future<void> load() async {
    state = DayLoad.loading;
    notifyListeners();
    try {
      day = await _api.getDay(planId, dayNumber);
      notes = day?.notes ?? '';
      final existing = await _api.getTracker(day!.id);
      tracker = existing ?? Tracker.empty();
      state = DayLoad.ready;
    } on ApiException catch (e) {
      errorMessage = e.message;
      state = DayLoad.error;
    } catch (e) {
      errorMessage = e.toString();
      state = DayLoad.error;
    }
    notifyListeners();
  }

  void setStatusLocal(StudyStatus status) {
    if (day == null) return;
    day = StudyDay(
      id: day!.id,
      planId: day!.planId,
      dayNumber: day!.dayNumber,
      weekNumber: day!.weekNumber,
      phase: day!.phase,
      focus: day!.focus,
      task: day!.task,
      difficulty: day!.difficulty,
      status: status,
      scheduledDate: day!.scheduledDate,
      completedAt: day!.completedAt,
      notes: day!.notes,
    );
    notifyListeners();
  }

  void updateTracker(Tracker t) {
    tracker = t;
    notifyListeners();
  }

  void updateNotes(String value) {
    notes = value;
  }

  /// Persist status, notes, and tracker. Returns true on success.
  Future<bool> save({StudyStatus? overrideStatus}) async {
    if (day == null) return false;
    saving = true;
    notifyListeners();
    try {
      final status = overrideStatus ?? day!.status;
      day = await _api.updateDay(planId, dayNumber,
          status: status, notes: notes);
      tracker = await _api.saveTracker(day!.id, tracker);
      saving = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      errorMessage = e.message;
      saving = false;
      notifyListeners();
      return false;
    }
  }
}
