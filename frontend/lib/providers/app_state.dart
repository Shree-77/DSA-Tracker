import 'package:flutter/foundation.dart';

import '../core/network/api_exception.dart';
import '../models/plan.dart';
import '../models/progress.dart';
import '../models/study_day.dart';
import '../models/study_status.dart';
import '../models/today.dart';
import '../services/cache_service.dart';
import '../services/plan_api_service.dart';

enum LoadState { idle, loading, ready, error, empty }

/// Central app state: active plan, today, days, and progress.
///
/// Uses [ChangeNotifier] (via Provider) — the simplest maintainable option.
/// Falls back to cached data when the backend is unreachable, and exposes an
/// [offline] flag so the UI can show a banner.
class AppState extends ChangeNotifier {
  AppState({PlanApiService? api, CacheService? cache})
      : _api = api ?? PlanApiService(),
        _cache = cache ?? CacheService();

  final PlanApiService _api;
  final CacheService _cache;

  LoadState state = LoadState.idle;
  String? errorMessage;
  bool offline = false;

  Plan? plan;
  Today? today;
  Progress? progress;
  List<StudyDay> days = [];

  /// All of the user's plans (for the switcher). Loaded lazily.
  List<Plan> allPlans = [];

  /// True while a plan switch is in flight (drives a spinner in the switcher).
  bool switching = false;

  bool get hasPlan => plan != null;

  /// Full refresh: active plan -> today, days, progress.
  Future<void> bootstrap() async {
    state = LoadState.loading;
    notifyListeners();

    try {
      allPlans = await _api.listPlans();
      plan = _pickSelected(allPlans);
      if (plan == null) {
        state = LoadState.empty;
        offline = false;
        notifyListeners();
        return;
      }
      await _cache.savePlan(plan!.toJson());
      await _loadPlanData();
      offline = false;
      state = LoadState.ready;
    } on ApiException catch (e) {
      await _tryLoadFromCache(e);
    } catch (e) {
      errorMessage = e.toString();
      state = LoadState.error;
    }
    notifyListeners();
  }

  /// Clear all in-memory + cached plan data. Called on sign-out so the next
  /// user never sees the previous user's cached plan.
  void reset() {
    plan = null;
    today = null;
    progress = null;
    days = [];
    allPlans = [];
    offline = false;
    switching = false;
    errorMessage = null;
    state = LoadState.idle;
    _cache.clear();
    notifyListeners();
  }

  static Plan? _pickSelected(List<Plan> plans) {
    if (plans.isEmpty) return null;
    for (final p in plans) {
      if (p.isSelected) return p;
    }
    return plans.first;
  }

  /// Reload the list of all plans (e.g. before opening the switcher).
  Future<void> refreshPlans() async {
    try {
      allPlans = await _api.listPlans();
      notifyListeners();
    } on ApiException {
      offline = true;
      notifyListeners();
    }
  }

  /// Fetch completed plans for the history screen.
  Future<List<Plan>> loadHistory() => _api.planHistory();

  /// Switch the current plan and reload everything for it.
  ///
  /// No-op when the target is already active. Non-destructive on the backend.
  Future<void> switchPlan(int planId) async {
    if (plan?.id == planId) return;
    switching = true;
    notifyListeners();
    try {
      final selected = await _api.selectPlan(planId);
      plan = selected;
      await _cache.savePlan(plan!.toJson());
      await _loadPlanData();
      // Reflect the new selection flags across the cached list.
      allPlans = [
        for (final p in allPlans)
          p.id == planId
              ? selected
              : (p.isSelected ? _copyDeselected(p) : p),
      ];
      offline = false;
      state = LoadState.ready;
    } on ApiException catch (e) {
      errorMessage = e.message;
      offline = true;
    } finally {
      switching = false;
      notifyListeners();
    }
  }

  static Plan _copyDeselected(Plan p) => Plan(
        id: p.id,
        name: p.name,
        totalDays: p.totalDays,
        status: p.status,
        isSelected: false,
        description: p.description,
        completedAt: p.completedAt,
        createdAt: p.createdAt,
      );

  Future<void> _loadPlanData() async {
    final results = await Future.wait([
      _api.getToday(plan!.id),
      _api.getProgress(plan!.id),
      _api.listDays(plan!.id),
    ]);
    today = results[0] as Today;
    progress = results[1] as Progress;
    days = results[2] as List<StudyDay>;

    await _cache.saveToday(today!.toJson());
    await _cache.saveProgress(_progressToCache(progress!));
    await _cache.saveDays(days.map((d) => d.toJson()).toList());
  }

  Future<void> _tryLoadFromCache(ApiException e) async {
    final cachedPlan = await _cache.readPlan();
    if (cachedPlan == null) {
      errorMessage = e.message;
      state = LoadState.error;
      return;
    }
    plan = Plan.fromJson(cachedPlan);
    final cachedToday = await _cache.readToday();
    final cachedDays = await _cache.readDays();
    if (cachedToday != null) today = Today.fromJson(cachedToday);
    if (cachedDays != null) {
      days = cachedDays.map(StudyDay.fromJson).toList();
    }
    offline = true;
    state = LoadState.ready;
  }

  /// Refresh just today + progress after a mutation (keeps UI in sync).
  Future<void> refreshTodayAndProgress() async {
    if (plan == null) return;
    try {
      final results = await Future.wait([
        _api.getToday(plan!.id),
        _api.getProgress(plan!.id),
        _api.listDays(plan!.id),
      ]);
      today = results[0] as Today;
      progress = results[1] as Progress;
      days = results[2] as List<StudyDay>;
      offline = false;
      notifyListeners();
    } on ApiException {
      offline = true;
      notifyListeners();
    }
  }

  /// Update a day's status and refresh derived state.
  Future<void> updateDayStatus(int dayNumber, StudyStatus status) async {
    if (plan == null) return;
    await _api.updateDay(plan!.id, dayNumber, status: status);
    await refreshTodayAndProgress();
  }

  Future<void> deletePlan() async {
    if (plan == null) return;
    final deletedId = plan!.id;
    await _api.deletePlan(deletedId);

    // The backend promotes another plan to "selected" when the active one is
    // deleted. Reload so we land on that plan instead of an empty screen.
    allPlans = await _api.listPlans();
    plan = _pickSelected(allPlans);
    if (plan == null) {
      await _cache.clear();
      today = null;
      progress = null;
      days = [];
      state = LoadState.empty;
      notifyListeners();
      return;
    }
    await _cache.savePlan(plan!.toJson());
    await _loadPlanData();
    state = LoadState.ready;
    notifyListeners();
  }

  /// The "current" day = first non-DONE day (used by the Plan screen marker).
  int? get currentDayNumber {
    for (final d in days) {
      if (d.status != StudyStatus.done) return d.dayNumber;
    }
    return null;
  }

  Map<String, dynamic> _progressToCache(Progress p) => {
        'total_days': p.totalDays,
        'completed_days': p.completedDays,
        'remaining_days': p.remainingDays,
        'completion_percentage': p.completionPercentage,
        'current_streak': p.currentStreak,
        'longest_streak': p.longestStreak,
        'total_study_hours': p.totalStudyHours,
        'problems_attempted': p.problemsAttempted,
        'solved_alone': p.solvedAlone,
        'needed_hint': p.neededHint,
        'needed_solution': p.neededSolution,
        'average_confidence': p.averageConfidence,
        'weekly': p.weekly
            .map((w) => {
                  'week_number': w.weekNumber,
                  'phase': w.phase,
                  'total': w.total,
                  'completed': w.completed,
                })
            .toList(),
        'difficulty': p.difficulty
            .map((d) => {
                  'difficulty': d.difficulty,
                  'total': d.total,
                  'completed': d.completed,
                })
            .toList(),
      };
}
