import 'package:flutter_test/flutter_test.dart';

import 'package:dsa_tracker/models/plan.dart';
import 'package:dsa_tracker/models/progress.dart';
import 'package:dsa_tracker/models/study_day.dart';
import 'package:dsa_tracker/models/study_status.dart';
import 'package:dsa_tracker/models/today.dart';

void main() {
  group('Plan.fromJson', () {
    test('parses status, selection and completion', () {
      final plan = Plan.fromJson({
        'id': 3,
        'name': 'DSA Sprint',
        'description': null,
        'total_days': 56,
        'status': 'COMPLETED',
        'is_selected': true,
        'completed_at': '2024-03-01T10:00:00Z',
        'created_at': '2024-01-01T00:00:00Z',
      });
      expect(plan.status, PlanStatus.completed);
      expect(plan.isCompleted, isTrue);
      expect(plan.isSelected, isTrue);
      expect(plan.completedAt, isNotNull);
    });

    test('defaults to active/unselected when fields are absent', () {
      final plan = Plan.fromJson({
        'id': 1,
        'name': 'Legacy',
        'total_days': 10,
      });
      expect(plan.status, PlanStatus.active);
      expect(plan.isSelected, isFalse);
      expect(plan.completedAt, isNull);
    });

    test('unknown status falls back to active', () {
      expect(PlanStatus.fromWire('WAT'), PlanStatus.active);
      expect(PlanStatus.fromWire(null), PlanStatus.active);
    });
  });

  group('StudyStatus', () {
    test('parses wire values', () {
      expect(StudyStatus.fromWire('DONE'), StudyStatus.done);
      expect(StudyStatus.fromWire('IN_PROGRESS'), StudyStatus.inProgress);
      expect(StudyStatus.fromWire(null), StudyStatus.notStarted);
      expect(StudyStatus.fromWire('garbage'), StudyStatus.notStarted);
    });
  });

  group('StudyDay.fromJson', () {
    test('deserialises the canonical response', () {
      final day = StudyDay.fromJson({
        'id': 8,
        'plan_id': 1,
        'day_number': 8,
        'week_number': 2,
        'phase': 'Recursive Sorting',
        'focus': 'Bubble Sort',
        'task': 'Recursive Bubble Sort',
        'difficulty': 'Easy',
        'status': 'NOT_STARTED',
        'scheduled_date': '2026-09-22',
        'completed_at': null,
        'notes': null,
      });

      expect(day.dayNumber, 8);
      expect(day.phase, 'Recursive Sorting');
      expect(day.status, StudyStatus.notStarted);
      expect(day.scheduledDate, DateTime.parse('2026-09-22'));
    });
  });

  group('Today.fromJson', () {
    test('parses active state with upcoming', () {
      final today = Today.fromJson({
        'state': 'active',
        'day': {
          'id': 8,
          'plan_id': 1,
          'day_number': 8,
          'status': 'NOT_STARTED',
        },
        'upcoming': [
          {'id': 9, 'plan_id': 1, 'day_number': 9, 'status': 'NOT_STARTED'},
        ],
        'total_days': 56,
        'completed_days': 7,
        'completion_percentage': 12.5,
      });

      expect(today.state, 'active');
      expect(today.day?.dayNumber, 8);
      expect(today.upcoming.length, 1);
      expect(today.completionPercentage, 12.5);
    });
  });

  group('Progress.fromJson', () {
    test('parses stats and streaks', () {
      final p = Progress.fromJson({
        'total_days': 56,
        'completed_days': 12,
        'remaining_days': 44,
        'completion_percentage': 21.43,
        'current_streak': 5,
        'longest_streak': 7,
        'total_study_hours': 24.5,
        'problems_attempted': 31,
        'solved_alone': 24,
        'needed_hint': 6,
        'needed_solution': 1,
        'average_confidence': 4.1,
        'weekly': [
          {'week_number': 1, 'phase': 'Recursion', 'total': 7, 'completed': 7},
        ],
        'difficulty': [
          {'difficulty': 'Easy', 'total': 10, 'completed': 5},
        ],
      });

      expect(p.currentStreak, 5);
      expect(p.longestStreak, 7);
      expect(p.averageConfidence, 4.1);
      expect(p.weekly.first.ratio, 1.0);
      expect(p.difficulty.first.difficulty, 'Easy');
    });
  });
}
