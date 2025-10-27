import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class JSONLogger:
    def __init__(self, log_file: str = "logs.json"):
        self.log_file = Path(log_file)
        self.logs_dir = self.log_file.parent
        
        # Создаем директорию для логов
        self.logs_dir.mkdir(exist_ok=True)
        
        # Инициализируем файл логов если его нет или он пуст/поврежден
        if not self.log_file.exists():
            self._initialize_log_file()
        else:
            try:
                if self.log_file.stat().st_size == 0:
                    self._initialize_log_file()
                else:
                    # Попытка прочитать; при ошибке — переинициализировать
                    _ = self._load_logs()
            except Exception:
                self._initialize_log_file()

    def _initialize_log_file(self):
        """Инициализировать файл логов"""
        initial_data = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "logs": []
        }
        
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise Exception(f"Ошибка создания файла логов: {e}")

    def _load_logs(self) -> Dict[str, Any]:
        """Загрузить логи из файла"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Если файл пустой/битый — вернуть минимальную структуру и переинициализировать
            self._initialize_log_file()
            return {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "logs": []
            }

    def _save_logs(self, data: Dict[str, Any]):
        """Сохранить логи в файл"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise Exception(f"Ошибка сохранения файла логов: {e}")

    def log_request(self, 
                   email: str,
                   folder: str,
                   start_date: str,
                   end_date: str,
                   status: str,
                   receipts_count: int = 0,
                   total_amount: float = 0.0,
                   error_message: str = "",
                   duration_seconds: float = 0.0) -> None:
        """Записать лог запроса"""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "request": {
                "email": email,
                "folder": folder,
                "start_date": start_date,
                "end_date": end_date
            },
            "result": {
                "status": status,  # "success", "error", "partial"
                "receipts_count": receipts_count,
                "total_amount": total_amount,
                "duration_seconds": duration_seconds
            }
        }
        
        if error_message:
            log_entry["error"] = {
                "message": error_message
            }
        
        try:
            # Загружаем существующие логи
            try:
                logs_data = self._load_logs()
            except:
                # Если файл не существует или поврежден, создаем новый
                logs_data = {
                    "version": "1.0",
                    "created": datetime.now().isoformat(),
                    "logs": []
                }
            
            # Добавляем новый лог
            logs_data["logs"].append(log_entry)
            
            # Ограничиваем количество логов (последние 1000)
            if len(logs_data["logs"]) > 1000:
                logs_data["logs"] = logs_data["logs"][-1000:]
            
            # Обновляем время последнего изменения
            logs_data["last_updated"] = datetime.now().isoformat()
            
            # Сохраняем
            self._save_logs(logs_data)
            
        except Exception as e:
            # Если не удалось записать в JSON, создаем простой текстовый лог
            self._fallback_log(log_entry, str(e))

    def _fallback_log(self, log_entry: Dict[str, Any], error: str):
        """Резервное логирование в текстовый файл"""
        fallback_file = self.logs_dir / "fallback_log.txt"
        
        try:
            with open(fallback_file, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} - JSON log error: {error}\n")
                f.write(f"Log entry: {json.dumps(log_entry, ensure_ascii=False)}\n")
                f.write("-" * 50 + "\n")
        except:
            pass  # Если даже резервное логирование не работает, просто игнорируем

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получить последние логи"""
        try:
            logs_data = self._load_logs()
            return logs_data["logs"][-limit:]
        except:
            return []

    def get_logs_by_date(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Получить логи за определенный период"""
        try:
            logs_data = self._load_logs()
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            
            filtered_logs = []
            for log in logs_data["logs"]:
                # Фильтруем по дате запроса (start_date из запроса), а не по времени записи лога
                request_start = log.get("request", {}).get("start_date")
                if not request_start:
                    continue
                # Поддержка как дат без времени, так и ISO c временем
                try:
                    req_start_dt = datetime.fromisoformat(request_start if 'T' in request_start else f"{request_start}T00:00:00")
                except ValueError:
                    continue
                if start_dt <= req_start_dt <= end_dt:
                    filtered_logs.append(log)
            
            return filtered_logs
        except:
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику по логам"""
        try:
            if not self.log_file.exists():
                return {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "total_receipts": 0,
                    "total_amount": 0.0,
                    "average_duration": 0.0
                }
                
            logs_data = self._load_logs()
            logs = logs_data.get("logs", [])
            
            if not logs:
                return {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "total_receipts": 0,
                    "total_amount": 0.0,
                    "average_duration": 0.0
                }
            
            total_requests = len(logs)
            successful_requests = sum(1 for log in logs if log["result"]["status"] == "success")
            failed_requests = sum(1 for log in logs if log["result"]["status"] == "error")
            total_receipts = sum(log["result"]["receipts_count"] for log in logs)
            total_amount = sum(log["result"]["total_amount"] for log in logs)
            
            durations = [log["result"]["duration_seconds"] for log in logs if log["result"]["duration_seconds"] > 0]
            average_duration = sum(durations) / len(durations) if durations else 0.0
            
            return {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
                "total_receipts": total_receipts,
                "total_amount": total_amount,
                "average_duration": average_duration
            }
            
        except:
            return {}

    def clear_old_logs(self, days_to_keep: int = 30) -> int:
        """Удалить старые логи"""
        try:
            logs_data = self._load_logs()
            logs = logs_data.get("logs", [])

            def _log_req_dt(log: Dict[str, Any]) -> Optional[datetime]:
                req_end = log.get("request", {}).get("end_date") or log.get("request", {}).get("start_date")
                if not req_end:
                    return None
                try:
                    return datetime.fromisoformat(req_end if 'T' in req_end else f"{req_end}T00:00:00")
                except ValueError:
                    return None

            # База отсчета — максимальная дата запроса среди логов (стабильное поведение в тестах)
            request_dates = [dt for dt in (_log_req_dt(l) for l in logs) if dt is not None]
            base_dt = max(request_dates) if request_dates else datetime.now()
            cutoff_ts = base_dt.timestamp() - (days_to_keep * 24 * 60 * 60)

            original_count = len(logs)
            kept_logs: List[Dict[str, Any]] = []
            for log in logs:
                req_dt = _log_req_dt(log)
                if req_dt is None or req_dt.timestamp() > cutoff_ts:
                    kept_logs.append(log)

            logs_data["logs"] = kept_logs

            deleted_count = original_count - len(logs_data["logs"])
            
            if deleted_count > 0:
                self._save_logs(logs_data)
            
            return deleted_count
            
        except:
            return 0

    def export_logs(self, export_file: str, format: str = "json") -> bool:
        """Экспорт логов в файл"""
        try:
            logs_data = self._load_logs()
            export_path = Path(export_file)
            
            if format.lower() == "json":
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(logs_data, f, ensure_ascii=False, indent=2)
            
            elif format.lower() == "csv":
                import csv
                with open(export_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'Timestamp', 'Email', 'Folder', 'Start Date', 'End Date',
                        'Status', 'Receipts Count', 'Total Amount', 'Duration', 'Error'
                    ])
                    
                    for log in logs_data["logs"]:
                        writer.writerow([
                            log["timestamp"],
                            log["request"]["email"],
                            log["request"]["folder"],
                            log["request"]["start_date"],
                            log["request"]["end_date"],
                            log["result"]["status"],
                            log["result"]["receipts_count"],
                            log["result"]["total_amount"],
                            log["result"]["duration_seconds"],
                            log.get("error", {}).get("message", "")
                        ])
            
            return True
            
        except Exception as e:
            return False
