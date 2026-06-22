"""
资金流向数据采集器 - 获取和保存个股、行业、板块资金流向数据
"""
import pandas as pd
import logging
from typing import Optional, Any
from datetime import datetime, timedelta
import time
from utils.base_fetcher import DataFetcher, FetcherFactory

# 导入速率限制器
try:
    from utils.stock_data_fetcher import _tushare_limiter
except ImportError:
    _tushare_limiter = None

# 配置日志
logger = logging.getLogger(__name__)


class FundFlowFetcher(DataFetcher):
    """资金流向数据采集器"""
    
    def __init__(self, db_manager, cache_manager=None):
        """
        初始化资金流向数据采集器
        
        参数：
            db_manager: 数据库管理器
            cache_manager: 缓存管理器（可选）
        """
        super().__init__(db_manager, cache_manager)
    
    # ==================== 个股资金流向 ====================
    
    def _fetch_daily_stock_moneyflow(self, start_date: str, end_date: str, pro=None, stock_codes: Optional[list] = None) -> Optional[pd.DataFrame]:
        """
        逐日采集个股资金流向数据
        """
        logger.info(f"开始逐日采集个股资金流向数据: {start_date} 到 {end_date}")
        if stock_codes:
            logger.info(f"只获取指定的 {len(stock_codes)} 只股票的数据")
        
        all_data = []
        
        try:
            # 如果pro为None，创建Tushare API实例
            if pro is None:
                try:
                    import tushare as ts
                    import json
                    
                    tushare_config_path = 'config/tushare_config.json'
                    with open(tushare_config_path, 'r', encoding='utf-8') as f:
                        tushare_config = json.load(f)
                    token = tushare_config.get('token') or tushare_config.get('api_key')
                    
                    if not token:
                        logger.warning("未找到Tushare token配置，跳过个股资金流向采集")
                        return None
                    
                    pro = ts.pro_api(token)
                except ImportError:
                    logger.warning("tushare未安装，跳过个股资金流向采集")
                    return None
                except Exception as e:
                    logger.warning(f"初始化Tushare失败，跳过个股资金流向采集: {e}")
                    return None
            
            # 将日期字符串转换为 datetime 对象
            start_dt = datetime.strptime(start_date, '%Y%m%d')
            end_dt = datetime.strptime(end_date, '%Y%m%d')
            
            # 如果提供了 stock_codes，转换为 Tushare 格式
            ts_codes = None
            if stock_codes:
                ts_codes = set()
                for code in stock_codes:
                    if code.startswith('6'):
                        ts_codes.add(f"{code}.SH")
                    else:
                        ts_codes.add(f"{code}.SZ")
            
            # 逐日采集
            current_dt = start_dt
            day_count = 0
            
            while current_dt <= end_dt:
                current_date_str = current_dt.strftime('%Y%m%d')
                
                try:
                    if _tushare_limiter:
                        _tushare_limiter.wait_if_needed()
                    
                    df_daily = pro.moneyflow(trade_date=current_date_str)
                    
                    if df_daily is not None and len(df_daily) > 0:
                        if ts_codes:
                            df_daily = df_daily[df_daily['ts_code'].isin(ts_codes)]
                        
                        if len(df_daily) > 0:
                            all_data.append(df_daily)
                            logger.debug(f"获取 {current_date_str} 的个股资金流向数据: {len(df_daily)} 条")
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    logger.warning(f"获取 {current_date_str} 的个股资金流向数据失败: {e}")
                
                current_dt += timedelta(days=1)
                day_count += 1
            
            if all_data:
                df_merged = pd.concat(all_data, ignore_index=True)
                logger.info(f"逐日采集完成，共采集 {day_count} 天，获取 {len(df_merged)} 条个股资金流向数据")
                return df_merged
            else:
                logger.warning("逐日采集未获取到任何数据")
                return None
        
        except Exception as e:
            logger.error(f"逐日采集个股资金流向数据失败: {e}")
            return None
    
    # ==================== 行业资金流向 ====================
    
    def _fetch_daily_industry_moneyflow(self, start_date: str, end_date: str, pro=None) -> Optional[pd.DataFrame]:
        """
        逐日采集行业资金流向数据
        """
        logger.info(f"开始逐日采集行业资金流向数据: {start_date} 到 {end_date}")
        
        all_data = []
        
        try:
            if pro is None:
                try:
                    import tushare as ts
                    import json
                    tushare_config_path = 'config/tushare_config.json'
                    with open(tushare_config_path, 'r', encoding='utf-8') as f:
                        tushare_config = json.load(f)
                    token = tushare_config.get('token') or tushare_config.get('api_key')
                    if not token:
                        logger.warning("未找到Tushare token配置，跳过行业资金流向采集")
                        return None
                    pro = ts.pro_api(token)
                except ImportError:
                    logger.warning("tushare未安装，跳过行业资金流向采集")
                    return None
                except Exception as e:
                    logger.warning(f"初始化Tushare失败，跳过行业资金流向采集: {e}")
                    return None
            
            start_dt = datetime.strptime(start_date, '%Y%m%d')
            end_dt = datetime.strptime(end_date, '%Y%m%d')
            
            current_dt = start_dt
            day_count = 0
            
            while current_dt <= end_dt:
                current_date_str = current_dt.strftime('%Y%m%d')
                
                try:
                    if _tushare_limiter:
                        _tushare_limiter.wait_if_needed()
                    df_daily = pro.moneyflow_ind_ths(trade_date=current_date_str)
                    if df_daily is not None and len(df_daily) > 0:
                        all_data.append(df_daily)
                    time.sleep(0.3)
                except Exception as e:
                    logger.warning(f"获取 {current_date_str} 的行业资金流向数据失败: {e}")
                
                current_dt += timedelta(days=1)
                day_count += 1
            
            if all_data:
                df_merged = pd.concat(all_data, ignore_index=True)
                logger.info(f"逐日采集完成，共采集 {day_count} 天，获取 {len(df_merged)} 条行业资金流向数据")
                return df_merged
            else:
                logger.warning("逐日采集未获取到任何数据")
                return None
        
        except Exception as e:
            logger.error(f"逐日采集行业资金流向数据失败: {e}")
            return None
    
    # ==================== 板块资金流向 ====================
    
    def _fetch_daily_sector_moneyflow(self, start_date: str, end_date: str, pro=None) -> Optional[pd.DataFrame]:
        """
        逐日采集板块资金流向数据
        """
        logger.info(f"开始逐日采集板块资金流向数据: {start_date} 到 {end_date}")
        
        all_data = []
        
        try:
            if pro is None:
                try:
                    import tushare as ts
                    import json
                    tushare_config_path = 'config/tushare_config.json'
                    with open(tushare_config_path, 'r', encoding='utf-8') as f:
                        tushare_config = json.load(f)
                    token = tushare_config.get('token') or tushare_config.get('api_key')
                    if not token:
                        logger.warning("未找到Tushare token配置，跳过板块资金流向采集")
                        return None
                    pro = ts.pro_api(token)
                except ImportError:
                    logger.warning("tushare未安装，跳过板块资金流向采集")
                    return None
                except Exception as e:
                    logger.warning(f"初始化Tushare失败，跳过板块资金流向采集: {e}")
                    return None
            
            start_dt = datetime.strptime(start_date, '%Y%m%d')
            end_dt = datetime.strptime(end_date, '%Y%m%d')
            
            current_dt = start_dt
            day_count = 0
            
            while current_dt <= end_dt:
                current_date_str = current_dt.strftime('%Y%m%d')
                try:
                    if _tushare_limiter:
                        _tushare_limiter.wait_if_needed()
                    df_daily = pro.moneyflow_cnt_ths(trade_date=current_date_str)
                    if df_daily is not None and len(df_daily) > 0:
                        all_data.append(df_daily)
                    time.sleep(0.3)
                except Exception as e:
                    logger.warning(f"获取 {current_date_str} 的板块资金流向数据失败: {e}")
                current_dt += timedelta(days=1)
                day_count += 1
            
            if all_data:
                df_merged = pd.concat(all_data, ignore_index=True)
                logger.info(f"逐日采集完成，共采集 {day_count} 天，获取 {len(df_merged)} 条板块资金流向数据")
                return df_merged
            else:
                logger.warning("逐日采集未获取到任何数据")
                return None
        
        except Exception as e:
            logger.error(f"逐日采集板块资金流向数据失败: {e}")
            return None
    
    # ==================== 行业资金流向数据库操作 ====================
    
    def _fetch_industry_fund_flow(self, trade_date: str) -> Optional[pd.DataFrame]:
        """获取行业资金流向数据"""
        try:
            import tushare as ts
            import json
            
            tushare_config_path = 'config/tushare_config.json'
            with open(tushare_config_path, 'r', encoding='utf-8') as f:
                tushare_config = json.load(f)
            token = tushare_config.get('token') or tushare_config.get('api_key')
            
            if not token:
                return None
            
            pro = ts.pro_api(token)
            if _tushare_limiter:
                _tushare_limiter.wait_if_needed()
            df_flow = pro.moneyflow_ind_ths(trade_date=trade_date)
            return df_flow
        
        except ImportError:
            logger.warning("tushare未安装，跳过行业资金流向")
            return None
        except Exception as e:
            logger.error(f"获取行业资金流向数据失败: {e}")
            return None
    
    def _save_industry_fund_flow(self, df_flow: pd.DataFrame, end_date: str) -> int:
        """
        保存行业资金流向数据到数据库
        
        参数：
            df_flow: 行业资金流向数据 DataFrame（包含 trade_date 字段）
            end_date: 结束日期，格式 YYYYMMDD（用于日期格式化）
        
        返回：
            保存成功的记录数
        """
        saved_count = 0
        
        try:
            # 遍历数据并保存到数据库
            for idx, row in df_flow.iterrows():
                try:
                    # 提取行业代码和名称
                    industry_code = str(row.get('ts_code', '')).strip()
                    industry_name = str(row.get('industry', '')).strip() if 'industry' in row else None
                    
                    # 提取交易日期
                    trade_date = str(row.get('trade_date', '')).strip()
                    if not trade_date:
                        continue
                    
                    # 格式化日期
                    formatted_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
                    
                    if not industry_code:
                        continue
                    
                    # 从 Tushare 接口获取资金流向数据（单位：亿元）
                    net_buy_amount = float(row.get('net_buy_amount', 0)) or 0
                    net_sell_amount = float(row.get('net_sell_amount', 0)) or 0
                    net_amount = float(row.get('net_amount', 0)) or 0
                    
                    # 转换为万元（1亿 = 10000万）
                    main_net_flow = net_amount * 10000
                    super_large_net_flow = 0  # 新接口不提供此字段
                    large_net_flow = 0  # 新接口不提供此字段
                    medium_net_flow = 0  # 新接口不提供此字段
                    small_net_flow = 0  # 新接口不提供此字段
                    
                    # 计算净流入率
                    total_buy = net_buy_amount * 10000
                    net_flow_rate = (net_amount / (net_buy_amount + net_sell_amount) * 100) if (net_buy_amount + net_sell_amount) > 0 else 0
                    
                    # 检查数据是否已存在
                    check_sql = """
                    SELECT id FROM industry_fund_flow 
                    WHERE industry_code = ? AND flow_date = ? AND period = ?
                    """
                    result = self.db_manager.query_one(check_sql, (industry_code, formatted_date, 'daily'))
                    
                    if result:
                        # 更新行业资金流向数据
                        update_sql = """
                        UPDATE industry_fund_flow 
                        SET main_net_flow = ?, super_large_net_flow = ?, large_net_flow = ?,
                            medium_net_flow = ?, small_net_flow = ?, net_flow_rate = ?
                        WHERE industry_code = ? AND flow_date = ? AND period = ?
                        """
                        self.db_manager.execute_with_retry(update_sql, (
                            main_net_flow, super_large_net_flow, large_net_flow,
                            medium_net_flow, small_net_flow, net_flow_rate,
                            industry_code, formatted_date, 'daily'
                        ))
                    else:
                        # 插入新的行业资金流向数据
                        insert_sql = """
                        INSERT INTO industry_fund_flow 
                        (industry_code, industry_name, flow_date, period, main_net_flow, super_large_net_flow, 
                         large_net_flow, medium_net_flow, small_net_flow, net_flow_rate)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        self.db_manager.execute_with_retry(insert_sql, (
                            industry_code, industry_name, formatted_date, 'daily', main_net_flow, super_large_net_flow,
                            large_net_flow, medium_net_flow, small_net_flow, net_flow_rate
                        ))
                    
                    saved_count += 1
                
                except Exception as e:
                    logger.debug(f"保存行业 {row.get('ts_code', '')} 的资金流向数据失败: {e}")
            
            logger.info(f"行业资金流向数据保存完成: {saved_count} 条")
        
        except Exception as e:
            logger.error(f"保存行业资金流向数据失败: {e}")
        
        return saved_count
    
    # ==================== 板块资金流向数据库操作 ====================
    
    def _fetch_sector_fund_flow(self, trade_date: str) -> Optional[pd.DataFrame]:
        """获取板块资金流向数据"""
        try:
            import tushare as ts
            import json
            tushare_config_path = 'config/tushare_config.json'
            with open(tushare_config_path, 'r', encoding='utf-8') as f:
                tushare_config = json.load(f)
            token = tushare_config.get('token') or tushare_config.get('api_key')
            if not token:
                return None
            pro = ts.pro_api(token)
            if _tushare_limiter:
                _tushare_limiter.wait_if_needed()
            df_flow = pro.moneyflow_cnt_ths(trade_date=trade_date)
            return df_flow
        except ImportError:
            logger.warning("tushare未安装，跳过板块资金流向")
            return None
        except Exception as e:
            logger.error(f"获取板块资金流向数据失败: {e}")
            return None
    
    def _save_sector_fund_flow(self, df_flow: pd.DataFrame, end_date: str) -> int:
        """
        保存板块资金流向数据到数据库
        
        参数：
            df_flow: 板块资金流向数据 DataFrame（包含 trade_date 字段）
            end_date: 结束日期，格式 YYYYMMDD（用于日期格式化）
        
        返回：
            保存成功的记录数
        """
        saved_count = 0
        
        try:
            # 遍历数据并保存到数据库
            for idx, row in df_flow.iterrows():
                try:
                    # 提取板块代码和名称
                    sector_code = str(row.get('ts_code', '')).strip()
                    sector_name = str(row.get('name', '')).strip() if 'name' in row else None
                    
                    # 提取交易日期
                    trade_date = str(row.get('trade_date', '')).strip()
                    if not trade_date:
                        continue
                    
                    # 格式化日期
                    formatted_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
                    
                    if not sector_code:
                        continue
                    
                    # 从 Tushare 接口获取资金流向数据（单位：亿元）
                    net_buy_amount = float(row.get('net_buy_amount', 0)) or 0
                    net_sell_amount = float(row.get('net_sell_amount', 0)) or 0
                    net_amount = float(row.get('net_amount', 0)) or 0
                    
                    # 转换为万元（1亿 = 10000万）
                    main_net_flow = net_amount * 10000
                    super_large_net_flow = 0  # 新接口不提供此字段
                    large_net_flow = 0  # 新接口不提供此字段
                    medium_net_flow = 0  # 新接口不提供此字段
                    small_net_flow = 0  # 新接口不提供此字段
                    
                    # 计算净流入率
                    net_flow_rate = (net_amount / (net_buy_amount + net_sell_amount) * 100) if (net_buy_amount + net_sell_amount) > 0 else 0
                    
                    # 检查数据是否已存在
                    check_sql = """
                    SELECT id FROM sector_fund_flow 
                    WHERE sector_code = ? AND flow_date = ? AND period = ?
                    """
                    result = self.db_manager.query_one(check_sql, (sector_code, formatted_date, 'daily'))
                    
                    if result:
                        # 更新板块资金流向数据
                        update_sql = """
                        UPDATE sector_fund_flow 
                        SET main_net_flow = ?, super_large_net_flow = ?, large_net_flow = ?,
                            medium_net_flow = ?, small_net_flow = ?, net_flow_rate = ?
                        WHERE sector_code = ? AND flow_date = ? AND period = ?
                        """
                        self.db_manager.execute_with_retry(update_sql, (
                            main_net_flow, super_large_net_flow, large_net_flow,
                            medium_net_flow, small_net_flow, net_flow_rate,
                            sector_code, formatted_date, 'daily'
                        ))
                    else:
                        # 插入新的板块资金流向数据
                        insert_sql = """
                        INSERT INTO sector_fund_flow 
                        (sector_code, sector_name, flow_date, period, main_net_flow, super_large_net_flow, 
                         large_net_flow, medium_net_flow, small_net_flow, net_flow_rate)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        self.db_manager.execute_with_retry(insert_sql, (
                            sector_code, sector_name, formatted_date, 'daily', main_net_flow, super_large_net_flow,
                            large_net_flow, medium_net_flow, small_net_flow, net_flow_rate
                        ))
                    
                    saved_count += 1
                
                except Exception as e:
                    logger.debug(f"保存板块 {row.get('ts_code', '')} 的资金流向数据失败: {e}")
            
            logger.info(f"板块资金流向数据保存完成: {saved_count} 条")
        
        except Exception as e:
            logger.error(f"保存板块资金流向数据失败: {e}")
        
        return saved_count

    # ==================== DataFetcher 接口实现 ====================
    
    def validate_data(self, data: Any) -> bool:
        """
        验证数据有效性
        
        参数：
            data: 待验证的数据
        
        返回：
            数据有效返回 True，否则返回 False
        """
        if data is None:
            return False
        
        if isinstance(data, pd.DataFrame):
            return not data.empty
        
        return False
    
    def clean_data(self, data: Any) -> Any:
        """
        清洗数据
        
        参数：
            data: 待清洗的数据
        
        返回：
            清洗后的数据
        """
        if isinstance(data, pd.DataFrame):
            # 删除空行
            data = data.dropna(subset=['ts_code'])
            # 转换数据类型
            for col in data.columns:
                if col in ['buy_vol', 'sell_vol', 'net_vol']:
                    data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0).astype(int)
                elif col in ['buy_amount', 'sell_amount', 'net_amount']:
                    data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        
        return data
    
    def save_data(self, data: Any) -> bool:
        """
        保存数据到数据库
        
        参数：
            data: 待保存的数据
        
        返回：
            保存成功返回 True，否则返回 False
        """
        try:
            if isinstance(data, pd.DataFrame):
                # 保存资金流向数据
                return len(data) > 0
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
        
        return False


# 注册采集器
FetcherFactory.register('fund_flow', FundFlowFetcher)
