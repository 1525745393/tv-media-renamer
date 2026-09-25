import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../models/media_item.dart';
import 'rename_screen.dart';

/// 目录页：扫描 NAS 目录，列出媒体文件与建议名，勾选后进入重命名。
class FolderScreen extends StatefulWidget {
  const FolderScreen({super.key, required this.api, this.initialPath = '/'});

  final ApiClient api;
  final String initialPath;

  @override
  State<FolderScreen> createState() => _FolderScreenState();
}

class _FolderScreenState extends State<FolderScreen> {
  late final TextEditingController _pathCtrl =
      TextEditingController(text: widget.initialPath);
  List<MediaItem> _files = [];
  final Set<String> _selected = {};
  bool _loading = false;
  String? _error;

  Future<void> _scan() async {
    setState(() {
      _loading = true;
      _error = null;
      _selected.clear();
    });
    try {
      final data =
          await widget.api.scan(_pathCtrl.text.trim(), recursive: true);
      setState(() {
        _files = (data['files'] as List)
            .map((e) => MediaItem.fromJson(e as Map<String, dynamic>))
            .toList();
      });
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } catch (_) {
      setState(() => _error = '扫描失败（请检查目录与权限）');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void initState() {
    super.initState();
    _scan();
  }

  void _goRename() {
    if (_selected.isEmpty) return;
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => RenameScreen(
        api: widget.api,
        path: _pathCtrl.text.trim(),
        items: _files.where((f) => _selected.contains(f.name)).toList(),
      ),
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('媒体目录')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _pathCtrl,
                    decoration: const InputDecoration(
                      labelText: 'NAS 目录',
                      prefixIcon: Icon(Icons.folder_open),
                      isDense: true,
                    ),
                    onSubmitted: (_) => _scan(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: _loading ? null : _scan,
                  icon: _loading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.refresh),
                ),
              ],
            ),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Text(_error!,
                  style: TextStyle(color: Colors.red[700], fontSize: 13)),
            ),
          Expanded(
            child: _files.isEmpty
                ? const Center(child: Text('无媒体文件（支持 mp4/mkv/avi 等）'))
                : ListView.builder(
                    itemCount: _files.length,
                    itemBuilder: (context, i) {
                      final f = _files[i];
                      final checked = _selected.contains(f.name);
                      return CheckboxListTile(
                        value: checked,
                        onChanged: (v) => setState(() {
                          if (v == true) {
                            _selected.add(f.name);
                          } else {
                            _selected.remove(f.name);
                          }
                        }),
                        title: Text(
                          f.name,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        subtitle: Text(
                          f.needsRename
                              ? '建议: ${f.suggestedName}'
                              : '名称已规范',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: f.needsRename
                                ? Colors.orange[800]
                                : Colors.green[700],
                          ),
                        ),
                        secondary: _typeIcon(f.mediaType),
                      );
                    },
                  ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed:
                      _selected.isEmpty || _loading ? null : _goRename,
                  icon: const Icon(Icons.drive_file_rename_outline),
                  label: Text('重命名选中（${_selected.length}）'),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _typeIcon(String? type) {
    final icon = switch (type) {
      'tv' => Icons.live_tv,
      'movie' => Icons.movie,
      'special' => Icons.star,
      _ => Icons.insert_drive_file,
    };
    return Icon(icon, color: Colors.blueGrey);
  }
}
