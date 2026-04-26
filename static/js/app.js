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
    else if (pageName === 'test') loadMode2PickList(); // Test 페이지 진입 시 picklist 로드
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

    const mode1LookupBtn = document.getElementById('mode1LookupBtn');
    if (mode1LookupBtn) {
        mode1LookupBtn.addEventListener('click', handleMode1Lookup);
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

    const mode2LookupBtn = document.getElementById('mode2LookupBtn');
    if (mode2LookupBtn) {
        mode2LookupBtn.addEventListener('click', handleMode2Lookup);
    }

    // Mode2 notify_only 체크박스 변경 시 polling 자동 조정
    const mode2NotifyOnly = document.getElementById('mode2NotifyOnly');
    const mode2PollingInterval = document.getElementById('mode2PollingInterval');
    if (mode2NotifyOnly && mode2PollingInterval) {
        mode2NotifyOnly.addEventListener('change', () => {
            // 알림 전용: 3분(180초), 자동매매: 30초
            mode2PollingInterval.value = mode2NotifyOnly.checked ? '180' : '30';
        });
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

    // 텔레그램 테스트
    const telegramTemplate = document.getElementById('telegramTemplate');
    if (telegramTemplate) {
        telegramTemplate.addEventListener('change', handleTelegramTemplateChange);
    }

    const testSendTelegram = document.getElementById('testSendTelegram');
    if (testSendTelegram) {
        testSendTelegram.addEventListener('click', handleTestSendTelegram);
    }

    const testClearTelegram = document.getElementById('testClearTelegram');
    if (testClearTelegram) {
        testClearTelegram.addEventListener('click', () => {
            document.getElementById('telegramMessage').value = '';
            document.getElementById('telegramTemplate').value = '';
            document.getElementById('testTelegramResult').innerHTML = '';
        });
    }

    // 미체결 주문 조회
    const refreshPendingOrders = document.getElementById('refreshPendingOrders');
    if (refreshPendingOrders) {
        refreshPendingOrders.addEventListener('click', loadPendingOrders);
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
            fetch('/api/mode1/watchers', { credentials: 'same-origin' }),
            fetch('/api/mode2/watchers', { credentials: 'same-origin' })
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

        // 매수타점 (Mode1: monitoring_price, Mode2: buy_target_price)
        const targetPrice = mode === 'mode1' ? w.monitoring_price : w.buy_target_price;

        return `
            <tr class="${w.active ? '' : 'inactive'}">
                <td><span class="mode-badge ${modeBadgeClass}">${modeText}</span></td>
                <td><strong>${w.code}</strong></td>
                <td>${w.name || '-'}</td>
                <td>${formatDate(w.created_at)}</td>
                <td><span class="status-badge status-${w.status}">${getStatusText(w.status)}</span></td>
                <td><strong>${holdingQty}주</strong></td>
                <td>${targetPrice ? formatNumber(targetPrice) : '-'}</td>
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
        // 섹션과 종목 데이터 동시 로드
        const [sectionsRes, watchersRes] = await Promise.all([
            fetch('/api/mode2/sections', { credentials: 'same-origin' }),
            fetch('/api/mode2/watchers', { credentials: 'same-origin' })
        ]);

        const sectionsResult = await sectionsRes.json();
        const watchersResult = await watchersRes.json();

        if (sectionsResult.success && watchersResult.success) {
            renderMode2SectionList(sectionsResult.data, watchersResult.data);
        }
    } catch (error) {
        console.error('Mode2 리스트 로드 실패:', error);
    }
}

function renderMode2SectionList(sections, allWatchers) {
    const container = document.getElementById('mode2SectionsContainer');
    if (!container) return;

    if (sections.length === 0) {
        container.innerHTML = '<div class="mode2-empty">섹션을 추가하여 종목을 관리하세요</div>';
        return;
    }

    // 섹션별로 종목 그룹화
    const watchersBySection = {};
    allWatchers.forEach(w => {
        const sectionId = w.section || 'uncategorized';
        if (!watchersBySection[sectionId]) {
            watchersBySection[sectionId] = [];
        }
        watchersBySection[sectionId].push(w);
    });

    // 각 섹션별로 정렬
    Object.keys(watchersBySection).forEach(sectionId => {
        watchersBySection[sectionId].sort((a, b) =>
            (a.display_order || 9999) - (b.display_order || 9999)
        );
    });

    container.innerHTML = sections.map(section => {
        const watchers = watchersBySection[section.id] || [];
        const collapsed = section.collapsed || false;

        return `
            <div class="mode2-section" data-section-id="${section.id}" data-section-order="${section.order}"
                 draggable="true" ondragstart="handleSectionDragStart(event)" ondragend="handleSectionDragEnd(event)"
                 ondragover="handleSectionDragOver(event)" ondrop="handleSectionDrop(event)">
                <div class="mode2-section-header ${collapsed ? 'collapsed' : ''}" onclick="toggleSection('${section.id}')">
                    <span class="section-drag-handle" title="드래그하여 섹션 이동" style="cursor: move;">☰</span>
                    <span class="section-toggle ${collapsed ? 'collapsed' : ''}">▼</span>
                    <input type="checkbox" class="section-select-all" data-section-id="${section.id}"
                           onclick="event.stopPropagation(); toggleSectionSelectAll('${section.id}')"
                           title="전체 선택" style="margin: 0 8px; width: 16px; height: 16px; cursor: pointer;">
                    <span class="section-name" data-section-id="${section.id}" ondblclick="editSectionName('${section.id}')">${section.name}</span>
                    <span style="color: #adb5bd; font-size: 13px;">(${watchers.length})</span>
                    <div class="section-actions" onclick="event.stopPropagation()">
                        <button class="section-btn section-delete-selected" data-section-id="${section.id}"
                                onclick="deleteSectionSelected('${section.id}')" title="선택 항목 삭제"
                                style="display: none; background: #c92a2a; color: white;">🗑️ 선택 삭제</button>
                        <button class="section-btn" onclick="toggleSectionEditMode('${section.id}')" title="섹션 일괄 편집">✏️</button>
                        ${section.id !== 'uncategorized' ?
                            `<button class="section-btn" onclick="deleteSectionConfirm('${section.id}')" title="섹션 삭제">🗑️</button>` :
                            ''
                        }
                    </div>
                </div>
                <div class="mode2-section-body ${collapsed ? 'collapsed' : ''}" id="section-body-${section.id}">
                    ${watchers.length > 0 ? renderMode2SectionWatchers(section.id, watchers) :
                        '<div class="mode2-empty">종목이 없습니다</div>'}
                </div>
            </div>
        `;
    }).join('');
}

function renderMode2SectionWatchers(sectionId, watchers) {
    // 헤더
    let html = `
        <div class="mode2-header-row">
            <div>✓</div>
            <div>🔼⬇️</div>
            <div>레코드번호</div>
            <div>코드</div>
            <div>종목명</div>
            <div>매수타점</div>
            <div>Budget</div>
            <div>수량</div>
            <div>2차지지</div>
            <div>1차지지</div>
            <div>1차저항</div>
            <div>2차저항</div>
            <div>Polling</div>
            <div>모드</div>
            <div>상태</div>
            <div>모니터링 상태</div>
            <div>자유노트</div>
            <div>액션</div>
        </div>
    `;

    // 종목 rows
    watchers.forEach((w, idx) => {
        html += renderMode2WatcherRow(w, idx);
    });

    return html;
}

function renderMode2WatcherRow(w, idx) {
    const notifyOnly = w.notify_only || false;
    const editMode = false; // 초기값

    return `
        <div class="mode2-watcher-row" data-code="${w.code}" data-section="${w.section}" data-edit-mode="false"
             draggable="true" ondragstart="handleWatcherDragStart(event)" ondragend="handleWatcherDragEnd(event)"
             ondragover="handleWatcherDragOver(event)" ondrop="handleWatcherDrop(event)">
            <div class="watcher-cell">
                <input type="checkbox" class="watcher-checkbox" value="${w.code}" data-section="${w.section}" onchange="handleWatcherCheckboxChange()">
            </div>
            <div class="watcher-drag-handle" style="cursor: move;">☰</div>
            <div class="watcher-cell">${w.record_id || '-'}</div>
            <div class="watcher-cell"><strong>${w.code}</strong></div>
            <div class="watcher-cell" onclick="showNoteModal('${w.name || '-'}', '${w.code}', '${(w.note || '').replace(/'/g, "\\'")}' )" style="cursor: pointer; color: #228be6; font-weight: 600;">${w.name || '-'}</div>
            <div class="watcher-cell editable" data-field="buy_target_price" ondblclick="enableCellEdit(this, '${w.code}')">${formatNumber(w.buy_target_price)}</div>
            <div class="watcher-cell editable" data-field="budget" ondblclick="enableCellEdit(this, '${w.code}')">${formatNumber(w.budget)}</div>
            <div class="watcher-cell">${w.quantity}주</div>
            <div class="watcher-cell editable" data-field="support_2_price" ondblclick="enableCellEdit(this, '${w.code}')">${formatNumber(w.support_2_price)}</div>
            <div class="watcher-cell editable" data-field="support_1_price" ondblclick="enableCellEdit(this, '${w.code}')">${formatNumber(w.support_1_price)}</div>
            <div class="watcher-cell editable" data-field="resistance_1_price" ondblclick="enableCellEdit(this, '${w.code}')">${formatNumber(w.resistance_1_price)}</div>
            <div class="watcher-cell editable" data-field="resistance_2_price" ondblclick="enableCellEdit(this, '${w.code}')">${formatNumber(w.resistance_2_price)}</div>
            <div class="watcher-cell">
                <select onchange="updateWatcherField('${w.code}', 'polling_interval', this.value)">
                    <option value="10" ${w.polling_interval == 10 ? 'selected' : ''}>10초</option>
                    <option value="30" ${w.polling_interval == 30 ? 'selected' : ''}>30초</option>
                    <option value="60" ${w.polling_interval == 60 ? 'selected' : ''}>1분</option>
                    <option value="180" ${w.polling_interval == 180 ? 'selected' : ''}>3분</option>
                    <option value="300" ${w.polling_interval == 300 ? 'selected' : ''}>5분</option>
                    <option value="600" ${w.polling_interval == 600 ? 'selected' : ''}>10분</option>
                </select>
            </div>
            <div class="watcher-cell">
                <div class="mode-toggle">
                    <button class="mode-toggle-btn ${notifyOnly ? 'active' : ''}" onclick="toggleMode2NotifyOnly('${w.code}', true)">🔔</button>
                    <button class="mode-toggle-btn ${!notifyOnly ? 'active' : ''}" onclick="toggleMode2NotifyOnly('${w.code}', false)">🤖</button>
                </div>
            </div>
            <div class="watcher-cell"><span class="status-badge status-${w.status}">${getStatusText(w.status)}</span></div>
            <div class="watcher-cell monitoring-status ${getMonitoringStatusClass(w.monitoring_status)}">${w.monitoring_status || '-'}</div>
            <div class="watcher-cell editable" data-field="note" title="${w.note || ''}" ondblclick="enableCellEdit(this, '${w.code}')">${truncateText(w.note || '', 20)}</div>
            <div class="watcher-actions">
                <div class="active-toggle ${w.active ? 'on' : 'off'}" onclick="toggleActive('${w.code}', ${!w.active})">
                    ${w.active ? 'ON' : 'OFF'}
                </div>
                <button class="watcher-action-btn" onclick="editWatcherRow('${w.code}')" title="수정">✏️</button>
                <button class="watcher-action-btn" onclick="deleteMode2('${w.code}')" title="삭제">🗑️</button>
            </div>
        </div>
    `;
}

function getMonitoringStatusClass(status) {
    if (!status) return '';
    if (status.includes('손절') || status.includes('이탈')) return 'danger';
    if (status.includes('익절') || status.includes('저항 통과')) return 'success';
    if (status.includes('매수타점')) return 'warning';
    return '';
}

function truncateText(text, maxLen) {
    if (!text) return '';
    return text.length > maxLen ? text.substring(0, maxLen) + '...' : text;
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

        // UPDATE일 때 기존 active 상태 유지
        if (isUpdate) {
            const existing = await existingResponse.json();
            if (existing.success && existing.data) {
                data.active = existing.data.active; // 기존 active 상태 보존
            }
        }

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
    // 체크박스 해제
    document.querySelectorAll('.mode1-row-checkbox').forEach(cb => cb.checked = false);

    // 폼 초기화
    document.getElementById('mode1FormElement').reset();
    document.getElementById('mode1Code').readOnly = false;
    document.getElementById('mode1FormTitle').textContent = '📊 종목 추가';
    document.getElementById('mode1SubmitBtn').textContent = '저장';

    // 폼 표시
    const formSection = document.getElementById('mode1Form');
    formSection.style.display = 'block';
    formSection.scrollIntoView({ behavior: 'smooth' });
}

function cancelMode1Form() {
    // 체크박스 해제
    document.querySelectorAll('.mode1-row-checkbox').forEach(cb => cb.checked = false);

    // 폼 숨기기 및 초기화
    document.getElementById('mode1Form').style.display = 'none';
    document.getElementById('mode1FormElement').reset();
    document.getElementById('mode1Code').readOnly = false;
    document.getElementById('mode1FormTitle').textContent = '📊 종목 추가';
    document.getElementById('mode1SubmitBtn').textContent = '저장';
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

    // 3단계 시스템 데이터
    const data = {
        code: formData.get('code'),
        name: formData.get('name'),
        monitoring_price: parseFloat(formData.get('monitoring_price')) || 0,
        expected_profit_rate: parseFloat(formData.get('expected_profit_rate')) || 0,
        polling_interval: parseInt(formData.get('polling_interval')) || 20,
        auto_buy: formData.get('auto_buy') === 'on',  // 체크박스
        step1: {
            interval: formData.get('step1_interval'),
            trend: formData.get('step1_trend'),
            count: parseInt(formData.get('step1_count')) || 4
        },
        step2: {
            interval: formData.get('step2_interval'),
            trend: formData.get('step2_trend'),
            count: parseInt(formData.get('step2_count')) || 1
        },
        step3: {
            interval: formData.get('step3_interval'),
            trend: formData.get('step3_trend'),
            count: parseInt(formData.get('step3_count')) || 2
        }
    };

    // 체크된 행이 있는지 확인 (UPDATE 모드)
    const checkedCheckbox = document.querySelector('.mode1-row-checkbox:checked');
    const isUpdate = checkedCheckbox !== null;
    const method = isUpdate ? 'PUT' : 'POST';
    const url = isUpdate ? `/api/mode1/watchers/${data.code}` : '/api/mode1/watchers';

    // UPDATE일 때 기존 active 상태 보존
    if (isUpdate) {
        try {
            const existingResponse = await fetch(`/api/mode1/watchers/${data.code}`, { credentials: 'same-origin' });
            const existing = await existingResponse.json();
            if (existing.success && existing.data) {
                data.active = existing.data.active; // 기존 active 상태 보존
            }
        } catch (err) {
            console.warn('기존 데이터 조회 실패, active 상태 기본값 사용:', err);
        }
    }

    try {
        const response = await fetch(url, {
            credentials: 'same-origin',
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showToast(isUpdate ? '✓ 수정 완료' : '✓ 등록 완료', 'success');
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
        const response = await fetch('/api/mode1/watchers', { credentials: 'same-origin' });
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
        tbody.innerHTML = '<tr><td colspan="11" class="empty-state"><h3>등록된 종목이 없습니다</h3><p>위 버튼으로 종목을 추가하세요</p></td></tr>';
        return;
    }

    tbody.innerHTML = watchers.map((w, index) => {
        // 3단계 조건 텍스트 생성
        const step1 = w.step1 || {};
        const step2 = w.step2 || {};
        const step3 = w.step3 || {};
        const conditionsText = `
            Step1: ${step1.interval || '1분'}/${step1.trend || '상승'}/${step1.count || 4}개<br>
            Step2: ${step2.interval || '3분'}/${step2.trend || '하락'}/${step2.count || 1}개<br>
            Step3: ${step3.interval || '1분'}/${step3.trend || '상승'}/${step3.count || 2}개
        `;

        return `
            <tr class="${w.active ? '' : 'inactive'}">
                <td>
                    <input type="checkbox" class="mode1-row-checkbox" data-code="${w.code}"
                           style="width: 16px; height: 16px; cursor: pointer;"
                           onchange="handleMode1RowSelect(this, '${w.code}')">
                </td>
                <td><strong>${index + 1}</strong></td>
                <td><strong>${w.code}</strong></td>
                <td>${w.name || '-'}</td>
                <td>${formatNumber(w.monitoring_price)}</td>
                <td style="font-size: 11px; line-height: 1.6;">${conditionsText}</td>
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
        const response = await fetch('/api/test/token', { credentials: 'same-origin' });
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
            credentials: 'same-origin',
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

            // 캔들스틱 차트 그리기
            window.lastDailyChartData = data; // 리사이즈 시 재렌더링용
            drawCandlestickChart(data);
        } else {
            resultDiv.innerHTML = `<div style="color: #c92a2a;">✗ 실패: ${result.error}</div>`;
            document.getElementById('dailyChartCanvas').style.display = 'none';
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
        const response = await fetch('/api/account/positions', {
            credentials: 'same-origin'
        });
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

            // silent 모드에서도 데이터 있으면 표시
            if (!silent) {
                resultDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else if (positions.length > 0) {
                // silent이지만 보유 종목이 있으면 표시
                resultDiv.style.display = 'block';
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
            credentials: 'same-origin',
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
            credentials: 'same-origin',
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
            credentials: 'same-origin',
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
            credentials: 'same-origin',
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

async function handleMode2Lookup() {
    const code = document.getElementById('mode2Code').value.trim();
    if (!code) {
        alert('종목코드를 입력하세요');
        return;
    }

    // 종목명 조회
    await autoFetchMode2StockName();

    // 일봉 차트 조회
    try {
        const response = await fetch('/api/test/daily-chart', {
            credentials: 'same-origin',
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: code })
        });

        const result = await response.json();

        if (result.success) {
            const chartContainer = document.getElementById('mode2ChartContainer');
            chartContainer.style.display = 'block';

            // Mode2 전용 차트 그리기
            window.lastMode2ChartData = result.data; // 리사이즈 시 재렌더링용
            drawMode2CandlestickChart(result.data);
            showToast('✓ 종목명 & 차트 조회 완료', 'success');
        } else {
            // 차트 컨테이너 숨김
            const chartContainer = document.getElementById('mode2ChartContainer');
            chartContainer.style.display = 'none';
            showToast('✓ 종목명 조회 완료 (차트: API 연결 필요)', 'info');
        }
    } catch (error) {
        console.error('차트 조회 실패:', error);
        // 차트 컨테이너 숨김
        const chartContainer = document.getElementById('mode2ChartContainer');
        if (chartContainer) {
            chartContainer.style.display = 'none';
        }
        showToast('✓ 종목명 조회 완료 (차트: API 연결 필요)', 'info');
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
            loadWatchlist(); // 감시리스트도 업데이트
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
            loadWatchlist(); // 감시리스트도 업데이트
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
        // 알림 → 자동매매 전환 시 손절/익절 % 검증
        if (!notifyOnly) {
            const response = await fetch(`/api/mode2/watchers/${code}`, {
                credentials: 'same-origin'
            });
            const result = await response.json();

            if (result.success && result.data) {
                const w = result.data;
                const hasR1 = w.resistance_1_price > 0 && w.resistance_1_profit_pct > 0;
                const hasR2 = w.resistance_2_price > 0 && w.resistance_2_profit_pct > 0;
                const hasS1 = w.support_1_price > 0 && w.support_1_loss_pct > 0;
                const hasS2 = w.support_2_price > 0 && w.support_2_loss_pct > 0;

                if (!hasR1 && !hasR2 && !hasS1 && !hasS2) {
                    showToast('⚠️ 자동매매 모드 전환 불가: 손절/익절 % 값이 없습니다', 'error');
                    return;
                }
            }
        }

        const updateResponse = await fetch(`/api/mode2/watchers/${code}`, {
            credentials: 'same-origin',
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notify_only: notifyOnly })
        });

        const updateResult = await updateResponse.json();

        if (updateResult.success) {
            const mode = notifyOnly ? '알림 전용' : '자동매매';
            showToast(`✓ ${mode} 모드로 변경됨`, 'success');
            loadMode2List();
            loadWatchlist(); // 감시리스트도 업데이트
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
            credentials: 'same-origin',
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

// ========== 미체결 주문 조회 및 취소 ==========
async function loadPendingOrders() {
    const tbody = document.getElementById('pendingOrdersBody');
    tbody.innerHTML = '<tr><td colspan="10" style="padding: 20px; text-align: center; color: #868e96;">조회 중...</td></tr>';

    try {
        const response = await fetch('/api/order/pending', { credentials: 'same-origin' });
        const result = await response.json();

        if (result.success) {
            const orders = result.orders;

            if (orders.length === 0) {
                tbody.innerHTML = '<tr><td colspan="10" style="padding: 20px; text-align: center; color: #868e96;">미체결 주문이 없습니다</td></tr>';
            } else {
                tbody.innerHTML = orders.map(order => {
                    const orderTypeColor = order.order_type === '매수' ? '#1971c2' : '#c92a2a';

                    return `
                        <tr style="border-bottom: 1px solid #e9ecef;">
                            <td style="padding: 10px; font-size: 12px;">${order.order_no}</td>
                            <td style="padding: 10px; font-size: 12px;"><strong>${order.stock_code}</strong></td>
                            <td style="padding: 10px; font-size: 12px;">${order.stock_name}</td>
                            <td style="padding: 10px; text-align: center;">
                                <span style="background: ${orderTypeColor}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">
                                    ${order.order_type}
                                </span>
                            </td>
                            <td style="padding: 10px; text-align: right; font-size: 12px;">${formatNumber(order.order_qty)}주</td>
                            <td style="padding: 10px; text-align: right; font-size: 12px;">${formatNumber(order.order_price)}원</td>
                            <td style="padding: 10px; text-align: right; font-size: 12px; font-weight: bold; color: #f76707;">${formatNumber(order.pending_qty)}주</td>
                            <td style="padding: 10px; text-align: right; font-size: 12px; color: #2b8a3e;">${formatNumber(order.executed_qty)}주</td>
                            <td style="padding: 10px; text-align: center; font-size: 12px;">${order.order_time}</td>
                            <td style="padding: 10px; text-align: center;">
                                <button class="btn btn-danger" style="font-size: 11px; padding: 4px 10px;"
                                        onclick="cancelPendingOrder('${order.order_no}', '${order.stock_code}', ${order.pending_qty}, '${order.order_type}')">
                                    취소
                                </button>
                            </td>
                        </tr>
                    `;
                }).join('');
            }
        } else {
            tbody.innerHTML = `<tr><td colspan="10" style="padding: 20px; text-align: center; color: #c92a2a;">조회 실패: ${result.message || result.error}</td></tr>`;
        }
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="10" style="padding: 20px; text-align: center; color: #c92a2a;">요청 실패: ${error.message}</td></tr>`;
    }
}

async function cancelPendingOrder(orderNo, stockCode, quantity, orderType) {
    const orderTypeEng = orderType === '매수' ? 'buy' : 'sell';

    if (!confirm(`주문을 취소하시겠습니까?\n\n주문번호: ${orderNo}\n종목: ${stockCode}\n수량: ${quantity}주`)) {
        return;
    }

    try {
        const response = await fetch('/api/order/cancel', {
            credentials: 'same-origin',
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                order_no: orderNo,
                code: stockCode,
                quantity: quantity,
                order_type: orderTypeEng
            })
        });

        const result = await response.json();

        if (result.success) {
            showToast('✅ 주문 취소 완료', 'success');
            // 미체결 목록 다시 조회
            loadPendingOrders();
        } else {
            alert(`주문 취소 실패\n\n${result.message || result.error}`);
        }
    } catch (error) {
        alert(`요청 실패: ${error.message}`);
    }
}

// ========== 꺾은선 그래프 (일봉) ==========
function drawCandlestickChart(data) {
    const canvas = document.getElementById('candlestickChart');
    const canvasContainer = document.getElementById('dailyChartCanvas');

    if (!canvas || !data.chart) {
        canvasContainer.style.display = 'none';
        return;
    }

    canvasContainer.style.display = 'block';

    // 반응형 캔버스 크기 조정
    const containerWidth = canvasContainer.offsetWidth;
    const isMobile = window.innerWidth <= 768;

    if (isMobile) {
        canvas.width = Math.min(containerWidth, 700);
        canvas.height = 280;
    } else {
        canvas.width = Math.min(containerWidth, 900);
        canvas.height = 400;
    }

    const ctx = canvas.getContext('2d');

    // Canvas 초기화
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 데이터 추출
    const chart = data.chart;
    const yesterday = {
        open: parseFloat(chart.yesterday_open) || 0,
        high: parseFloat(chart.yesterday_high) || 0,
        low: parseFloat(chart.yesterday_low) || 0,
        close: parseFloat(chart.yesterday_close) || 0
    };
    const today = {
        open: parseFloat(chart.today_open) || 0,
        high: parseFloat(chart.today_high) || 0,
        low: parseFloat(chart.today_low) || 0,
        close: parseFloat(chart.today_current) || 0
    };

    // 분봉 요약에서 시간 정보 추출 (intraday_summary)
    const summary = data.intraday_summary || {};
    const yesterdayHighFirst = true; // 전일은 시간 정보 없으므로 기본값
    const todayHighFirst = summary.high_time && summary.low_time ?
        summary.high_time < summary.low_time : true;

    // X축 8등분: 0~7
    // 전일: 0=시가, 1=첫번째(고/저), 2=두번째(저/고), 3=종가
    // 당일: 4=시가, 5=첫번째(고/저), 6=두번째(저/고), 7=종가
    const points = [];

    // 전일 포인트 (시간 정보 없으므로 고가 먼저 가정)
    points.push({ x: 0, price: yesterday.open, label: '전일\n시가' });
    if (yesterdayHighFirst) {
        points.push({ x: 1, price: yesterday.high, label: '고가' });
        points.push({ x: 2, price: yesterday.low, label: '저가' });
    } else {
        points.push({ x: 1, price: yesterday.low, label: '저가' });
        points.push({ x: 2, price: yesterday.high, label: '고가' });
    }
    points.push({ x: 3, price: yesterday.close, label: '전일\n종가' });

    // 당일 포인트
    points.push({ x: 4, price: today.open, label: '당일\n시가' });
    if (todayHighFirst) {
        points.push({ x: 5, price: today.high, label: '고가' });
        points.push({ x: 6, price: today.low, label: '저가' });
    } else {
        points.push({ x: 5, price: today.low, label: '저가' });
        points.push({ x: 6, price: today.high, label: '고가' });
    }
    points.push({ x: 7, price: today.close, label: '당일\n종가' });

    // 가격 범위 계산
    const allPrices = points.map(p => p.price).filter(p => p > 0);
    if (allPrices.length === 0) {
        canvasContainer.style.display = 'none';
        return;
    }

    const minPrice = Math.min(...allPrices);
    const maxPrice = Math.max(...allPrices);
    const priceRange = maxPrice - minPrice;
    const padding = priceRange * 0.15; // 15% 여유

    // 차트 영역
    const chartLeft = 80;
    const chartRight = canvas.width - 40;
    const chartTop = 40;
    const chartBottom = canvas.height - 80;
    const chartWidth = chartRight - chartLeft;
    const chartHeight = chartBottom - chartTop;

    // 가격 -> Y좌표 변환
    function priceToY(price) {
        return chartTop + chartHeight * (1 - (price - minPrice + padding) / (priceRange + 2 * padding));
    }

    // X 인덱스 -> X좌표 변환
    function indexToX(index) {
        return chartLeft + (chartWidth / 7) * index;
    }

    // 배경
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 그리드 라인
    ctx.strokeStyle = '#e9ecef';
    ctx.lineWidth = 1;
    const gridLines = 5;
    for (let i = 0; i <= gridLines; i++) {
        const y = chartTop + (chartHeight / gridLines) * i;
        ctx.beginPath();
        ctx.moveTo(chartLeft, y);
        ctx.lineTo(chartRight, y);
        ctx.stroke();

        // 가격 레이블
        const price = maxPrice + padding - ((maxPrice + padding - minPrice - padding) / gridLines) * i;
        ctx.fillStyle = '#868e96';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(Math.round(price).toLocaleString(), chartLeft - 10, y + 4);
    }

    // 수직 구분선 (전일/당일)
    ctx.strokeStyle = '#dee2e6';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    const midX = indexToX(3.5);
    ctx.beginPath();
    ctx.moveTo(midX, chartTop);
    ctx.lineTo(midX, chartBottom);
    ctx.stroke();
    ctx.setLineDash([]);

    // 최고점/최저점 수평선
    const highY = priceToY(maxPrice);
    const lowY = priceToY(minPrice);

    // 최고점 점선 (빨간색)
    ctx.strokeStyle = '#ff6b6b';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(chartLeft, highY);
    ctx.lineTo(chartRight, highY);
    ctx.stroke();

    // 최고점 레이블
    ctx.fillStyle = '#ff6b6b';
    ctx.font = 'bold 11px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`최고 ${maxPrice.toLocaleString()}`, chartRight + 5, highY + 4);

    // 최저점 점선 (파란색)
    ctx.strokeStyle = '#339af0';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(chartLeft, lowY);
    ctx.lineTo(chartRight, lowY);
    ctx.stroke();

    // 최저점 레이블
    ctx.fillStyle = '#339af0';
    ctx.font = 'bold 11px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`최저 ${minPrice.toLocaleString()}`, chartRight + 5, lowY + 4);

    ctx.setLineDash([]);

    // 꺾은선 그래프
    ctx.strokeStyle = '#228be6';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    points.forEach((point, i) => {
        const x = indexToX(point.x);
        const y = priceToY(point.price);
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();

    // 포인트 + 레이블
    points.forEach(point => {
        const x = indexToX(point.x);
        const y = priceToY(point.price);

        // 포인트 원
        ctx.fillStyle = '#228be6';
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, 2 * Math.PI);
        ctx.fill();

        // 테두리
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.stroke();

        // 가격 레이블 + 등락율
        const basePrice = yesterday.close; // 전일 종가 기준
        const changeRate = basePrice > 0 ? ((point.price - basePrice) / basePrice * 100) : 0;
        const changeRateText = changeRate >= 0 ? `(+${changeRate.toFixed(2)}%)` : `(${changeRate.toFixed(2)}%)`;
        const changeColor = changeRate >= 0 ? '#c92a2a' : '#1971c2';

        ctx.fillStyle = '#212529';
        ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(point.price.toLocaleString(), x, y - 24);

        // 등락율 표시
        ctx.fillStyle = changeColor;
        ctx.font = 'bold 12px sans-serif';
        ctx.fillText(changeRateText, x, y - 10);

        // X축 레이블
        ctx.fillStyle = '#495057';
        ctx.font = '13px sans-serif';
        const labels = point.label.split('\n');
        labels.forEach((line, i) => {
            ctx.fillText(line, x, chartBottom + 20 + i * 12);
        });
    });

    // 차트 제목
    ctx.fillStyle = '#212529';
    ctx.font = 'bold 16px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`📊 ${data.name} (${data.code}) - 일봉 차트`, 20, 25);

    // 시간 순서 표시
    if (summary.high_time && summary.low_time) {
        ctx.fillStyle = '#868e96';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'right';
        const timeText = todayHighFirst ? '당일: 고가 → 저가' : '당일: 저가 → 고가';
        ctx.fillText(timeText, canvas.width - 20, 25);
    }
}

// ========== Mode2 전용 일봉 차트 그리기 ==========
function drawMode2CandlestickChart(data) {
    drawCandlestickChart(data, 'mode2CandlestickChart', 'mode2ChartContainer');
}

function drawCandlestickChart(data, canvasId, containerId) {
    const canvas = document.getElementById(canvasId);

    if (!canvas || !data.chart) {
        return;
    }

    // 반응형 캔버스 크기 조정
    const container = document.getElementById(containerId);
    const containerWidth = container.offsetWidth - 32; // padding 제외
    const isMobile = window.innerWidth <= 768;

    if (isMobile) {
        canvas.width = Math.min(containerWidth, 700);
        canvas.height = 280;
    } else {
        // 전체 폭 사용 (최대 제한 제거)
        canvas.width = containerWidth;
        canvas.height = 400;
    }

    const ctx = canvas.getContext('2d');

    // Canvas 초기화
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 데이터 추출
    const chart = data.chart;
    const yesterday = {
        open: parseFloat(chart.yesterday_open) || 0,
        high: parseFloat(chart.yesterday_high) || 0,
        low: parseFloat(chart.yesterday_low) || 0,
        close: parseFloat(chart.yesterday_close) || 0
    };

    // 장중/장 종료 판단 (평일 09:00~15:30)
    const now = new Date();
    const isWeekday = now.getDay() >= 1 && now.getDay() <= 5;
    const hour = now.getHours();
    const minute = now.getMinutes();
    const isMarketOpen = isWeekday && ((hour === 9 && minute >= 0) || (hour > 9 && hour < 15) || (hour === 15 && minute <= 30));

    const today = {
        open: parseFloat(chart.today_open) || 0,
        high: parseFloat(chart.today_high) || 0,
        low: parseFloat(chart.today_low) || 0,
        close: isMarketOpen ? parseFloat(chart.today_current) || 0 : parseFloat(chart.today_close) || parseFloat(chart.today_current) || 0
    };

    // 감시 레벨 데이터 추출
    const levels = data.levels || {};
    const currentPrice = today.close; // 현재가 (장중: today_current, 장 종료: today_close)

    // 분봉 요약에서 시간 정보 추출
    const summary = data.intraday_summary || {};
    const todayHighFirst = summary.high_time && summary.low_time ?
        summary.high_time < summary.low_time : true;

    // X축 8등분 포인트
    const points = [];

    // 전일 포인트
    points.push({ x: 0, price: yesterday.open, label: '전일\n시가' });
    points.push({ x: 1, price: yesterday.high, label: '고가' });
    points.push({ x: 2, price: yesterday.low, label: '저가' });
    points.push({ x: 3, price: yesterday.close, label: '전일\n종가' });

    // 당일 포인트
    points.push({ x: 4, price: today.open, label: '당일\n시가' });
    if (todayHighFirst) {
        points.push({ x: 5, price: today.high, label: '고가' });
        points.push({ x: 6, price: today.low, label: '저가' });
    } else {
        points.push({ x: 5, price: today.low, label: '저가' });
        points.push({ x: 6, price: today.high, label: '고가' });
    }
    points.push({ x: 7, price: today.close, label: '당일\n종가' });

    // 가격 범위 계산 (감시 레벨 포함)
    const allPrices = points.map(p => p.price).filter(p => p > 0);

    // 감시 레벨 가격들도 범위에 포함
    if (levels.buy_target > 0) allPrices.push(levels.buy_target);
    if (levels.resistance_1 > 0) allPrices.push(levels.resistance_1);
    if (levels.resistance_2 > 0) allPrices.push(levels.resistance_2);
    if (levels.support_1 > 0) allPrices.push(levels.support_1);
    if (levels.support_2 > 0) allPrices.push(levels.support_2);

    if (allPrices.length === 0) {
        return;
    }

    const minPrice = Math.min(...allPrices);
    const maxPrice = Math.max(...allPrices);
    const priceRange = maxPrice - minPrice;
    const padding = priceRange * 0.15;

    // 차트 영역
    const chartLeft = 80;
    const chartRight = canvas.width - 150;  // 우측 여유 공간 확보 (레벨 레이블용)
    const chartTop = 30;
    const chartBottom = canvas.height - 60;
    const chartWidth = chartRight - chartLeft;
    const chartHeight = chartBottom - chartTop;

    // 가격 -> Y좌표 변환
    function priceToY(price) {
        return chartTop + chartHeight * (1 - (price - minPrice + padding) / (priceRange + 2 * padding));
    }

    // X 인덱스 -> X좌표 변환
    function indexToX(index) {
        return chartLeft + (chartWidth / 7) * index;
    }

    // 배경
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 그리드 라인
    ctx.strokeStyle = '#e9ecef';
    ctx.lineWidth = 1;
    const gridLines = 4;
    for (let i = 0; i <= gridLines; i++) {
        const y = chartTop + (chartHeight / gridLines) * i;
        ctx.beginPath();
        ctx.moveTo(chartLeft, y);
        ctx.lineTo(chartRight, y);
        ctx.stroke();

        // 가격 레이블
        const price = maxPrice + padding - ((maxPrice + padding - minPrice - padding) / gridLines) * i;
        ctx.fillStyle = '#868e96';
        ctx.font = '13px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(Math.round(price).toLocaleString(), chartLeft - 10, y + 4);
    }

    // 수직 구분선 (전일/당일)
    ctx.strokeStyle = '#dee2e6';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    const midX = indexToX(3.5);
    ctx.beginPath();
    ctx.moveTo(midX, chartTop);
    ctx.lineTo(midX, chartBottom);
    ctx.stroke();
    ctx.setLineDash([]);

    // 최고점/최저점 수평선
    const highY = priceToY(maxPrice);
    const lowY = priceToY(minPrice);

    // 최고점 점선 (빨간색)
    ctx.strokeStyle = '#ff6b6b';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(chartLeft, highY);
    ctx.lineTo(chartRight, highY);
    ctx.stroke();

    // 최고점 레이블
    ctx.fillStyle = '#ff6b6b';
    ctx.font = 'bold 13px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`최고 ${maxPrice.toLocaleString()}`, chartRight + 5, highY + 4);

    // 최저점 점선 (파란색)
    ctx.strokeStyle = '#339af0';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(chartLeft, lowY);
    ctx.lineTo(chartRight, lowY);
    ctx.stroke();

    // 최저점 레이블
    ctx.fillStyle = '#339af0';
    ctx.font = 'bold 13px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`최저 ${minPrice.toLocaleString()}`, chartRight + 5, lowY + 4);

    ctx.setLineDash([]);

    // 감시 레벨 수평선 그리기
    const levelConfig = [
        { price: levels.resistance_2, label: '2차저항', color: '#c92a2a' },
        { price: levels.resistance_1, label: '1차저항', color: '#e03131' },
        { price: levels.buy_target, label: '매수타점', color: '#fab005' },
        { price: levels.support_1, label: '1차지지', color: '#1971c2' },
        { price: levels.support_2, label: '2차지지', color: '#1864ab' }
    ];

    levelConfig.forEach(level => {
        if (level.price > 0 && currentPrice > 0) {
            const levelY = priceToY(level.price);

            // 수평선 그리기
            ctx.strokeStyle = level.color;
            ctx.lineWidth = 1.5;
            ctx.setLineDash([6, 3]);
            ctx.beginPath();
            ctx.moveTo(chartLeft, levelY);
            ctx.lineTo(chartRight, levelY);
            ctx.stroke();

            // 등락율 계산
            const changeRate = ((level.price - currentPrice) / currentPrice * 100);
            const changeRateText = changeRate >= 0 ? `+${changeRate.toFixed(1)}%` : `${changeRate.toFixed(1)}%`;

            // 레이블 (레벨명 + 가격 + 등락율)
            ctx.fillStyle = level.color;
            ctx.font = 'bold 13px sans-serif';
            ctx.textAlign = 'left';
            ctx.fillText(`${level.label} ${level.price.toLocaleString()} (${changeRateText})`, chartRight + 5, levelY + 4);

            ctx.setLineDash([]);
        }
    });

    // 꺾은선 그래프
    ctx.strokeStyle = '#228be6';
    ctx.lineWidth = 2;
    ctx.beginPath();
    points.forEach((point, i) => {
        const x = indexToX(point.x);
        const y = priceToY(point.price);
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();

    // 포인트 + 레이블
    const basePrice = yesterday.close; // 전일 종가 기준
    points.forEach(point => {
        const x = indexToX(point.x);
        const y = priceToY(point.price);

        // 포인트 원
        ctx.fillStyle = '#228be6';
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, 2 * Math.PI);
        ctx.fill();

        // 테두리
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // 가격 레이블 + 등락율
        const changeRate = basePrice > 0 ? ((point.price - basePrice) / basePrice * 100) : 0;
        const changeRateText = changeRate >= 0 ? `(+${changeRate.toFixed(2)}%)` : `(${changeRate.toFixed(2)}%)`;
        const changeColor = changeRate >= 0 ? '#c92a2a' : '#1971c2';

        ctx.fillStyle = '#212529';
        ctx.font = 'bold 13px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(point.price.toLocaleString(), x, y - 22);

        // 등락율 표시
        ctx.fillStyle = changeColor;
        ctx.font = 'bold 14px sans-serif';
        ctx.fillText(changeRateText, x, y - 9);

        // X축 레이블
        ctx.fillStyle = '#495057';
        ctx.font = '12px sans-serif';
        const labels = point.label.split('\n');
        labels.forEach((line, i) => {
            ctx.fillText(line, x, chartBottom + 15 + i * 10);
        });
    });

    // 차트 제목
    ctx.fillStyle = '#495057';
    ctx.font = 'bold 13px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`${data.name} (${data.code})`, 10, 20);

    // 시간 순서 표시
    if (summary.high_time && summary.low_time) {
        ctx.fillStyle = '#868e96';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'right';
        const timeText = todayHighFirst ? '당일: 고가 → 저가' : '당일: 저가 → 고가';
        ctx.fillText(timeText, canvas.width - 10, 20);
    }
}

// ========== Mode1 종목 조회 ==========
async function handleMode1Lookup() {
    const codeInput = document.getElementById('mode1Code');
    const nameInput = document.getElementById('mode1Name');
    const priceInput = document.getElementById('mode1MonitoringPrice');

    const code = codeInput.value.trim();
    if (!code) {
        alert('종목코드를 입력하세요');
        return;
    }

    try {
        const response = await fetch(`/api/test/stock-info/${code}`, {
            credentials: 'same-origin'
        });
        const result = await response.json();

        if (result.success) {
            nameInput.value = result.data.name;
            priceInput.value = result.data.current_price;
            showToast('✓ 종목 정보 조회 완료', 'success');
        } else {
            alert(`조회 실패: ${result.error}`);
        }
    } catch (error) {
        alert(`조회 실패: ${error.message}`);
    }
}

// ========== Mode1 행 선택 ==========
function handleMode1RowSelect(checkbox, code) {
    // 다른 체크박스 해제
    document.querySelectorAll('.mode1-row-checkbox').forEach(cb => {
        if (cb !== checkbox) {
            cb.checked = false;
        }
    });

    if (checkbox.checked) {
        loadMode1ToForm(code);
    } else {
        cancelMode1Form();
    }
}

// ========== Mode1 폼에 데이터 로드 ==========
async function loadMode1ToForm(code) {
    try {
        const response = await fetch(`/api/mode1/watchers/${code}`, {
            credentials: 'same-origin'
        });
        const result = await response.json();

        if (result.success) {
            const watcher = result.data;

            // 폼 표시
            document.getElementById('mode1Form').style.display = 'block';
            document.getElementById('mode1FormTitle').textContent = '📊 종목 수정';
            document.getElementById('mode1SubmitBtn').textContent = '수정';

            // 기본 정보
            document.getElementById('mode1Code').value = watcher.code;
            document.getElementById('mode1Code').readOnly = true;
            document.getElementById('mode1Name').value = watcher.name || '';
            document.getElementById('mode1MonitoringPrice').value = watcher.monitoring_price || 0;

            // 3단계 조건
            const step1 = watcher.step1 || {};
            const step2 = watcher.step2 || {};
            const step3 = watcher.step3 || {};

            document.querySelector('[name="step1_interval"]').value = step1.interval || '1분';
            document.querySelector('[name="step1_trend"]').value = step1.trend || '상승';
            document.querySelector('[name="step1_count"]').value = step1.count || 4;

            document.querySelector('[name="step2_interval"]').value = step2.interval || '3분';
            document.querySelector('[name="step2_trend"]').value = step2.trend || '하락';
            document.querySelector('[name="step2_count"]').value = step2.count || 1;

            document.querySelector('[name="step3_interval"]').value = step3.interval || '1분';
            document.querySelector('[name="step3_trend"]').value = step3.trend || '상승';
            document.querySelector('[name="step3_count"]').value = step3.count || 2;

            document.querySelector('[name="auto_buy"]').checked = watcher.auto_buy || false;
            document.querySelector('[name="expected_profit_rate"]').value = watcher.expected_profit_rate || 0;
            document.querySelector('[name="polling_interval"]').value = watcher.polling_interval || 20;

            // 스크롤
            document.getElementById('mode1Form').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    } catch (error) {
        showToast('데이터 로드 실패', 'error');
    }
}

// ========== 텔레그램 테스트 ==========
const telegramTemplates = {
    'mode1_signal': `🎯 Mode1 매수 시그널! (Step 2 완료)

📈 삼성전자 (005930)
💰 추천 매수가: 75,200원 (조정 저가)
📊 모니터링가: 76,000원
🎯 기대수익률: 5.0%

✅ 조건 상태:
Step 1 (상승 추세): ✅ 1분봉 상승 4개 연속
Step 2 (첫 조정): ✅ 3분봉 하락 1개

📋 최근 3분봉:
09:15:00 | 시:76000 고:76200 저:75900 종:76100 ↗
09:18:00 | 시:76100 고:76300 저:76000 종:76200 ↗
09:21:00 | 시:76200 고:76300 저:75200 종:75300 ↘`,

    'mode1_buy': `✅ Mode1 자동매수 체결! (Step 3 완료)

📈 삼성전자 (005930)
💰 매수가: 75,500원
📊 수량: 13주
💵 총액: 981,500원

✨ 3단계 완료:
Step 1: 상승 추세 전환 ✅
Step 2: 첫 조정 ✅
Step 3: 재반등 ✅`,

    'mode2_buy_signal': `🔔 Mode2 매수타점 도달!

📈 카카오 (035720)
💰 매수타점: 50,000원
📊 현재가: 49,900원
💵 Budget: 1,000,000원
📦 예상수량: 20주

⚠️ 알림 전용 모드: 수동 매수 필요`,

    'mode2_buy': `✅ Mode2 자동매수 체결!

📈 카카오 (035720)
💰 매수가: 50,000원
📊 수량: 20주
💵 총액: 1,000,000원

🎯 목표가:
1차저항: 52,000원 (+4.0%)
2차저항: 54,000원 (+8.0%)`,

    'mode2_sell': `📉 Mode2 익절 매도!

📈 카카오 (035720)
💰 매도가: 52,100원 (1차저항)
📊 수량: 20주
💵 총액: 1,042,000원

💎 수익:
매수가: 50,000원
수익: +42,000원 (+4.2%)`,

    'test': `🧪 텔레그램 연동 테스트

현재 시각: ${new Date().toLocaleString('ko-KR')}
메시지 전송 정상 작동 중입니다! ✅`
};

function handleTelegramTemplateChange(e) {
    const template = e.target.value;
    const messageArea = document.getElementById('telegramMessage');

    if (template && telegramTemplates[template]) {
        messageArea.value = telegramTemplates[template];
    } else {
        messageArea.value = '';
    }
}

async function handleTestSendTelegram() {
    const messageArea = document.getElementById('telegramMessage');
    const resultDiv = document.getElementById('testTelegramResult');
    const message = messageArea.value.trim();

    if (!message) {
        alert('메시지를 입력하세요');
        return;
    }

    resultDiv.innerHTML = '<div style="color: #868e96;">전송 중...</div>';

    try {
        const response = await fetch('/api/test/telegram', {
            credentials: 'same-origin',
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const result = await response.json();

        if (result.success) {
            resultDiv.innerHTML = `
                <div style="color: #2b8a3e; font-weight: bold;">✅ 전송 성공</div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-top: 8px; font-size: 13px; color: #495057;">
                    ${result.message || '텔레그램으로 메시지가 전송되었습니다.'}
                </div>
            `;
            showToast('✅ 텔레그램 전송 완료', 'success');
        } else {
            resultDiv.innerHTML = `
                <div style="color: #c92a2a; font-weight: bold;">❌ 전송 실패</div>
                <div style="background: #fff5f5; padding: 12px; border-radius: 6px; margin-top: 8px; font-size: 13px; color: #c92a2a;">
                    ${result.error || '알 수 없는 오류'}
                </div>
            `;
            showToast('❌ 텔레그램 전송 실패', 'error');
        }
    } catch (error) {
        resultDiv.innerHTML = `
            <div style="color: #c92a2a; font-weight: bold;">❌ 요청 실패</div>
            <div style="background: #fff5f5; padding: 12px; border-radius: 6px; margin-top: 8px; font-size: 13px; color: #c92a2a;">
                ${error.message}
            </div>
        `;
        showToast('❌ 요청 실패', 'error');
    }
}

// ========== Mode2 모니터링 ==========
let monitorInterval = null;
let monitorRunning = false;
let monitorLogLines = [];

function addMonitorLog(message, type = 'info') {
    const now = new Date();
    const timestamp = now.toLocaleTimeString('ko-KR', { hour12: false });

    let color = '#adb5bd';
    let prefix = 'ℹ️';

    if (type === 'success') {
        color = '#51cf66';
        prefix = '✅';
    } else if (type === 'warning') {
        color = '#ffd43b';
        prefix = '⚠️';
    } else if (type === 'error') {
        color = '#ff6b6b';
        prefix = '❌';
    } else if (type === 'buy') {
        color = '#339af0';
        prefix = '💰';
    } else if (type === 'sell') {
        color = '#f06595';
        prefix = '📉';
    }

    const logLine = `<div style="margin-bottom: 4px;"><span style="color: #868e96;">[${timestamp}]</span> <span style="color: ${color};">${prefix} ${message}</span></div>`;
    monitorLogLines.push(logLine);

    // 최대 100줄 유지
    if (monitorLogLines.length > 100) {
        monitorLogLines.shift();
    }

    const container = document.getElementById('monitorLogContainer');
    if (container) {
        container.innerHTML = monitorLogLines.join('');
        container.scrollTop = container.scrollHeight;
    }
}

async function checkMode2Status() {
    const code = document.getElementById('monitorCode').textContent;

    if (!code || code === '-') {
        addMonitorLog('종목을 먼저 선택하세요', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/test/mode2-monitor', {
            credentials: 'same-origin',
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        });

        const result = await response.json();

        if (result.success) {
            const data = result.data;

            // UI 업데이트
            document.getElementById('monitorName').textContent = data.name || '';
            document.getElementById('monitorStatus').textContent = data.status;
            document.getElementById('monitorCurrentPrice').textContent = data.current_price.toLocaleString();

            // 가격 변동 색상
            const priceElem = document.getElementById('monitorCurrentPrice');
            if (data.current_price >= data.buy_target_price) {
                priceElem.style.color = '#f03e3e';
            } else {
                priceElem.style.color = '#228be6';
            }

            // 로그 출력
            const message = `현재가: ${data.current_price.toLocaleString()}원 | 상태: ${data.status}`;

            if (data.signal) {
                // 시그널 발생!
                addMonitorLog(`🚨 ${data.signal} 시그널 발생! (${data.current_price.toLocaleString()}원)`, 'warning');

                if (data.signal === '매수') {
                    if (data.notify_only) {
                        addMonitorLog('📢 알림 전용 모드 - 주문 실행하지 않음', 'info');
                    } else {
                        addMonitorLog('💰 자동 매수 주문 실행 (실제 환경에서는 주문됨)', 'buy');
                    }
                } else if (data.signal.includes('익절')) {
                    addMonitorLog(`📈 ${data.signal} 조건 충족`, 'sell');
                } else if (data.signal.includes('손절')) {
                    addMonitorLog(`📉 ${data.signal} 조건 충족`, 'error');
                }
            } else {
                addMonitorLog(message, 'info');
            }

            // 트리거 상태 로그
            if (data.buy_triggered) {
                addMonitorLog(`  └ 매수타점(${data.buy_target_price.toLocaleString()}) 도달!`, 'success');
            }
            if (data.resist1_triggered) {
                addMonitorLog(`  └ 1차저항(${data.resistance_1.toLocaleString()}) 도달!`, 'success');
            }
            if (data.resist2_triggered) {
                addMonitorLog(`  └ 2차저항(${data.resistance_2.toLocaleString()}) 도달!`, 'success');
            }
            if (data.support1_triggered) {
                addMonitorLog(`  └ 1차지지(${data.support_1.toLocaleString()}) 도달!`, 'warning');
            }
            if (data.support2_triggered) {
                addMonitorLog(`  └ 2차지지(${data.support_2.toLocaleString()}) 도달!`, 'error');
            }

        } else {
            addMonitorLog(`오류: ${result.error}`, 'error');
        }

    } catch (error) {
        addMonitorLog(`API 호출 실패: ${error.message}`, 'error');
    }
}

function toggleMonitoring() {
    const btn = document.getElementById('toggleMonitorLog');

    if (monitorRunning) {
        // 중지
        clearInterval(monitorInterval);
        monitorRunning = false;
        btn.textContent = '▶️ 시작';
        btn.style.background = '#228be6';
        document.getElementById('monitorStatus').textContent = '중지됨';
        addMonitorLog('모니터링 중지', 'warning');
    } else {
        // 시작
        monitorRunning = true;
        btn.textContent = '⏸️ 중지';
        btn.style.background = '#f03e3e';
        document.getElementById('monitorStatus').textContent = '실행 중';
        addMonitorLog('모니터링 시작 (10초 간격)', 'success');

        // 즉시 한 번 실행
        checkMode2Status();

        // 10초마다 반복
        monitorInterval = setInterval(checkMode2Status, 10000);
    }
}

function clearMonitorLog() {
    monitorLogLines = [];
    document.getElementById('monitorLogContainer').innerHTML = '<div style="color: #868e96; text-align: center; padding: 20px;">로그가 초기화되었습니다</div>';
}

// ========== 주문 모드 관리 ==========
async function loadOrderMode() {
    try {
        const response = await fetch('/api/config/order-mode', {
            credentials: 'same-origin'
        });
        const result = await response.json();

        if (result.success) {
            const mode = result.data.order_mode;
            syncOrderModeRadios(mode); // 모든 라디오 버튼 동기화
        }
    } catch (error) {
        console.error('주문 모드 로드 실패:', error);
    }
}

async function handleOrderModeChange(event) {
    const mode = event.target.value;
    const modeText = mode === 'simulation' ? '시뮬레이션' : '실전';

    if (mode === 'real') {
        const confirmed = confirm(`⚠️ 주문 모드를 '실전'으로 변경하시겠습니까?\n\n실전 모드에서는 실제 주문이 나갑니다!`);
        if (!confirmed) {
            // 취소하면 시뮬레이션으로 되돌림
            document.querySelector('input[name="orderMode"][value="simulation"]').checked = true;
            return;
        }
    }

    try {
        const response = await fetch('/api/config/order-mode', {
            credentials: 'same-origin',
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode })
        });

        const result = await response.json();

        if (result.success) {
            showToast(`✅ 주문 모드: ${modeText}`, 'success');
            // 모든 페이지의 라디오 버튼 동기화
            syncOrderModeRadios(mode);
        } else {
            showToast('❌ 주문 모드 변경 실패', 'error');
            // 실패 시 원래대로
            const otherMode = mode === 'simulation' ? 'real' : 'simulation';
            syncOrderModeRadios(otherMode);
        }
    } catch (error) {
        showToast('❌ 요청 실패', 'error');
        // 실패 시 원래대로
        const otherMode = mode === 'simulation' ? 'real' : 'simulation';
        syncOrderModeRadios(otherMode);
    }
}

// 모든 페이지의 주문 모드 라디오 버튼 동기화
function syncOrderModeRadios(mode) {
    document.querySelectorAll('input[name="orderMode"]').forEach(radio => {
        radio.checked = (radio.value === mode);
    });
}

// ========== 종목명 노트 모달 ==========
let currentNoteStockCode = null;
let originalNoteText = '';

function showNoteModal(stockName, stockCode, noteText) {
    const modal = document.getElementById('noteModal');
    const modalStockName = document.getElementById('noteModalStockName');
    const modalText = document.getElementById('noteModalText');
    const modalTextarea = document.getElementById('noteModalTextarea');
    const modalBody = document.getElementById('noteModalBody');
    const editBtn = document.getElementById('noteEditBtn');
    const saveBtn = document.getElementById('noteSaveBtn');
    const cancelBtn = document.getElementById('noteCancelBtn');

    // 현재 종목 코드 저장
    currentNoteStockCode = stockCode;
    originalNoteText = noteText || '';

    modalStockName.textContent = `${stockName} (${stockCode})`;

    // 읽기 모드로 초기화
    modalText.style.display = 'block';
    modalTextarea.style.display = 'none';
    editBtn.style.display = 'inline-block';
    saveBtn.style.display = 'none';
    cancelBtn.style.display = 'none';

    if (noteText && noteText.trim()) {
        modalText.textContent = noteText;
        modalBody.classList.remove('empty');
    } else {
        modalText.textContent = '노트 내용이 없습니다';
        modalText.style.color = '#adb5bd';
        modalText.style.fontStyle = 'italic';
        modalBody.classList.add('empty');
    }

    modal.style.display = 'block';
}

function closeNoteModal() {
    const modal = document.getElementById('noteModal');
    modal.style.display = 'none';
    currentNoteStockCode = null;
    originalNoteText = '';
}

function enableNoteEdit() {
    const modalText = document.getElementById('noteModalText');
    const modalTextarea = document.getElementById('noteModalTextarea');
    const editBtn = document.getElementById('noteEditBtn');
    const saveBtn = document.getElementById('noteSaveBtn');
    const cancelBtn = document.getElementById('noteCancelBtn');

    // 편집 모드로 전환
    modalText.style.display = 'none';
    modalTextarea.style.display = 'block';
    modalTextarea.value = originalNoteText;

    editBtn.style.display = 'none';
    saveBtn.style.display = 'inline-block';
    cancelBtn.style.display = 'inline-block';

    // 포커스
    modalTextarea.focus();
}

function cancelNoteEdit() {
    const modalText = document.getElementById('noteModalText');
    const modalTextarea = document.getElementById('noteModalTextarea');
    const editBtn = document.getElementById('noteEditBtn');
    const saveBtn = document.getElementById('noteSaveBtn');
    const cancelBtn = document.getElementById('noteCancelBtn');

    // 읽기 모드로 복귀
    modalText.style.display = 'block';
    modalTextarea.style.display = 'none';

    editBtn.style.display = 'inline-block';
    saveBtn.style.display = 'none';
    cancelBtn.style.display = 'none';
}

async function saveNote() {
    const modalTextarea = document.getElementById('noteModalTextarea');
    const newNoteText = modalTextarea.value.trim();

    if (!currentNoteStockCode) {
        showToast('종목 정보를 찾을 수 없습니다', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/mode2/watchers/${currentNoteStockCode}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ note: newNoteText })
        });

        const result = await response.json();

        if (result.success) {
            showToast('✓ 노트 저장 완료', 'success');

            // 원본 텍스트 업데이트
            originalNoteText = newNoteText;

            // 읽기 모드로 전환하고 내용 업데이트
            const modalText = document.getElementById('noteModalText');
            if (newNoteText) {
                modalText.textContent = newNoteText;
                modalText.style.color = '#495057';
                modalText.style.fontStyle = 'normal';
            } else {
                modalText.textContent = '노트 내용이 없습니다';
                modalText.style.color = '#adb5bd';
                modalText.style.fontStyle = 'italic';
            }

            cancelNoteEdit();

            // 리스트 새로고침
            loadMode2List();
        } else {
            showToast('노트 저장 실패: ' + result.error, 'error');
        }
    } catch (error) {
        showToast('요청 실패: ' + error.message, 'error');
    }
}

// 모달 외부 클릭 시 닫기
window.addEventListener('click', (event) => {
    const modal = document.getElementById('noteModal');
    if (event.target === modal) {
        closeNoteModal();
    }
});

// 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggleMonitorLog');
    const clearBtn = document.getElementById('clearMonitorLog');
    const monitorCodeSelect = document.getElementById('monitorCodeSelect');

    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleMonitoring);
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', clearMonitorLog);
    }

    if (monitorCodeSelect) {
        monitorCodeSelect.addEventListener('change', handleMonitorCodeChange);
    }

    // 주문 모드 라디오 버튼
    const orderModeRadios = document.querySelectorAll('input[name="orderMode"]');
    orderModeRadios.forEach(radio => {
        radio.addEventListener('change', handleOrderModeChange);
    });

    // 주문 모드 초기 로드
    loadOrderMode();

    // Mode2 종목 리스트 로드 (Test 페이지 picklist용)
    loadMode2PickList();

    // 윈도우 리사이즈 시 차트 재렌더링
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            // Mode2 차트가 표시되어 있으면 재렌더링
            const mode2Container = document.getElementById('mode2ChartContainer');
            if (mode2Container && mode2Container.style.display !== 'none') {
                // 마지막 차트 데이터가 저장되어 있다면 재렌더링
                if (window.lastMode2ChartData) {
                    drawMode2CandlestickChart(window.lastMode2ChartData);
                }
            }

            // Test 페이지 차트가 표시되어 있으면 재렌더링
            const testContainer = document.getElementById('dailyChartCanvas');
            if (testContainer && testContainer.style.display !== 'none') {
                if (window.lastDailyChartData) {
                    drawCandlestickChart(window.lastDailyChartData);
                }
            }
        }, 300);
    });
});

// Mode2 종목 리스트를 picklist에 로드
async function loadMode2PickList() {
    try {
        const response = await fetch('/api/mode2/watchers', { credentials: 'same-origin' });
        const result = await response.json();

        if (result.success) {
            const select = document.getElementById('monitorCodeSelect');
            if (!select) return;

            // 기존 옵션 제거 (첫 번째 "-- 선택 --" 제외)
            while (select.options.length > 1) {
                select.remove(1);
            }

            // Mode2 종목 추가
            result.data.forEach(w => {
                const option = document.createElement('option');
                option.value = w.code;
                option.textContent = `${w.code} ${w.name || ''}`.trim();
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Mode2 종목 리스트 로드 실패:', error);
    }
}

// Test 페이지 종목 선택 시
async function handleMonitorCodeChange() {
    const select = document.getElementById('monitorCodeSelect');
    const code = select.value;

    if (!code) {
        document.getElementById('monitorCode').textContent = '-';
        document.getElementById('monitorName').textContent = '';
        document.getElementById('monitorBuyTarget').textContent = '-';
        document.getElementById('monitorResist1').textContent = '-';
        return;
    }

    try {
        // 종목 정보 조회
        const response = await fetch(`/api/mode2/watchers/${code}`, { credentials: 'same-origin' });
        const result = await response.json();

        if (result.success && result.data) {
            const w = result.data;
            document.getElementById('monitorCode').textContent = w.code;
            document.getElementById('monitorName').textContent = w.name || '';
            document.getElementById('monitorBuyTarget').textContent = (w.buy_target_price || 0).toLocaleString();
            document.getElementById('monitorResist1').textContent = (w.resistance_1_price || 0).toLocaleString();
        }
    } catch (error) {
        console.error('종목 정보 조회 실패:', error);
    }
}

// ========== Seeking Signal ==========

let currentSSReport = null;

// 분석 실행
document.getElementById('ssAnalyze').addEventListener('click', async () => {
    const stockCode = document.getElementById('ssStockCode').value.trim();
    
    if (!stockCode) {
        showToast('종목코드를 입력하세요', 'error');
        return;
    }

    // 파라미터 수집
    const params = {
        stock_code: stockCode,
        bbwp_threshold: parseFloat(document.getElementById('ssBbwpThreshold').value),
        bbwp_consecutive_days: parseInt(document.getElementById('ssBbwpDays').value),
        pullback_max_pct: parseFloat(document.getElementById('ssPullbackMax').value),
        rally_min_pct: parseFloat(document.getElementById('ssRallyMin').value),
        range_threshold_pct: parseFloat(document.getElementById('ssRangeThreshold').value),
        volume_ratio: parseFloat(document.getElementById('ssVolumeRatio').value),
        adx_threshold: parseFloat(document.getElementById('ssAdxThreshold').value),
    };

    try {
        showToast('분석 중...', 'info');

        const response = await fetch('/api/seeking-signal/analyze', {
            credentials: 'same-origin',
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });

        const result = await response.json();

        if (!result.success) {
            showToast(`분석 실패: ${result.error}`, 'error');
            return;
        }

        currentSSReport = result.data;
        renderSSReport(result.data);

        // 전일/당일 가격 흐름 차트 그리기 (Mode2와 동일한 방식)
        fetchSSDailyChart(stockCode);

        showToast('✓ 분석 완료', 'success');

    } catch (error) {
        console.error('분석 실패:', error);
        showToast('분석 실패', 'error');
    }
});

// Seeking Signal 전일/당일 차트 조회
async function fetchSSDailyChart(stockCode) {
    try {
        const response = await fetch('/api/test/daily-chart', {
            credentials: 'same-origin',
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: stockCode })
        });

        const result = await response.json();

        if (result.success) {
            const chartContainer = document.getElementById('ssChartsContainer');
            chartContainer.style.display = 'block';

            // Mode2 차트 함수 재사용
            drawCandlestickChart(result.data, 'ssDailyFlowChart', 'ssDailyFlowChartContainer');
        }
    } catch (error) {
        console.error('차트 조회 실패:', error);
    }
}

// 설정 초기화
document.getElementById('ssReset').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/seeking-signal/defaults', {
            credentials: 'same-origin'
        });
        const result = await response.json();

        if (result.success) {
            const { type1, type2 } = result.data;
            document.getElementById('ssBbwpThreshold').value = type1.bbwp_threshold;
            document.getElementById('ssBbwpDays').value = type1.bbwp_consecutive_days;
            document.getElementById('ssPullbackMax').value = type1.pullback_max_pct;
            document.getElementById('ssRallyMin').value = type1.rally_min_pct;
            document.getElementById('ssRangeThreshold').value = type2.range_threshold_pct;
            document.getElementById('ssVolumeRatio').value = type2.volume_ratio;
            document.getElementById('ssAdxThreshold').value = type2.adx_threshold;
            showToast('✓ 설정 초기화 완료', 'success');
        }
    } catch (error) {
        console.error('설정 초기화 실패:', error);
    }
});

// 탭 전환
document.querySelectorAll('.ss-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        
        // 탭 버튼 활성화
        document.querySelectorAll('.ss-tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // 탭 콘텐츠 전환
        document.querySelectorAll('.ss-tab-content').forEach(c => c.classList.remove('active'));
        document.querySelector(`.ss-tab-content[data-tab="${tab}"]`).classList.add('active');
    });
});

// 리포트 렌더링
function renderSSReport(report) {
    const resultSection = document.getElementById('ssResultSection');
    resultSection.style.display = 'block';

    // 종목 정보 저장 (차트에서 사용)
    window.currentSSStockCode = report.meta.stock_code;
    window.currentSSStockName = report.meta.stock_name;

    // ========== Enhanced Analysis 렌더링 ==========
    if (report.key_insights) {
        renderEnhancedAnalysis(report.key_insights, report.micro);
    }

    // 판정 요약
    const summary = report.summary;
    const verdict = summary.verdict;
    const confidence = summary.confidence;

    const verdictCard = document.getElementById('ssVerdictCard');
    const verdictEl = document.getElementById('ssVerdict');
    const confidenceEl = document.getElementById('ssConfidence');

    // 판정에 따른 색상
    let verdictColor = '#868e96';
    let verdictText = '';
    let cardBgColor = '#f8f9fa';

    if (verdict === 'buyable') {
        verdictColor = '#37b24d';
        verdictText = '✅ BUYABLE (매수 가능)';
        cardBgColor = '#d3f9d8';
    } else if (verdict === 'watch') {
        verdictColor = '#fd7e14';
        verdictText = '👀 WATCH (관망)';
        cardBgColor = '#ffe8cc';
    } else {
        verdictColor = '#f03e3e';
        verdictText = '❌ AVOID (회피)';
        cardBgColor = '#ffe3e3';
    }

    verdictEl.textContent = verdictText;
    verdictEl.style.color = verdictColor;
    confidenceEl.textContent = `${(confidence * 100).toFixed(0)}%`;
    confidenceEl.style.color = verdictColor;
    verdictCard.style.background = cardBgColor;

    // 주요 신호
    const signalsList = document.getElementById('ssKeySignals');
    signalsList.innerHTML = '';
    summary.key_signals.forEach(signal => {
        const li = document.createElement('li');
        li.style.padding = '8px 0';
        li.style.borderBottom = '1px solid #e9ecef';
        li.textContent = `✓ ${signal}`;
        signalsList.appendChild(li);
    });

    // 리스크
    const risksCard = document.getElementById('ssRisksCard');
    const risksList = document.getElementById('ssRisks');
    if (summary.risks && summary.risks.length > 0) {
        risksCard.style.display = 'block';
        risksList.innerHTML = '';
        summary.risks.forEach(risk => {
            const li = document.createElement('li');
            li.style.padding = '8px 0';
            li.style.borderBottom = '1px solid #e9ecef';
            li.style.color = '#f03e3e';
            li.textContent = `⚠ ${risk}`;
            risksList.appendChild(li);
        });
    } else {
        risksCard.style.display = 'none';
    }

    // 탭 콘텐츠 렌더링
    renderType1Tab(report.macro.type1);
    renderType2Tab(report.macro.type2);
    renderVolumeTab(report.volume_spike);
    renderMicroTab(report.micro);
    renderRawTab(report.raw);
}

// 타입1 탭
function renderType1Tab(type1) {
    const container = document.getElementById('ssType1Content');
    let html = '<h4>타입1 분석 (강한 상승 후 눌림)</h4>';

    html += `<div class="ss-metric">
        <span class="ss-metric-label">적용 가능</span>
        <span class="ss-status-badge ${type1.applicable ? 'success' : 'error'}">
            ${type1.applicable ? 'YES' : 'NO'}
        </span>
    </div>`;

    html += `<div class="ss-metric">
        <span class="ss-metric-label">횡보 중</span>
        <span class="ss-status-badge ${type1.is_sideways ? 'success' : 'error'}">
            ${type1.is_sideways ? 'YES' : 'NO'}
        </span>
    </div>`;

    if (type1.metrics) {
        html += `<h5 style="margin-top: 16px;">주요 지표</h5>`;
        html += `<div class="ss-metric">
            <span class="ss-metric-label">BBWP 현재</span>
            <span class="ss-metric-value">${type1.metrics.bbwp_today.toFixed(1)}</span>
        </div>`;
        html += `<div class="ss-metric">
            <span class="ss-metric-label">60일 상승률</span>
            <span class="ss-metric-value positive">+${type1.metrics.rally_60d_pct.toFixed(1)}%</span>
        </div>`;
        html += `<div class="ss-metric">
            <span class="ss-metric-label">고점대비 하락</span>
            <span class="ss-metric-value negative">-${type1.metrics.pullback_from_60d_high_pct.toFixed(1)}%</span>
        </div>`;
    }

    if (type1.is_perfect_bull) {
        html += `<div style="margin-top: 12px; padding: 8px; background: #d3f9d8; border-radius: 4px; font-size: 13px; color: #2b8a3e;">
            ✅ 이동평균선 정배열
        </div>`;
    } else if (type1.is_perfect_bear) {
        html += `<div style="margin-top: 12px; padding: 8px; background: #ffe3e3; border-radius: 4px; font-size: 13px; color: #c92a2a;">
            ❌ 이동평균선 역배열
        </div>`;
    }

    container.innerHTML = html;
}

// 타입2 탭
function renderType2Tab(type2) {
    const container = document.getElementById('ssType2Content');
    let html = '<h4>타입2 분석 (답보 중인 종목)</h4>';

    html += `<div class="ss-metric">
        <span class="ss-metric-label">적용 가능</span>
        <span class="ss-status-badge ${type2.applicable ? 'success' : 'error'}">
            ${type2.applicable ? 'YES' : 'NO'}
        </span>
    </div>`;

    html += `<div class="ss-metric">
        <span class="ss-metric-label">횡보 중</span>
        <span class="ss-status-badge ${type2.is_sideways ? 'success' : 'error'}">
            ${type2.is_sideways ? 'YES' : 'NO'}
        </span>
    </div>`;

    if (type2.metrics) {
        html += `<h5 style="margin-top: 16px;">주요 지표</h5>`;
        html += `<div class="ss-metric">
            <span class="ss-metric-label">20일 변동폭</span>
            <span class="ss-metric-value">${type2.metrics.range_pct_20d.toFixed(2)}%</span>
        </div>`;
        html += `<div class="ss-metric">
            <span class="ss-metric-label">거래량 비율</span>
            <span class="ss-metric-value">${type2.metrics.volume_ratio_recent_vs_longterm.toFixed(3)}</span>
        </div>`;
        html += `<div class="ss-metric">
            <span class="ss-metric-label">ADX14</span>
            <span class="ss-metric-value">${type2.metrics.adx14.toFixed(1)}</span>
        </div>`;
    }

    container.innerHTML = html;
}

// 거래대금 탭
function renderVolumeTab(volume) {
    const container = document.getElementById('ssVolumeContent');
    let html = '<h4>거래대금 스파이크</h4>';

    const quality = volume.signal_quality;
    let qualityBadge = '';
    let qualityText = '';

    if (quality === 'imminent') {
        qualityBadge = 'success';
        qualityText = '🔥 돌파 임박';
    } else if (quality === 'watch') {
        qualityBadge = 'info';
        qualityText = '👀 관망';
    } else {
        qualityBadge = 'error';
        qualityText = '💀 Dead';
    }

    html += `<div class="ss-metric">
        <span class="ss-metric-label">신호 품질</span>
        <span class="ss-status-badge ${qualityBadge}">${qualityText}</span>
    </div>`;

    html += `<div class="ss-metric">
        <span class="ss-metric-label">시가총액</span>
        <span class="ss-metric-value">${volume.market_cap_won.toFixed(0)} 억원</span>
    </div>`;

    if (volume.days_ago_strong !== null) {
        html += `<div class="ss-metric">
            <span class="ss-metric-label">마지막 강한 거래대금</span>
            <span class="ss-metric-value">${volume.days_ago_strong}일 전</span>
        </div>`;
    }

    if (volume.days_ago_interest !== null) {
        html += `<div class="ss-metric">
            <span class="ss-metric-label">마지막 관심 거래대금</span>
            <span class="ss-metric-value">${volume.days_ago_interest}일 전</span>
        </div>`;
    }

    container.innerHTML = html;
}

// 분봉 탭
function renderMicroTab(micro) {
    const container = document.getElementById('ssMicroContent');
    let html = '<h4>분봉 마이크로 분석</h4>';

    if (micro.error) {
        html += `<div style="padding: 12px; background: #ffe3e3; border-radius: 6px; color: #c92a2a;">
            ⚠️ ${micro.error}
        </div>`;
    }

    if (micro.three_min_sideways) {
        const sideways = micro.three_min_sideways;
        html += `<div class="ss-metric">
            <span class="ss-metric-label">3분봉 횡보</span>
            <span class="ss-status-badge ${sideways.is_sideways ? 'success' : 'error'}">
                ${sideways.is_sideways ? 'YES' : 'NO'}
            </span>
        </div>`;
        html += `<div class="ss-metric">
            <span class="ss-metric-label">변동폭</span>
            <span class="ss-metric-value">${sideways.range_pct.toFixed(3)}%</span>
        </div>`;
    }

    html += `<div class="ss-metric">
        <span class="ss-metric-label">120분봉 추세 위</span>
        <span class="ss-status-badge ${micro.above_120min_trend ? 'success' : 'error'}">
            ${micro.above_120min_trend ? 'YES' : 'NO'}
        </span>
    </div>`;

    if (micro.today_trend) {
        const trend = micro.today_trend;
        html += `<div class="ss-metric">
            <span class="ss-metric-label">당일 추세 살아있음</span>
            <span class="ss-status-badge ${trend.alive ? 'success' : 'error'}">
                ${trend.alive ? 'YES' : 'NO'}
            </span>
        </div>`;
    }

    container.innerHTML = html;
}

// Raw Data 탭
function renderRawTab(raw) {
    const container = document.getElementById('ssRawContent');
    let html = '<h4>Raw Data (Debug)</h4>';
    html += `<pre style="background: #f8f9fa; padding: 12px; border-radius: 6px; overflow: auto; font-size: 12px;">${JSON.stringify(raw, null, 2)}</pre>`;
    container.innerHTML = html;
}

// ========== Enhanced Analysis 렌더링 ==========
function renderEnhancedAnalysis(insights, micro) {
    // 1. 강한 상승일
    renderStrongRallyDay(insights.strong_rally_day);

    // 2. 이평선-현재가 위치
    renderMaAlignment(insights.ma_price_alignment);

    // 3. 볼린저 밴드 횡보
    renderBollingerConsolidation(insights.bollinger_consolidation);

    // 4. 분봉 추세
    renderMinuteTrend(micro);
}

// 강한 상승일 렌더링
function renderStrongRallyDay(rallyDay) {
    const container = document.getElementById('ssStrongRallyContent');
    
    if (!rallyDay) {
        container.innerHTML = `
            <div style="color: #868e96; text-align: center; padding: 12px;">
                ❌ 조건에 맞는 강한 상승일 없음 (거래대금 500억+ & 종가 15%+)
            </div>
        `;
        return;
    }
    
    const html = `
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
            <div>
                <div style="font-size: 12px; color: #868e96;">날짜</div>
                <div style="font-size: 18px; font-weight: bold; color: #212529;">
                    ${rallyDay.date} <span style="color: #667eea; font-size: 14px;">(${rallyDay.days_ago}일 전)</span>
                </div>
            </div>
            <div>
                <div style="font-size: 12px; color: #868e96;">거래대금</div>
                <div style="font-size: 18px; font-weight: bold; color: #212529;">
                    ${rallyDay.volume_billion}억원
                </div>
            </div>
            <div>
                <div style="font-size: 12px; color: #868e96;">종가 상승률</div>
                <div style="font-size: 18px; font-weight: bold; color: #37b24d;">
                    +${rallyDay.close_change_pct}%
                </div>
            </div>
            <div>
                <div style="font-size: 12px; color: #868e96;">시가 상승률</div>
                <div style="font-size: 18px; font-weight: bold; color: #37b24d;">
                    +${rallyDay.open_change_pct}%
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// 이평선-현재가 위치 렌더링
function renderMaAlignment(alignment) {
    const container = document.getElementById('ssMaAlignmentContent');
    
    if (!alignment || alignment.error) {
        container.innerHTML = '<div style="color: #868e96;">데이터 없음</div>';
        return;
    }
    
    // 가격순 정렬 문자열
    let html = `
        <div style="margin-bottom: 16px;">
            <div style="font-size: 12px; color: #868e96; margin-bottom: 8px;">가격 순 정렬:</div>
            <div style="font-family: monospace; font-size: 14px; font-weight: 500; line-height: 1.8; color: #212529; background: white; padding: 12px; border-radius: 4px; overflow-x: auto;">
                ${alignment.alignment_string}
            </div>
        </div>
    `;
    
    // 현재가 위치 요약
    html += `
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px;">
            <div style="background: white; padding: 12px; border-radius: 4px;">
                <div style="font-size: 12px; color: #868e96;">현재가보다 위</div>
                <div style="font-size: 14px; font-weight: 600; color: #c92a2a;">
                    ${alignment.above_current.length > 0 ? alignment.above_current.join(', ') : '없음'}
                </div>
            </div>
            <div style="background: white; padding: 12px; border-radius: 4px;">
                <div style="font-size: 12px; color: #868e96;">현재가보다 아래</div>
                <div style="font-size: 14px; font-weight: 600; color: #1971c2;">
                    ${alignment.below_current.length > 0 ? alignment.below_current.join(', ') : '없음'}
                </div>
            </div>
        </div>
    `;
    
    // 거리 상세 테이블
    html += `
        <div style="background: white; padding: 12px; border-radius: 4px;">
            <div style="font-size: 12px; color: #868e96; margin-bottom: 8px;">각 이평선과의 거리:</div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
    `;
    
    // ma_distances를 숫자 순으로 정렬
    const sortedMas = Object.entries(alignment.ma_distances)
        .sort((a, b) => parseInt(a[0]) - parseInt(b[0]));
    
    sortedMas.forEach(([maName, info]) => {
        const symbol = info.position === 'above' ? '↑' : '↓';
        const color = info.position === 'above' ? '#37b24d' : '#f03e3e';
        html += `
            <div style="font-size: 13px;">
                <span style="font-weight: 600;">${maName}:</span>
                <span style="color: ${color}; font-weight: 600;">${symbol} ${Math.abs(info.distance_pct).toFixed(2)}%</span>
            </div>
        `;
    });
    
    html += `
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// 볼린저 밴드 횡보 렌더링
function renderBollingerConsolidation(bb) {
    const container = document.getElementById('ssBollingerContent');
    
    if (!bb || bb.error) {
        container.innerHTML = '<div style="color: #868e96;">데이터 없음</div>';
        return;
    }
    
    const statusBadge = bb.is_consolidating 
        ? '<span style="background: #d3f9d8; color: #2b8a3e; padding: 4px 12px; border-radius: 4px; font-weight: 600;">✅ 횡보 중</span>'
        : '<span style="background: #ffe3e3; color: #c92a2a; padding: 4px 12px; border-radius: 4px; font-weight: 600;">❌ 횡보 아님</span>';
    
    let html = `
        <div style="margin-bottom: 16px;">
            <div style="font-size: 14px; font-weight: 600; margin-bottom: 8px;">
                판정: ${statusBadge}
            </div>
            <div style="font-size: 12px; color: #868e96;">
                파라미터: ${bb.parameters.period}일, 표준편차 ${bb.parameters.std}, 임계값 ${bb.parameters.squeeze_threshold_pct}%
            </div>
        </div>
    `;
    
    // 현재 밴드 정보
    html += `
        <div style="background: white; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <div style="font-size: 12px; color: #868e96; margin-bottom: 8px;">현재 밴드:</div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;">
                <div>
                    <span style="color: #f03e3e; font-weight: 600;">상단:</span>
                    <span style="font-size: 14px; font-weight: 600;">${bb.current.upper_band.toLocaleString()}원</span>
                </div>
                <div>
                    <span style="color: #495057; font-weight: 600;">중심:</span>
                    <span style="font-size: 14px; font-weight: 600;">${bb.current.middle_band.toLocaleString()}원</span>
                </div>
                <div>
                    <span style="color: #1971c2; font-weight: 600;">하단:</span>
                    <span style="font-size: 14px; font-weight: 600;">${bb.current.lower_band.toLocaleString()}원</span>
                </div>
                <div>
                    <span style="color: #495057; font-weight: 600;">밴드폭:</span>
                    <span style="font-size: 14px; font-weight: 600; color: ${bb.current.width_pct <= bb.parameters.squeeze_threshold_pct ? '#37b24d' : '#f03e3e'};">
                        ${bb.current.width_pct}%
                    </span>
                </div>
            </div>
            <div style="margin-top: 8px; font-size: 13px;">
                <span style="color: #868e96;">현재가 위치:</span>
                <span style="font-weight: 600; color: #495057;">${bb.current.position}</span>
            </div>
        </div>
    `;
    
    // 최근 5일 밴드폭 추이
    html += `
        <div style="background: white; padding: 12px; border-radius: 4px;">
            <div style="font-size: 12px; color: #868e96; margin-bottom: 8px;">최근 ${bb.parameters.lookback_days}일 밴드폭 추이:</div>
            <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px;">
                ${bb.recent_widths.map((w, i) => `
                    <div style="flex: 1; text-align: center;">
                        <div style="font-size: 11px; color: #868e96;">${bb.parameters.lookback_days - i}일 전</div>
                        <div style="font-size: 14px; font-weight: 600; color: ${w <= bb.parameters.squeeze_threshold_pct ? '#37b24d' : '#495057'};">
                            ${w}%
                        </div>
                    </div>
                `).join('')}
            </div>
            <div style="font-size: 12px; color: #868e96;">
                평균: ${bb.avg_width_last_n_days}% | 최대: ${bb.max_width_last_n_days}% | 최소: ${bb.min_width_last_n_days}%
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// 분봉 추세 렌더링
function renderMinuteTrend(micro) {
    const container = document.getElementById('ssMinuteTrendContent');
    const chartContainer = document.getElementById('ss120MinChartContainer');

    if (!micro || micro.error) {
        container.innerHTML = `
            <div style="color: #868e96; text-align: center; padding: 12px;">
                ⚠️ 분봉 데이터 없음 (${micro?.error || '장시간 외'})
            </div>
        `;
        chartContainer.style.display = 'none';
        return;
    }

    const above120 = micro.above_120min_trend;
    const statusBadge = above120
        ? '<span style="background: #d3f9d8; color: #2b8a3e; padding: 4px 12px; border-radius: 4px; font-weight: 600;">✅ 120분봉선 위</span>'
        : '<span style="background: #ffe3e3; color: #c92a2a; padding: 4px 12px; border-radius: 4px; font-weight: 600;">❌ 120분봉선 아래</span>';

    let html = `
        <div style="margin-bottom: 16px;">
            <div style="font-size: 14px; font-weight: 600; margin-bottom: 8px;">
                현재가 위치: ${statusBadge}
            </div>
            <div style="font-size: 12px; color: #868e96;">
                120분봉 5개 이동평균선 기준
            </div>
        </div>
    `;

    // 당일 추세 정보
    if (micro.today_trend) {
        const trend = micro.today_trend;
        html += `
            <div style="background: white; padding: 12px; border-radius: 4px;">
                <div style="font-size: 12px; color: #868e96; margin-bottom: 8px;">당일 추세:</div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
                    <div>
                        <span style="font-weight: 600;">시가 대비:</span>
                        <span style="color: ${trend.above_today_open ? '#37b24d' : '#f03e3e'}; font-weight: 600;">
                            ${trend.above_today_open ? '↑ 위' : '↓ 아래'}
                        </span>
                    </div>
                    <div>
                        <span style="font-weight: 600;">전일 종가 대비:</span>
                        <span style="color: ${trend.above_prev_close ? '#37b24d' : '#f03e3e'}; font-weight: 600;">
                            ${trend.above_prev_close ? '↑ 위' : '↓ 아래'}
                        </span>
                    </div>
                    <div>
                        <span style="font-weight: 600;">추세:</span>
                        <span style="color: ${trend.alive ? '#37b24d' : '#f03e3e'}; font-weight: 600;">
                            ${trend.alive ? '✅ 살아있음' : '❌ 약함'}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }

    container.innerHTML = html;
}

// 120분봉 캔들스틱 + MA5 차트 그리기
function draw120MinChart(data) {
    const canvas = document.getElementById('ss120MinChart');
    if (!canvas || !data || !data.candles || data.candles.length === 0) {
        return;
    }

    // 반응형 캔버스 크기 조정
    const container = document.getElementById('ss120MinChartContainer');
    const containerWidth = container.offsetWidth - 32; // padding 제외
    const isMobile = window.innerWidth <= 768;

    if (isMobile) {
        canvas.width = Math.min(containerWidth, 700);
        canvas.height = 280;
    } else {
        canvas.width = Math.min(containerWidth, 800);
        canvas.height = 300;
    }

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const candles = data.candles;

    // 가격 범위 계산
    const allPrices = [];
    candles.forEach(c => {
        allPrices.push(c.high, c.low);
        if (c.ma5) allPrices.push(c.ma5);
    });

    const minPrice = Math.min(...allPrices);
    const maxPrice = Math.max(...allPrices);
    const priceRange = maxPrice - minPrice;
    const padding = priceRange * 0.1;

    // 차트 영역
    const chartLeft = 80;
    const chartRight = canvas.width - 20;
    const chartTop = 30;
    const chartBottom = canvas.height - 60;
    const chartWidth = chartRight - chartLeft;
    const chartHeight = chartBottom - chartTop;

    // 가격 -> Y좌표 변환
    function priceToY(price) {
        return chartTop + chartHeight * (1 - (price - minPrice + padding) / (priceRange + 2 * padding));
    }

    // 배경
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 그리드 라인
    ctx.strokeStyle = '#e9ecef';
    ctx.lineWidth = 1;
    const gridLines = 5;
    for (let i = 0; i <= gridLines; i++) {
        const y = chartTop + (chartHeight / gridLines) * i;
        ctx.beginPath();
        ctx.moveTo(chartLeft, y);
        ctx.lineTo(chartRight, y);
        ctx.stroke();

        // 가격 레이블
        const price = maxPrice + padding - ((maxPrice + padding - minPrice - padding) / gridLines) * i;
        ctx.fillStyle = '#868e96';
        ctx.font = '13px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(Math.round(price).toLocaleString(), chartLeft - 10, y + 4);
    }

    // 캔들 그리기
    const candleWidth = chartWidth / candles.length;
    const barWidth = Math.max(2, candleWidth * 0.6);

    candles.forEach((candle, i) => {
        const x = chartLeft + candleWidth * (i + 0.5);
        const isRed = candle.close >= candle.open;

        // 봉 색상
        ctx.strokeStyle = isRed ? '#ef5350' : '#1e88e5';
        ctx.fillStyle = isRed ? '#ef5350' : '#1e88e5';
        ctx.lineWidth = 1;

        // 고가-저가 심지
        ctx.beginPath();
        ctx.moveTo(x, priceToY(candle.high));
        ctx.lineTo(x, priceToY(candle.low));
        ctx.stroke();

        // 시가-종가 박스
        const openY = priceToY(candle.open);
        const closeY = priceToY(candle.close);
        const boxHeight = Math.abs(openY - closeY);
        const boxTop = Math.min(openY, closeY);

        if (boxHeight < 1) {
            // 도지형 (시가=종가)
            ctx.beginPath();
            ctx.moveTo(x - barWidth/2, openY);
            ctx.lineTo(x + barWidth/2, openY);
            ctx.stroke();
        } else {
            ctx.fillRect(x - barWidth/2, boxTop, barWidth, boxHeight);
        }
    });

    // MA5 선 그리기
    ctx.strokeStyle = '#9c27b0'; // 보라색
    ctx.lineWidth = 2;
    ctx.beginPath();

    let firstPoint = true;
    candles.forEach((candle, i) => {
        if (candle.ma5) {
            const x = chartLeft + candleWidth * (i + 0.5);
            const y = priceToY(candle.ma5);

            if (firstPoint) {
                ctx.moveTo(x, y);
                firstPoint = false;
            } else {
                ctx.lineTo(x, y);
            }
        }
    });
    ctx.stroke();

    // X축 시간 레이블 (일부만 표시)
    ctx.fillStyle = '#495057';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';

    const labelStep = Math.max(1, Math.floor(candles.length / 5));
    candles.forEach((candle, i) => {
        if (i % labelStep === 0 || i === candles.length - 1) {
            const x = chartLeft + candleWidth * (i + 0.5);
            const timeStr = candle.time.split(' ')[1].substring(0, 5); // HH:MM만 추출
            ctx.fillText(timeStr, x, chartBottom + 15);
        }
    });

    // 차트 제목
    ctx.fillStyle = '#495057';
    ctx.font = 'bold 13px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('120분봉 차트 (MA5)', 10, 20);

    // 범례
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillStyle = '#9c27b0';
    ctx.fillText('━━ 5봉 이동평균', canvas.width - 10, 20);
}

// ========== Mode2 섹션 관리 ==========

// 드래그앤드롭 상태 관리
let draggedWatcher = null;
let draggedSection = null;

// 섹션 추가 버튼 이벤트
document.getElementById('addSectionBtn')?.addEventListener('click', async () => {
    const name = prompt('섹션명을 입력하세요:');
    if (!name || !name.trim()) return;

    try {
        const response = await fetch('/api/mode2/sections', {
            credentials: 'same-origin',
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name.trim() })
        });

        const result = await response.json();
        if (result.success) {
            showToast('✓ 섹션 추가 완료', 'success');
            loadMode2List();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast('요청 실패: ' + error.message, 'error');
    }
});

// 섹션 접기/펴기
async function toggleSection(sectionId) {
    try {
        const response = await fetch(`/api/mode2/sections/${sectionId}/toggle-collapse`, {
            credentials: 'same-origin',
            method: 'POST'
        });

        if (response.ok) {
            loadMode2List();
        }
    } catch (error) {
        console.error('섹션 토글 실패:', error);
    }
}

// 섹션명 편집
function editSectionName(sectionId) {
    event.stopPropagation();

    const sectionHeader = document.querySelector(`[data-section-id="${sectionId}"]`);
    if (!sectionHeader) return;

    const nameSpan = sectionHeader.querySelector('.section-name');
    const currentName = nameSpan.textContent;

    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentName;
    input.className = 'section-name editing';
    input.style.width = '200px';

    input.onblur = async () => {
        const newName = input.value.trim();
        if (newName && newName !== currentName) {
            try {
                const response = await fetch(`/api/mode2/sections/${sectionId}`, {
                    credentials: 'same-origin',
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: newName })
                });

                if (response.ok) {
                    showToast('✓ 섹션명 변경 완료', 'success');
                    loadMode2List();
                } else {
                    nameSpan.textContent = currentName;
                }
            } catch (error) {
                nameSpan.textContent = currentName;
            }
        } else {
            nameSpan.textContent = currentName;
        }
    };

    input.onkeydown = (e) => {
        if (e.key === 'Enter') input.blur();
        if (e.key === 'Escape') {
            input.value = currentName;
            input.blur();
        }
    };

    nameSpan.replaceWith(input);
    input.focus();
    input.select();
}

// 섹션 삭제
async function deleteSectionConfirm(sectionId) {
    if (!confirm('이 섹션을 삭제하시겠습니까?\n(종목은 미분류로 이동됩니다)')) return;

    try {
        const response = await fetch(`/api/mode2/sections/${sectionId}`, {
            credentials: 'same-origin',
            method: 'DELETE'
        });

        const result = await response.json();
        if (result.success) {
            showToast('✓ 섹션 삭제 완료', 'success');
            loadMode2List();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast('요청 실패: ' + error.message, 'error');
    }
}

// 종목 편집 모드
async function editWatcherRow(code) {
    const row = document.querySelector(`.mode2-watcher-row[data-code="${code}"]`);
    if (!row) return;

    const isEditMode = row.getAttribute('data-edit-mode') === 'true';

    if (isEditMode) {
        // 저장
        saveWatcherRow(code);
    } else {
        // 종목 데이터 조회
        try {
            const response = await fetch(`/api/mode2/watchers/${code}`, {
                credentials: 'same-origin'
            });
            const result = await response.json();

            if (result.success && result.data) {
                const w = result.data;

                // Mode2 폼에 값 채우기
                fillMode2Form(w);

                // 폼으로 스크롤
                document.getElementById('mode2Form').scrollIntoView({ behavior: 'smooth', block: 'start' });

                showToast('✓ 편집 모드 - 상단 폼에서 수정 후 저장하세요', 'info');
            }
        } catch (error) {
            console.error('데이터 조회 실패:', error);
            showToast('데이터 조회 실패', 'error');
        }

        // 편집 모드로 전환
        enterEditMode(row, code);

        // 차트 조회 및 표시
        await loadWatcherChart(code);
    }
}

// Mode2 폼에 watcher 데이터 채우기
function fillMode2Form(watcher) {
    document.getElementById('mode2Code').value = watcher.code;
    document.getElementById('mode2Name').value = watcher.name || '';
    document.getElementById('mode2Budget').value = watcher.budget;
    document.getElementById('mode2PollingInterval').value = watcher.polling_interval || 10;
    document.getElementById('mode2NotifyOnly').checked = watcher.notify_only || false;

    document.querySelector('input[name="buy_target_price"]').value = watcher.buy_target_price || '';
    document.querySelector('input[name="resistance_2_price"]').value = watcher.resistance_2_price || '';
    document.querySelector('input[name="resistance_2_profit_pct"]').value = watcher.resistance_2_profit_pct || 50;
    document.querySelector('input[name="resistance_1_price"]').value = watcher.resistance_1_price || '';
    document.querySelector('input[name="resistance_1_profit_pct"]').value = watcher.resistance_1_profit_pct || 50;
    document.querySelector('input[name="support_1_price"]').value = watcher.support_1_price || '';
    document.querySelector('input[name="support_1_loss_pct"]').value = watcher.support_1_loss_pct || 50;
    document.querySelector('input[name="support_2_price"]').value = watcher.support_2_price || '';
    document.querySelector('input[name="support_2_loss_pct"]').value = watcher.support_2_loss_pct || 50;
}

// 종목 편집 취소
function cancelWatcherEdit(code) {
    loadMode2List(); // 다시 로드하여 원래 상태로
}

// 종목 차트 조회 및 표시
async function loadWatcherChart(code) {
    try {
        // 종목 데이터 조회
        const watcherResponse = await fetch(`/api/mode2/watchers/${code}`, {
            credentials: 'same-origin'
        });
        const watcherResult = await watcherResponse.json();

        if (!watcherResult.success) {
            console.error('종목 데이터 조회 실패');
            return;
        }

        const watcher = watcherResult.data;

        // 차트 데이터 조회
        const chartResponse = await fetch('/api/test/daily-chart', {
            credentials: 'same-origin',
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: code })
        });

        const chartResult = await chartResponse.json();

        if (chartResult.success) {
            const chartContainer = document.getElementById('mode2ChartContainer');
            chartContainer.style.display = 'block';

            // 차트 데이터에 감시 레벨 추가
            const chartDataWithLevels = {
                ...chartResult.data,
                levels: {
                    buy_target: watcher.buy_target_price || 0,
                    resistance_1: watcher.resistance_1_price || 0,
                    resistance_2: watcher.resistance_2_price || 0,
                    support_1: watcher.support_1_price || 0,
                    support_2: watcher.support_2_price || 0
                }
            };

            // 차트 그리기
            window.lastMode2ChartData = chartDataWithLevels;
            drawMode2CandlestickChart(chartDataWithLevels);

            // 차트 위치로 스크롤
            chartContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    } catch (error) {
        console.error('차트 조회 실패:', error);
    }
}

// 종목 편집 저장
async function saveWatcherRow(code) {
    const row = document.querySelector(`.mode2-watcher-row[data-code="${code}"]`);
    if (!row) return;

    const data = {};
    let hasChanges = false;

    row.querySelectorAll('.editable').forEach(cell => {
        const field = cell.getAttribute('data-field');
        const input = cell.querySelector('input, textarea');

        if (input) {
            const originalValue = input.getAttribute('data-original-value');
            const currentValue = input.value;

            // 변경사항 체크
            if (originalValue !== currentValue) {
                hasChanges = true;
            }

            if (field === 'note') {
                data[field] = currentValue;
            } else {
                data[field] = parseInt(currentValue) || 0;
            }
        }
    });

    try {
        if (hasChanges) {
            const response = await fetch(`/api/mode2/watchers/${code}`, {
                credentials: 'same-origin',
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            if (result.success) {
                showToast('✓ 저장 완료', 'success');
                loadMode2List();
            } else {
                showToast(result.error, 'error');
            }
        } else {
            showToast('변경사항이 없습니다', 'info');
            loadMode2List();
        }
    } catch (error) {
        showToast('요청 실패: ' + error.message, 'error');
    }
}

// 단일 필드 즉시 업데이트
async function updateWatcherField(code, field, value) {
    try {
        const data = {};
        data[field] = field === 'polling_interval' ? parseInt(value) : value;

        const response = await fetch(`/api/mode2/watchers/${code}`, {
            credentials: 'same-origin',
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            showToast('✓ 업데이트 완료', 'success');
            loadMode2List();
        }
    } catch (error) {
        console.error('업데이트 실패:', error);
    }
}

// ========== 셀 더블클릭 인라인 편집 ==========

function enableCellEdit(cell, code) {
    // 이미 편집 중이면 무시
    if (cell.querySelector('input, textarea')) return;

    const field = cell.getAttribute('data-field');
    const isNote = field === 'note';
    const originalValue = isNote ? cell.getAttribute('title') : cell.textContent.replace(/,/g, '').replace(/원/g, '').trim();

    // input 또는 textarea 생성
    const input = document.createElement(isNote ? 'textarea' : 'input');

    if (isNote) {
        input.value = originalValue || '';
        input.maxLength = 500;
        input.style.width = '100%';
        input.style.minHeight = '40px';
        input.style.resize = 'vertical';
    } else {
        input.type = 'number';
        input.value = originalValue;
        input.style.width = '100%';
    }

    input.style.padding = '4px';
    input.style.border = '2px solid #228be6';
    input.style.borderRadius = '4px';
    input.style.fontSize = '13px';

    // 저장 함수
    const saveEdit = async () => {
        const newValue = input.value.trim();

        // 변경사항 체크
        if (newValue === originalValue) {
            cell.innerHTML = isNote ? truncateText(originalValue, 20) : formatNumber(originalValue);
            if (isNote) cell.setAttribute('title', originalValue);
            return;
        }

        // API 호출
        try {
            const data = {};
            data[field] = isNote ? newValue : (parseInt(newValue) || 0);

            const response = await fetch(`/api/mode2/watchers/${code}`, {
                credentials: 'same-origin',
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            if (result.success) {
                showToast('✓ 저장 완료', 'success');
                loadMode2List();
            } else {
                showToast(result.error || '저장 실패', 'error');
                cell.innerHTML = isNote ? truncateText(originalValue, 20) : formatNumber(originalValue);
                if (isNote) cell.setAttribute('title', originalValue);
            }
        } catch (error) {
            showToast('저장 실패: ' + error.message, 'error');
            cell.innerHTML = isNote ? truncateText(originalValue, 20) : formatNumber(originalValue);
            if (isNote) cell.setAttribute('title', originalValue);
        }
    };

    // 취소 함수
    const cancelEdit = () => {
        cell.innerHTML = isNote ? truncateText(originalValue, 20) : formatNumber(originalValue);
        if (isNote) cell.setAttribute('title', originalValue);
    };

    // 이벤트 리스너
    input.addEventListener('blur', saveEdit);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !isNote) {
            e.preventDefault();
            input.blur(); // blur 이벤트로 저장
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelEdit();
        }
    });

    // DOM 교체 및 포커스
    cell.innerHTML = '';
    cell.appendChild(input);
    input.focus();
    input.select();
}

// ========== 섹션별 일괄 편집 ==========

function toggleSectionEditMode(sectionId) {
    const section = document.querySelector(`.mode2-section[data-section-id="${sectionId}"]`);
    if (!section) return;

    const sectionBody = section.querySelector('.mode2-section-body');
    const rows = sectionBody.querySelectorAll('.mode2-watcher-row');

    // 첫 번째 row의 edit 상태 확인
    if (rows.length === 0) return;
    const firstRow = rows[0];
    const isEditMode = firstRow.getAttribute('data-edit-mode') === 'true';

    if (isEditMode) {
        // 저장 모드: 모든 row 저장
        saveSectionWatchers(sectionId, rows);
    } else {
        // 편집 모드: 모든 row를 편집 모드로 전환
        rows.forEach(row => {
            const code = row.getAttribute('data-code');
            enterEditMode(row, code);
        });

        // 섹션 버튼 아이콘 변경
        const editBtn = section.querySelector('.section-actions .section-btn[onclick*="toggleSectionEditMode"]');
        if (editBtn) {
            editBtn.textContent = '💾';
            editBtn.title = '섹션 일괄 저장';
        }
    }
}

function enterEditMode(row, code) {
    row.setAttribute('data-edit-mode', 'true');
    row.classList.add('editing');

    // editable 필드를 input으로 변경
    row.querySelectorAll('.editable').forEach(cell => {
        const field = cell.getAttribute('data-field');
        const value = cell.textContent.replace(/,/g, '').replace(/원/g, '').replace(/주/g, '').trim();

        if (field === 'note') {
            const textarea = document.createElement('textarea');
            textarea.value = cell.getAttribute('title') || '';
            textarea.maxLength = 500;
            textarea.setAttribute('data-original-value', textarea.value); // 원본 값 저장
            cell.innerHTML = '';
            cell.appendChild(textarea);
        } else {
            const input = document.createElement('input');
            input.type = 'number';
            input.value = value;
            input.setAttribute('data-original-value', value); // 원본 값 저장
            cell.innerHTML = '';
            cell.appendChild(input);
        }
    });

    // 액션 버튼 변경
    const actions = row.querySelector('.watcher-actions');
    actions.innerHTML = `
        <button class="watcher-action-btn save" onclick="saveWatcherRow('${code}')">✓</button>
        <button class="watcher-action-btn cancel" onclick="cancelWatcherEdit('${code}')">✗</button>
    `;
}

async function saveSectionWatchers(sectionId, rows) {
    const savePromises = [];

    rows.forEach(row => {
        const code = row.getAttribute('data-code');
        const data = {};
        let hasChanges = false;

        row.querySelectorAll('.editable').forEach(cell => {
            const field = cell.getAttribute('data-field');
            const input = cell.querySelector('input, textarea');

            if (input) {
                const originalValue = input.getAttribute('data-original-value');
                const currentValue = input.value;

                // 변경사항 체크
                if (originalValue !== currentValue) {
                    hasChanges = true;
                }

                if (field === 'note') {
                    data[field] = currentValue;
                } else {
                    data[field] = parseInt(currentValue) || 0;
                }
            }
        });

        // 변경사항이 있는 경우에만 저장
        if (hasChanges) {
            const promise = fetch(`/api/mode2/watchers/${code}`, {
                credentials: 'same-origin',
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            savePromises.push(promise);
        }
    });

    try {
        if (savePromises.length > 0) {
            await Promise.all(savePromises);
            showToast(`✓ ${savePromises.length}개 종목 저장 완료`, 'success');
        } else {
            showToast('변경사항이 없습니다', 'info');
        }
        loadMode2List();
    } catch (error) {
        showToast('저장 실패: ' + error.message, 'error');
    }
}

// ========== 벌크 등록 ==========

function openBulkAddModal() {
    document.getElementById('bulkAddModal').style.display = 'block';
    document.getElementById('bulkAddInput').value = '';
    document.getElementById('bulkAddResult').style.display = 'none';
}

function closeBulkAddModal() {
    document.getElementById('bulkAddModal').style.display = 'none';
}

async function executeBulkAdd() {
    const input = document.getElementById('bulkAddInput').value.trim();
    const resultDiv = document.getElementById('bulkAddResult');

    if (!input) {
        alert('입력 내용이 없습니다.');
        return;
    }

    // 줄 단위로 분리
    const lines = input.split('\n').map(line => line.trim()).filter(line => line.length > 0);

    if (lines.length < 2) {
        alert('최소 헤더 1줄 + 데이터 1줄 이상 입력하세요.');
        return;
    }

    // 첫 줄은 헤더 (무시)
    const dataLines = lines.slice(1);

    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<p style="color: #228be6;">⏳ 등록 중...</p>';

    const results = {
        success: [],
        skipped: [],
        failed: []
    };

    // 기존 종목 코드 조회
    const existingCodesResponse = await fetch('/api/mode2/watchers', { credentials: 'same-origin' });
    const existingCodesResult = await existingCodesResponse.json();
    const existingCodes = new Set(existingCodesResult.data.map(w => w.code));

    // 각 줄 처리
    for (const line of dataLines) {
        const parts = line.split(',').map(p => p.trim());

        if (parts.length < 2) {
            results.failed.push({ line, reason: '최소 2개 컬럼 필요 (종목코드, 매수타점)' });
            continue;
        }

        const [code, buy_target, support_1, resistance_1, support_2, resistance_2, sectionName] = parts;

        // 종목코드 검증
        if (!code) {
            results.failed.push({ line, reason: '종목코드 누락' });
            continue;
        }

        // 이미 등록된 종목이면 스킵
        if (existingCodes.has(code)) {
            results.skipped.push(code);
            continue;
        }

        // 매수타점 검증
        const buyTargetPrice = parseInt(buy_target) || 0;
        if (buyTargetPrice <= 0) {
            results.failed.push({ line, reason: '매수타점 필수 (양수)' });
            continue;
        }

        // 종목명 조회
        let stockName = '';
        try {
            const nameResponse = await fetch('/api/test/stock-info/' + code, { credentials: 'same-origin' });
            const nameResult = await nameResponse.json();
            if (nameResult.success) {
                stockName = nameResult.data.name || code;
            } else {
                stockName = code;
            }
        } catch (e) {
            stockName = code;
        }

        // 섹션 처리
        let targetSectionId = 'uncategorized';
        if (sectionName && sectionName !== '') {
            // 섹션 존재 여부 확인
            const sectionsResponse = await fetch('/api/mode2/sections', { credentials: 'same-origin' });
            const sectionsResult = await sectionsResponse.json();

            if (sectionsResult.success) {
                const existingSection = sectionsResult.data.find(s => s.name === sectionName);
                if (existingSection) {
                    targetSectionId = existingSection.id;
                } else {
                    // 섹션 생성
                    const createSectionResponse = await fetch('/api/mode2/sections', {
                        credentials: 'same-origin',
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name: sectionName })
                    });
                    const createSectionResult = await createSectionResponse.json();
                    if (createSectionResult.success) {
                        targetSectionId = createSectionResult.data.id;
                    }
                }
            }
        }

        // Mode2 종목 등록
        const data = {
            code: code,
            name: stockName,
            buy_target_price: buyTargetPrice,
            budget: 300000, // 기본값
            polling_interval: 180, // 기본값 (3분)
            notify_only: true, // 기본값 (알림 모드)
            resistance_1_price: parseInt(resistance_1) || 0,
            resistance_1_profit_pct: 0,
            resistance_2_price: parseInt(resistance_2) || 0,
            resistance_2_profit_pct: 0,
            support_1_price: parseInt(support_1) || 0,
            support_1_loss_pct: 0,
            support_2_price: parseInt(support_2) || 0,
            support_2_loss_pct: 0,
            section: targetSectionId
        };

        try {
            const response = await fetch('/api/mode2/watchers', {
                credentials: 'same-origin',
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                results.success.push(`${stockName} (${code})`);
            } else {
                results.failed.push({ line, reason: result.error || '등록 실패' });
            }
        } catch (error) {
            results.failed.push({ line, reason: error.message });
        }
    }

    // 결과 표시
    let resultHtml = '<div style="background: #f8f9fa; padding: 12px; border-radius: 6px;">';
    resultHtml += `<p style="font-weight: 600; margin-bottom: 8px;">📊 등록 결과</p>`;

    if (results.success.length > 0) {
        resultHtml += `<p style="color: #2f9e44; margin: 4px 0;">✓ 성공: ${results.success.length}개</p>`;
        resultHtml += `<ul style="font-size: 12px; color: #495057; margin: 4px 0 8px 20px;">`;
        results.success.forEach(name => {
            resultHtml += `<li>${name}</li>`;
        });
        resultHtml += `</ul>`;
    }

    if (results.skipped.length > 0) {
        resultHtml += `<p style="color: #f59f00; margin: 4px 0;">⊘ 스킵 (이미 등록됨): ${results.skipped.length}개</p>`;
        resultHtml += `<ul style="font-size: 12px; color: #495057; margin: 4px 0 8px 20px;">`;
        results.skipped.forEach(code => {
            resultHtml += `<li>${code}</li>`;
        });
        resultHtml += `</ul>`;
    }

    if (results.failed.length > 0) {
        resultHtml += `<p style="color: #c92a2a; margin: 4px 0;">✗ 실패: ${results.failed.length}개</p>`;
        resultHtml += `<ul style="font-size: 12px; color: #495057; margin: 4px 0 8px 20px;">`;
        results.failed.forEach(item => {
            resultHtml += `<li>${item.line} → ${item.reason}</li>`;
        });
        resultHtml += `</ul>`;
    }

    resultHtml += '</div>';
    resultDiv.innerHTML = resultHtml;

    // 리스트 리로드
    if (results.success.length > 0) {
        setTimeout(() => {
            loadMode2List();
            showToast(`✓ ${results.success.length}개 종목 등록 완료`, 'success');
        }, 1000);
    }
}

// ========== 종목 드래그앤드롭 ==========

function handleWatcherDragStart(event) {
    const row = event.currentTarget;
    draggedWatcher = {
        code: row.getAttribute('data-code'),
        section: row.getAttribute('data-section')
    };
    row.style.opacity = '0.4';
    event.dataTransfer.effectAllowed = 'move';
}

function handleWatcherDragEnd(event) {
    event.currentTarget.style.opacity = '1';
    draggedWatcher = null;
}

function handleWatcherDragOver(event) {
    if (!draggedWatcher) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
}

async function handleWatcherDrop(event) {
    event.preventDefault();
    event.stopPropagation();

    if (!draggedWatcher) return;

    const targetRow = event.currentTarget;
    const targetCode = targetRow.getAttribute('data-code');
    const targetSection = targetRow.getAttribute('data-section');

    // 같은 종목이면 무시
    if (draggedWatcher.code === targetCode) return;

    // 섹션이 다르면 섹션 이동
    if (draggedWatcher.section !== targetSection) {
        await moveWatcherToSection(draggedWatcher.code, targetSection);
        return;
    }

    // 같은 섹션 내 순서 변경
    await reorderWatchersInSection(targetSection, draggedWatcher.code, targetCode);
}

async function reorderWatchersInSection(sectionId, draggedCode, targetCode) {
    try {
        // 현재 섹션의 모든 종목 가져오기
        const response = await fetch(`/api/mode2/sections/${sectionId}/watchers`, {
            credentials: 'same-origin'
        });
        const result = await response.json();

        if (!result.success) return;

        const watchers = result.data;
        const draggedIdx = watchers.findIndex(w => w.code === draggedCode);
        const targetIdx = watchers.findIndex(w => w.code === targetCode);

        if (draggedIdx === -1 || targetIdx === -1) return;

        // 순서 재정렬
        const [draggedItem] = watchers.splice(draggedIdx, 1);
        watchers.splice(targetIdx, 0, draggedItem);

        // display_order 재할당
        const watcher_orders = watchers.map((w, idx) => ({
            code: w.code,
            display_order: idx + 1
        }));

        // 서버에 순서 업데이트
        const updateResponse = await fetch(`/api/mode2/sections/${sectionId}/reorder-watchers`, {
            credentials: 'same-origin',
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ watcher_orders })
        });

        if (updateResponse.ok) {
            loadMode2List();
        }
    } catch (error) {
        console.error('순서 변경 실패:', error);
    }
}

async function moveWatcherToSection(code, targetSectionId) {
    try {
        const response = await fetch(`/api/mode2/watchers/${code}/move-section`, {
            credentials: 'same-origin',
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ section_id: targetSectionId })
        });

        if (response.ok) {
            showToast('✓ 섹션 이동 완료', 'success');
            loadMode2List();
        }
    } catch (error) {
        console.error('섹션 이동 실패:', error);
    }
}

// ========== 섹션 드래그앤드롭 ==========

function handleSectionDragStart(event) {
    const section = event.currentTarget;
    draggedSection = {
        id: section.getAttribute('data-section-id'),
        order: parseInt(section.getAttribute('data-section-order'))
    };
    section.style.opacity = '0.4';
    event.dataTransfer.effectAllowed = 'move';
}

function handleSectionDragEnd(event) {
    event.currentTarget.style.opacity = '1';
    draggedSection = null;
}

function handleSectionDragOver(event) {
    if (!draggedSection) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
}

async function handleSectionDrop(event) {
    event.preventDefault();
    event.stopPropagation();

    if (!draggedSection) return;

    const targetSection = event.currentTarget;
    const targetId = targetSection.getAttribute('data-section-id');
    const targetOrder = parseInt(targetSection.getAttribute('data-section-order'));

    if (draggedSection.id === targetId) return;

    // 섹션 순서 재정렬
    await reorderSections(draggedSection.id, draggedSection.order, targetId, targetOrder);
}

async function reorderSections(draggedId, draggedOrder, targetId, targetOrder) {
    try {
        // 모든 섹션 가져오기
        const response = await fetch('/api/mode2/sections', {
            credentials: 'same-origin'
        });
        const result = await response.json();

        if (!result.success) return;

        const sections = result.data;
        const draggedIdx = sections.findIndex(s => s.id === draggedId);
        const targetIdx = sections.findIndex(s => s.id === targetId);

        if (draggedIdx === -1 || targetIdx === -1) return;

        // 순서 재정렬
        const [draggedItem] = sections.splice(draggedIdx, 1);
        sections.splice(targetIdx, 0, draggedItem);

        // order 재할당
        const section_orders = sections.map((s, idx) => ({
            id: s.id,
            order: idx + 1
        }));

        // 서버에 순서 업데이트
        const updateResponse = await fetch('/api/mode2/sections/reorder', {
            credentials: 'same-origin',
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ section_orders })
        });

        if (updateResponse.ok) {
            loadMode2List();
        }
    } catch (error) {
        console.error('섹션 순서 변경 실패:', error);
    }
}

// ========== 복수 종목 선택 및 섹션 이동 ==========

function handleWatcherCheckboxChange() {
    const checkboxes = document.querySelectorAll('.watcher-checkbox:checked');
    const count = checkboxes.length;

    const bulkPanel = document.getElementById('bulkActionsPanel');
    const selectedCountSpan = document.getElementById('selectedCount');

    if (count > 0) {
        bulkPanel.style.display = 'flex';
        selectedCountSpan.textContent = count;
        updateTargetSectionSelect();
    } else {
        bulkPanel.style.display = 'none';
    }

    // 섹션별 전체 선택 체크박스 상태 동기화
    syncSectionSelectAllCheckboxes();

    // 섹션별 선택 삭제 버튼 표시/숨김
    updateSectionDeleteButtons();
}

// 섹션별 전체 선택 체크박스 상태 동기화
function syncSectionSelectAllCheckboxes() {
    const sections = document.querySelectorAll('.mode2-section');

    sections.forEach(section => {
        const sectionId = section.getAttribute('data-section-id');
        const selectAllCheckbox = section.querySelector('.section-select-all');
        const watcherCheckboxes = section.querySelectorAll('.watcher-checkbox');
        const checkedCheckboxes = section.querySelectorAll('.watcher-checkbox:checked');

        if (selectAllCheckbox && watcherCheckboxes.length > 0) {
            // 모두 선택되었으면 전체 선택 체크박스도 체크
            selectAllCheckbox.checked = (watcherCheckboxes.length === checkedCheckboxes.length);
            // 일부만 선택되었으면 indeterminate 상태로
            selectAllCheckbox.indeterminate = (checkedCheckboxes.length > 0 && checkedCheckboxes.length < watcherCheckboxes.length);
        }
    });
}

// 섹션별 전체 선택/해제
function toggleSectionSelectAll(sectionId) {
    const section = document.querySelector(`.mode2-section[data-section-id="${sectionId}"]`);
    if (!section) return;

    const selectAllCheckbox = section.querySelector('.section-select-all');
    const watcherCheckboxes = section.querySelectorAll('.watcher-checkbox');

    watcherCheckboxes.forEach(cb => {
        cb.checked = selectAllCheckbox.checked;
    });

    handleWatcherCheckboxChange();
}

// 섹션별 선택 삭제 버튼 표시 업데이트
function updateSectionDeleteButtons() {
    const sections = document.querySelectorAll('.mode2-section');

    sections.forEach(section => {
        const sectionId = section.getAttribute('data-section-id');
        const checkboxes = section.querySelectorAll('.watcher-checkbox:checked');
        const deleteBtn = section.querySelector('.section-delete-selected');

        if (deleteBtn) {
            if (checkboxes.length > 0) {
                deleteBtn.style.display = 'inline-block';
                deleteBtn.textContent = `🗑️ 선택 삭제 (${checkboxes.length})`;
            } else {
                deleteBtn.style.display = 'none';
            }
        }
    });
}

// 섹션 내 선택 항목 일괄 삭제
async function deleteSectionSelected(sectionId) {
    const section = document.querySelector(`.mode2-section[data-section-id="${sectionId}"]`);
    if (!section) return;

    const checkboxes = section.querySelectorAll('.watcher-checkbox:checked');
    const codes = Array.from(checkboxes).map(cb => cb.value);

    if (codes.length === 0) {
        showToast('선택된 종목이 없습니다', 'error');
        return;
    }

    if (!confirm(`선택한 ${codes.length}개 종목을 삭제하시겠습니까?`)) {
        return;
    }

    try {
        const deletePromises = codes.map(code =>
            fetch(`/api/mode2/watchers/${code}`, {
                credentials: 'same-origin',
                method: 'DELETE'
            })
        );

        await Promise.all(deletePromises);

        showToast(`✓ ${codes.length}개 종목 삭제 완료`, 'success');
        loadMode2List();
    } catch (error) {
        showToast('삭제 실패: ' + error.message, 'error');
    }
}

async function updateTargetSectionSelect() {
    const select = document.getElementById('targetSectionSelect');
    if (!select) return;

    try {
        const response = await fetch('/api/mode2/sections', {
            credentials: 'same-origin'
        });
        const result = await response.json();

        if (result.success) {
            select.innerHTML = '<option value="">이동할 섹션 선택</option>' +
                result.data.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
        }
    } catch (error) {
        console.error('섹션 목록 로드 실패:', error);
    }
}

// 복수 종목 이동 버튼
document.getElementById('moveBulkBtn')?.addEventListener('click', async () => {
    const targetSectionId = document.getElementById('targetSectionSelect').value;
    if (!targetSectionId) {
        showToast('섹션을 선택하세요', 'error');
        return;
    }

    const checkboxes = document.querySelectorAll('.watcher-checkbox:checked');
    const codes = Array.from(checkboxes).map(cb => cb.value);

    if (codes.length === 0) return;

    try {
        // 각 종목을 대상 섹션으로 이동
        const promises = codes.map(code =>
            fetch(`/api/mode2/watchers/${code}/move-section`, {
                credentials: 'same-origin',
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ section_id: targetSectionId })
            })
        );

        await Promise.all(promises);
        showToast(`✓ ${codes.length}개 종목 이동 완료`, 'success');
        loadMode2List();
    } catch (error) {
        showToast('이동 실패: ' + error.message, 'error');
    }
});

// 선택 취소 버튼
document.getElementById('cancelBulkBtn')?.addEventListener('click', () => {
    document.querySelectorAll('.watcher-checkbox').forEach(cb => cb.checked = false);
    handleWatcherCheckboxChange();
});
