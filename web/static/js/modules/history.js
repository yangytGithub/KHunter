/**
 * 选股历史查询功能模块
 */

/**
 * 查询选股历史
 */
export function searchSelectionHistory() {
    console.log('开始查询选股历史...');
    
    const strategyFilter = document.getElementById('history-strategy-filter');
    const startDateInput = document.getElementById('history-start-date');
    const endDateInput = document.getElementById('history-end-date');
    const excludeChinext = document.getElementById('history-exclude-chinext');
    const excludeStar = document.getElementById('history-exclude-star');
    
    const strategyName = strategyFilter?.value?.trim() || '';
    const startDate = startDateInput?.value || '';
    const endDate = endDateInput?.value || '';
    const excludeChinextVal = excludeChinext?.checked ? '1' : '0';
    const excludeStarVal = excludeStar?.checked ? '1' : '0';
    
    fetchSelectionHistory(strategyName, startDate, endDate, 1, excludeChinextVal, excludeStarVal);
}

/**
 * 获取选股历史数据
 * @param {string} strategyName - 策略名称
 * @param {string} startDate - 开始日期
 * @param {string} endDate - 结束日期
 * @param {number} page - 页码
 */
export function fetchSelectionHistory(strategyName, startDate, endDate, page, excludeChinext, excludeStar) {
    const params = new URLSearchParams();
    if (strategyName) params.append('strategy_name', strategyName);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (excludeChinext === '1') params.append('exclude_chinext', '1');
    if (excludeStar === '1') params.append('exclude_star', '1');
    params.append('page', page);
    params.append('limit', 20);
    
    // 发送请求
    const url = `/api/selection-history?${params.toString()}`;
    console.log('请求URL:', url);
    
    fetch(url)
        .then(response => {
            console.log('API响应状态:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('API返回数据:', data);
            if (data.success) {
                renderHistoryTable(data.data);
                updateHistoryStats(data);
                renderStrategyRanking(data.strategy_groups || []);
                renderHistoryPagination(data.total, data.page, data.limit);
            } else {
                showHistoryError(data.error || '查询失败');
            }
        })
        .catch(error => {
            console.error('API请求错误:', error);
            showHistoryError('网络错误: ' + error.message);
        });
}

/**
 * 渲染历史表格
 * @param {Array} data - 历史数据
 */
export function renderHistoryTable(data) {
    const tbody = document.getElementById('history-tbody');
    const table = document.getElementById('history-table');
    const emptyState = document.getElementById('history-empty');
    
    // 检查元素是否存在
    if (!tbody || !table || !emptyState) {
        console.error('历史记录表格元素不存在');
        return;
    }
    
    tbody.innerHTML = '';
    
    if (data.length === 0) {
        table.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    table.style.display = 'table';
    emptyState.style.display = 'none';
    
    // 遍历数据
    data.forEach(record => {
        const returnRate = record.return_rate || 0;
        let returnClass = 'return-neutral';
        if (returnRate > 0) {
            returnClass = 'return-positive';
        } else if (returnRate < 0) {
            returnClass = 'return-negative';
        }
        
        const row = document.createElement('tr');
        const selectionPrice = record.selection_day_price || record.selection_price || 0;
        const priceDiff = record.price_diff || 0;
        const priceDiffPct = record.price_diff_pct || 0;
        const diffColor = priceDiff > 0 ? '#dc2626' : priceDiff < 0 ? '#16a34a' : '#6b7280';
        const diffSign = priceDiff > 0 ? '+' : '';
        const pctSign = priceDiffPct > 0 ? '+' : '';
        row.innerHTML = `
            <td><span style="background: #dbeafe; color: #0c4a6e; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;">${escapeHtml(record.strategy_name)}</span></td>
            <td><a href="javascript:void(0)" onclick="viewStockDetail('${escapeHtml(record.stock_code)}')" class="stock-link" style="color: #2563eb; text-decoration: none; cursor: pointer; font-weight: 600;">${escapeHtml(record.stock_code)}</a></td>
            <td>${escapeHtml(record.stock_name)}</td>
            <td>${formatDate(record.selection_date)}</td>
            <td>¥${formatPrice(selectionPrice)}</td>
            <td>¥${formatPrice(record.current_price)}</td>
            <td style="color: ${diffColor}; font-weight: 600;">${diffSign}¥${formatPrice(priceDiff)}</td>
            <td style="color: ${diffColor}; font-weight: 600;">${pctSign}${formatPrice(priceDiffPct)}%</td>
            <td>${formatDailyChange(record.daily_change_pct)}</td>
            <td>
                <div style="font-size: 12px;">
                    <div>最高: ¥${formatPrice(record.highest_price)}</div>
                    <div>最低: ¥${formatPrice(record.lowest_price)}</div>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * 渲染策略分组胜率排名
 * @param {Array} groups - 策略分组数据
 */
export function renderStrategyRanking(groups) {
    const container = document.getElementById('history-strategy-ranking');
    const tbody = document.getElementById('history-strategy-ranking-tbody');
    
    if (!container || !tbody) return;
    
    if (!groups || groups.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    tbody.innerHTML = '';
    
    groups.forEach((group, index) => {
        const wr = group.win_rate || 0;
        const wrColor = wr >= 50 ? '#dc2626' : wr >= 30 ? '#eab308' : '#16a34a';
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="text-align: center; font-weight: 600;">${index + 1}</td>
            <td><span style="background: #dbeafe; color: #0c4a6e; padding: 2px 6px; border-radius: 3px; font-size: 12px;">${escapeHtml(group.strategy_name)}</span></td>
            <td style="text-align: center;">${group.total}</td>
            <td style="text-align: center; color: #dc2626; font-weight: 600;">${group.positive}</td>
            <td style="text-align: center; color: #16a34a; font-weight: 600;">${group.negative}</td>
            <td style="text-align: center; color: ${wrColor}; font-weight: 600;">${wr}%</td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * 更新统计信息
 * @param {Object} apiData - API返回的完整数据对象
 */
export function updateHistoryStats(apiData) {
    const statsDiv = document.getElementById('history-stats');
    const totalElem = document.getElementById('history-total');
    const positiveElem = document.getElementById('history-positive');
    const negativeElem = document.getElementById('history-negative');
    const winrateElem = document.getElementById('history-winrate');
    const pageElem = document.getElementById('history-current-page');
    const totalPagesElem = document.getElementById('history-total-pages');
    
    if (!statsDiv || !totalElem || !pageElem) {
        console.error('统计信息元素不存在');
        return;
    }
    
    const total = apiData.total || 0;
    const page = apiData.page || 1;
    const limit = apiData.limit || 20;
    const totalPages = Math.ceil(total / limit);
    
    totalElem.textContent = total;
    pageElem.textContent = page;
    if (positiveElem) positiveElem.textContent = apiData.positive_count || 0;
    if (negativeElem) negativeElem.textContent = apiData.negative_count || 0;
    if (winrateElem) winrateElem.textContent = (apiData.win_rate || 0) + '%';
    if (totalPagesElem) {
        totalPagesElem.textContent = totalPages;
    }
    statsDiv.style.display = 'block';
}

/**
 * 渲染分页
 * @param {number} total - 总数
 * @param {number} currentPage - 当前页码
 * @param {number} limit - 每页数量
 */
export function renderHistoryPagination(total, currentPage, limit) {
    const pagination = document.getElementById('history-pagination');
    const totalPages = Math.ceil(total / limit);
    
    if (totalPages <= 1) {
        pagination.style.display = 'none';
        return;
    }
    
    pagination.style.display = 'block';
    pagination.innerHTML = '';
    
    // 上一页
    const prevBtn = document.createElement('button');
    prevBtn.textContent = '← 上一页';
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => goToHistoryPage(currentPage - 1);
    prevBtn.style.cssText = 'padding: 6px 12px; margin: 0 5px; border: 1px solid #d1d5db; background: white; border-radius: 4px; cursor: pointer; font-size: 12px;';
    pagination.appendChild(prevBtn);
    
    // 页码
    for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.style.cssText = `padding: 6px 10px; margin: 0 2px; border: 1px solid #d1d5db; background: ${i === currentPage ? '#2563eb' : 'white'}; color: ${i === currentPage ? 'white' : '#374151'}; border-radius: 4px; cursor: pointer; font-size: 12px;`;
        btn.onclick = () => goToHistoryPage(i);
        pagination.appendChild(btn);
    }
    
    // 下一页
    const nextBtn = document.createElement('button');
    nextBtn.textContent = '下一页 →';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = () => goToHistoryPage(currentPage + 1);
    nextBtn.style.cssText = 'padding: 6px 12px; margin: 0 5px; border: 1px solid #d1d5db; background: white; border-radius: 4px; cursor: pointer; font-size: 12px;';
    pagination.appendChild(nextBtn);
}

/**
 * 跳转到指定页
 * @param {number} page - 页码
 */
export function goToHistoryPage(page) {
    const strategyName = document.getElementById('history-strategy-filter')?.value.trim() || '';
    const startDate = document.getElementById('history-start-date')?.value || '';
    const endDate = document.getElementById('history-end-date')?.value || '';
    const excludeChinext = document.getElementById('history-exclude-chinext')?.checked ? '1' : '0';
    const excludeStar = document.getElementById('history-exclude-star')?.checked ? '1' : '0';
    
    fetchSelectionHistory(strategyName, startDate, endDate, page, excludeChinext, excludeStar);
}

/**
 * 重置筛选条件
 */
export function resetHistoryFilters() {
    const strategyFilter = document.getElementById('history-strategy-filter');
    const startDate = document.getElementById('history-start-date');
    const endDate = document.getElementById('history-end-date');
    const excludeChinext = document.getElementById('history-exclude-chinext');
    const excludeStar = document.getElementById('history-exclude-star');
    
    if (strategyFilter) strategyFilter.value = '';
    if (startDate) startDate.value = '';
    if (endDate) endDate.value = '';
    if (excludeChinext) excludeChinext.checked = false;
    if (excludeStar) excludeStar.checked = false;
    
    showHistoryEmptyState('请点击"查询"按钮加载数据');
}

/**
 * 显示空状态提示
 * @param {string} message - 提示信息
 */
export function showHistoryEmptyState(message) {
    const emptyState = document.getElementById('history-empty');
    if (emptyState) {
        emptyState.innerHTML = `<p style="color: #6b7280;">📭 ${message}</p>`;
        emptyState.style.display = 'block';
    }
    const table = document.getElementById('history-table');
    if (table) table.style.display = 'none';
    const stats = document.getElementById('history-stats');
    if (stats) stats.style.display = 'none';
    const pagination = document.getElementById('history-pagination');
    if (pagination) pagination.style.display = 'none';
}

/**
 * 显示错误信息
 * @param {string} error - 错误信息
 */
export function showHistoryError(error) {
    const errorDiv = document.getElementById('history-error');
    if (errorDiv) {
        errorDiv.innerHTML = `<p style="color: #ef4444;">❌ ${error}</p>`;
        errorDiv.style.display = 'block';
    }
    showHistoryEmptyState('查询失败，请重试');
}

/**
 * 格式化日期
 * @param {string} dateStr - 日期字符串
 * @returns {string} 格式化后的日期
 */
export function formatDate(dateStr) {
    if (!dateStr) return '--';
    // 假设 dateStr 是 YYYYMMDD 格式
    if (dateStr.length === 8) {
        return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`;
    }
    return dateStr;
}

/**
 * 格式化价格
 * @param {number} price - 价格
 * @returns {string} 格式化后的价格
 */
export function formatPrice(price) {
    if (price == null || isNaN(price)) return '--';
    return price.toFixed(2);
}

/**
 * 格式化当日涨跌幅
 * @param {number|null} pct - 涨跌百分比
 * @returns {string} 格式化后的HTML
 */
export function formatDailyChange(pct) {
    if (pct == null || isNaN(pct)) return '<span style="color: #9ca3af;">--</span>';
    const color = pct > 0 ? '#dc2626' : pct < 0 ? '#16a34a' : '#6b7280';
    const sign = pct > 0 ? '+' : '';
    return `<span style="color: ${color}; font-weight: 600;">${sign}${pct.toFixed(2)}%</span>`;
}

/**
 * 转义HTML字符
 * @param {string} text - 文本
 * @returns {string} 转义后的文本
 */
export function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
