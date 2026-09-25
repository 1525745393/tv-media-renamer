import 'package:flutter/material.dart';

import 'screens/login_screen.dart';

void main() {
  runApp(const TvRenamerApp());
}

class TvRenamerApp extends StatelessWidget {
  const TvRenamerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '影视重命名助手',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueGrey),
        useMaterial3: true,
      ),
      home: const LoginScreen(),
    );
  }
}
