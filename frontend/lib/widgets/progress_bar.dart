import 'package:flutter/material.dart';

/// A labelled linear progress bar.
class LabeledProgressBar extends StatelessWidget {
  const LabeledProgressBar({
    super.key,
    required this.value,
    this.label,
    this.height = 10,
  });

  final double value; // 0..1
  final String? label;
  final double height;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (label != null) ...[
          Text(label!, style: Theme.of(context).textTheme.labelLarge),
          const SizedBox(height: 6),
        ],
        ClipRRect(
          borderRadius: BorderRadius.circular(height),
          child: LinearProgressIndicator(
            value: value.clamp(0.0, 1.0),
            minHeight: height,
            backgroundColor:
                Theme.of(context).colorScheme.surfaceContainerHighest,
          ),
        ),
      ],
    );
  }
}
