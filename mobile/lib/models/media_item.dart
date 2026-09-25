/// 单个媒体文件（scan 返回项）。
class MediaItem {
  MediaItem.fromJson(Map<String, dynamic> json)
      : name = json['name'] as String? ?? '',
        path = json['path'] as String? ?? '',
        suggestedName = json['suggested_name'] as String? ?? '',
        size = json['size'] as int? ?? 0,
        analysis = (json['analysis'] as Map<String, dynamic>?) ?? {};

  final String name;
  final String path;
  final String suggestedName;
  final int size;
  final Map<String, dynamic> analysis;

  String? get mediaType => analysis['type'] as String?;

  /// 当前文件名与建议名是否一致。
  bool get needsRename => name != suggestedName;
}
