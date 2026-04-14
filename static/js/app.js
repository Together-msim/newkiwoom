// ========== 페이지 전환 ==========
document.addEventListener('DOMContentLoaded', () => {
    // 네비게이션 클릭 이벤트
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const page = item.dataset.page;
            switchPage(page);
        });
    });

    // 초기 페이지 로드
    loadWatchlist();
    loadMode2List();

    // 이벤트 리스너 등록
    setupEventListeners();
});

function switchPage(pageName) {
    // 네비게이션 활성화
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === pageName) {
            item.classList.add('active');
        }
    });

    // 페이지 표시
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });

    const targetPage = document.getElementById(pageName + 'Page');
    if (targetPage) {
        targetPage.classList.add('active');
    }

    // 페이지별 데이터 로드
    if (pageName === 'watchlist') loadWatchlist();
    else if (pageName === 'mode1') loadMode1List();
    else if (pageName === 'mode2') loadMode2List();
    else if (pageName === 'tradelog') loadTradelog();
}

function setupEventListeners() {
    // Mode1 페이지
    const addMode1 = document.getElementById('addMode1');
    if (addMode1) {
        addMode1.addEventListener('click', showMode1Form);
    }

    const mode1Form = document.getElementById('mode1FormElement');
    if (mode1Form) {
        mode1Form.addEventListener('submit', handleMode1Submit);
    }

    const addCondition = document.getElementById('addCondition');
    if (addCondition) {
        addCondition.addEventListener('click', addConditionRow);
    }

    const mode1Code = document.getElementById('mode1Code');
    if (mode1Code) {
        mode1Code.addEventListener('blur', autoFetchStockName);
    }

    // Mode2 폼
    const mode2Form = document.getElementById('mode2Form');
    if (mode2Form) {
        mode2Form.addEventListener('submit', handleMode2Submit);
    }

    const mode2Code = document.getElementById('mode2Code');
    if (mode2Code) {
        mode2Code.addEventListener('blur', autoFetchMode2StockName);
    }

    // Test 페이지
    const testGetInfo = document.getElementById('testGetInfo');
    if (testGetInfo) {
        testGetInfo.addEventListener('click', handleTestStockInfo);
    }

    const testGetChart = document.getElementById('testGetChart');
    if (testGetChart) {
        testGetChart.addEventListener('click', handleTestChart);
    }

    const testCheckToken = document.getElementById('testCheckToken');
    if (testCheckToken) {
        testCheckToken.addEventListener('click', handleTestToken);
    }

    const testGetDailyChart = document.getElementById('testGetDailyChart');
    if (testGetDailyChart) {
        testGetDailyChart.addEventListener('click', handleTestDailyChart);
    }

    // 새로고침
    const refreshWatchlist = document.getElementById('refreshWatchlist');
    if (refreshWatchlist) {
        refreshWatchlist.addEventListener('click', loadWatchlist);
    }

    const loadAccountPositions = document.getElementById('loadAccountPositions');
    if (loadAccountPositions) {
        loadAccountPositions.addEventListener('click', handleLoadAccountPositions);
    }

    const testPlaceBuy = document.getElementById('testPlaceBuy');
    if (testPlaceBuy) {
        testPlaceBuy.addEventListener('click', handleTestPlaceBuy);
    }

    const testPlaceSell = document.getElementById('testPlaceSell');
    if (testPlaceSell) {
        testPlaceSell.addEventListener('click', handleTestPlaceSell);
    }

    const syncHoldingsToWatchlist = document.getElementById('syncHoldingsToWatchlist');
    if (syncHoldingsToWatchlist) {
        syncHoldingsToWatchlist.addEventListener('click', handleSyncHoldings);
    }

    // 주문 모드 토글 이벤트 리스너
    const testOrderRealMode = document.getElementById('testOrderRealMode');
    if (testOrderRealMode) {
        testOrderRealMode.addEventListener('change', handleTestOrderModeToggle);
    }
}

// ========== 주문 모드 토글 ==========
function handleTestOrderModeToggle() {
    const checkbox = document.getElementById('testOrderRealMode');
    const label = document.getElementById('testOrderModeLabel');
    const warning = document.getElementById('testOrderWarning');

    if (checkbox.checked) {
        // 실제 주문 모드
        label.textContent = '🔥 실제주문';
        label.style.color = '#c92a2a';
        label.style.fontWeight = 'bold';
        warning.innerHTML = `
            <div style="background: #ffe3e3; border-left: 4px solid #c92a2a; padding: 16px; margin-top: 12px; border-radius: 6px;">
                <div style="color: #c92a2a; font-weight: bold; font-size: 15px; margin-bottom: 8px;">⚠️ 실제 주문 모드 활성화됨</div>
                <div style="color: #495057; font-size: 13px;">
                    - 실제 계좌에 주문이 실행됩니다<br>
                    - 주문 전 반드시 종목, 수량, 가격을 확인하세요<br>
                    - 시장 상황에 따라 체결 가격이 다를 수 있습니다
                </div>
            </div>
        `;
    } else {
        // 시뮬레이션 모드
        label.textContent = '🔒 시뮬레이션';
        label.style.color = '#868e96';
        label.style.fontWeight = 'normal';
        warning.innerHTML = `
            <div style="background: #e9ecef; border-left: 4px solid #868e96; padding: 16px; margin-top: 12px; border-radius: 6px;">
                <div style="color: #495057; font-weight: bold; font-size: 15px; margin-bottom: 8px;">ℹ️ 시뮬레이션 모드</div>
                <div style="color: #868e96; font-size: 13px;">
                    - 실제 주문이 실행되지 않습니다<br>
                    - 주문 API 테스트 및 동작 확인 용도<br>
                    - 실제 주문을 원하시면 위 토글을 켜주세요
                </div>
            </div>
        `;
    }
}

// ========== 감시리스트 (통합) ==========
async function loadWatchlist() {
    try {
        // Mode1과 Mode2 데이터 모두 로드
        const [mode1Response, mode2Response] = await Promise.all([
            fetch('/api/mode1/watchers'),
            fetch('/api/mode2/watchers')
        ]);

        const mode1Result = await mode1Response.json();
        const mode2Result = await mode2Response.json();

        const allWatchers = [];

        if (mode1Result.success) {
            mode1Result.data.forEach(w => {
                w.mode = 'mode1';
                allWatchers.push(w);
            });
        }

        if (mode2Result.success) {
            mode2Result.data.forEach(w => {
                w.mode = 'mode2';
                allWatchers.push(w);
            });
        }

        renderWatchlist(allWatchers);

        // 자동으로 보유종목 조회 (백그라운드)
        handleLoadAccountPositions(true);  // silent mode
    } catch (error) {
        console.error('감시리스트 로드 실패:', error);
    }
}

function renderWatchlist(watchers) {
    const tbody = document.getElementById('watchlistTableBody');
    if (!tbody) return;

    if (watchers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="empty-state"><h3>등록된 종목이 없습니다</h3></td></tr>';
        return;
    }

    tbody.innerHTML = watchers.map(w => {
        const profit = w.bought_price ?
            ((w.current_price || 0) - w.bought_price) / w.bought_price * 100 : 0;

        const mode = w.mode || 'mode2';
        const modeBadgeClass = mode === 'mode1' ? 'mode1' : 'mode2';
        const modeText = mode === 'mode1' ? 'Mode1' : 'Mode2';

        // 보유수량
        const holdingQty = w.bought_quantity || 0;

        // 액션 버튼
        let actionButtons = `
            <button class="btn ${w.active ? 'btn-warning' : 'btn-success'}"
                    onclick="toggleWatchlistActive('${w.code}', '${mode}', ${!w.active})"
                    style="font-size: 11px; padding: 4px 8px;">
                ${w.active ? 'OFF' : 'ON'}
            </button>
        `;

        // waiting_sell 상태일 때 매도 버튼 추가
        if (w.status === 'waiting_sell' && holdingQty > 0) {
            actionButtons += `
                <button class="btn btn-danger"
                        onclick="showSellModal('${w.code}', '${w.name || w.code}', ${holdingQty}, ${w.bought_price || 0}, '${mode}')"
                        style="font-size: 11px; padding: 4px 8px; margin-left: 4px;">
                    매도
                </button>
            `;
        }

        actionButtons += `
            <button class="btn btn-danger" onclick="deleteWatchlistItem('${w.code}', '${mode}')"
                    style="font-size: 11px; padding: 4px 8px; margin-left: 4px;">X</button>
        `;

        return `
            <tr class="${w.active ? '' : 'inactive'}">
                <td><span class="mode-badge ${modeBadgeClass}">${modeText}</span></td>
                <td><strong>${w.code}</strong></td>
                <td>${w.name || '-'}</td>
                <td>${formatDate(w.created_at)}</td>
                <td><span class="status-badge status-${w.status}">${getStatusText(w.status)}</span></td>
                <td><strong>${holdingQty}주</strong></td>
                <td>-</td>
                <td>${w.bought_price ? formatNumber(w.bought_price) : '-'}</td>
                <td class="${profit >= 0 ? 'text-profit' : 'text-loss'}">${profit.toFixed(2)}%</td>
                <td style="white-space: nowrap;">
                    ${actionButtons}
                </td>
            </tr>
        `;
    }).join('');
}

// ========== Mode2 ==========
async function loadMode2List() {
    try {
        const response = await fetch('/api/mode2/watchers');
        const result = await response.json();

        if (result.success) {
            renderMode2Table(result.data);
        }
    } catch (error) {
        console.error('Mode2 리스트 로드 실패:', error);
    }
}

function renderMode2Table(watchers) {
    const tbody = document.getElementById('mode2TableBody');
    if (!tbody) return;

    if (watchers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="14" class="empty-state"><h3>등록된 종목이 없습니다</h3></td></tr>';
        return;
    }

    tbody.innerHTML = watchers.map(w => {
        const notifyOnly = w.notify_only || false;
        const modeTag = notifyOnly
            ? '<span style="background: #ffc107; color: #000; padding: 2px 8px; border-radius: 4px; font-size: 11px;">🔔 알림</span>'
            : '<span style="background: #28a745; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 11px;">🤖 자동</span>';

        return `
        <tr class="${w.active ? '' : 'inactive'}">
            <td><input type="checkbox" class="row-checkbox" data-code="${w.code}" onclick="selectMode2Row('${w.code}')"></td>
            <td><strong>${w.code}</strong></td>
            <td contenteditable="true" data-field="name" data-code="${w.code}" onblur="updateMode2Field('${w.code}', 'name', this.textContent)">${w.name || '-'}</td>
            <td contenteditable="true" data-field="buy_target_price" data-code="${w.code}" onblur="updateMode2Field('${w.code}', 'buy_target_price', this.textContent)">${formatNumber(w.buy_target_price)}</td>
            <td contenteditable="true" data-field="budget" data-code="${w.code}" onblur="updateMode2Field('${w.code}', 'budget', this.textContent)">${formatNumber(w.budget)}</td>
            <td>${w.quantity}주</td>
            <td contenteditable="true" data-field="support_2" data-code="${w.code}" onblur="updateMode2LevelField('${w.code}', 'support_2', this.textContent)">${formatNumber(w.support_2_price)} (${w.support_2_loss_pct}%)</td>
            <td contenteditable="true" data-field="support_1" data-code="${w.code}" onblur="updateMode2LevelField('${w.code}', 'support_1', this.textContent)">${formatNumber(w.support_1_price)} (${w.support_1_loss_pct}%)</td>
            <td contenteditable="true" data-field="resistance_1" data-code="${w.code}" onblur="updateMode2LevelField('${w.code}', 'resistance_1', this.textContent)">${formatNumber(w.resistance_1_price)} (${w.resistance_1_profit_pct}%)</td>
            <td contenteditable="true" data-field="resistance_2" data-code="${w.code}" onblur="updateMode2LevelField('${w.code}', 'resistance_2', this.textContent)">${formatNumber(w.resistance_2_price)} (${w.resistance_2_profit_pct}%)</td>
            <td contenteditable="true" data-field="polling_interval" data-code="${w.code}" onblur="updateMode2Field('${w.code}', 'polling_interval', this.textContent)">${w.polling_interval || 10}초</td>
            <td onclick="toggleMode2NotifyOnly('${w.code}', ${!notifyOnly})" style="cursor: pointer;" title="클릭하여 모드 변경">${modeTag}</td>
            <td><span class="status-badge status-${w.status}">${getStatusText(w.status)}</span></td>
            <td>
                <button class="btn ${w.active ? 'btn-warning' : 'btn-success'}"
                        onclick="toggleActive('${w.code}', ${!w.active})">
                    ${w.active ? 'OFF' : 'ON'}
                </button>
                <button class="btn btn-danger" onclick="deleteMode2('${w.code}')">X</button>
            </td>
        </tr>
        `;
    }).join('');
}

async function handleMode2Submit(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const code = formData.get('code');
    const name = formData.get('name');
    const notifyOnly = document.getElementById('mode2NotifyOnly').checked;

    const data = {
        code: code,
        name: name,
        buy_target_price: parseInt(formData.get('buy_target_price')) || 0,
        budget: parseInt(formData.get('budget')) || 1000000,
        polling_interval: parseInt(formData.get('polling_interval')) || 10,
        notify_only: notifyOnly,
        resistance_1_price: parseInt(formData.get('resistance_1_price')) || 0,
        resistance_1_profit_pct: parseFloat(formData.get('resistance_1_profit_pct')) || 0,
        resistance_2_price: parseInt(formData.get('resistance_2_price')) || 0,
        resistance_2_profit_pct: parseFloat(formData.get('resistance_2_profit_pct')) || 0,
        support_1_price: parseInt(formData.get('support_1_price')) || 0,
        support_1_loss_pct: parseFloat(formData.get('support_1_loss_pct')) || 0,
        support_2_price: parseInt(formData.get('support_2_price')) || 0,
        support_2_loss_pct: parseFloat(formData.get('support_2_loss_pct')) || 0,
    };

    try {
        // 종목이 이미 있는지 확인하고 있으면 UPDATE
        const existingResponse = await fetch(`/api/mode2/watchers/${code}`);
        const isUpdate = existingResponse.ok;

        const url = isUpdate ? `/api/mode2/watchers/${code}` : '/api/mode2/watchers';
        const method = isUpdate ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showToast(`✓ ${isUpdate ? '수정' : '등록'} 완료`, 'success');
            e.target.reset();
            document.getElementById('mode2Name').value = '';
            loadMode2List();
            loadWatchlist();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast('요청 실패: ' + error.message, 'error');
    }
}

async function deleteMode2(code) {
    if (!confirm(`종목 ${code}를 삭제하시겠습니까?`)) return;

    try {
        const response = await fetch(`/api/mode2/watchers/${code}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showToast('✓ 삭제 완료', 'success');
            loadMode2List();
            loadWatchlist();
        }
    } catch (error) {
        showToast('요청 실패: ' + error.message, 'error');
    }
}

// ========== Mode1 ==========
let conditionCounter = 0;

function showMode1Form() {
    const formSection = document.getElementById('mode1Form');
    formSection.style.display = 'block';

    // 조건 컨테이너 초기화
    const container = document.getElementById('conditionsContainer');
    container.innerHTML = '';
    conditionCounter = 0;

    // 기본 조건 1개 추가
    addConditionRow();

    formSection.scrollIntoView({ behavior: 'smooth' });
}

function cancelMode1Form() {
    document.getElementById('mode1Form').style.display = 'none';
    document.getElementById('mode1FormElement').reset();
}

function addConditionRow() {
    const container = document.getElementById('conditionsContainer');
    const id = conditionCounter++;

    const row = document.createElement('div');
    row.className = 'condition-row';
    row.dataset.id = id;
    row.innerHTML = `
        <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px; padding: 12px; background: #f8f9fa; border-radius: 6px;">
            <select name="condition_interval_${id}" style="padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;">
                <option value="1분">1분봉</option>
                <option value="3분">3분봉</option>
                <option value="5분">5분봉</option>
                <option value="10분">10분봉</option>
            </select>
            <select name="condition_trend_${id}" style="padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;">
                <option value="상승">상승</option>
                <option value="하락">하락</option>
            </select>
            <input type="number" name="condition_count_${id}" placeholder="연속 N개" value="1" min="1"
                   style="width: 90px; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;">
            <span style="font-size: 13px; color: #868e96;">개 연속</span>
            <input type="number" name="condition_candle_count_${id}" placeholder="조회 봉수" value="20" min="1" max="200"
                   style="width: 90px; padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;">
            <span style="font-size: 13px; color: #868e96;">개 조회</span>
            <button type="button" onclick="removeConditionRow(${id})" class="btn btn-danger" style="margin-left: auto;">삭제</button>
        </div>
    `;

    container.appendChild(row);
}

function removeConditionRow(id) {
    const row = document.querySelector(`.condition-row[data-id="${id}"]`);
    if (row) {
        row.remove();
    }
}

async function autoFetchStockName() {
    const codeInput = document.getElementById('mode1Code');
    const nameInput = document.getElementById('mode1Name');
    const code = codeInput.value.trim();

    if (!code) return;

    try {
        const response = await fetch(`/api/test/stock-info/${code}`);
        const result = await response.json();

        if (result.success && result.data.name) {
            nameInput.value = result.data.name;
        }
    } catch (error) {
        console.error('종목명 조회 실패:', error);
    }
}

async function handleMode1Submit(e) {
    e.preventDefault();

    const formData = new FormData(e.target);

    // 기본 데이터
    const data = {
        code: formData.get('code'),
        name: formData.get('name'),
        monitoring_price: parseFloat(formData.get('monitoring_price')) || 0,
        expected_profit_rate: parseFloat(formData.get('expected_profit_rate')) || 0,
        polling_interval: parseInt(formData.get('polling_interval')) || 20,
        monitoring_conditions: []
    };

    // 모니터링 조건 수집
    const conditions = document.querySelectorAll('.condition-row');
    conditions.forEach(row => {
        const id = row.dataset.id;
        const interval = formData.get(`condition_interval_${id}`);
        const trend = formData.get(`condition_trend_${id}`);
        const count = parseInt(formData.get(`condition_count_${id}`)) || 1;
        const candle_count = parseInt(formData.get(`condition_candle_count_${id}`)) || 20;

        data.monitoring_conditions.push({
            interval: interval,
            trend: trend,
            count: count,
            candle_count: candle_count
        });
    });

    try {
        const response = await fetch('/api/mode1/watchers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showToast('✓ 등록 완료', 'success');
            cancelMode1Form();
            loadMode1List();
            loadWatchlist();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast('요청 실패: ' + error.message, 'error');
    }
}

async function loadMode1List() {
    try {
        const response = await fetch('/api/mode1/watchers');
        const result = await response.json();

        if (result.success) {
            renderMode1Table(result.data);
        }
    } catch (error) {
        console.error('Mode1 리스트 로드 실패:', error);
    }
}

function renderMode1Table(watchers) {
    const tbody = document.getElementById('mode1TableBody');
    if (!tbody) return;

    if (watchers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="empty-state"><h3>등록된 종목이 없습니다</h3><p>위 버튼으로 종목을 추가하세요</p></td></tr>';
        return;
    }

    tbody.innerHTML = watchers.map(w => {
        const conditions = w.monitoring_conditions || [];
        const conditionsText = conditions.map(c =>
            `${c.interval}/${c.trend}/${c.count}개 (조회:${c.candle_count || 20})`
        ).join('<br>');

        return `
            <tr class="${w.active ? '' : 'inactive'}">
                <td><strong>${w.code}</strong></td>
                <td>${w.name || '-'}</td>
                <td>${formatNumber(w.monitoring_price)}</td>
                <td style="font-size: 11px; line-height: 1.6;">${conditionsText || '-'}</td>
                <td>${w.polling_interval}초</td>
                <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${w.insight || ''}">${w.insight || '-'}</td>
                <td>${w.expected_profit_rate}%</td>
                <td><span class="status-badge status-${w.status}">${getStatusText(w.status)}</span></td>
                <td>
                    <div class="action-buttons">
                        <button class="btn ${w.active ? 'btn-warning' : 'btn-success'}"
                                onclick="toggleMode1Active('${w.code}', ${!w.active})">
                            ${w.active ? 'OFF' : 'ON'}
                        </button>
                        <button class="btn btn-danger" onclick="deleteMode1('${w.code}')">X</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

async function toggleMode1Active(code, active) {
    try {
        const response = await fetch(`/api/mode1/watchers/${code}/active`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ active })
        });

        const result = await response.json();

        if (result.success) {
            showToast(active ? '✓ ON' : '✓ OFF', 'success');
            loadMode1List();
            loadWatchlist();
        }
    } catch (error) {
        showToast('요청 실패', 'error');
    }
}

async function deleteMode1(code) {
    if (!confirm(`종목 ${code}를 삭제하시겠습니까?`)) return;

    try {
        const response = await fetch(`/api/mode1/watchers/${code}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showToast('✓ 삭제 완료', 'success');
            loadMode1List();
            loadWatchlist();
        }
    } catch (error) {
        showToast('요청 실패', 'error');
    }
}

// ========== 매매일지 ==========
function loadTradelog() {
    const tbody = document.getElementById('tradelogTableBody');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="9" class="empty-state"><h3>확정 손익 내역이 없습니다</h3></td></tr>';
}

// ========== Test 페이지 ==========
async function handleTestStockInfo() {
    const code = document.getElementById('testCode').value.trim();
    if (!code) {
        alert('종목코드를 입력하세요');
        return;
    }

    const resultDiv = document.getElementById('testInfoResult');
    resultDiv.innerHTML = '<div style="color: #868e96;">조회 중...</div>';

    try {
        const response = await fetch(`/api/test/stock-info/${code}`);
        const result = await response.json();

        if (result.success) {
            const data = result.data;
            resultDiv.innerHTML = `
                <div style="color: #2b8a3e; font-weight: bold; margin-bottom: 12px;">✓ 조회 성공</div>
                <pre>${JSON.stringify(data, null, 2)}</pre>
                <div style="margin-top: 12px; padding: 12px; background: #e7f5ff; border-radius: 6px;">
                    <div><strong>종목코드:</strong> ${data.code}</div>
                    <div><strong>종목명:</strong> ${data.name || '(조회 안됨)'}</div>
                    <div><strong>현재가:</strong> ${data.current_price ? formatNumber(data.current_price) + '원' : '0원'}</div>
                </div>
            `;
        } else {
            resultDiv.innerHTML = `<div style="color: #c92a2a;">✗ 실패: ${result.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div style="color: #c92a2a;">✗ 요청 실패: ${error.message}</div>`;
    }
}

async function handleTestChart() {
    const code = document.getElementById('testChartCode').value.trim();
    const interval = document.getElementById('testChartInterval').value;

    if (!code) {
        alert('종목코드를 입력하세요');
        return;
    }

    const resultDiv = document.getElementById('testChartResult');
    resultDiv.innerHTML = '<div style="color: #868e96;">조회 중...</div>';

    try {
        const response = await fetch(`/api/test/chart/${code}?interval=${interval}`);
        const result = await response.json();

        if (result.success) {
            resultDiv.innerHTML = `
                <div style="color: #2b8a3e; font-weight: bold; margin-bottom: 12px;">✓ 조회 성공</div>
                <pre>${JSON.stringify(result.data, null, 2)}</pre>
            `;
        } else {
            resultDiv.innerHTML = `<div style="color: #c92a2a;">✗ 실패: ${result.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div style="color: #c92a2a;">✗ 요청 실패: ${error.message}</div>`;
    }
}

async function handleTestToken() {
    const resultDiv = document.getElementById('testTokenResult');
    resultDiv.innerHTML = '<div style="color: #868e96;">확인 중...</div>';

    try {
        const response = await fetch('/api/test/token');
        const result = await response.json();

        if (result.success) {
            const data = result.data;
            resultDiv.innerHTML = `
                <div style="color: #2b8a3e; font-weight: bold; margin-bottom: 12px;">✓ 연결 정상</div>
                <pre>${JSON.stringify(data, null, 2)}</pre>
            `;
        } else {
            resultDiv.innerHTML = `<div style="color: #c92a2a;">✗ 실패: ${result.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div style="color: #c92a2a;">✗ 요청 실패: ${error.message}</div>`;
    }
}

async function handleTestDailyChart() {
    const symbol = document.getElementById('testDailyChartInput').value.trim();
    if (!symbol) {
        alert('종목명 또는 종목코드를 입력하세요');
        return;
    }

    const resultDiv = document.getElementById('testDailyChartResult');
    resultDiv.innerHTML = '<div style="color: #868e96;">조회 중...</div>';

    try {
        const response = await fetch('/api/test/daily-chart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol })
        });

        const result = await response.json();

        if (result.success) {
            const data = result.data;

            // 포맷팅된 메시지 표시
            const formattedMsg = data.formatted_message.split('\n').join('<br>');

            resultDiv.innerHTML = `
                <div style="color: #2b8a3e; font-weight: bold; margin-bottom: 16px;">✓ 조회 성공</div>
                <div style="background: #f8f9fa; padding: 16px; border-radius: 8px; border-left: 4px solid #667eea; margin-bottom: 16px;">
                    <div style="font-size: 18px; font-weight: bold; color: #212529; margin-bottom: 8px;">
                        📈 ${data.name} (${data.code})
                    </div>
                    <div style="font-size: 14px; line-height: 1.8; color: #495057;">
                        ${formattedMsg}
                    </div>
                </div>
                <details>
                    <summary style="cursor: pointer; color: #868e96; margin-bottom: 8px;">📋 원본 데이터 보기</summary>
                    <pre style="background: #f1f3f5; padding: 12px; border-radius: 6px; font-size: 11px; overflow-x: auto;">${JSON.stringify(data.chart, null, 2)}</pre>
                </details>
            `;
        } else {
            resultDiv.innerHTML = `<div style="color: #c92a2a;">✗ 실패: ${result.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div style="color: #c92a2a;">✗ 요청 실패: ${error.message}</div>`;
    }
}

// ========== 공통 함수 ==========
async function toggleActive(code, active) {
    try {
        const response = await fetch(`/api/mode2/watchers/${code}/active`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ active })
        });

        const result = await response.json();

        if (result.success) {
            showToast(active ? '✓ ON' : '✓ OFF', 'success');
            loadMode2List();
            loadWatchlist();
        }
    } catch (error) {
        showToast('요청 실패', 'error');
    }
}

async function deleteWatcher(code) {
    if (!confirm(`종목 ${code}를 삭제하시겠습니까?`)) return;

    try {
        const response = await fetch(`/api/mode2/watchers/${code}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showToast('✓ 삭제 완료', 'success');
            loadMode2List();
            loadWatchlist();
        }
    } catch (error) {
        showToast('요청 실패', 'error');
    }
}

function formatNumber(num) {
    return new Intl.NumberFormat('ko-KR').format(num);
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

function getStatusText(status) {
    const map = {
        'waiting_buy': '매수대기',
        'waiting_sell': '매도대기',
        'auto_sold': '자동매도',
        'manual_sold': '수동매도'
    };
    return map[status] || status;
}

// ========== 계좌 보유 종목 ==========
async function handleLoadAccountPositions(silent = false) {
    const resultDiv = document.getElementById('accountPositionsSection');
    const tableBody = document.getElementById('accountPositionsTableBody');

    if (!silent) {
        resultDiv.style.display = 'block';
        tableBody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 20px; color: #868e96;">조회 중...</td></tr>';
    }

    try {
        const response = await fetch('/api/account/positions');
        const result = await response.json();

        if (result.success) {
            const data = result.data;
            const summary = data.summary;
            const positions = data.positions;

            // 계좌 요약 업데이트
            document.getElementById('accountTotalValue').textContent = formatNumber(summary.total_value) + '원';

            const totalProfit = parseFloat(summary.total_profit || 0);
            const totalProfitEl = document.getElementById('accountTotalProfit');
            totalProfitEl.textContent = formatNumber(Math.abs(totalProfit)) + '원';
            totalProfitEl.style.color = totalProfit >= 0 ? '#2b8a3e' : '#c92a2a';

            const totalProfitRate = parseFloat(summary.total_profit_rate || 0);
            const totalProfitRateEl = document.getElementById('accountTotalProfitRate');
            totalProfitRateEl.textContent = totalProfitRate.toFixed(2) + '%';
            totalProfitRateEl.style.color = totalProfitRate >= 0 ? '#2b8a3e' : '#c92a2a';

            document.getElementById('accountDeposit').textContent = formatNumber(summary.deposit_balance) + '원';

            // 보유 종목 테이블 렌더링
            if (positions.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 20px; color: #868e96;">보유 종목이 없습니다</td></tr>';
            } else {
                tableBody.innerHTML = positions.map(p => {
                    const profitRate = parseFloat(p.profit_rate || 0);
                    const profit = parseFloat(p.profit || 0);

                    return `
                        <tr style="border-bottom: 1px solid #e9ecef;">
                            <td style="padding: 10px; font-size: 13px;"><strong>${p.code}</strong></td>
                            <td style="padding: 10px; font-size: 13px;">${p.name}</td>
                            <td style="padding: 10px; text-align: right; font-size: 13px;">${formatNumber(p.quantity)}주</td>
                            <td style="padding: 10px; text-align: right; font-size: 13px;">${formatNumber(p.buy_price)}원</td>
                            <td style="padding: 10px; text-align: right; font-size: 13px;">${formatNumber(p.current_price)}원</td>
                            <td style="padding: 10px; text-align: right; font-size: 13px; color: ${profit >= 0 ? '#2b8a3e' : '#c92a2a'};">
                                ${profit >= 0 ? '+' : ''}${formatNumber(Math.abs(profit))}원
                            </td>
                            <td style="padding: 10px; text-align: right; font-size: 13px; font-weight: bold; color: ${profitRate >= 0 ? '#2b8a3e' : '#c92a2a'};">
                                ${profitRate >= 0 ? '+' : ''}${profitRate.toFixed(2)}%
                            </td>
                            <td style="padding: 10px; text-align: right; font-size: 13px;">${formatNumber(p.eval_amount)}원</td>
                            <td style="padding: 10px; text-align: center;">
                                <button class="btn btn-danger" style="font-size: 11px; padding: 4px 12px;"
                                        onclick="showHoldingSellModal('${p.code}', '${p.name}', ${p.quantity}, ${p.buy_price})">
                                    매도
                                </button>
                            </td>
                        </tr>
                    `;
                }).join('');
            }

            if (!silent) {
                resultDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        } else {
            tableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 20px; color: #c92a2a;">조회 실패: ${result.error}</td></tr>`;
        }
    } catch (error) {
        tableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 20px; color: #c92a2a;">요청 실패: ${error.message}</td></tr>`;
    }
}

function closeAccountPositions() {
    document.getElementById('accountPositionsSection').style.display = 'none';
}

// 보유종목에서 매도 (감시리스트 모달 재사용)
function showHoldingSellModal(code, name, quantity, buyPrice) {
    showSellModal(code, name, quantity, buyPrice, null);  // mode=null (보유종목 직접 매도)
}

// ========== 감시리스트 매도 기능 ==========
let currentSellItem = null;

function showSellModal(code, name, holdingQty, buyPrice, mode) {
    currentSellItem = { code, name, holdingQty, buyPrice, mode };

    document.getElementById('sellModalCode').textContent = code;
    document.getElementById('sellModalName').textContent = name;
    document.getElementById('sellModalHoldingQty').textContent = holdingQty;
    document.getElementById('sellModalBuyPrice').textContent = formatNumber(buyPrice);
    document.getElementById('sellModalQty').value = '';
    document.getElementById('sellModalType').value = 'market';
    document.getElementById('sellModalPrice').value = '';

    const modal = document.getElementById('sellModal');
    modal.style.display = 'flex';
}

function closeSellModal() {
    document.getElementById('sellModal').style.display = 'none';
    currentSellItem = null;
}

async function executeSellOrder() {
    if (!currentSellItem) return;

    const qtyInput = document.getElementById('sellModalQty').value.trim();
    const qty = qtyInput ? parseInt(qtyInput) : null;
    const orderType = document.getElementById('sellModalType').value;
    const price = parseInt(document.getElementById('sellModalPrice').value) || 0;

    if (orderType === 'limit' && (!price || price <= 0)) {
        alert('지정가 주문일 때 가격을 입력하세요');
        return;
    }

    const qtyText = qty ? `${qty}주` : '전량';
    if (!confirm(`매도 주문을 실행하시겠습니까?\n\n종목: ${currentSellItem.name} (${currentSellItem.code})\n수량: ${qtyText}\n타입: ${orderType}\n가격: ${price || '시장가'}원`)) {
        return;
    }

    try {
        const response = await fetch('/api/order/sell', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: currentSellItem.code,
                quantity: qty,
                order_type: orderType,
                price: price,
                mode: currentSellItem.mode
            })
        });

        const result = await response.json();

        if (result.success) {
            showToast(`✅ 매도 주문 성공 (주문번호: ${result.order_no})`, 'success');
            closeSellModal();
            loadWatchlist();  // 감시리스트 새로고침
            handleLoadAccountPositions(true);  // 보유종목 새로고침 (silent)

            // 텔레그램 알림 전송
            sendTelegramNotification('sell', currentSellItem, qty, price, orderType, result.order_no);
        } else {
            alert(`매도 주문 실패\n\n${result.message || result.error}`);
        }
    } catch (error) {
        alert(`요청 실패: ${error.message}`);
    }
}

async function toggleWatchlistActive(code, mode, active) {
    try {
        const endpoint = mode === 'mode1' ? `/api/mode1/watchers/${code}/active` : `/api/mode2/watchers/${code}/active`;

        const response = await fetch(endpoint, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ active })
        });

        const result = await response.json();

        if (result.success) {
            showToast(active ? '✓ ON' : '✓ OFF', 'success');
            loadWatchlist();
        }
    } catch (error) {
        showToast('요청 실패', 'error');
    }
}

async function deleteWatchlistItem(code, mode) {
    if (!confirm(`종목 ${code}를 삭제하시겠습니까?`)) return;

    try {
        const endpoint = mode === 'mode1' ? `/api/mode1/watchers/${code}` : `/api/mode2/watchers/${code}`;

        const response = await fetch(endpoint, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showToast('✓ 삭제 완료', 'success');
            loadWatchlist();
        }
    } catch (error) {
        showToast('요청 실패', 'error');
    }
}

async function handleSyncHoldings() {
    if (!confirm('계좌 보유 종목 수량을 감시리스트에 동기화하시겠습니까?')) return;

    try {
        const response = await fetch('/api/watchlist/sync-holdings', {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            showToast(`✅ ${result.message}`, 'success');
            loadWatchlist();  // 감시리스트 새로고침
        } else {
            alert(`동기화 실패\n\n${result.error}`);
        }
    } catch (error) {
        alert(`요청 실패: ${error.message}`);
    }
}

// ========== 주문 테스트 ==========
async function handleTestPlaceBuy() {
    const code = document.getElementById('testBuyCode').value.trim();
    const qty = parseInt(document.getElementById('testBuyQty').value);
    const orderType = document.getElementById('testBuyType').value;
    const price = parseInt(document.getElementById('testBuyPrice').value) || 0;

    if (!code) {
        alert('종목코드를 입력하세요');
        return;
    }

    if (!qty || qty <= 0) {
        alert('수량을 입력하세요');
        return;
    }

    if (orderType === 'limit' && (!price || price <= 0)) {
        alert('지정가 주문일 때 가격을 입력하세요');
        return;
    }

    // 시뮬레이션 모드 확인
    const isRealMode = document.getElementById('testOrderRealMode').checked;
    const modeText = isRealMode ? '🔥 실제 주문' : '🔒 시뮬레이션 주문';

    if (!confirm(`${modeText}을 실행하시겠습니까?\n\n종목: ${code}\n수량: ${qty}주\n타입: ${orderType}\n가격: ${price || '시장가'}원`)) {
        return;
    }

    const resultDiv = document.getElementById('testBuyResult');
    resultDiv.innerHTML = '<div style="color: #868e96;">주문 중...</div>';

    try {
        const response = await fetch('/api/order/buy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                quantity: qty,
                order_type: orderType,
                price: price,
                simulation_mode: !isRealMode  // checkbox 체크 안되면 simulation
            })
        });

        const result = await response.json();

        if (result.success) {
            resultDiv.innerHTML = `
                <div style="color: #2b8a3e; font-weight: bold; margin-bottom: 12px;">✅ 매수 주문 성공</div>
                <div style="background: #e7f5ff; padding: 12px; border-radius: 6px;">
                    <div><strong>주문번호:</strong> ${result.order_no || '-'}</div>
                    <div><strong>메시지:</strong> ${result.message}</div>
                </div>
            `;
            showToast('✅ 매수 주문 성공', 'success');
        } else {
            resultDiv.innerHTML = `
                <div style="color: #c92a2a; font-weight: bold; margin-bottom: 12px;">❌ 매수 주문 실패</div>
                <div style="background: #ffe3e3; padding: 12px; border-radius: 6px;">
                    <div><strong>오류:</strong> ${result.message || result.error}</div>
                </div>
            `;
            showToast('❌ 매수 주문 실패', 'error');
        }
    } catch (error) {
        resultDiv.innerHTML = `<div style="color: #c92a2a;">요청 실패: ${error.message}</div>`;
        showToast('요청 실패', 'error');
    }
}

async function handleTestPlaceSell() {
    const code = document.getElementById('testSellCode').value.trim();
    const qtyInput = document.getElementById('testSellQty').value.trim();
    const qty = qtyInput ? parseInt(qtyInput) : null;
    const orderType = document.getElementById('testSellType').value;
    const price = parseInt(document.getElementById('testSellPrice').value) || 0;

    if (!code) {
        alert('종목코드를 입력하세요');
        return;
    }

    if (orderType === 'limit' && (!price || price <= 0)) {
        alert('지정가 주문일 때 가격을 입력하세요');
        return;
    }

    // 시뮬레이션 모드 확인
    const isRealMode = document.getElementById('testOrderRealMode').checked;
    const modeText = isRealMode ? '🔥 실제 주문' : '🔒 시뮬레이션 주문';

    const qtyText = qty ? `${qty}주` : '전량';
    if (!confirm(`${modeText}을 실행하시겠습니까?\n\n종목: ${code}\n수량: ${qtyText}\n타입: ${orderType}\n가격: ${price || '시장가'}원`)) {
        return;
    }

    const resultDiv = document.getElementById('testSellResult');
    resultDiv.innerHTML = '<div style="color: #868e96;">주문 중...</div>';

    try {
        const response = await fetch('/api/order/sell', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                quantity: qty,
                order_type: orderType,
                price: price,
                simulation_mode: !isRealMode  // checkbox 체크 안되면 simulation
            })
        });

        const result = await response.json();

        if (result.success) {
            resultDiv.innerHTML = `
                <div style="color: #2b8a3e; font-weight: bold; margin-bottom: 12px;">✅ 매도 주문 성공</div>
                <div style="background: #e7f5ff; padding: 12px; border-radius: 6px;">
                    <div><strong>주문번호:</strong> ${result.order_no || '-'}</div>
                    <div><strong>메시지:</strong> ${result.message}</div>
                </div>
            `;
            showToast('✅ 매도 주문 성공', 'success');
        } else {
            resultDiv.innerHTML = `
                <div style="color: #c92a2a; font-weight: bold; margin-bottom: 12px;">❌ 매도 주문 실패</div>
                <div style="background: #ffe3e3; padding: 12px; border-radius: 6px;">
                    <div><strong>오류:</strong> ${result.message || result.error}</div>
                </div>
            `;
            showToast('❌ 매도 주문 실패', 'error');
        }
    } catch (error) {
        resultDiv.innerHTML = `<div style="color: #c92a2a;">요청 실패: ${error.message}</div>`;
        showToast('요청 실패', 'error');
    }
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 2500);
}

// ========== Mode2 전용 함수 ==========

// Mode2 종목코드 blur 시 종목명 자동 조회
async function autoFetchMode2StockName() {
    const codeInput = document.getElementById('mode2Code');
    const nameInput = document.getElementById('mode2Name');

    if (!codeInput || !nameInput) return;

    const code = codeInput.value.trim();
    if (!code) {
        nameInput.value = '';
        return;
    }

    try {
        const response = await fetch(`/api/test/stock-info/${code}`);
        const result = await response.json();

        if (result.success && result.data) {
            nameInput.value = result.data.name || '';
        } else {
            nameInput.value = '조회 실패';
        }
    } catch (error) {
        console.error('종목명 조회 실패:', error);
        nameInput.value = '조회 실패';
    }
}

// 체크박스 클릭 시 폼에 auto-fill
let mode2Watchers = [];

async function selectMode2Row(code) {
    // 모든 체크박스를 uncheck하고 현재 것만 check
    document.querySelectorAll('.row-checkbox').forEach(cb => {
        cb.checked = (cb.dataset.code === code);
    });

    // 해당 종목의 데이터 가져오기
    try {
        const response = await fetch(`/api/mode2/watchers/${code}`);
        const result = await response.json();

        if (result.success && result.data) {
            const w = result.data;

            // 폼에 값 채우기
            document.getElementById('mode2Code').value = w.code;
            document.getElementById('mode2Name').value = w.name || '';
            document.getElementById('mode2Budget').value = w.budget;
            document.getElementById('mode2PollingInterval').value = w.polling_interval || 10;
            document.getElementById('mode2NotifyOnly').checked = w.notify_only || false;

            document.querySelector('input[name="buy_target_price"]').value = w.buy_target_price;
            document.querySelector('input[name="resistance_2_price"]').value = w.resistance_2_price;
            document.querySelector('input[name="resistance_2_profit_pct"]').value = w.resistance_2_profit_pct;
            document.querySelector('input[name="resistance_1_price"]').value = w.resistance_1_price;
            document.querySelector('input[name="resistance_1_profit_pct"]').value = w.resistance_1_profit_pct;
            document.querySelector('input[name="support_1_price"]').value = w.support_1_price;
            document.querySelector('input[name="support_1_loss_pct"]').value = w.support_1_loss_pct;
            document.querySelector('input[name="support_2_price"]').value = w.support_2_price;
            document.querySelector('input[name="support_2_loss_pct"]').value = w.support_2_loss_pct;

            showToast('✓ 데이터 로드 완료', 'success');
        }
    } catch (error) {
        console.error('종목 데이터 조회 실패:', error);
        showToast('데이터 로드 실패', 'error');
    }
}

// 인라인 에디팅 - 일반 필드 (name, buy_target_price, budget, polling_interval)
async function updateMode2Field(code, field, value) {
    const cleanValue = value.replace(/[^0-9]/g, ''); // 숫자만 추출

    let updateData = {};

    if (field === 'name') {
        updateData[field] = value;
    } else if (field === 'buy_target_price' || field === 'budget') {
        updateData[field] = parseInt(cleanValue) || 0;
    } else if (field === 'polling_interval') {
        updateData[field] = parseInt(cleanValue) || 10;
    }

    try {
        const response = await fetch(`/api/mode2/watchers/${code}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });

        const result = await response.json();

        if (result.success) {
            showToast('✓ 저장됨', 'success');
            loadMode2List();
        } else {
            showToast('저장 실패', 'error');
        }
    } catch (error) {
        console.error('필드 업데이트 실패:', error);
        showToast('저장 실패', 'error');
    }
}

// 인라인 에디팅 - 레벨 필드 (support_1, support_2, resistance_1, resistance_2)
async function updateMode2LevelField(code, level, value) {
    // 형식: "123000 (5%)" 또는 "123000 (5.5%)"
    const match = value.match(/(\d+)\s*\(([0-9.]+)%?\)/);

    if (!match) {
        showToast('형식 오류: 123000 (5%)', 'error');
        loadMode2List();
        return;
    }

    const price = parseInt(match[1]);
    const pct = parseFloat(match[2]);

    const updateData = {};
    updateData[`${level}_price`] = price;

    if (level.startsWith('support')) {
        updateData[`${level}_loss_pct`] = pct;
    } else {
        updateData[`${level}_profit_pct`] = pct;
    }

    try {
        const response = await fetch(`/api/mode2/watchers/${code}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });

        const result = await response.json();

        if (result.success) {
            showToast('✓ 저장됨', 'success');
            loadMode2List();
        } else {
            showToast('저장 실패', 'error');
        }
    } catch (error) {
        console.error('레벨 업데이트 실패:', error);
        showToast('저장 실패', 'error');
    }
}

// 알림 전용 모드 토글
async function toggleMode2NotifyOnly(code, notifyOnly) {
    try {
        const response = await fetch(`/api/mode2/watchers/${code}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notify_only: notifyOnly })
        });

        const result = await response.json();

        if (result.success) {
            const mode = notifyOnly ? '알림 전용' : '자동매매';
            showToast(`✓ ${mode} 모드로 변경됨`, 'success');
            loadMode2List();
        } else {
            showToast('모드 변경 실패', 'error');
        }
    } catch (error) {
        console.error('모드 변경 실패:', error);
        showToast('모드 변경 실패', 'error');
    }
}

// 텔레그램 알림 전송
async function sendTelegramNotification(action, item, quantity, price, orderType, orderNo) {
    try {
        const qtyText = quantity ? `${quantity}주` : '전량';
        const priceText = orderType === 'market' ? '시장가' : `${formatNumber(price)}원`;

        const message = `
🔔 ${action === 'sell' ? '매도' : '매수'} 체결 알림

종목: ${item.name} (${item.code})
수량: ${qtyText}
가격: ${priceText}
타입: ${orderType === 'market' ? '시장가' : '지정가'}
주문번호: ${orderNo}

✅ 주문이 성공적으로 체결되었습니다.
        `.trim();

        const response = await fetch('/api/test/telegram', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const result = await response.json();

        if (result.success) {
            console.log('텔레그램 알림 전송 완료');
        } else {
            console.error('텔레그램 알림 실패:', result.error);
        }
    } catch (error) {
        console.error('텔레그램 알림 전송 실패:', error);
    }
}
