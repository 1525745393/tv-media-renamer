#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作历史系统 - 影视文件重命名工具 v1.3
完善的历史记录和撤销重做功能
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import shutil

logger = logging.getLogger(__name__)

class OperationType(Enum):
    """操作类型枚举"""
    RENAME = "rename"
    MOVE = "move"
    DELETE = "delete"
    BACKUP = "backup"
    BATCH_OPERATION = "batch_operation"
    SCAN = "scan"
    ANALYZE = "analyze"

@dataclass
class OperationRecord:
    """操作记录数据类"""
    id: str
    operation_type: OperationType
    timestamp: datetime
    description: str
    original_path: str
    new_path: Optional[str] = None
    file_size: int = 0
    file_hash: str = ""
    metadata: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: str = ""
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class EnhancedOperationHistory:
    """增强的操作历史管理器"""
    
    def __init__(self, history_file: str = "operation_history.json", max_history: int = 1000):
        self.history_file = history_file
        self.max_history = max_history
        self.operations: List[OperationRecord] = []
        self.current_index = -1
        self.load_history()
    
    def add_operation(self, operation_type: OperationType, original_path: str, 
                     new_path: Optional[str] = None, description: str = "", 
                     metadata: Optional[Dict[str, Any]] = None, success: bool = True, 
                     error_message: str = "") -> str:
        """添加操作记录"""
        try:
            # 生成操作ID
            operation_id = self._generate_operation_id()
            
            # 获取文件信息
            file_size = 0
            file_hash = ""
            if os.path.exists(original_path):
                file_size = os.path.getsize(original_path)
                file_hash = self._calculate_file_hash(original_path)
            
            # 创建操作记录
            operation = OperationRecord(
                id=operation_id,
                operation_type=operation_type,
                timestamp=datetime.now(),
                description=description,
                original_path=original_path,
                new_path=new_path,
                file_size=file_size,
                file_hash=file_hash,
                metadata=metadata or {},
                success=success,
                error_message=error_message
            )
            
            # 清除当前位置之后的历史（撤销后添加新操作）
            if self.current_index < len(self.operations) - 1:
                self.operations = self.operations[:self.current_index + 1]
            
            # 添加新操作
            self.operations.append(operation)
            self.current_index = len(self.operations) - 1
            
            # 限制历史记录数量
            if len(self.operations) > self.max_history:
                self.operations = self.operations[-self.max_history:]
                self.current_index = len(self.operations) - 1
            
            # 保存历史记录
            self.save_history()
            
            logger.info(f"添加操作记录: {operation_type.value} - {description}")
            return operation_id
            
        except Exception as e:
            logger.error(f"添加操作记录失败: {e}")
            raise
    
    def undo_last_operation(self) -> Optional[OperationRecord]:
        """撤销最后一个操作"""
        if not self.can_undo():
            return None
        
        try:
            operation = self.operations[self.current_index]
            
            # 执行撤销操作
            if self._undo_operation(operation):
                self.current_index -= 1
                self.save_history()
                logger.info(f"撤销操作成功: {operation.operation_type.value} - {operation.description}")
                return operation
            else:
                logger.error(f"撤销操作失败: {operation.operation_type.value}")
                return None
                
        except Exception as e:
            logger.error(f"撤销操作异常: {e}")
            return None
    
    def redo_last_operation(self) -> Optional[OperationRecord]:
        """重做最后一个操作"""
        if not self.can_redo():
            return None
        
        try:
            self.current_index += 1
            operation = self.operations[self.current_index]
            
            # 执行重做操作
            if self._redo_operation(operation):
                self.save_history()
                logger.info(f"重做操作成功: {operation.operation_type.value} - {operation.description}")
                return operation
            else:
                # 重做失败，回退索引
                self.current_index -= 1
                logger.error(f"重做操作失败: {operation.operation_type.value}")
                return None
                
        except Exception as e:
            logger.error(f"重做操作异常: {e}")
            self.current_index -= 1
            return None
    
    def can_undo(self) -> bool:
        """检查是否可以撤销"""
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """检查是否可以重做"""
        return self.current_index < len(self.operations) - 1
    
    def get_undo_info(self) -> Optional[Dict[str, Any]]:
        """获取撤销操作信息"""
        if not self.can_undo():
            return None
        
        operation = self.operations[self.current_index]
        return {
            'operation_type': operation.operation_type.value,
            'description': operation.description,
            'timestamp': operation.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_redo_info(self) -> Optional[Dict[str, Any]]:
        """获取重做操作信息"""
        if not self.can_redo():
            return None
        
        operation = self.operations[self.current_index + 1]
        return {
            'operation_type': operation.operation_type.value,
            'description': operation.description,
            'timestamp': operation.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_operation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取操作历史"""
        history = []
        start_index = max(0, len(self.operations) - limit)
        
        for i in range(start_index, len(self.operations)):
            operation = self.operations[i]
            history.append({
                'id': operation.id,
                'operation_type': operation.operation_type.value,
                'timestamp': operation.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'description': operation.description,
                'original_path': operation.original_path,
                'new_path': operation.new_path,
                'success': operation.success,
                'can_undo': i <= self.current_index,
                'can_redo': i > self.current_index
            })
        
        return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取操作统计信息"""
        stats = {
            'total_operations': len(self.operations),
            'successful_operations': 0,
            'failed_operations': 0,
            'operation_types': {},
            'recent_operations': 0,
            'undo_available': self.can_undo(),
            'redo_available': self.can_redo()
        }
        
        # 统计操作类型和成功率
        for operation in self.operations:
            op_type = operation.operation_type.value
            stats['operation_types'][op_type] = stats['operation_types'].get(op_type, 0) + 1
            
            if operation.success:
                stats['successful_operations'] += 1
            else:
                stats['failed_operations'] += 1
        
        # 统计最近操作（24小时内）
        recent_time = datetime.now().timestamp() - 24 * 3600
        for operation in self.operations:
            if operation.timestamp.timestamp() > recent_time:
                stats['recent_operations'] += 1
        
        return stats
    
    def get_history_summary(self) -> Dict[str, Any]:
        """获取历史记录摘要"""
        stats = self.get_statistics()
        return {
            'total_operations': stats['total_operations'],
            'successful_operations': stats['successful_operations'],
            'failed_operations': stats['failed_operations'],
            'can_undo': self.can_undo(),
            'can_redo': self.can_redo(),
            'recent_operations': stats['recent_operations']
        }
    
    def clear_history(self) -> None:
        """清除历史记录"""
        self.operations.clear()
        self.current_index = -1
        self.save_history()
        logger.info("操作历史已清除")
    
    def export_history(self, export_file: str) -> bool:
        """导出历史记录"""
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'total_operations': len(self.operations),
                'operations': [asdict(op) for op in self.operations]
            }
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"历史记录已导出到: {export_file}")
            return True
            
        except Exception as e:
            logger.error(f"导出历史记录失败: {e}")
            return False
    
    def import_history(self, import_file: str) -> bool:
        """导入历史记录"""
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 验证导入数据
            if 'operations' not in import_data:
                raise ValueError("无效的历史记录文件格式")
            
            # 转换操作记录
            imported_operations = []
            for op_data in import_data['operations']:
                # 转换时间戳
                if isinstance(op_data['timestamp'], str):
                    op_data['timestamp'] = datetime.fromisoformat(op_data['timestamp'])
                
                # 转换操作类型
                op_data['operation_type'] = OperationType(op_data['operation_type'])
                
                # 创建操作记录
                operation = OperationRecord(**op_data)
                imported_operations.append(operation)
            
            # 合并历史记录
            self.operations.extend(imported_operations)
            self.current_index = len(self.operations) - 1
            
            # 限制历史记录数量
            if len(self.operations) > self.max_history:
                self.operations = self.operations[-self.max_history:]
                self.current_index = len(self.operations) - 1
            
            self.save_history()
            logger.info(f"历史记录已导入: {len(imported_operations)} 个操作")
            return True
            
        except Exception as e:
            logger.error(f"导入历史记录失败: {e}")
            return False
    
    def _undo_operation(self, operation: OperationRecord) -> bool:
        """执行撤销操作"""
        try:
            if operation.operation_type == OperationType.RENAME:
                return self._undo_rename(operation)
            elif operation.operation_type == OperationType.MOVE:
                return self._undo_move(operation)
            elif operation.operation_type == OperationType.DELETE:
                return self._undo_delete(operation)
            elif operation.operation_type == OperationType.BACKUP:
                return self._undo_backup(operation)
            else:
                # 其他操作类型不需要物理撤销
                return True
                
        except Exception as e:
            logger.error(f"撤销操作失败: {e}")
            return False
    
    def _redo_operation(self, operation: OperationRecord) -> bool:
        """执行重做操作"""
        try:
            if operation.operation_type == OperationType.RENAME:
                return self._redo_rename(operation)
            elif operation.operation_type == OperationType.MOVE:
                return self._redo_move(operation)
            elif operation.operation_type == OperationType.DELETE:
                return self._redo_delete(operation)
            elif operation.operation_type == OperationType.BACKUP:
                return self._redo_backup(operation)
            else:
                # 其他操作类型不需要物理重做
                return True
                
        except Exception as e:
            logger.error(f"重做操作失败: {e}")
            return False
    
    def _undo_rename(self, operation: OperationRecord) -> bool:
        """撤销重命名操作"""
        if not operation.new_path or not os.path.exists(operation.new_path):
            return False
        
        # 检查原路径是否被占用
        if os.path.exists(operation.original_path):
            # 生成新的文件名
            base_name, ext = os.path.splitext(operation.original_path)
            counter = 1
            while os.path.exists(operation.original_path):
                operation.original_path = f"{base_name}_{counter}{ext}"
                counter += 1
        
        # 重命名回原文件名
        os.rename(operation.new_path, operation.original_path)
        return True
    
    def _redo_rename(self, operation: OperationRecord) -> bool:
        """重做重命名操作"""
        if not operation.new_path or not os.path.exists(operation.original_path):
            return False
        
        # 检查目标路径是否被占用
        if os.path.exists(operation.new_path):
            # 生成新的文件名
            base_name, ext = os.path.splitext(operation.new_path)
            counter = 1
            while os.path.exists(operation.new_path):
                operation.new_path = f"{base_name}_{counter}{ext}"
                counter += 1
        
        # 重命名到新文件名
        os.rename(operation.original_path, operation.new_path)
        return True
    
    def _undo_move(self, operation: OperationRecord) -> bool:
        """撤销移动操作"""
        if not operation.new_path or not os.path.exists(operation.new_path):
            return False
        
        # 检查原路径是否被占用
        if os.path.exists(operation.original_path):
            # 生成新的文件名
            base_name, ext = os.path.splitext(operation.original_path)
            counter = 1
            while os.path.exists(operation.original_path):
                operation.original_path = f"{base_name}_{counter}{ext}"
                counter += 1
        
        # 移动回原位置
        shutil.move(operation.new_path, operation.original_path)
        return True
    
    def _redo_move(self, operation: OperationRecord) -> bool:
        """重做移动操作"""
        if not operation.new_path or not os.path.exists(operation.original_path):
            return False
        
        # 检查目标路径是否被占用
        if os.path.exists(operation.new_path):
            # 生成新的文件名
            base_name, ext = os.path.splitext(operation.new_path)
            counter = 1
            while os.path.exists(operation.new_path):
                operation.new_path = f"{base_name}_{counter}{ext}"
                counter += 1
        
        # 移动到新位置
        shutil.move(operation.original_path, operation.new_path)
        return True
    
    def _undo_delete(self, operation: OperationRecord) -> bool:
        """撤销删除操作（从回收站恢复）"""
        # 这里需要实现从回收站恢复文件的逻辑
        # 由于不同操作系统的回收站实现不同，这里只是示例
        logger.warning("撤销删除操作需要从回收站恢复，暂未实现")
        return False
    
    def _redo_delete(self, operation: OperationRecord) -> bool:
        """重做删除操作"""
        if not os.path.exists(operation.original_path):
            return False
        
        # 删除文件
        os.remove(operation.original_path)
        return True
    
    def _undo_backup(self, operation: OperationRecord) -> bool:
        """撤销备份操作"""
        # 备份操作通常不需要撤销
        return True
    
    def _redo_backup(self, operation: OperationRecord) -> bool:
        """重做备份操作"""
        # 重新创建备份
        if not os.path.exists(operation.original_path):
            return False
        
        if operation.new_path:
            # 确保备份目录存在
            backup_dir = os.path.dirname(operation.new_path)
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # 创建备份
            shutil.copy2(operation.original_path, operation.new_path)
        
        return True
    
    def _generate_operation_id(self) -> str:
        """生成操作ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        try:
            import hashlib
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def load_history(self) -> None:
        """加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 转换操作记录
                self.operations = []
                for op_data in data.get('operations', []):
                    # 转换时间戳
                    if isinstance(op_data['timestamp'], str):
                        op_data['timestamp'] = datetime.fromisoformat(op_data['timestamp'])
                    
                    # 转换操作类型
                    op_data['operation_type'] = OperationType(op_data['operation_type'])
                    
                    # 创建操作记录
                    operation = OperationRecord(**op_data)
                    self.operations.append(operation)
                
                self.current_index = len(self.operations) - 1
                logger.info(f"加载历史记录: {len(self.operations)} 个操作")
                
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
            self.operations = []
            self.current_index = -1
    
    def save_history(self) -> None:
        """保存历史记录"""
        try:
            data = {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'operations': [asdict(op) for op in self.operations]
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}") 