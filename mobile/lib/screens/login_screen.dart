import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../api/api_client.dart';
import 'folder_screen.dart';

/// 登录页：填写 NAS 服务地址与 API Token。
/// 凭据保存在本地（shared_preferences），下次启动自动恢复。
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _baseUrlCtrl = TextEditingController();
  final _tokenCtrl = TextEditingController();
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _restore();
  }

  Future<void> _restore() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrlCtrl.text = prefs.getString('server_url') ?? 'http://192.168.1.100:8123';
    _tokenCtrl.text = prefs.getString('api_token') ?? '';
  }

  Future<void> _save(String baseUrl, String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('server_url', baseUrl);
    await prefs.setString('api_token', token);
  }

  Future<void> _connect() async {
    final baseUrl = _baseUrlCtrl.text.trim().replaceAll(RegExp(r'/+$'), '');
    final token = _tokenCtrl.text.trim();
    if (baseUrl.isEmpty || token.isEmpty) {
      setState(() => _error = '请填写服务器地址与 Token');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = ApiClient(baseUrl: baseUrl, token: token);
      final health = await api.health();
      await _save(baseUrl, token);
      if (!mounted) return;
      Navigator.of(context).pushReplacement(MaterialPageRoute(
        builder: (_) => FolderScreen(api: api),
      ));
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('已连接 ${health['app']} v${health['version']}')));
    } on ApiException catch (e) {
      setState(() => _error = e.statusCode == 401 ? 'Token 无效或服务器配置错误' : e.message);
    } catch (_) {
      setState(() => _error = '无法连接服务器（请检查地址与网络）');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('连接 NAS 服务')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Icon(Icons.movie_filter, size: 64, color: Colors.blueGrey),
            const SizedBox(height: 8),
            const Text('影视文件智能重命名工具',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 24),
            TextField(
              controller: _baseUrlCtrl,
              decoration: const InputDecoration(
                labelText: 'NAS 服务地址',
                hintText: 'http://192.168.1.100:8123',
                prefixIcon: Icon(Icons.dns),
              ),
              keyboardType: TextInputType.url,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _tokenCtrl,
              decoration: const InputDecoration(
                labelText: 'API Token',
                prefixIcon: Icon(Icons.key),
              ),
              obscureText: true,
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: TextStyle(color: Colors.red[700])),
            ],
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: _loading ? null : _connect,
              icon: _loading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.link),
              label: const Text('连接并扫描'),
            ),
          ],
        ),
      ),
    );
  }
}
