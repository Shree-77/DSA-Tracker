/// Centralized user-facing strings.
class AppStrings {
  AppStrings._();

  static const appName = 'Study Tracker';

  // Empty states
  static const noPlanTitle = 'No study plan yet.';
  static const noPlanBody = 'Import your Excel plan to get started.';
  static const importPlan = 'Import Plan';

  // Import format helper
  static const importFormatLabel = 'Excel format required for import';

  /// Prompt to copy and paste to an AI tool (ChatGPT, etc.) so it generates
  /// the workbook using the exact columns our backend parser understands.
  /// Keep this in sync with `PLAN_COLUMN_ALIASES` / `FIELD_LABELS` in
  /// backend/app/utils/excel_parser.py.
  static const importFormat = '''
Create an Excel (.xlsx) study plan with a sheet named "Study Plan" using exactly these columns, in this order:

Day | Week | Phase | Focus | Problems / Task | Difficulty | Status | Completed Date | Notes

Rules:
- Day: required, a positive whole number, unique per row (1, 2, 3, ...).
- Week: whole number (e.g. 1, 2, 3).
- Phase: the topic/module name for that day (e.g. "Recursion").
- Focus: the subtopic/focus area (e.g. "Backtracking basics").
- Problems / Task: the task or problems to complete that day.
- Difficulty: one of Easy, Medium, Hard, or Mixed.
- Status: one of Not Started, In Progress, Done, or Skipped.
- Completed Date: leave blank unless the day is already done (format YYYY-MM-DD).
- Notes: optional free text.

Generate one row per study day, ordered by Day.''';

  static const importFormatHelp =
      'Copy this prompt and paste it into an AI tool (ChatGPT, etc.) to '
      'generate your Excel sheet automatically. Prefer to build it yourself? '
      'Use the sample table below as a visual guide — same column names, '
      'same order.';
  static const importFormatCopied = 'Prompt copied to clipboard';

  /// A small, human-readable sample table users can copy as a starting
  /// point if they want to build the spreadsheet manually instead of using
  /// an AI tool. Column order matches `importFormat` / the backend parser.
  static const importSampleTable = '''
Day  Week  Phase       Focus              Problems / Task              Difficulty  Status        Completed Date  Notes
1    1     Recursion   Basics             Reverse a string recursively Easy        Done          2024-01-01      Warm-up
2    1     Recursion   Backtracking       N-Queens problem             Medium      In Progress                   
3    1     Trees       Binary Tree Intro  Implement BST insert/search  Easy        Not Started                  ''';

  // Existing plan
  static const replacesExistingPlan =
      'Importing a new plan replaces your current plan and its progress.';

  // Error states
  static const genericError = 'Something went wrong.';
  static const retry = 'Retry';

  // Navigation
  static const home = 'Home';
  static const plan = 'Plan';
  static const progress = 'Progress';
  static const settings = 'Settings';
}
