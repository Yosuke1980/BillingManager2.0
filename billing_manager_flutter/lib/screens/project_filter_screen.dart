import 'package:flutter/material.dart';

class ProjectFilterScreen extends StatefulWidget {
  const ProjectFilterScreen({super.key});

  @override
  State<ProjectFilterScreen> createState() => _ProjectFilterScreenState();
}

class _ProjectFilterScreenState extends State<ProjectFilterScreen> {
  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.filter_alt, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              'プロジェクトフィルタ',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text(
              'プロジェクト別のフィルタリング機能',
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}