import 'package:flutter/material.dart';

class MonitoringScreen extends StatefulWidget {
  const MonitoringScreen({super.key});

  @override
  State<MonitoringScreen> createState() => _MonitoringScreenState();
}

class _MonitoringScreenState extends State<MonitoringScreen> {
  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.monitor, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              'モニタリング',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text(
              'システム監視とファイル監視機能',
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}