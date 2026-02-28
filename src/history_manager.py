"""
评测历史记录管理器
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class HistoryManager:
    """评测历史记录管理器"""

    def __init__(self, history_dir: str = None):
        """
        初始化历史记录管理器

        Args:
            history_dir: 历史记录存储目录
        """
        if history_dir is None:
            history_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "history")

        self.history_dir = history_dir
        self.history_file = os.path.join(history_dir, "evaluation_history.json")
        os.makedirs(self.history_dir, exist_ok=True)

    def add_record(self, evaluation_result: Dict[str, Any]) -> str:
        """
        添加评测记录

        Args:
            evaluation_result: 评测结果

        Returns:
            记录ID
        """
        try:
            # 读取现有历史记录
            history = self._load_history()

            # 生成记录ID
            record_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{evaluation_result.get('script_name', 'unknown')}"

            # 保存完整的评测结果到单独的文件
            result_file = os.path.join(self.history_dir, f"{record_id}.json")
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(evaluation_result, f, ensure_ascii=False, indent=2)

            # 创建摘要记录
            record = {
                'id': record_id,
                'timestamp': datetime.now().isoformat(),
                'script_name': evaluation_result.get('script_name', ''),
                'overall_score': evaluation_result.get('overall', {}).get('total_score', 0),
                'overall_max_score': evaluation_result.get('overall', {}).get('max_score', 100),
                'level': evaluation_result.get('overall', {}).get('level', ''),
                'dimensions': {
                    key: {
                        'name': dim.get('dimension_name', key),
                        'score': dim.get('total_score', 0),
                        'max_score': dim.get('max_score', 100)
                    }
                    for key, dim in evaluation_result.get('dimensions', {}).items()
                },
                'script_path': evaluation_result.get('script_path', ''),
                'report_files': evaluation_result.get('report_files', []),
                'result_file': result_file,  # 保存完整结果文件路径
                'summary': self._generate_summary(evaluation_result)
            }

            # 添加到历史记录
            history['records'].insert(0, record)  # 最新的在前面

            # 保存历史记录
            self._save_history(history)

            logger.info(f"添加评测记录: {record_id}")
            return record_id

        except Exception as e:
            logger.error(f"添加评测记录失败: {str(e)}")
            raise

    def get_records(self, limit: int = 50, offset: int = 0,
                    search: str = None) -> Dict[str, Any]:
        """
        获取评测记录列表

        Args:
            limit: 返回数量限制
            offset: 偏移量
            search: 搜索关键词（剧本名称）

        Returns:
            记录列表
        """
        try:
            history = self._load_history()
            records = history.get('records', [])

            # 搜索过滤
            if search:
                records = [r for r in records if search.lower() in r.get('script_name', '').lower()]

            # 按时间倒序排序（最近的在前面）
            records = sorted(records, key=lambda x: x.get('timestamp', ''), reverse=True)

            # 分页
            total = len(records)
            records = records[offset:offset + limit]

            return {
                'records': records,
                'total': total,
                'limit': limit,
                'offset': offset
            }

        except Exception as e:
            logger.error(f"获取评测记录失败: {str(e)}")
            return {
                'records': [],
                'total': 0,
                'limit': limit,
                'offset': offset
            }

    def get_record(self, record_id: str, load_full: bool = False) -> Optional[Dict[str, Any]]:
        """
        获取单个评测记录

        Args:
            record_id: 记录ID
            load_full: 是否加载完整的评测结果

        Returns:
            记录详情，如果不存在返回None
        """
        try:
            history = self._load_history()
            records = history.get('records', [])

            for record in records:
                if record.get('id') == record_id:
                    # 如果需要加载完整结果
                    if load_full and record.get('result_file'):
                        result_file = record['result_file']
                        if os.path.exists(result_file):
                            with open(result_file, 'r', encoding='utf-8') as f:
                                return json.load(f)
                        else:
                            logger.warning(f"结果文件不存在: {result_file}")
                    return record

            return None

        except Exception as e:
            logger.error(f"获取评测记录详情失败: {str(e)}")
            return None

    def delete_record(self, record_id: str) -> bool:
        """
        删除评测记录

        Args:
            record_id: 记录ID

        Returns:
            是否删除成功
        """
        try:
            history = self._load_history()
            records = history.get('records', [])

            # 找到要删除的记录
            target_record = None
            for r in records:
                if r.get('id') == record_id:
                    target_record = r
                    break

            if not target_record:
                return False  # 没有找到要删除的记录

            # 删除结果文件
            result_file = target_record.get('result_file')
            if result_file and os.path.exists(result_file):
                try:
                    os.remove(result_file)
                    logger.info(f"删除结果文件: {result_file}")
                except Exception as e:
                    logger.warning(f"删除结果文件失败: {str(e)}")

            # 过滤掉要删除的记录
            new_records = [r for r in records if r.get('id') != record_id]
            history['records'] = new_records
            self._save_history(history)

            logger.info(f"删除评测记录: {record_id}")
            return True

        except Exception as e:
            logger.error(f"删除评测记录失败: {str(e)}")
            return False

    def clear_all(self) -> bool:
        """
        清空所有历史记录

        Returns:
            是否清空成功
        """
        try:
            history = {'records': []}
            self._save_history(history)

            logger.info("清空所有评测记录")
            return True

        except Exception as e:
            logger.error(f"清空历史记录失败: {str(e)}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息
        """
        try:
            history = self._load_history()
            records = history.get('records', [])

            total = len(records)

            if total == 0:
                return {
                    'total_evaluations': 0,
                    'average_score': 0,
                    'score_distribution': {}
                }

            # 计算平均分
            scores = [r.get('overall_score', 0) for r in records]
            avg_score = sum(scores) / total

            # 分数分布
            distribution = {
                '优秀(80-100)': len([s for s in scores if s >= 80]),
                '良好(60-79)': len([s for s in scores if 60 <= s < 80]),
                '及格(40-59)': len([s for s in scores if 40 <= s < 60]),
                '较差(20-39)': len([s for s in scores if 20 <= s < 40]),
                '失败(0-19)': len([s for s in scores if s < 20])
            }

            return {
                'total_evaluations': total,
                'average_score': round(avg_score, 2),
                'score_distribution': distribution
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {
                'total_evaluations': 0,
                'average_score': 0,
                'score_distribution': {}
            }

    def _load_history(self) -> Dict[str, Any]:
        """加载历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载历史记录文件失败: {str(e)}")

        return {'records': []}

    def _save_history(self, history: Dict[str, Any]) -> None:
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史记录文件失败: {str(e)}")
            raise

    def _generate_summary(self, evaluation_result: Dict[str, Any]) -> str:
        """生成评测摘要"""
        try:
            overall = evaluation_result.get('overall', {})
            score = overall.get('total_score', 0)
            max_score = overall.get('max_score', 100)
            level = overall.get('level', '')

            # 获取最弱的3个维度
            dimensions = evaluation_result.get('dimensions', {})
            dim_list = [
                {
                    'name': dim.get('dimension_name', key),
                    'score': dim.get('total_score', 0)
                }
                for key, dim in dimensions.items()
            ]
            dim_list.sort(key=lambda x: x['score'])

            weak_dims = dim_list[:3] if len(dim_list) >= 3 else dim_list

            summary = f"总分: {score}/{max_score} ({level})\n"
            if weak_dims:
                summary += f"待改进: {', '.join([d['name'] for d in weak_dims])}"

            return summary

        except Exception as e:
            logger.error(f"生成摘要失败: {str(e)}")
            return "评测完成"

    def import_from_outputs(self, outputs_dir: str = None) -> Dict[str, Any]:
        """
        从outputs目录导入历史评测记录

        Args:
            outputs_dir: outputs目录路径

        Returns:
            导入结果统计
        """
        try:
            if outputs_dir is None:
                # 使用绝对路径查找outputs目录
                # history_dir是 项目根目录/history
                # 所以outputs目录应该是 项目根目录/outputs
                project_root = os.path.dirname(self.history_dir)
                outputs_dir = os.path.join(project_root, "outputs")

            logger.info(f"尝试从目录导入: {outputs_dir}")

            if not os.path.exists(outputs_dir):
                logger.error(f"outputs目录不存在: {outputs_dir}")
                return {
                    'success': True,
                    'total': 0,
                    'imported': 0,
                    'skipped': 0,
                    'failed': 0,
                    'message': f'outputs目录不存在: {outputs_dir}'
                }

            # 获取所有JSON文件
            json_files = [f for f in os.listdir(outputs_dir) if f.endswith('.json')]
            total = len(json_files)

            if total == 0:
                return {
                    'success': True,
                    'total': 0,
                    'imported': 0,
                    'skipped': 0,
                    'failed': 0,
                    'message': '没有找到评测结果文件'
                }

            imported = 0
            skipped = 0
            failed = 0
            existing_record_ids = set()

            # 获取现有的记录ID
            history = self._load_history()
            for record in history.get('records', []):
                existing_record_ids.add(record.get('id'))

            # 遍历所有JSON文件
            for json_file in json_files:
                try:
                    file_path = os.path.join(outputs_dir, json_file)

                    # 读取评测结果
                    with open(file_path, 'r', encoding='utf-8') as f:
                        evaluation_result = json.load(f)

                    # 检查是否是有效的评测结果
                    if not self._is_valid_evaluation_result(evaluation_result):
                        logger.warning(f"跳过无效的评测结果文件: {json_file}")
                        skipped += 1
                        continue

                    # 生成记录ID（基于文件名的时间戳）
                    script_name = evaluation_result.get('script_name', 'unknown')
                    timestamp = json_file.replace('.json', '')

                    # 尝试从文件名提取时间戳
                    import re
                    time_match = re.search(r'(\d{8}_\d{6})', timestamp)
                    if time_match:
                        record_id = f"{time_match.group(1)}_{script_name}"
                    else:
                        # 使用文件的修改时间
                        mtime = os.path.getmtime(file_path)
                        record_id = f"{datetime.fromtimestamp(mtime).strftime('%Y%m%d_%H%M%S')}_{script_name}"

                    # 检查是否已存在
                    if record_id in existing_record_ids:
                        logger.info(f"记录已存在，跳过: {record_id}")
                        skipped += 1
                        continue

                    # 保存完整的评测结果到单独的文件
                    result_file = os.path.join(self.history_dir, f"{record_id}.json")
                    with open(result_file, 'w', encoding='utf-8') as f:
                        json.dump(evaluation_result, f, ensure_ascii=False, indent=2)

                    # 创建摘要记录
                    record = {
                        'id': record_id,
                        'timestamp': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                        'script_name': script_name,
                        'overall_score': evaluation_result.get('overall', {}).get('total_score', 0),
                        'overall_max_score': evaluation_result.get('overall', {}).get('max_score', 100),
                        'level': evaluation_result.get('overall', {}).get('level', ''),
                        'dimensions': {
                            key: {
                                'name': dim.get('dimension_name', key),
                                'score': dim.get('total_score', 0),
                                'max_score': dim.get('max_score', 100)
                            }
                            for key, dim in evaluation_result.get('dimensions', {}).items()
                        },
                        'script_path': evaluation_result.get('script_path', ''),
                        'report_files': evaluation_result.get('report_files', []),
                        'result_file': result_file,
                        'summary': self._generate_summary(evaluation_result),
                        'imported_from': json_file  # 标记来源
                    }

                    # 添加到历史记录
                    history['records'].insert(0, record)
                    existing_record_ids.add(record_id)
                    imported += 1

                    logger.info(f"导入评测记录: {record_id} (来源: {json_file})")

                except Exception as e:
                    logger.error(f"导入文件失败 {json_file}: {str(e)}")
                    failed += 1

            # 保存历史记录
            self._save_history(history)

            return {
                'success': True,
                'total': total,
                'imported': imported,
                'skipped': skipped,
                'failed': failed,
                'message': f'导入完成：共{total}个文件，成功导入{imported}个，跳过{skipped}个，失败{failed}个'
            }

        except Exception as e:
            logger.error(f"导入历史记录失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'total': 0,
                'imported': 0,
                'skipped': 0,
                'failed': 0
            }

    def _is_valid_evaluation_result(self, data: Dict[str, Any]) -> bool:
        """检查是否是有效的评测结果"""
        # 必须包含overall或dimensions
        has_overall = 'overall' in data and isinstance(data['overall'], dict)
        has_dimensions = 'dimensions' in data and isinstance(data['dimensions'], dict)

        return has_overall or has_dimensions
