/// Centralized user-facing strings.
class AppStrings {
  AppStrings._();

  static const appName = 'DSA Tracker';

  // Empty states
  static const noPlanTitle = 'No DSA plan yet.';
  static const noPlanBody = 'Import your Excel plan to get started.';
  static const importPlan = 'Import Plan';

  // Import format helper
  static const importFormat = 'name,week,topic,level';
  static const importFormatLabel = 'Format: "$importFormat"';
  static const importFormatHelp =
      'Copy this format and paste it to the AI before asking it to build '
      'your Excel sheet. Or use the same column order if you create the '
      'sheet yourself. Columns: name (the task/problem), week (week number), '
      'topic (phase/focus area) and level (Easy / Medium / Hard / Mixed).';
  static const importFormatCopied = 'Format copied to clipboard';

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
