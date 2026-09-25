import 'dart:convert';

import 'package:http/http.dart' as http;

/// NAS 端 API 客户端：封装全部后端接口。
class ApiClient {
  ApiClient({required this.baseUrl, required this.token});

  final String baseUrl;
  final String token;

  Uri _uri(String path, [Map<String, String>? query]) =>
      Uri.parse('$baseUrl$path').replace(queryParameters: query);

  Map<String, String> get _headers => {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      };

  Future<Map<String, dynamic>> _getJson(String path,
      [Map<String, String>? query]) async {
    final resp =
        await http.get(_uri(path, query), headers: _headers).timeout(
              const Duration(seconds: 15),
            );
    if (resp.statusCode != 200) {
      throw ApiException(resp.statusCode, _detail(resp.body));
    }
    return jsonDecode(utf8.decode(resp.bodyBytes)) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> _postJson(
      String path, Map<String, dynamic> body) async {
    final resp = await http
        .post(_uri(path), headers: _headers, body: jsonEncode(body))
        .timeout(const Duration(seconds: 30));
    if (resp.statusCode != 200) {
      throw ApiException(resp.statusCode, _detail(resp.body));
    }
    return jsonDecode(utf8.decode(resp.bodyBytes)) as Map<String, dynamic>;
  }

  String _detail(String body) {
    try {
      final d = jsonDecode(body);
      return d is Map && d['detail'] != null ? d['detail'].toString() : body;
    } catch (_) {
      return body;
    }
  }

  /// 健康检查：验证服务器与 token。
  Future<Map<String, dynamic>> health() => _getJson('/api/health');

  /// 解析单个文件名。
  Future<Map<String, dynamic>> analyze(String filename,
          {String folder = ''}) =>
      _getJson('/api/analyze', {'filename': filename, 'folder': folder});

  /// 扫描目录，返回媒体文件列表（含建议名）。
  Future<Map<String, dynamic>> scan(String path,
          {bool recursive = true}) =>
      _getJson('/api/scan', {'path': path, 'recursive': '$recursive'});

  /// 重命名预览（不执行）。
  Future<Map<String, dynamic>> renamePreview(
          String path, List<String> filenames) =>
      _postJson('/api/rename-preview',
          {'path': path, 'filenames': filenames});

  /// 执行重命名（dryRun 默认 true 仅预览）。
  Future<Map<String, dynamic>> rename(String path,
      List<Map<String, String>> renames,
      {bool dryRun = true}) {
    return _postJson('/api/rename',
        {'path': path, 'renames': renames, 'dry_run': dryRun});
  }
}

class ApiException implements Exception {
  ApiException(this.statusCode, this.message);

  final int statusCode;
  final String message;

  @override
  String toString() => 'HTTP $statusCode: $message';
}
