import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../models/media_item.dart';

/// 重命名页：预览选中文件的建议名 → 确认执行（dry_run → 实际执行）。
class RenameScreen extends StatefulWidget {
  const RenameScreen({
    super.key,
    required this.api,
    required this.path,
    required this.items,
  });

  final ApiClient api;
  final String path;
  final List<MediaItem> items;

  @override
  State<RenameScreen> createState() => _RenameScreenState();
}

class _RenameScreenState extends State<RenameScreen> {
  late final Map<String, String> _newNames = {
    for (final f in widget.items)
      (f.relPath.isNotEmpty ? f.relPath : f.name): f.suggestedName,
  };
  bool _executing = false;
  String? _resultMessage;

  Future<void> _run({required bool dryRun}) async {
    setState(() {
      _executing = true;
      _resultMessage = null;
    });
    try {
      final renames = _newNames.entries
          .where((e) => e.key != e.value)
          .map((e) => {'old': e.key, 'new': e.value})
          .toList();
      final data = await widget.api
          .rename(widget.path, renames, dryRun: dryRun);
      final results = (data['results'] as List).cast<Map<String, dynamic>>();
      final ok = results.where((r) => r['ok'] == true).length;
      setState(() {
        _resultMessage = dryRun
            ? '预览完成：$ok/${results.length} 项可重命名'
            : '执行完成：$ok/${results.length} 项成功（原文件已备份）';
      });
    } on ApiException catch (e) {
      setState(() => _resultMessage = '失败：${e.message}');
    } catch (_) {
      setState(() => _resultMessage = '网络错误');
    } finally {
      if (mounted) setState(() => _executing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final changed = _newNames.entries.where((e) => e.key != e.value).length;
    return Scaffold(
      appBar: AppBar(title: const Text('重命名预览')),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              itemCount: widget.items.length,
              itemBuilder: (context, i) {
                final f = widget.items[i];
                final key = f.relPath.isNotEmpty ? f.relPath : f.name;
                final newName = _newNames[key] ?? f.suggestedName;
                final isSame = f.name == newName;
                return ListTile(
                  leading: isSame
                      ? const Icon(Icons.check_circle, color: Colors.green)
                      : const Icon(Icons.arrow_forward, color: Colors.orange),
                  title: Text(f.name,
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                  subtitle: Text(isSame ? '无需修改' : newName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: isSame ? Colors.grey : Colors.blue[800],
                      )),
                );
              },
            ),
          ),
          if (_resultMessage != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(_resultMessage!,
                  style: TextStyle(color: Colors.teal[800], fontSize: 13)),
            ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: _executing || changed == 0
                          ? null
                          : () => _run(dryRun: true),
                      child: const Text('预览'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton.icon(
                      onPressed: _executing || changed == 0
                          ? null
                          : () async {
                              final confirm = await showDialog<bool>(
                                context: context,
                                builder: (_) => AlertDialog(
                                  title: const Text('确认执行重命名？'),
                                  content: Text('将重命名 $changed 个文件，原文件自动备份到服务器。'),
                                  actions: [
                                    TextButton(
                                        onPressed: () =>
                                            Navigator.pop(context, false),
                                        child: const Text('取消')),
                                    FilledButton(
                                        onPressed: () =>
                                            Navigator.pop(context, true),
                                        child: const Text('执行')),
                                  ],
                                ),
                              );
                              if (confirm == true) {
                                await _run(dryRun: false);
                              }
                            },
                      icon: _executing
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.check),
                      label: const Text('执行重命名'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
