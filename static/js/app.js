// ========== 페이지 전환 ==========
document.addEventListener('DOMContentLoaded', () => {
    // 상단 nav 클릭
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => switchPage(item.dataset.page));
    });
    // 하단 탭바 클릭
    document.querySelectorAll('.tab-item').forEach(item => {
        item.addEventListener('click', () => switchPage(item.dataset.page));
    });

    // 초기 페이지: mode2
    loadMode2List();
    _syncTabBar('mode2');

    // 이벤트 리스너 등록
    setupEventListeners();
});

function _syncTabBar(pageName) {
    document.querySelectorAll('.tab-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === pageName);
    });
}

function switchPage(pageName) {
    // 상단 nav 활성화
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === pageName);
    });
    // 하단 탭바 활성화
    _syncTabBar(pageName);

    // 페이지 표시
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    const targetPage = document.getElementById(pageName + 'Page');
    if (targetPage) targetPage.classList.add('active');

    // 페이지별 데이터 로드
    if (pageName === 'watchlist') loadWatchlist();
    else if (pageName === 'mode1') loadMode1List();
    else if (pageName === 'mode2') loadMode2List();
    else if (pageName === 'tradelog') loadTradelog();
    else if (pageName === 'siwhang') loadSiwhang();
    else if (pageName === 'live') loadLive();
    else if (pageName === 'seeking-signal') loadTradeWatchlist();
    else if (pageName === 'backtest') { loadBacktestSessions(); loadMottos(); }
    else if (pageName === 'test') loadMode2PickList();
}

function toggleSupport1Mode(mode) {
    const lossPct = document.getElementById('support1LossPct');
    const addBudget = document.getElementById('support1AddBudget');
    if (mode === '물타기') {
        lossPct.style.display = 'none';
        addBudget.style.display = '';
    } else {
        lossPct.style.display = '';
        addBudget.style.display = 'none';
    }
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

    // 검색 드롭다운 외부 클릭 시 닫기
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.stock-search-wrap')) {
            const dd = document.getElementById('stockSearchDropdown');
            if (dd) dd.style.display = 'none';
        }
    });

    // Mode2 notify_only 체크박스 변경 시 polling 자동 조정
    const mode2NotifyOnly = document.getElementById('mode2NotifyOnly');
    const mode2PollingInterval = document.getElementById('mode2PollingInterval');
    if (mode2NotifyOnly && mode2PollingInterval) {
        mode2NotifyOnly.addEventListener('change', () => {
            // 알림 전용: 3분(180초), 자동매매: 30초
            mode2PollingInterval.value = mode2NotifyOnly.checked ? '180' : '30';
        });
    }

    // Mode2 Budget picklist 변경 시 처리
    const mode2BudgetSelect = document.getElementById('mode2BudgetSelect');
    const mode2BudgetInput = document.getElementById('mode2Budget');
    if (mode2BudgetSelect && mode2BudgetInput) {
        mode2BudgetSelect.addEventListener('change', () => {
            if (mode2BudgetSelect.value === 'custom') {
                mode2BudgetInput.style.display = 'inline-block';
                mode2BudgetInput.focus();
            } else {
                mode2BudgetInput.style.display = 'none';
                mode2BudgetInput.value = mode2BudgetSelect.value;
            }
        });
    }

    // Mode2 익절/손절 % 자동 계산 (합=100)
    const resistance1ProfitPct = document.getElementById('resistance1ProfitPct');
    const resistance2ProfitPct = document.querySelector('select[name="resistance_2_profit_pct"]');
    const support1LossPct = document.getElementById('support1LossPct');
    const support2LossPct = document.querySelector('select[name="support_2_loss_pct"]');

    if (resistance1ProfitPct && resistance2ProfitPct) {
        resistance1ProfitPct.addEventListener('change', () => {
            const val1 = parseInt(resistance1ProfitPct.value);
            const val2 = 100 - val1;
            resistance2ProfitPct.value = val2;
        });
    }

    if (support1LossPct && support2LossPct) {
        support1LossPct.addEventListener('change', () => {
            const val1 = parseInt(support1LossPct.value);
            const val2 = 100 - val1;
            support2LossPct.value = val2;
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
                <td style="cursor:pointer; color:#228be6;" onclick="openStockNotesModal('${w.code}','${(w.name||'-').replace(/'/g,"\\'")}')">${w.name || '-'}</td>
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

    // 구역 정렬 우선순위: 3→4→5→1→2 (0=미설정은 맨 뒤)
    const ZONE_SORT = {3: 0, 4: 1, 5: 2, 1: 3, 2: 4, 0: 5};
    Object.keys(watchersBySection).forEach(sectionId => {
        watchersBySection[sectionId].sort((a, b) => {
            // 1순위: auto_paused (최상단)
            const pausedA = a.auto_paused ? 0 : 1;
            const pausedB = b.auto_paused ? 0 : 1;
            if (pausedA !== pausedB) return pausedA - pausedB;

            // 2순위: 구역 (3→4→5→1→2)
            const za = ZONE_SORT[a.zone || 0] ?? 5;
            const zb = ZONE_SORT[b.zone || 0] ?? 5;
            if (za !== zb) return za - zb;

            // 3순위: notify_only (false가 우선)
            const notifyA = a.notify_only ? 1 : 0;
            const notifyB = b.notify_only ? 1 : 0;
            if (notifyA !== notifyB) return notifyA - notifyB;

            // 4순위: display_order
            return (a.display_order || 9999) - (b.display_order || 9999);
        });
    });

    // 날짜 필터 상태 유지
    const activeFilter = document.getElementById('mode2DateFilter')?.value || '';

    container.innerHTML = sections.map(section => {
        const watchers = watchersBySection[section.id] || [];
        const collapsed = section.collapsed || false;

        // 섹션명에서 날짜 추출 (YYYY-MM-DD 패턴)
        const dateMatch = (section.name || '').match(/(\d{4}-\d{2}-\d{2})/);
        const sectionDate = dateMatch ? dateMatch[1] : '';
        const hideSection = activeFilter && sectionDate && sectionDate !== activeFilter ? ' style="display:none"' : '';

        return `
            <div class="mode2-section mode2-section-card" data-section-id="${section.id}" data-section-order="${section.order}" data-section-date="${sectionDate}"
                 draggable="true" ondragstart="handleSectionDragStart(event)" ondragend="handleSectionDragEnd(event)"
                 ondragover="handleSectionDragOver(event)" ondrop="handleSectionDrop(event)"${hideSection}>
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
    const autoPaused = w.auto_paused || false;
    const editMode = false; // 초기값

    return `
        <div class="mode2-watcher-row ${autoPaused ? 'auto-paused' : ''}" data-code="${w.code}" data-section="${w.section}" data-edit-mode="false"
             draggable="true" ondragstart="handleWatcherDragStart(event)" ondragend="handleWatcherDragEnd(event)"
             ondragover="handleWatcherDragOver(event)" ondrop="handleWatcherDrop(event)">
            <div class="watcher-cell">
                <input type="checkbox" class="watcher-checkbox" value="${w.code}" data-section="${w.section}" onchange="handleWatcherCheckboxChange()">
            </div>
            <div class="watcher-drag-handle" style="cursor: move;">☰</div>
            <div class="watcher-cell">${w.record_id || '-'}</div>
            <div class="watcher-cell"><strong>${w.code}</strong></div>
            <div class="watcher-cell" onclick="openStockNotesModal('${w.code}', '${(w.name || '-').replace(/'/g, "\\'")}')"
                 onmouseenter="showStockTooltip(event, '${w.code}', '${(w.name || '').replace(/'/g, "\\'")}')"
                 onmouseleave="hideStockTooltip()"
                 style="cursor: pointer; color: #228be6; font-weight: 600;">${autoPaused ? '⚠️ ' : ''}${w.name || '-'}</div>
            <div class="watcher-cell editable" data-field="buy_target_price" ondblclick="enableCellEdit(this, '${w.code}')">${formatNumber(w.buy_target_price)}</div>
            <div class="watcher-cell editable" data-field="budget" ondblclick="enableCellEdit(this, '${w.code}')">${(w.budget / 10000).toFixed(0)}만</div>
            <div class="watcher-cell">${w.quantity}주</div>
            <div class="watcher-cell editable" data-field="support_2_price" ondblclick="enableCellEdit(this, '${w.code}')">${formatNumber(w.support_2_price)}</div>
            <div class="watcher-cell editable" data-field="support_1_price" ondblclick="enableCellEdit(this, '${w.code}')">
                ${formatNumber(w.support_1_price)}${w.support_1_price > 0 ? `<span style="font-size:10px;margin-left:3px;color:${w.support_1_mode === '물타기' ? '#1971c2' : '#e03131'};">${w.support_1_mode === '물타기' ? '📥' : '✂️'}</span>` : ''}
            </div>
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
            <div class="watcher-cell monitoring-status ${getMonitoringStatusClass(w.monitoring_status)}">${renderZoneCell(w)}</div>
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
    if (status.includes('5구역') || status.includes('손절') || status.includes('이탈')) return 'danger';
    if (status.includes('4구역')) return 'warning';
    if (status.includes('1구역') || status.includes('익절') || status.includes('저항 통과')) return 'success';
    if (status.includes('2구역')) return 'success';
    if (status.includes('매수타점')) return 'warning';
    return '';
}

function renderZoneCell(w) {
    const zone = w.zone || 0;
    const status = w.monitoring_status || '';
    if (!status && !zone) return '-';

    // 진입 시각
    let enteredStr = '';
    if (w.zone_entered_at) {
        const d = new Date(w.zone_entered_at);
        enteredStr = `<span style="font-size:10px;color:#868e96;display:block;">${d.toLocaleTimeString('ko-KR', {hour:'2-digit',minute:'2-digit'})}</span>`;
    }

    // 왕복 카운트
    let transStr = '';
    if (w.zone_transitions && Object.keys(w.zone_transitions).length > 0) {
        const parts = Object.entries(w.zone_transitions)
            .filter(([,v]) => v > 0)
            .map(([k,v]) => `${k}구역 ${v}회`);
        if (parts.length > 0) {
            transStr = `<span style="font-size:10px;color:#868e96;display:block;">↔ ${parts.join(' / ')}</span>`;
        }
    }

    return `${status}${enteredStr}${transStr}`;
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

    // Budget 계산 (만원 단위)
    const budgetSelect = document.getElementById('mode2BudgetSelect').value;
    let budgetValue = 0;
    if (budgetSelect === 'custom') {
        const manwon = parseInt(document.getElementById('mode2Budget').value) || 0;
        budgetValue = manwon * 10000;
    } else {
        const manwon = parseInt(budgetSelect);
        budgetValue = manwon * 10000;
    }

    const data = {
        code: code,
        name: name,
        buy_target_price: parseInt(formData.get('buy_target_price')) || 0,
        budget: budgetValue,
        polling_interval: parseInt(formData.get('polling_interval')) || 10,
        notify_only: notifyOnly,
        resistance_1_price: parseInt(formData.get('resistance_1_price')) || 0,
        resistance_1_profit_pct: parseFloat(formData.get('resistance_1_profit_pct')) || 0,
        resistance_2_price: parseInt(formData.get('resistance_2_price')) || 0,
        resistance_2_profit_pct: parseFloat(formData.get('resistance_2_profit_pct')) || 0,
        support_1_price: parseInt(formData.get('support_1_price')) || 0,
        support_1_mode: formData.get('support_1_mode') || '손절',
        support_1_loss_pct: parseFloat(formData.get('support_1_loss_pct')) || 0,
        support_1_add_budget: (parseInt(formData.get('support_1_add_budget_manwon')) || 0) * 10000,
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

// 날짜 문자열에서 4자리 연도를 '26 형식으로 축약 (표시용)
function shortenYear(text) {
    if (!text) return text;
    return text.replace(/\b(20\d{2})\b/g, (m, y) => "'" + y.slice(2));
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
                                <div style="display: flex; gap: 6px; justify-content: center; flex-wrap: wrap;">
                                    <button class="btn btn-primary" style="font-size: 11px; padding: 4px 10px;"
                                            onclick="showMode2TransferModal('${p.code}', '${p.name}', ${p.quantity}, ${p.buy_price})">
                                        📊 Mode2
                                    </button>
                                    <button class="btn btn-danger" style="font-size: 11px; padding: 4px 10px;"
                                            onclick="showHoldingSellModal('${p.code}', '${p.name}', ${p.quantity}, ${p.buy_price})">
                                        매도
                                    </button>
                                </div>
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

// ─── 종목명 검색 자동완성 ──────────────────────────────────────────────────

let _stockSearchTimer = null;
let _stockSearchActiveIdx = -1;

function stockSearchDebounce(q) {
    clearTimeout(_stockSearchTimer);
    if (!q.trim()) {
        const dd = document.getElementById('stockSearchDropdown');
        if (dd) dd.style.display = 'none';
        return;
    }
    _stockSearchTimer = setTimeout(() => doStockSearch(q), 200);
}

async function doStockSearch(q) {
    const dd = document.getElementById('stockSearchDropdown');
    if (!dd) return;
    try {
        const res = await fetch(`/api/stock/search?q=${encodeURIComponent(q)}`, { credentials: 'same-origin' });
        const r = await res.json();
        const results = r.results || [];
        if (!results.length) { dd.style.display = 'none'; return; }
        _stockSearchActiveIdx = -1;
        dd.innerHTML = results.map((item, i) =>
            `<div class="stock-search-item" data-idx="${i}" data-code="${item.stock_code}" data-name="${item.stock_name}"
                  onmousedown="selectStockSearchItem('${item.stock_code}','${item.stock_name}')"
                  onmouseenter="highlightSearchItem(${i})">
                <span class="ssi-name">${item.stock_name}</span>
                <span class="ssi-code">${item.stock_code}</span>
            </div>`
        ).join('');
        dd.style.display = 'block';
    } catch (e) { /* 검색 실패 무시 */ }
}

function selectStockSearchItem(code, name) {
    const codeInput = document.getElementById('mode2Code');
    const nameInput = document.getElementById('mode2Name');
    const searchInput = document.getElementById('mode2SearchInput');
    if (codeInput) codeInput.value = code;
    if (nameInput) nameInput.value = name;
    if (searchInput) searchInput.value = name;
    const dd = document.getElementById('stockSearchDropdown');
    if (dd) dd.style.display = 'none';
    // 차트 자동 조회
    handleMode2Lookup();
}

function onMode2CodeInput(val) {
    // 코드 직접 입력 시 검색 인풋 초기화
    const searchInput = document.getElementById('mode2SearchInput');
    if (searchInput && val) searchInput.value = '';
}

function highlightSearchItem(idx) {
    _stockSearchActiveIdx = idx;
    document.querySelectorAll('.stock-search-item').forEach((el, i) => {
        el.classList.toggle('active', i === idx);
    });
}

function stockSearchKeyNav(e) {
    const dd = document.getElementById('stockSearchDropdown');
    if (!dd || dd.style.display === 'none') return;
    const items = dd.querySelectorAll('.stock-search-item');
    if (!items.length) return;
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        _stockSearchActiveIdx = Math.min(_stockSearchActiveIdx + 1, items.length - 1);
        highlightSearchItem(_stockSearchActiveIdx);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        _stockSearchActiveIdx = Math.max(_stockSearchActiveIdx - 1, 0);
        highlightSearchItem(_stockSearchActiveIdx);
    } else if (e.key === 'Enter') {
        e.preventDefault();
        if (_stockSearchActiveIdx >= 0 && items[_stockSearchActiveIdx]) {
            const el = items[_stockSearchActiveIdx];
            selectStockSearchItem(el.dataset.code, el.dataset.name);
        }
    } else if (e.key === 'Escape') {
        dd.style.display = 'none';
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

            // 전일 OHLC → 디마크 입력란 자동 채움 + 계산
            const ch = result.data.chart;
            if (ch) {
                const o = parseFloat(ch.yesterday_open), h = parseFloat(ch.yesterday_high),
                      l = parseFloat(ch.yesterday_low),  c = parseFloat(ch.yesterday_close);
                if (o && h && l && c) {
                    document.getElementById('demarkOpen').value  = o;
                    document.getElementById('demarkHigh').value  = h;
                    document.getElementById('demarkLow').value   = l;
                    document.getElementById('demarkClose').value = c;
                    calcAndFillDemark();
                }
            }

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
            document.querySelector('select[name="resistance_2_profit_pct"]').value = w.resistance_2_profit_pct;
            document.querySelector('input[name="resistance_1_price"]').value = w.resistance_1_price;
            document.querySelector('select[name="resistance_1_profit_pct"]').value = w.resistance_1_profit_pct;
            document.querySelector('input[name="support_1_price"]').value = w.support_1_price;
            const s1modeLoad = w.support_1_mode || '손절';
            document.querySelector('select[name="support_1_mode"]').value = s1modeLoad;
            toggleSupport1Mode(s1modeLoad);
            document.querySelector('select[name="support_1_loss_pct"]').value = w.support_1_loss_pct;
            document.getElementById('support1AddBudget').value = w.support_1_add_budget ? Math.round(w.support_1_add_budget / 10000) : '';
            document.querySelector('input[name="support_2_price"]').value = w.support_2_price;
            document.querySelector('select[name="support_2_loss_pct"]').value = w.support_2_loss_pct;

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

        // 자동매매 전환 시 auto_paused 플래그도 함께 초기화
        const updatePayload = { notify_only: notifyOnly };
        if (!notifyOnly) updatePayload.auto_paused = false;

        const updateResponse = await fetch(`/api/mode2/watchers/${code}`, {
            credentials: 'same-origin',
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatePayload)
        });

        const updateResult = await updateResponse.json();

        if (updateResult.success) {
            const mode = notifyOnly ? '알림 전용' : '자동매매';
            showToast(`✓ ${mode} 모드로 변경됨`, 'success');
            loadMode2List();
            loadWatchlist();
        } else {
            showToast(`⚠️ ${updateResult.error || '모드 변경 실패'}`, 'error');
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

function _calcDemark(open, high, low, close) {
    // Demark pivot formula
    let x;
    if (close < open)      x = high + 2 * low + close;
    else if (close > open) x = 2 * high + low + close;
    else                   x = high + low + 2 * close;
    return { targetHigh: Math.round(x / 2 - low), targetLow: Math.round(x / 2 - high) };
}

function calcAndFillDemark() {
    const o = parseFloat(document.getElementById('demarkOpen')?.value);
    const h = parseFloat(document.getElementById('demarkHigh')?.value);
    const l = parseFloat(document.getElementById('demarkLow')?.value);
    const c = parseFloat(document.getElementById('demarkClose')?.value);
    if (!o || !h || !l || !c) return;
    const dm = _calcDemark(o, h, l, c);
    const r1 = document.querySelector('[name="resistance_1_price"]');
    const s1 = document.querySelector('[name="support_1_price"]');
    if (r1) r1.value = dm.targetHigh;
    if (s1) s1.value = dm.targetLow;
    const resultEl = document.getElementById('demarkResult');
    if (resultEl) resultEl.textContent = `1차저항: ${dm.targetHigh.toLocaleString()}  1차지지: ${dm.targetLow.toLocaleString()}`;
}

function redrawMode2Chart() {
    if (window.lastMode2ChartData) drawMode2CandlestickChart(window.lastMode2ChartData);
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
    const padding = priceRange * 0.25;  // 15% → 25% 여유 공간 증가 (전일 데이터 포함)

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

    // ── 디마크 오버레이 ───────────────────────────────────────
    const demarkChk = document.getElementById('demarkOverlayChk');
    if (demarkChk && demarkChk.checked) {
        const dO = parseFloat(document.getElementById('demarkOpen')?.value);
        const dH = parseFloat(document.getElementById('demarkHigh')?.value);
        const dL = parseFloat(document.getElementById('demarkLow')?.value);
        const dC = parseFloat(document.getElementById('demarkClose')?.value);
        if (dO && dH && dL && dC) {
            const dm = _calcDemark(dO, dH, dL, dC);
            const demarkLevels = [
                { price: dm.targetHigh, label: '디마크고', color: '#e64980' },
                { price: dm.targetLow,  label: '디마크저', color: '#7950f2' },
            ];
            demarkLevels.forEach(lv => {
                const ly = priceToY(lv.price);
                ctx.strokeStyle = lv.color;
                ctx.lineWidth = 2;
                ctx.setLineDash([8, 4]);
                ctx.beginPath();
                ctx.moveTo(chartLeft, ly);
                ctx.lineTo(chartRight, ly);
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.fillStyle = lv.color;
                ctx.font = 'bold 12px sans-serif';
                ctx.textAlign = 'left';
                ctx.fillText(`${lv.label} ${lv.price.toLocaleString()}`, chartRight + 5, ly + 4);
            });
        }
    }

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

// ========== 종목 마스터 Hover Tooltip ==========
const _stockTooltipCache = {};  // stock_code → {data, history, fetchedAt}
let _tooltipHideTimer = null;
let _tooltipActiveCode = null;

function _getOrCreateTooltip() {
    let el = document.getElementById('stockMasterTooltip');
    if (!el) {
        el = document.createElement('div');
        el.id = 'stockMasterTooltip';
        el.className = 'sm-tooltip';
        el.addEventListener('mouseenter', () => {
            clearTimeout(_tooltipHideTimer);
        });
        el.addEventListener('mouseleave', () => {
            hideStockTooltip();
        });
        document.body.appendChild(el);
    }
    return el;
}

function showStockTooltip(event, stockCode, stockName) {
    clearTimeout(_tooltipHideTimer);
    _tooltipActiveCode = stockCode;

    const tooltip = _getOrCreateTooltip();
    tooltip.innerHTML = `<div class="sm-tooltip-loading">⏳ 로딩 중...</div>`;
    _positionTooltip(tooltip, event);
    tooltip.style.display = 'block';

    const cached = _stockTooltipCache[stockCode];
    const now = Date.now();
    if (cached && (now - cached.fetchedAt) < 300000) {  // 5분 캐시
        _renderTooltip(tooltip, cached.data, cached.history, cached.financeStale);
        return;
    }

    fetch(`/api/stock-master/${stockCode}`, { credentials: 'same-origin' })
        .then(r => r.json())
        .then(res => {
            if (_tooltipActiveCode !== stockCode) return;
            if (res.success) {
                _stockTooltipCache[stockCode] = {
                    data: res.data || {},
                    history: res.history || [],
                    financeStale: res.finance_stale,
                    fetchedAt: Date.now(),
                };
                _renderTooltip(tooltip, res.data || {}, res.history || [], res.finance_stale);
            }
        })
        .catch(() => {
            if (_tooltipActiveCode === stockCode)
                tooltip.innerHTML = `<div class="sm-tooltip-loading">조회 실패</div>`;
        });
}

function _positionTooltip(tooltip, event) {
    const margin = 12;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    let x = event.clientX + margin;
    let y = event.clientY + margin;
    tooltip.style.left = x + 'px';
    tooltip.style.top = y + 'px';
    tooltip.style.right = 'auto';
    // 오른쪽 경계 보정은 렌더 후 처리
    requestAnimationFrame(() => {
        const rect = tooltip.getBoundingClientRect();
        if (rect.right > vw - 8) {
            tooltip.style.left = (event.clientX - rect.width - margin) + 'px';
        }
        if (rect.bottom > vh - 8) {
            tooltip.style.top = (event.clientY - rect.height - margin) + 'px';
        }
    });
}

function hideStockTooltip() {
    _tooltipHideTimer = setTimeout(() => {
        const el = document.getElementById('stockMasterTooltip');
        if (el) el.style.display = 'none';
        _tooltipActiveCode = null;
    }, 200);
}

function _fmt(v, unit = '', fallback = '-') {
    if (v == null || v === '') return fallback;
    return v + unit;
}

function _renderTooltip(tooltip, d, history, financeStale) {
    const themes = d.themes ? d.themes.split(',').map(t => t.trim()).filter(Boolean) : [];
    const themesHtml = themes.length
        ? themes.map(t => `<span class="sm-theme-tag">${t}</span>`).join('')
        : '<span style="color:#868e96">테마 미설정</span>';

    // 재무 지표
    const debtRatio = d.debt_ratio != null ? d.debt_ratio : null;
    const currentRatio = d.current_ratio != null ? d.current_ratio : null;
    const opIncome = d.op_income_bil != null ? d.op_income_bil : null;
    const opIncomePrev = d.op_income_prev_bil != null ? d.op_income_prev_bil : null;

    let opDeltaHtml = '';
    if (opIncome != null && opIncomePrev != null && opIncomePrev !== 0) {
        const delta = ((opIncome - opIncomePrev) / Math.abs(opIncomePrev) * 100).toFixed(1);
        const cls = delta >= 0 ? 'sm-fi-up' : 'sm-fi-down';
        opDeltaHtml = `<span class="${cls}">${delta >= 0 ? '+' : ''}${delta}%</span>`;
    }

    const debtClass = debtRatio == null ? '' : debtRatio > 200 ? 'sm-fi-warn' : debtRatio > 100 ? 'sm-fi-caution' : 'sm-fi-good';
    const crClass = currentRatio == null ? '' : currentRatio < 100 ? 'sm-fi-warn' : currentRatio < 150 ? 'sm-fi-caution' : 'sm-fi-good';

    const finStaleHtml = financeStale
        ? `<button class="sm-refresh-btn" onclick="refreshStockFinance('${d.stock_code}')">🔄 재무 갱신</button>`
        : '';

    // 시황 히스토리
    let histHtml = '';
    if (history && history.length > 0) {
        histHtml = history.slice(0, 10).map(h => {
            const tagCls = h.tag_type === 'ss_up' ? 'sm-tag-up' : h.tag_type === 'vi' ? 'sm-tag-vi' : 'sm-tag-ss';
            const tagLabel = h.tag_type === 'ss_up' ? 'SS⬆️' : h.tag_type === 'vi' ? 'VI' : 'SS';
            const shortText = (h.feed_text || '').substring(0, 80);
            return `<div class="sm-hist-row">
                <span class="sm-hist-date">${shortenYear(h.event_date)}</span>
                <span class="sm-tag ${tagCls}">${tagLabel}</span>
                ${h.theme ? `<span class="sm-hist-theme">${h.theme}</span>` : ''}
                <div class="sm-hist-text">${shortText}${h.feed_text && h.feed_text.length > 80 ? '…' : ''}</div>
            </div>`;
        }).join('');
    } else {
        histHtml = '<div style="color:#868e96;font-size:11px">히스토리 없음</div>';
    }

    const notesBtn = d.stock_code
        ? `<button class="sm-refresh-btn" style="background:#4dabf7" onclick="hideStockTooltip(); openStockNotesModal('${d.stock_code}','${(d.stock_name||'').replace(/'/g,"\\'")}')">📝 노트</button>`
        : '';

    tooltip.innerHTML = `
        <div class="sm-tooltip-header">
            <strong>${d.stock_name || d.stock_code}</strong>
            <span style="color:#868e96;font-size:11px;margin-left:6px">${d.stock_code || ''}</span>
            ${notesBtn}
            ${finStaleHtml}
        </div>
        <div class="sm-themes">${themesHtml}</div>
        <div class="sm-finance-grid">
            <div class="sm-fi-item">
                <span class="sm-fi-label">부채비율</span>
                <span class="sm-fi-value ${debtClass}">${debtRatio != null ? debtRatio + '%' : '-'}</span>
            </div>
            <div class="sm-fi-item">
                <span class="sm-fi-label">유동비율</span>
                <span class="sm-fi-value ${crClass}">${currentRatio != null ? currentRatio + '%' : '-'}</span>
            </div>
            <div class="sm-fi-item">
                <span class="sm-fi-label">영업이익</span>
                <span class="sm-fi-value">${opIncome != null ? opIncome + '억' : '-'} ${opDeltaHtml}</span>
            </div>
            <div class="sm-fi-item">
                <span class="sm-fi-label">시가총액</span>
                <span class="sm-fi-value">${d.market_cap_bil != null ? Math.round(d.market_cap_bil / 100) + '조' : '-'}</span>
            </div>
            <div class="sm-fi-item">
                <span class="sm-fi-label">PER</span>
                <span class="sm-fi-value">${d.per != null ? d.per : '-'}</span>
            </div>
            <div class="sm-fi-item">
                <span class="sm-fi-label">ROE</span>
                <span class="sm-fi-value">${d.roe != null ? d.roe + '%' : '-'}</span>
            </div>
        </div>
        <div class="sm-hist-title">📋 시황 히스토리</div>
        <div class="sm-hist-list">${histHtml}</div>
    `;
}

async function refreshStockFinance(stockCode) {
    const tooltip = document.getElementById('stockMasterTooltip');
    if (tooltip) tooltip.innerHTML = `<div class="sm-tooltip-loading">⏳ 재무 조회 중...</div>`;
    try {
        const res = await fetch(`/api/stock-master/${stockCode}/refresh-finance`, {
            method: 'POST',
            credentials: 'same-origin',
        });
        const r = await res.json();
        if (r.success) {
            delete _stockTooltipCache[stockCode];
            // 업데이트된 데이터 다시 fetch
            const r2 = await fetch(`/api/stock-master/${stockCode}`, { credentials: 'same-origin' });
            const res2 = await r2.json();
            if (res2.success) {
                _stockTooltipCache[stockCode] = {
                    data: res2.data || {},
                    history: res2.history || [],
                    financeStale: false,
                    fetchedAt: Date.now(),
                };
                const tt = document.getElementById('stockMasterTooltip');
                if (tt && tt.style.display !== 'none') {
                    _renderTooltip(tt, res2.data || {}, res2.history || [], false);
                }
            }
        }
    } catch (e) {
        showToast('재무 갱신 실패', 'error');
    }
}

// ─── 종목 노트 모달 (1종목 1노트 단일 텍스트) ────────────────────────────

let _stockNotesCurrentCode = null;
let _stockNotesCurrentName = null;

async function openStockNotesModal(stockCode, stockName) {
    _stockNotesCurrentCode = stockCode;
    _stockNotesCurrentName = stockName;
    document.getElementById('stockNotesModalTitle').textContent = `${stockName} (${stockCode}) 노트`;
    // 오늘 날짜 기본값 (M/D 형식 — 2026→'26 변환)
    const today = new Date();
    const dateStr = _fmtNoteDate(today);
    document.getElementById('stockNotePrependDate').value = today.toISOString().slice(0, 10);
    document.getElementById('stockNotePrependContent').value = '';
    document.getElementById('stockNotesModal').style.display = 'flex';
    await _reloadStockNote();
    setTimeout(() => document.getElementById('stockNotePrependContent').focus(), 100);
}

function closeStockNotesModal() {
    document.getElementById('stockNotesModal').style.display = 'none';
    _stockNotesCurrentCode = null;
}

// M/D 포맷 (연도 앞 2자리 '26 형식)
function _fmtNoteDate(dateObj) {
    const yy = String(dateObj.getFullYear()).slice(2);
    return `'${yy}/${dateObj.getMonth()+1}/${dateObj.getDate()}`;
}

async function _reloadStockNote() {
    const code = _stockNotesCurrentCode;
    if (!code) return;
    const res = await fetch(`/api/stock-master/${code}/note`, { credentials: 'same-origin' }).then(r => r.json()).catch(() => ({}));
    document.getElementById('stockNotesFullText').value = res.note || '';
}

async function prependStockNote() {
    const code = _stockNotesCurrentCode;
    const rawDate = document.getElementById('stockNotePrependDate').value; // YYYY-MM-DD
    const content = document.getElementById('stockNotePrependContent').value.trim();
    if (!content) return;
    // 날짜 표시 포맷: 'YY/M/D
    let dateStr = '';
    if (rawDate) {
        const d = new Date(rawDate + 'T00:00:00');
        dateStr = _fmtNoteDate(d);
    }
    const res = await fetch(`/api/stock-master/${code}/note/prepend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ date_str: dateStr, content }),
    }).then(r => r.json()).catch(() => ({}));
    if (res.success) {
        document.getElementById('stockNotesFullText').value = res.note || '';
        document.getElementById('stockNotePrependContent').value = '';
        showToast('추가됨', 'success');
    }
}

async function saveFullStockNote() {
    const code = _stockNotesCurrentCode;
    const note = document.getElementById('stockNotesFullText').value;
    const res = await fetch(`/api/stock-master/${code}/note`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ note }),
    }).then(r => r.json()).catch(() => ({}));
    if (res.success) showToast('저장됨', 'success');
}

// ─── 종목 마스터 관리 모달 ─────────────────────────────────────────────────

let _smEditCode = null;

let _smSearchTimer = null;
function smSearch(q) {
    clearTimeout(_smSearchTimer);
    _smSearchTimer = setTimeout(() => _doSmSearch(q), 300);
}

async function _doSmSearch(q) {
    if (!q || q.length < 1) { document.getElementById('smSearchResults').innerHTML = ''; return; }
    const res = await fetch(`/api/stock-master/search?q=${encodeURIComponent(q)}`, { credentials: 'same-origin' }).then(r => r.json()).catch(() => ({}));
    const items = res.data || [];
    const container = document.getElementById('smSearchResults');
    if (!items.length) {
        container.innerHTML = '<div style="color:#adb5bd; font-size:13px; padding:8px;">검색 결과 없음</div>';
        return;
    }
    container.innerHTML = items.map(item => {
        const notePreview = shortenYear((item.note || '').slice(0, 60).replace(/\n/g, ' '));
        const themes = (item.themes || '').split(',').filter(Boolean).map(t => `<span style="background:#e7f5ff;color:#1971c2;padding:1px 6px;border-radius:10px;font-size:11px;">${t.trim()}</span>`).join(' ');
        return `<div class="sm-result-row" onclick="smOpenEdit('${item.stock_code}', '${(item.stock_name||'').replace(/'/g,"\\'")}', '${(item.themes||'').replace(/'/g,"\\'")}', \`${(item.note||'').replace(/`/g,'\\`')}\`)">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:600;">${item.stock_name || '-'} <span style="color:#868e96; font-size:11px;">${item.stock_code}</span></span>
                <span style="font-size:10px; color:#adb5bd;">${(item.updated_at||'').slice(0,10)}</span>
            </div>
            ${themes ? `<div style="margin-top:4px;">${themes}</div>` : ''}
            ${notePreview ? `<div style="font-size:12px; color:#868e96; margin-top:3px;">${notePreview}${item.note && item.note.length > 60 ? '…' : ''}</div>` : ''}
        </div>`;
    }).join('');
}

function smOpenEdit(code, name, themes, note) {
    _smEditCode = code;
    document.getElementById('smEditTitle').textContent = `✏️ ${name} (${code})`;
    document.getElementById('smEditThemes').value = themes || '';
    document.getElementById('smEditNote').value = note || '';
    document.getElementById('smSaveStatus').textContent = '';
    document.getElementById('smEditPanel').style.display = 'block';
    document.getElementById('smEditPanel').scrollIntoView({ behavior: 'smooth' });
}

async function smSaveEdit() {
    if (!_smEditCode) return;
    const themes = document.getElementById('smEditThemes').value.trim();
    const note = document.getElementById('smEditNote').value;
    const status = document.getElementById('smSaveStatus');
    const res = await fetch(`/api/stock-master/${_smEditCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ themes, note }),
    }).then(r => r.json()).catch(() => ({}));
    if (res.success) {
        status.textContent = '저장됨 ✓';
        showToast('종목 마스터 저장됨', 'success');
        // 검색 결과 갱신
        _doSmSearch(document.getElementById('smSearchInput').value);
        setTimeout(() => { status.textContent = ''; }, 3000);
    } else {
        status.textContent = '실패';
    }
}

async function smSyncWatchlist() {
    const res = await fetch('/api/stock-master/sync-watchlist', {
        method: 'POST',
        credentials: 'same-origin',
    }).then(r => r.json()).catch(() => ({}));
    if (res.success) showToast(`감시종목 ${res.synced}개 동기화됨`, 'success');
}

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

// ========== Mode2 편입 모달 ==========
let transferStockData = null;

function showMode2TransferModal(code, name, quantity, buyPrice) {
    const modal = document.getElementById('mode2TransferModal');
    const budget = quantity * buyPrice;

    // 데이터 저장
    transferStockData = { code, name, quantity, buyPrice, budget };

    // 자동 입력 값 표시
    document.getElementById('transferStockCode').textContent = code;
    document.getElementById('transferStockName').textContent = name;
    document.getElementById('transferQuantity').textContent = formatNumber(quantity);
    document.getElementById('transferBuyPrice').textContent = formatNumber(buyPrice);
    document.getElementById('transferBudget').textContent = formatNumber(budget);

    // 입력 필드 초기화
    document.getElementById('transferResistance1').value = '';
    document.getElementById('transferSupport1').value = '';

    modal.style.display = 'block';
}

function closeMode2TransferModal() {
    const modal = document.getElementById('mode2TransferModal');
    modal.style.display = 'none';
    transferStockData = null;
}

async function handleMode2TransferSubmit(e) {
    e.preventDefault();

    if (!transferStockData) {
        showToast('종목 데이터를 찾을 수 없습니다', 'error');
        return;
    }

    const resistance1 = parseInt(document.getElementById('transferResistance1').value) || 0;
    const support1 = parseInt(document.getElementById('transferSupport1').value) || 0;

    if (resistance1 <= 0 || support1 <= 0) {
        showToast('1차 저항/지지 가격을 입력해주세요', 'error');
        return;
    }

    if (support1 >= transferStockData.buyPrice) {
        showToast('1차 지지는 매입가보다 낮아야 합니다', 'error');
        return;
    }

    if (resistance1 <= transferStockData.buyPrice) {
        showToast('1차 저항은 매입가보다 높아야 합니다', 'error');
        return;
    }

    const data = {
        code: transferStockData.code,
        name: transferStockData.name,
        buy_target_price: transferStockData.buyPrice,
        budget: transferStockData.budget,
        quantity: transferStockData.quantity,
        polling_interval: 30, // 기본 30초
        notify_only: false, // 자동매매 모드
        resistance_1_price: resistance1,
        resistance_1_profit_pct: 100, // 1차 저항에서 100% 익절
        resistance_2_price: 0,
        resistance_2_profit_pct: 0,
        support_1_price: support1,
        support_1_loss_pct: 100, // 1차 지지에서 100% 손절
        support_2_price: 0,
        support_2_loss_pct: 0,
        status: 'waiting_sell', // 이미 매수 완료 상태
        bought_price: transferStockData.buyPrice,
        bought_quantity: transferStockData.quantity,
        bought_at: new Date().toISOString()
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
            showToast('✅ Mode2 감시 종목으로 편입되었습니다', 'success');
            closeMode2TransferModal();
            loadMode2List();
            loadWatchlist();
        } else {
            showToast(result.error || '편입 실패', 'error');
        }
    } catch (error) {
        showToast('요청 실패: ' + error.message, 'error');
    }
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

// Mode2 편입 폼 submit 이벤트 리스너
document.addEventListener('DOMContentLoaded', () => {
    const mode2TransferForm = document.getElementById('mode2TransferForm');
    if (mode2TransferForm) {
        mode2TransferForm.addEventListener('submit', handleMode2TransferSubmit);
    }
});

// 모달 외부 클릭 시 닫기
window.addEventListener('click', (event) => {
    const noteModal = document.getElementById('noteModal');
    if (event.target === noteModal) {
        closeNoteModal();
    }

    const transferModal = document.getElementById('mode2TransferModal');
    if (event.target === transferModal) {
        closeMode2TransferModal();
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
    document.querySelector('select[name="resistance_2_profit_pct"]').value = watcher.resistance_2_profit_pct || 50;
    document.querySelector('input[name="resistance_1_price"]').value = watcher.resistance_1_price || '';
    document.querySelector('select[name="resistance_1_profit_pct"]').value = watcher.resistance_1_profit_pct || 50;
    document.querySelector('input[name="support_1_price"]').value = watcher.support_1_price || '';
    const s1mode = watcher.support_1_mode || '손절';
    document.querySelector('select[name="support_1_mode"]').value = s1mode;
    toggleSupport1Mode(s1mode);
    document.querySelector('select[name="support_1_loss_pct"]').value = watcher.support_1_loss_pct || 50;
    document.getElementById('support1AddBudget').value = watcher.support_1_add_budget ? Math.round(watcher.support_1_add_budget / 10000) : '';
    document.querySelector('input[name="support_2_price"]').value = watcher.support_2_price || '';
    document.querySelector('select[name="support_2_loss_pct"]').value = watcher.support_2_loss_pct || 50;
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

            // 전일 OHLC → 디마크 자동계산
            const ch = chartResult.data.chart;
            if (ch) {
                const o = parseFloat(ch.yesterday_open), h = parseFloat(ch.yesterday_high),
                      l = parseFloat(ch.yesterday_low),  c = parseFloat(ch.yesterday_close);
                if (o && h && l && c) {
                    document.getElementById('demarkOpen').value  = o;
                    document.getElementById('demarkHigh').value  = h;
                    document.getElementById('demarkLow').value   = l;
                    document.getElementById('demarkClose').value = c;
                    calcAndFillDemark();
                }
            }

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
    const isBudget = field === 'budget';
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
        // Budget 필드는 만원 단위로 표시
        input.value = isBudget ? (parseInt(originalValue) / 10000 || 0) : originalValue;
        input.style.width = '100%';
        if (isBudget) {
            input.placeholder = '만원 단위 (예: 30 = 30만원)';
        }
    }

    input.style.padding = '4px';
    input.style.border = '2px solid #228be6';
    input.style.borderRadius = '4px';
    input.style.fontSize = '13px';

    // 저장 함수
    const saveEdit = async () => {
        const newValue = input.value.trim();

        // Budget 필드는 만원 단위로 입력받아 원 단위로 변환
        const actualValue = isBudget ? (parseInt(newValue) * 10000 || 0) : (parseInt(newValue) || 0);

        // 변경사항 체크
        const compareValue = isBudget ? (parseInt(originalValue) || 0) : originalValue;
        if (actualValue == compareValue && !isNote) {
            cell.innerHTML = isNote ? truncateText(originalValue, 20) : formatNumber(originalValue);
            if (isNote) cell.setAttribute('title', originalValue);
            return;
        }

        if (isNote && newValue === originalValue) {
            cell.innerHTML = truncateText(originalValue, 20);
            cell.setAttribute('title', originalValue);
            return;
        }

        // API 호출
        try {
            const data = {};
            data[field] = isNote ? newValue : actualValue;

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
            support_1_mode: '손절',
            support_1_loss_pct: 0,
            support_1_add_budget: 0,
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

// ============================================================
// 📊 시황체크 페이지
// ============================================================

// ─── 시황체크 상태 ─────────────────────────────────────────
let _kwTab = 'news'; // 현재 키워드 탭 ('news' | 'hotstock')
let _kwDataNews = null;
let _kwDataHotstock = null;
// 테이블별 데이터 캐시 (삭제 기능용)
const _tableData = { newsAll: [], hotstockAll: [], newsFiltered: [], hotstockFiltered: [] };
// 관심종목 캐시
let _watchlistData = [];

// ─── 시황체크 진입점 ───────────────────────────────────────
async function loadSiwhang() {
    await Promise.all([loadWatchlist_siwhang(), loadHotstockParsed(), loadSiwhangResults(), loadNewsFilter(), loadListeningStatus()]);
}

// ─── 관심종목 관리 ─────────────────────────────────────────
async function loadWatchlist_siwhang() {
    try {
        const r = await (await fetch('/api/watchlist', { credentials: 'same-origin' })).json();
        _watchlistData = r.success ? r.data : [];
        const countEl = document.getElementById('watchlistCount');
        if (countEl) countEl.textContent = `(${_watchlistData.length}개)`;
        _renderWatchlistTags();
    } catch (e) { console.error('watchlist load error', e); }
}

function _renderWatchlistTags() {
    const container = document.getElementById('watchlistTags');
    if (!container) return;
    if (!_watchlistData.length) {
        container.innerHTML = '<span style="color:#868e96;font-size:13px;">관심종목이 없습니다. 종목코드를 추가하세요.</span>';
        return;
    }
    container.innerHTML = _watchlistData.map(item => {
        const badge = item.origin === 'mode2' ? ' <span style="background:#339af0;color:#fff;font-size:10px;padding:1px 4px;border-radius:3px;vertical-align:middle;">M2</span>'
                    : item.origin === 'both'  ? ' <span style="background:#37b24d;color:#fff;font-size:10px;padding:1px 4px;border-radius:3px;vertical-align:middle;">M2</span>'
                    : '';
        const deleteBtn = (item.origin === 'manual' || item.origin === 'both')
            ? `<span onclick="deleteWatchlistItem('${item.code}')" style="cursor:pointer;color:#c92a2a;margin-left:4px;font-size:12px;">×</span>`
            : '';
        return `<span style="display:inline-flex;align-items:center;background:#f1f3f5;border:1px solid #dee2e6;border-radius:16px;padding:4px 10px;font-size:12px;">
            ${item.name}(${item.code})${badge}${deleteBtn}
        </span>`;
    }).join('');
}

async function addWatchlistItems() {
    const input = document.getElementById('watchlistInput');
    const raw = input?.value?.trim();
    if (!raw) return;
    try {
        const r = await (await fetch('/api/watchlist', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codes: raw }),
        })).json();
        if (r.success) {
            input.value = '';
            showToast(`✓ ${r.added}개 추가됨`, 'success');
            await loadWatchlist_siwhang();
        } else { showToast(r.error || '추가 실패', 'error'); }
    } catch (e) { showToast('요청 실패', 'error'); }
}

async function deleteWatchlistItem(code) {
    try {
        const r = await (await fetch(`/api/watchlist/${code}`, {
            method: 'DELETE', credentials: 'same-origin',
        })).json();
        if (r.success) { showToast('✓ 삭제됨', 'success'); await loadWatchlist_siwhang(); }
        else { showToast(r.error || '삭제 실패', 'error'); }
    } catch (e) { showToast('요청 실패', 'error'); }
}

function toggleWatchlistEdit() {
    const tagsEl = document.getElementById('watchlistTags');
    const editEl = document.getElementById('watchlistEditView');
    const areaEl = document.getElementById('watchlistEditArea');
    if (!tagsEl || !editEl || !areaEl) return;
    const isEditing = editEl.style.display !== 'none';
    if (isEditing) {
        cancelWatchlistEdit();
    } else {
        // 수동 추가 종목만 textarea에 채움
        const manualItems = _watchlistData.filter(i => i.origin === 'manual' || i.origin === 'both');
        areaEl.value = manualItems.map(i => i.code).join('\n');
        tagsEl.style.display = 'none';
        editEl.style.display = '';
    }
}

async function saveWatchlistEdit() {
    const areaEl = document.getElementById('watchlistEditArea');
    const raw = areaEl?.value || '';
    const codes = raw.split(/[\n,]/).map(s => s.trim()).filter(Boolean);
    try {
        const r = await (await fetch('/api/watchlist/bulk', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codes }),
        })).json();
        if (r.success) {
            showToast('✓ 관심종목 저장됨', 'success');
            document.getElementById('watchlistEditView').style.display = 'none';
            document.getElementById('watchlistTags').style.display = '';
            await loadWatchlist_siwhang();
        } else { showToast(r.error || '저장 실패', 'error'); }
    } catch (e) { showToast('요청 실패', 'error'); }
}

function cancelWatchlistEdit() {
    document.getElementById('watchlistEditView').style.display = 'none';
    document.getElementById('watchlistTags').style.display = '';
}

// ─── 급등주 파싱 테이블 ────────────────────────────────────
// 파싱 데이터 캐시 (message_id 기반 삭제용)
const _parsedData = { ssUp: [], vi: [], ss: [] };

async function loadHotstockParsed() {
    const date = _newsFilterDate();
    const qs = date ? `?date=${date}` : '';
    try {
        const r = await (await fetch(`/api/hotstock/parsed${qs}`, { credentials: 'same-origin' })).json();
        if (!r.success) return;
        _parsedData.ssUp = r.data.filter(d => d.tag_type === 'ss_up');
        _parsedData.vi   = r.data.filter(d => d.tag_type === 'vi');
        _parsedData.ss   = r.data.filter(d => d.tag_type === 'ss');
        const upCountEl = document.getElementById('ssUpCount');
        if (upCountEl) upCountEl.textContent = `(${_parsedData.ssUp.length}건)`;
        const viCountEl = document.getElementById('viCount');
        if (viCountEl) viCountEl.textContent = `(${_parsedData.vi.length}건)`;
        const ssCountEl = document.getElementById('ssAllCount');
        if (ssCountEl) ssCountEl.textContent = `(${_parsedData.ss.length}건)`;
        _renderParsedTable('ssUpBody', _parsedData.ssUp, 'ssUp');
        _renderParsedTable('viBody', _parsedData.vi, 'vi');
        _renderParsedTable('ssAllBody', _parsedData.ss, 'ss');
    } catch (e) { console.error('hotstock parsed error', e); }
}

function toggleParsedCheckboxes(tableKey, masterCb) {
    document.querySelectorAll(`.cb-parsed-${tableKey}`).forEach(cb => { cb.checked = masterCb.checked; });
}

async function deleteParsedSelected(tableKey) {
    const ids = Array.from(document.querySelectorAll(`.cb-parsed-${tableKey}:checked`)).map(cb => parseInt(cb.dataset.id));
    if (ids.length === 0) { showToast('삭제할 항목을 선택하세요', 'error'); return; }
    if (!confirm(`${ids.length}건을 삭제하시겠습니까?`)) return;
    try {
        const r = await (await fetch('/api/messages/delete', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids }),
        })).json();
        if (r.success) {
            showToast(`✓ ${r.deleted}건 삭제됨`, 'success');
            await loadHotstockParsed();
        } else { showToast(r.error || '삭제 실패', 'error'); }
    } catch (e) { showToast('요청 실패', 'error'); }
}

function _renderParsedTable(tbodyId, data, tableKey) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;
    if (!data.length) {
        tbody.innerHTML = `<tr><td colspan="7" style="padding:16px;text-align:center;color:#868e96;font-size:13px;">데이터 없음</td></tr>`;
        return;
    }
    tbody.innerHTML = data.map(m => {
        const matchHtml = m.watchlist_match && m.watchlist_match.length
            ? m.watchlist_match.map(n => `<span style="background:#fff3bf;border:1px solid #ffd43b;border-radius:10px;padding:1px 6px;font-size:11px;">🔔${n}</span>`).join(' ')
            : '<span style="color:#868e96;">-</span>';
        const related = (m.related_stocks || []).join(', ') || '-';
        const isNeg = m.change && (m.change.startsWith('-') || m.change.startsWith('▼'));
        const priceColor = isNeg ? '#1971c2' : '#c92a2a';
        const price = m.price ? `<span style="color:${priceColor}">${m.price}</span><br><span style="font-size:11px;color:#868e96;">${m.change || ''}</span>` : '-';
        const rawEsc = (m.raw_text || '').replace(/\\/g, '\\\\').replace(/`/g, '\\`');
        const searchVal = [m.stock_name, m.theme, related, m.raw_text].join(' ').toLowerCase().replace(/"/g, '&quot;');
        return `<tr style="border-bottom:1px solid #f1f3f5;cursor:pointer;" data-search="${searchVal}" onclick="showHotstockCopyModal(\`${rawEsc}\`)">
            <td style="padding:5px 4px;width:24px;" onclick="event.stopPropagation()"><input type="checkbox" class="cb-parsed-${tableKey}" data-id="${m.message_id}"></td>
            <td style="padding:5px 8px;font-size:13px;font-weight:500;">${m.stock_name || '-'}</td>
            <td style="padding:5px 8px;font-size:12px;text-align:right;">${price}</td>
            <td style="padding:5px 8px;font-size:12px;">${m.theme || '-'}</td>
            <td style="padding:5px 8px;font-size:11px;color:#495057;max-width:200px;">${related}</td>
            <td style="padding:5px 8px;text-align:center;">${matchHtml}</td>
            <td style="padding:5px 6px;font-size:11px;color:#868e96;text-align:right;white-space:nowrap;">${_fmtDatetime(m.received_at)}</td>
        </tr>`;
    }).join('');
}

function showHotstockCopyModal(rawText) {
    const existing = document.getElementById('hotstockCopyModal');
    if (existing) existing.remove();
    const modal = document.createElement('div');
    modal.id = 'hotstockCopyModal';
    modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    modal.innerHTML = `
        <div style="background:#fff;border-radius:12px;padding:20px;max-width:560px;width:90%;max-height:80vh;display:flex;flex-direction:column;gap:12px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <strong style="font-size:14px;">📋 원문 복사</strong>
                <button onclick="document.getElementById('hotstockCopyModal').remove()" style="border:none;background:none;font-size:18px;cursor:pointer;color:#868e96;">✕</button>
            </div>
            <textarea id="hotstockCopyText" readonly style="flex:1;min-height:200px;resize:vertical;font-size:12px;line-height:1.6;border:1px solid #dee2e6;border-radius:6px;padding:10px;font-family:monospace;white-space:pre;">${rawText.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</textarea>
            <button onclick="navigator.clipboard.writeText(document.getElementById('hotstockCopyText').value).then(()=>{showToast('✓ 복사됨','success');document.getElementById('hotstockCopyModal').remove();})" style="background:#339af0;color:#fff;border:none;border-radius:6px;padding:8px 20px;font-size:13px;cursor:pointer;font-weight:600;">📋 클립보드 복사</button>
        </div>`;
    modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
    document.body.appendChild(modal);
}

// ─── AI 분석 결과 ─────────────────────────────────────────
async function loadSiwhangResults() {
    const date = _newsFilterDate();
    const qs = date ? `?date=${date}` : '';
    try {
        const r = await (await fetch(`/api/siwhang/results${qs}`, { credentials: 'same-origin' })).json();
        const data = r.success ? r.data : [];
        const countEl = document.getElementById('siwhangResultCount');
        if (countEl) countEl.textContent = `(${data.length}건)`;
        const tbody = document.getElementById('siwhangResultBody');
        if (!tbody) return;
        if (!data.length) {
            tbody.innerHTML = `<tr><td colspan="8" style="padding:16px;text-align:center;color:#868e96;font-size:13px;">/siwhang 스킬 실행 후 결과가 표시됩니다</td></tr>`;
            return;
        }
        const tagLabel = { ss_up: '🚀상한가', vi: '⚡VI', ss: '📈급등' };
        tbody.innerHTML = data.map(m => {
            const related = Array.isArray(m.related_stocks) ? m.related_stocks.join(', ') : (m.related_stocks || '-');
            const matchHtml = m.watchlist_match && m.watchlist_match.length
                ? m.watchlist_match.map(n => `<span style="background:#fff3bf;border:1px solid #ffd43b;border-radius:10px;padding:1px 6px;font-size:11px;">🔔${n}</span>`).join(' ')
                : '-';
            return `<tr style="border-bottom:1px solid #f1f3f5;">
                <td style="padding:5px 6px;font-size:11px;color:#868e96;white-space:nowrap;">${_fmtDatetime(m.run_at)}</td>
                <td style="padding:5px 6px;text-align:center;">${tagLabel[m.tag_type] || m.tag_type}</td>
                <td style="padding:5px 8px;font-size:13px;font-weight:500;white-space:nowrap;">${m.stock_name || '-'}</td>
                <td style="padding:5px 8px;font-size:12px;white-space:nowrap;">${m.theme || '-'}</td>
                <td style="padding:5px 8px;font-size:11px;color:#495057;max-width:160px;">${related}</td>
                <td style="padding:5px 8px;text-align:center;">${m.has_news_match ? '✅' : '❌'}</td>
                <td style="padding:5px 8px;">${matchHtml}</td>
                <td style="padding:5px 8px;font-size:11px;color:#495057;max-width:200px;" title="${m.analysis_text || ''}">${(m.analysis_text || '').slice(0, 60)}${(m.analysis_text || '').length > 60 ? '…' : ''}</td>
            </tr>`;
        }).join('');
    } catch (e) { console.error('siwhang results error', e); }
}

function _newsFilterDate() {
    const d = document.getElementById('newsfilterDate');
    return d && d.value ? d.value : '';
}

function _fmtDatetime(dtStr) {
    if (!dtStr) return '-';
    const d = new Date(dtStr.replace(' ', 'T') + (dtStr.includes('T') ? '' : 'Z'));
    if (isNaN(d)) return dtStr;
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const hh = String(d.getHours()).padStart(2, '0');
    const mi = String(d.getMinutes()).padStart(2, '0');
    return `${mm}/${dd} ${hh}:${mi}`;
}

function filterTable(inputEl, tbodyId) {
    const kw = (inputEl.value || '').toLowerCase().trim();
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;
    tbody.querySelectorAll('tr').forEach(row => {
        const text = (row.dataset.search || row.textContent).toLowerCase();
        row.style.display = (!kw || text.includes(kw)) ? '' : 'none';
    });
}

function filterSiwhangTables() {
    // no-op: 각 카드별 검색으로 교체됨
}

async function loadNewsFilter() {
    const date = _newsFilterDate();
    const qs = date ? `?date=${date}` : '';
    await Promise.all([
        _loadNewsAll(qs), _loadHotstockAll(qs),
        _loadNewsFiltered(qs), _loadHotstockFiltered(qs),
        loadKeywords(), loadThemes(), loadSavedNews(),
    ]);
}

async function _loadNewsAll(qs) {
    try {
        const r = await (await fetch(`/api/news/today${qs}`, { credentials: 'same-origin' })).json();
        const data = r.success ? r.data : [];
        _tableData.newsAll = data;
        document.getElementById('newsAllCount').textContent = `(${data.length}건)`;
        _renderMsgTable('newsAllBody', data, 'newsAll');
    } catch (e) {}
}

async function _loadHotstockAll(qs) {
    try {
        const r = await (await fetch(`/api/hotstock/today${qs}`, { credentials: 'same-origin' })).json();
        const data = r.success ? r.data : [];
        _tableData.hotstockAll = data;
        document.getElementById('hotstockAllCount').textContent = `(${data.length}건)`;
        _renderMsgTable('hotstockAllBody', data, 'hotstockAll');
    } catch (e) {}
}

async function _loadNewsFiltered(qs) {
    try {
        const r = await (await fetch(`/api/news/filtered${qs}`, { credentials: 'same-origin' })).json();
        const data = r.success ? r.data : [];
        _tableData.newsFiltered = data;
        document.getElementById('newsFilteredCount').textContent = `(${data.length}건)`;
        _renderMsgTable('newsFilteredBody', data, 'newsFiltered');
    } catch (e) {}
}

async function _loadHotstockFiltered(qs) {
    try {
        const r = await (await fetch(`/api/hotstock/filtered${qs}`, { credentials: 'same-origin' })).json();
        const data = r.success ? r.data : [];
        _tableData.hotstockFiltered = data;
        document.getElementById('hotstockFilteredCount').textContent = `(${data.length}건)`;
        _renderMsgTable('hotstockFilteredBody', data, 'hotstockFiltered');
    } catch (e) {}
}

function _renderMsgTable(tbodyId, data, tableKey) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;
    if (!data || data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" style="padding:16px;text-align:center;color:#868e96;font-size:13px;">데이터 없음</td></tr>`;
        return;
    }
    tbody.innerHTML = data.map(m => {
        const dt = _fmtDatetime(m.received_at);
        const text = (m.text || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        const preview = text.length > 90 ? text.slice(0, 90) + '…' : text;
        const searchVal = (m.text || '').toLowerCase().replace(/"/g, '&quot;');
        return `<tr style="border-bottom:1px solid #f1f3f5;" data-search="${searchVal}">
            <td style="padding:4px 4px;width:24px;"><input type="checkbox" class="msg-cb cb-${tableKey}" data-id="${m.id}" onchange="_onMsgCbChange('${tableKey}')"></td>
            <td style="padding:4px 8px;font-size:12px;line-height:1.4;" title="${text}">${preview}</td>
            <td style="padding:4px 6px;font-size:11px;color:#868e96;text-align:right;white-space:nowrap;">${dt}</td>
        </tr>`;
    }).join('');
}

function toggleSection(sectionId, chevronId) {
    const el = document.getElementById(sectionId);
    const ch = document.getElementById(chevronId);
    if (!el) return;
    const open = el.style.display === 'none';
    el.style.display = open ? '' : 'none';
    if (ch) ch.textContent = open ? '▼' : '▶';
}

function toggleTableCheckboxes(tableKey, masterCb) {
    document.querySelectorAll(`.cb-${tableKey}`).forEach(cb => { cb.checked = masterCb.checked; });
    _onMsgCbChange(tableKey);
}

function _onMsgCbChange(tableKey) {
    if (tableKey === 'newsFiltered') {
        const selected = document.querySelectorAll('.cb-newsFiltered:checked').length;
        const btn = document.getElementById('newsInsightSelectedBtn');
        if (btn) btn.style.display = selected > 0 ? 'inline-block' : 'none';
    }
}

function runNewsInsightSelected() {
    const ids = Array.from(document.querySelectorAll('.cb-newsFiltered:checked')).map(cb => cb.dataset.id);
    if (ids.length === 0) { showToast('선택된 뉴스가 없습니다', 'error'); return; }
    const idStr = ids.join(',');
    navigator.clipboard?.writeText(idStr).catch(() => {});
    showToast(`${ids.length}건 선택됨 (ID: ${idStr}) - /news-insight-selected 스킬에서 사용`, 'info');
}

async function deleteSelectedMessages(tableKey) {
    const ids = Array.from(document.querySelectorAll(`.cb-${tableKey}:checked`)).map(cb => parseInt(cb.dataset.id));
    if (ids.length === 0) { showToast('삭제할 항목을 선택하세요', 'error'); return; }
    if (!confirm(`${ids.length}건을 삭제하시겠습니까?`)) return;
    try {
        const r = await (await fetch('/api/messages/delete', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids }),
        })).json();
        if (r.success) {
            showToast(`✓ ${r.deleted}건 삭제됨`, 'success');
            const qs = _newsFilterDate() ? `?date=${_newsFilterDate()}` : '';
            if (tableKey === 'newsAll') await _loadNewsAll(qs);
            else if (tableKey === 'hotstockAll') await _loadHotstockAll(qs);
            else if (tableKey === 'newsFiltered') await _loadNewsFiltered(qs);
            else if (tableKey === 'hotstockFiltered') await _loadHotstockFiltered(qs);
        } else { showToast(r.error || '삭제 실패', 'error'); }
    } catch (e) { showToast('요청 실패', 'error'); }
}

async function loadListeningStatus() {
    try {
        const r = await (await fetch('/api/listening/status', { credentials: 'same-origin' })).json();
        updateListeningBtn(r.paused);
    } catch (e) {
        const btn = document.getElementById('listeningToggleBtn');
        if (btn) btn.textContent = '🔊 리스닝 상태';
    }
}

function updateListeningBtn(paused) {
    const btn = document.getElementById('listeningToggleBtn');
    if (!btn) return;
    if (paused) {
        btn.textContent = '🔴 Stop-Listening 중 (클릭 시 재개)';
        btn.className = 'btn btn-danger';
    } else {
        btn.textContent = '🔊 Stop-Listening';
        btn.className = 'btn btn-secondary';
    }
}

async function toggleListening() {
    try {
        const statusR = await (await fetch('/api/listening/status', { credentials: 'same-origin' })).json();
        const isPaused = statusR.paused;
        const endpoint = isPaused ? '/api/listening/resume' : '/api/listening/pause';
        const r = await (await fetch(endpoint, { method: 'POST', credentials: 'same-origin' })).json();
        if (r.success) {
            updateListeningBtn(r.paused);
            showToast(r.paused ? '🔇 신규 뉴스 수신 정지됨' : '🔊 뉴스 수신 재개됨', r.paused ? 'error' : 'success');
        }
    } catch (e) { showToast('상태 변경 실패', 'error'); }
}

async function cleanupOldMessages(sourceType) {
    const label = sourceType === 'hot_stock' ? '급등주' : '뉴스';
    if (!confirm(`오늘 날짜 이전 ${label} 메시지를 모두 삭제하시겠습니까?\n(스크래핑된 뉴스는 보존됩니다)`)) return;
    try {
        const r = await (await fetch('/api/messages/cleanup', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source_type: sourceType }),
        })).json();
        if (r.success) {
            showToast(`✓ ${r.message}`, 'success');
            loadNewsFilter();
        } else { showToast(r.error || '실패', 'error'); }
    } catch (e) { showToast('요청 실패', 'error'); }
}

async function scrapeSelectedNews() {
    const ids = Array.from(document.querySelectorAll('.cb-newsFiltered:checked')).map(cb => parseInt(cb.dataset.id));
    if (ids.length === 0) { showToast('스크래핑할 뉴스를 선택하세요', 'error'); return; }
    try {
        const r = await (await fetch('/api/news/save', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids }),
        })).json();
        if (r.success) {
            showToast(`✓ ${r.saved}건 스크래핑 저장됨`, 'success');
            await loadSavedNews();
        } else { showToast(r.error || '실패', 'error'); }
    } catch (e) { showToast('요청 실패', 'error'); }
}

const _savedNewsData = [];

async function loadSavedNews() {
    const q = (document.getElementById('savedNewsSearch')?.value || '').trim();
    const qs = q ? `?q=${encodeURIComponent(q)}` : '';
    try {
        const r = await (await fetch(`/api/news/saved${qs}`, { credentials: 'same-origin' })).json();
        const data = r.success ? r.data : [];
        _savedNewsData.length = 0;
        data.forEach(d => _savedNewsData.push(d));
        const countEl = document.getElementById('savedNewsCount');
        if (countEl) countEl.textContent = `(${data.length}건)`;
        const tbody = document.getElementById('savedNewsBody');
        if (!tbody) return;
        if (!data.length) {
            tbody.innerHTML = `<tr><td colspan="5" style="padding:16px;text-align:center;color:#868e96;font-size:13px;">저장된 뉴스 없음</td></tr>`;
            return;
        }
        tbody.innerHTML = data.map(m => {
            const text = (m.text || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            const preview = text.length > 100 ? text.slice(0, 100) + '…' : text;
            return `<tr style="border-bottom:1px solid #f1f3f5;">
                <td style="padding:5px 4px;width:24px;"><input type="checkbox" class="msg-cb cb-savedNews" data-id="${m.id}" onchange="_onMsgCbChange('savedNews')"></td>
                <td style="padding:5px 8px;font-size:12px;line-height:1.4;" title="${text}">${preview}</td>
                <td style="padding:5px 8px;font-size:11px;color:#495057;text-align:center;white-space:nowrap;">${m.original_date || '-'}</td>
                <td style="padding:5px 8px;font-size:11px;color:#868e96;text-align:center;white-space:nowrap;">${_fmtDatetime(m.saved_at)}</td>
                <td style="padding:5px 6px;text-align:center;">
                    <button onclick="deleteSavedNews(${m.id})" style="border:none;background:none;cursor:pointer;color:#c92a2a;font-size:14px;" title="삭제">🗑</button>
                </td>
            </tr>`;
        }).join('');
    } catch (e) {}
}

function _extractUrlFromText(text) {
    const m = text.match(/https?:\/\/[^\s\)\"\']+/);
    return m ? m[0] : null;
}

function extractJsonClipboard(tableKey) {
    let items;
    if (tableKey === 'savedNews') {
        const checkedIds = new Set(
            Array.from(document.querySelectorAll('.cb-savedNews:checked')).map(cb => parseInt(cb.dataset.id))
        );
        if (checkedIds.size === 0) { showToast('JSON으로 추출할 항목을 선택하세요', 'error'); return; }
        items = _savedNewsData.filter(m => checkedIds.has(m.id)).map(m => {
            const text = m.text || '';
            const title = text.split('\n')[0].trim().replace(/https?:\/\/\S+/g, '').trim() || text.slice(0, 80);
            const url = _extractUrlFromText(text);
            return { title, url };
        });
    } else {
        const sourceData = _tableData[tableKey] || [];
        const checkedIds = new Set(
            Array.from(document.querySelectorAll(`.cb-${tableKey}:checked`)).map(cb => parseInt(cb.dataset.id))
        );
        if (checkedIds.size === 0) { showToast('JSON으로 추출할 항목을 선택하세요', 'error'); return; }
        items = sourceData.filter(m => checkedIds.has(m.id)).map(m => {
            const text = m.text || '';
            const title = text.split('\n')[0].trim().replace(/https?:\/\/\S+/g, '').trim() || text.slice(0, 80);
            const url = _extractUrlFromText(text);
            return { title, url };
        });
    }
    const json = JSON.stringify(items, null, 2);
    navigator.clipboard.writeText(json)
        .then(() => showToast(`✓ ${items.length}건 JSON 클립보드 복사됨`, 'success'))
        .catch(() => {
            const ta = document.createElement('textarea');
            ta.value = json; ta.style.position = 'fixed'; ta.style.opacity = '0';
            document.body.appendChild(ta); ta.select(); document.execCommand('copy');
            document.body.removeChild(ta);
            showToast(`✓ ${items.length}건 JSON 클립보드 복사됨`, 'success');
        });
}

async function deleteSavedNews(id) {
    if (!confirm('이 스크래핑 뉴스를 삭제하시겠습니까?')) return;
    try {
        const r = await (await fetch(`/api/news/saved/${id}`, {
            method: 'DELETE', credentials: 'same-origin',
        })).json();
        if (r.success) { showToast('✓ 삭제됨', 'success'); await loadSavedNews(); }
        else { showToast(r.error || '실패', 'error'); }
    } catch (e) { showToast('요청 실패', 'error'); }
}

// ─── 키워드 관리 ───────────────────────────────────────────

function switchKwTab(tab) {
    _kwTab = tab;
    const newsBtn = document.getElementById('kwTabNews');
    const hsBtn = document.getElementById('kwTabHotstock');
    if (newsBtn) { newsBtn.style.background = tab === 'news' ? '#228be6' : 'white'; newsBtn.style.color = tab === 'news' ? 'white' : '#495057'; }
    if (hsBtn) { hsBtn.style.background = tab === 'hotstock' ? '#228be6' : 'white'; hsBtn.style.color = tab === 'hotstock' ? 'white' : '#495057'; }
    loadKeywords();
}

async function loadKeywords() {
    try {
        const r = await (await fetch(`/api/keywords?type=${_kwTab}`, { credentials: 'same-origin' })).json();
        if (!r.success) return;
        if (_kwTab === 'news') _kwDataNews = r.data; else _kwDataHotstock = r.data;
        const data = r.data;
        _renderKeywordTags('includeKeywordTags', data.include_keywords || [], 'include');
        _renderKeywordTags('excludeKeywordTags', data.exclude_keywords || [], 'exclude');
        _renderGroupTags('keywordGroupTags', data.include_groups || []);
        const mode = data.mode || 'loose';
        const btn = document.getElementById('keywordModeBtn');
        const desc = document.getElementById('keywordModeDesc');
        if (btn) btn.textContent = mode;
        if (desc) desc.textContent = mode === 'loose' ? '키워드 하나라도 일치하면 전달' : '모든 키워드가 일치해야 전달';
    } catch (e) {}
}

function _kwData() { return _kwTab === 'news' ? _kwDataNews : _kwDataHotstock; }

function _renderKeywordTags(containerId, keywords, type) {
    const container = document.getElementById(containerId);
    if (!container) return;
    // 편집 중이면 태그 렌더링 스킵
    const editDiv = document.getElementById(`${type}KeywordEdit`);
    if (editDiv && editDiv.style.display !== 'none') return;
    container.innerHTML = keywords.map(kw => {
        const escaped = kw.replace(/'/g, "\\'");
        return `<span style="display:inline-flex;align-items:center;gap:4px;background:${type==='include'?'#d3f9d8':'#ffe3e3'};color:${type==='include'?'#2f9e44':'#c92a2a'};padding:3px 10px;border-radius:12px;font-size:12px;">
            ${kw}<span style="cursor:pointer;font-size:14px;line-height:1;" onclick="removeKeyword('${type}','${escaped}')" title="삭제">×</span>
        </span>`;
    }).join('') || `<span style="font-size:12px;color:#adb5bd;">없음</span>`;
}

function _renderGroupTags(containerId, groups) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = groups.map(g =>
        `<span style="display:inline-flex;align-items:center;gap:4px;background:#e7f5ff;color:#1971c2;padding:3px 10px;border-radius:12px;font-size:12px;">
            ${g.join(' AND ')}<span style="cursor:pointer;font-size:14px;line-height:1;" onclick="removeKeywordGroup(${JSON.stringify(g)})" title="삭제">×</span>
        </span>`
    ).join('') || `<span style="font-size:12px;color:#adb5bd;">없음</span>`;
}

function toggleKwEdit(type) {
    const tagsDiv = document.getElementById(`${type}KeywordTags`);
    const editDiv = document.getElementById(`${type}KeywordEdit`);
    const textarea = document.getElementById(`${type}KeywordTextarea`);
    if (!tagsDiv || !editDiv || !textarea) return;
    const isEditing = editDiv.style.display !== 'none';
    if (isEditing) {
        cancelKwEdit(type);
    } else {
        const kw = _kwData();
        const keywords = (kw && kw[`${type}_keywords`]) || [];
        textarea.value = keywords.join(', ');
        tagsDiv.style.display = 'none';
        editDiv.style.display = 'block';
        const btn = document.getElementById(`${type}EditBtn`);
        if (btn) btn.textContent = '✕ 닫기';
    }
}

async function saveKwEdit(type) {
    const textarea = document.getElementById(`${type}KeywordTextarea`);
    if (!textarea) return;
    const keywords = textarea.value.split(',').map(k => k.trim()).filter(k => k);
    try {
        const r = await (await fetch('/api/keywords/set', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: _kwTab, field: type, keywords }),
        })).json();
        if (r.success) {
            if (_kwTab === 'news') _kwDataNews = r.keywords; else _kwDataHotstock = r.keywords;
            cancelKwEdit(type);
            _renderKeywordTags(`${type}KeywordTags`, r.keywords[`${type}_keywords`] || [], type);
            showToast(`✓ ${type === 'include' ? 'Include' : 'Exclude'} 키워드 저장됨 (${keywords.length}개)`, 'success');
        } else { showToast(r.error || '저장 실패', 'error'); }
    } catch (e) { showToast('요청 실패', 'error'); }
}

function cancelKwEdit(type) {
    const tagsDiv = document.getElementById(`${type}KeywordTags`);
    const editDiv = document.getElementById(`${type}KeywordEdit`);
    const btn = document.getElementById(`${type}EditBtn`);
    if (tagsDiv) tagsDiv.style.display = 'flex';
    if (editDiv) editDiv.style.display = 'none';
    if (btn) btn.textContent = '✏️ 편집';
}

async function addKeywordBulk(type) {
    const inputId = type === 'include' ? 'includeKeywordInput' : 'excludeKeywordInput';
    const input = document.getElementById(inputId);
    const raw = input ? input.value.trim() : '';
    if (!raw) { showToast('키워드를 입력하세요', 'error'); return; }
    const newKws = raw.split(',').map(k => k.trim()).filter(k => k);
    const existing = (_kwData() && _kwData()[`${type}_keywords`]) || [];
    const merged = [...existing];
    let addedCount = 0;
    for (const kw of newKws) {
        if (!merged.some(e => e.toLowerCase() === kw.toLowerCase())) {
            merged.push(kw);
            addedCount++;
        }
    }
    try {
        const r = await (await fetch('/api/keywords/set', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: _kwTab, field: type, keywords: merged }),
        })).json();
        if (r.success) {
            if (_kwTab === 'news') _kwDataNews = r.keywords; else _kwDataHotstock = r.keywords;
            if (input) input.value = '';
            _renderKeywordTags(`${type}KeywordTags`, r.keywords[`${type}_keywords`] || [], type);
            showToast(`✓ ${addedCount}개 추가됨`, 'success');
        } else { showToast(r.error || '실패', 'error'); }
    } catch (e) { showToast('요청 실패', 'error'); }
}

async function removeKeyword(type, keyword) {
    try {
        const r = await (await fetch(`/api/keywords/${type}`, {
            method: 'DELETE', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keyword, type: _kwTab }),
        })).json();
        if (r.success) {
            if (_kwTab === 'news') _kwDataNews = r.keywords; else _kwDataHotstock = r.keywords;
            _renderKeywordTags(`${type}KeywordTags`, r.keywords[`${type}_keywords`] || [], type);
            showToast(`✓ "${keyword}" 삭제`, 'success');
        } else { showToast(r.error, 'error'); }
    } catch (e) { showToast('요청 실패', 'error'); }
}

async function addKeywordGroup() {
    const input = document.getElementById('groupKeywordInput');
    const raw = input ? input.value.trim() : '';
    const keywords = raw.split(',').map(k => k.trim()).filter(k => k);
    if (keywords.length < 2) { showToast('2개 이상 입력하세요', 'error'); return; }
    try {
        const r = await (await fetch('/api/keywords/group', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keywords, type: _kwTab }),
        })).json();
        if (r.success) {
            if (input) input.value = '';
            if (_kwTab === 'news') _kwDataNews = r.keywords; else _kwDataHotstock = r.keywords;
            _renderGroupTags('keywordGroupTags', r.keywords.include_groups || []);
            showToast(`✓ AND 그룹 추가`, 'success');
        } else { showToast(r.error, 'error'); }
    } catch (e) { showToast('요청 실패', 'error'); }
}

async function removeKeywordGroup(keywords) {
    try {
        const r = await (await fetch('/api/keywords/group', {
            method: 'DELETE', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keywords, type: _kwTab }),
        })).json();
        if (r.success) {
            if (_kwTab === 'news') _kwDataNews = r.keywords; else _kwDataHotstock = r.keywords;
            _renderGroupTags('keywordGroupTags', r.keywords.include_groups || []);
            showToast('✓ 그룹 삭제', 'success');
        } else { showToast(r.error, 'error'); }
    } catch (e) { showToast('요청 실패', 'error'); }
}

async function toggleKeywordMode() {
    const kw = _kwData();
    const currentMode = (kw && kw.mode) || 'loose';
    const newMode = currentMode === 'loose' ? 'strict' : 'loose';
    try {
        const r = await (await fetch('/api/keywords/mode', {
            method: 'PATCH', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: newMode, type: _kwTab }),
        })).json();
        if (r.success) {
            if (kw) kw.mode = newMode;
            const btn = document.getElementById('keywordModeBtn');
            const desc = document.getElementById('keywordModeDesc');
            if (btn) btn.textContent = newMode;
            if (desc) desc.textContent = newMode === 'loose' ? '키워드 하나라도 일치하면 전달' : '모든 키워드가 일치해야 전달';
            showToast(`✓ 모드 변경: ${newMode}`, 'success');
        } else { showToast(r.error, 'error'); }
    } catch (e) { showToast('요청 실패', 'error'); }
}

// 엔터키 지원
document.getElementById('includeKeywordInput')?.addEventListener('keydown', e => { if (e.key === 'Enter') addKeywordBulk('include'); });
document.getElementById('excludeKeywordInput')?.addEventListener('keydown', e => { if (e.key === 'Enter') addKeywordBulk('exclude'); });
document.getElementById('groupKeywordInput')?.addEventListener('keydown', e => { if (e.key === 'Enter') addKeywordGroup(); });
document.getElementById('themeAddInput')?.addEventListener('keydown', e => { if (e.key === 'Enter') addTheme(); });
document.getElementById('savedNewsSearch')?.addEventListener('keydown', e => { if (e.key === 'Enter') loadSavedNews(); });

// ─── 테마 라이브러리 ────────────────────────────────────────

async function loadThemes() {
    try {
        const res = await fetch('/api/themes', { credentials: 'same-origin' });
        const r = await res.json();
        if (!r.success) return;
        _renderThemeTable(r.data || []);
    } catch (e) { /* ignore */ }
}

function _renderThemeTable(themes) {
    const tbody = document.getElementById('themeTableBody');
    if (!tbody) return;
    if (!themes.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="padding:16px; text-align:center; color:#868e96; font-size:13px;">테마 없음 (급등주 메시지 수신 시 자동 누적)</td></tr>';
        return;
    }
    tbody.innerHTML = themes.map(t => {
        const first = t.first_seen_at ? new Date(t.first_seen_at).toLocaleDateString('ko-KR', {month:'short',day:'numeric'}) : '-';
        const last = t.last_seen_at ? new Date(t.last_seen_at).toLocaleDateString('ko-KR', {month:'short',day:'numeric'}) : '-';
        const activeLabel = t.active ? '<span style="color:#2f9e44;">●</span>' : '<span style="color:#adb5bd;">○</span>';
        return `<tr style="border-bottom:1px solid #f1f3f5;">
            <td style="padding:6px 8px; font-size:13px;">${t.name}</td>
            <td style="padding:6px 8px; text-align:center; font-size:13px;">${t.count}</td>
            <td style="padding:6px 8px; text-align:center; font-size:12px; color:#868e96;">${first}</td>
            <td style="padding:6px 8px; text-align:center; font-size:12px; color:#868e96;">${last}</td>
            <td style="padding:6px 8px; text-align:center; cursor:pointer;" onclick="toggleTheme(${t.id})" title="클릭해서 토글">${activeLabel}</td>
            <td style="padding:6px 8px; text-align:center;">
                <button style="background:none;border:none;color:#fa5252;cursor:pointer;font-size:14px;" onclick="deleteTheme(${t.id})" title="삭제">🗑</button>
            </td>
        </tr>`;
    }).join('');
}

async function addTheme() {
    const input = document.getElementById('themeAddInput');
    const name = input ? input.value.trim() : '';
    if (!name) { showToast('테마명을 입력하세요', 'error'); return; }
    try {
        const res = await fetch('/api/themes', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name }),
        });
        const r = await res.json();
        if (r.success) {
            if (input) input.value = '';
            showToast(`✓ "${name}" 추가`, 'success');
            await loadThemes();
        } else { showToast(r.error, 'error'); }
    } catch (e) { showToast('요청 실패', 'error'); }
}

async function resetThemes() {
    if (!confirm('테마 라이브러리 전체를 초기화하시겠습니까?\n(모든 테마가 삭제됩니다)')) return;
    try {
        const res = await fetch('/api/themes/reset', { method: 'POST', credentials: 'same-origin' });
        const r = await res.json();
        if (r.success) { showToast('✓ 테마 초기화 완료', 'success'); await loadThemes(); }
        else showToast(r.error || '초기화 실패', 'error');
    } catch (e) { showToast('요청 실패', 'error'); }
}

async function toggleTheme(id) {
    try {
        const res = await fetch(`/api/themes/${id}`, { method: 'PATCH', credentials: 'same-origin' });
        const r = await res.json();
        if (r.success) await loadThemes();
        else showToast(r.error, 'error');
    } catch (e) { showToast('요청 실패', 'error'); }
}

async function deleteTheme(id) {
    if (!confirm('테마를 삭제하시겠습니까?')) return;
    try {
        const res = await fetch(`/api/themes/${id}`, { method: 'DELETE', credentials: 'same-origin' });
        const r = await res.json();
        if (r.success) { showToast('✓ 삭제', 'success'); await loadThemes(); }
        else showToast(r.error, 'error');
    } catch (e) { showToast('요청 실패', 'error'); }
}

// ─── 백테스트 ─────────────────────────────────────────────

let _btAllPicks = [];
let _btActiveSlot = 'all';
let _btAllSessions = [];
let _btCompareMode = false;
let _acpVisible = false;

function toggleAnalysisContextPanel() {
    _acpVisible = !_acpVisible;
    document.getElementById('analysisContextPanel').style.display = _acpVisible ? 'block' : 'none';
    if (_acpVisible) loadAnalysisContext();
}

async function loadAnalysisContext() {
    try {
        const today = new Date().toISOString().slice(0, 10);
        document.getElementById('acpDate').textContent = today;
        const res = await fetch(`/api/analysis/context?date=${today}`, { credentials: 'same-origin' });
        const r = await res.json();
        if (!r.success) return;
        const ctx = r.context;

        // Morning Report 복원
        if (ctx.morning_report) {
            const mr = ctx.morning_report;
            document.getElementById('acpUsMarket').value = mr.us_market || '';
            document.getElementById('acpPredictedThemes').value = (mr.predicted_themes || []).join(', ');
            document.getElementById('acpMorningText').value = mr.text || '';
            document.getElementById('acpMorningStatus').textContent = '✅ 저장됨';
            document.getElementById('acpMorningStatus').className = 'acp-status saved';
        } else {
            document.getElementById('acpMorningStatus').textContent = '미입력';
            document.getElementById('acpMorningStatus').className = 'acp-status empty';
        }

        // Next Instruction
        const instrEl = document.getElementById('acpInstruction');
        const instrMeta = document.getElementById('acpInstrMeta');
        const instrStatus = document.getElementById('acpInstrStatus');
        if (ctx.next_instruction) {
            instrEl.value = ctx.next_instruction;
            if (ctx.instruction_used) {
                instrStatus.textContent = '✅ 사용됨';
                instrStatus.className = 'acp-status used';
                instrMeta.textContent = '다음 슬롯 분석에 반영되었습니다.';
            } else {
                instrStatus.textContent = '⏳ 대기중';
                instrStatus.className = 'acp-status pending';
                instrMeta.textContent = '다음 분석 실행 시 1회 반영됩니다.';
            }
        } else {
            instrEl.value = '';
            instrStatus.textContent = '없음';
            instrStatus.className = 'acp-status empty';
            instrMeta.textContent = '';
        }

        // Interval Context
        const icEl = document.getElementById('acpIntervalContext');
        if (ctx.interval_context) {
            icEl.textContent = JSON.stringify(ctx.interval_context, null, 2);
        } else {
            icEl.textContent = '(아직 분석 없음)';
        }
    } catch (e) {
        console.error('loadAnalysisContext 실패', e);
    }
}

async function saveMorningReport() {
    const us_market = document.getElementById('acpUsMarket').value.trim();
    const themes_raw = document.getElementById('acpPredictedThemes').value.trim();
    const text = document.getElementById('acpMorningText').value.trim();
    const predicted_themes = themes_raw ? themes_raw.split(',').map(s => s.trim()).filter(Boolean) : [];
    const morning_report = { us_market, predicted_themes, text };
    try {
        const res = await fetch('/api/analysis/morning-report', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ morning_report })
        });
        const r = await res.json();
        if (r.success) {
            document.getElementById('acpMorningStatus').textContent = '✅ 저장됨';
            document.getElementById('acpMorningStatus').className = 'acp-status saved';
            showToast('Morning Report 저장됨', 'success');
        } else {
            showToast('저장 실패', 'error');
        }
    } catch (e) { showToast('저장 실패', 'error'); }
}

async function saveNextInstruction() {
    const instruction = document.getElementById('acpInstruction').value.trim();
    try {
        const res = await fetch('/api/analysis/instruction', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instruction: instruction || null })
        });
        const r = await res.json();
        if (r.success) {
            const status = document.getElementById('acpInstrStatus');
            const meta = document.getElementById('acpInstrMeta');
            if (instruction) {
                status.textContent = '⏳ 대기중';
                status.className = 'acp-status pending';
                meta.textContent = '다음 분석 실행 시 1회 반영됩니다.';
            } else {
                status.textContent = '없음';
                status.className = 'acp-status empty';
                meta.textContent = '';
            }
            showToast('인스트럭션 저장됨', 'success');
        } else {
            showToast('저장 실패', 'error');
        }
    } catch (e) { showToast('저장 실패', 'error'); }
}

async function clearNextInstruction() {
    document.getElementById('acpInstruction').value = '';
    await saveNextInstruction();
}

async function loadBacktestSessions() {
    try {
        const res = await fetch('/api/backtest/sessions', { credentials: 'same-origin' });
        const r = await res.json();
        if (!r.success) { showToast(r.error || '세션 로드 실패', 'error'); return; }
        _btAllSessions = r.data || [];

        const makeOption = s => {
            const ver = s.version ? `[${s.version}] ` : '';
            const label = `${ver}${s.run_date}${s.notes ? ' — ' + s.notes : ''}`;
            return `<option value="${s.id}">${label}</option>`;
        };
        const blankOpt = '<option value="">-- 선택 --</option>';

        // 메인 select
        const sel = document.getElementById('backtestSessionSelect');
        const prev = sel.value;
        sel.innerHTML = blankOpt + _btAllSessions.map(makeOption).join('');
        if (prev) sel.value = prev;
        if (sel.value) loadBacktestSession();

        // 비교 selects
        ['btSessionA', 'btSessionB'].forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            const pv = el.value;
            el.innerHTML = blankOpt + _btAllSessions.map(makeOption).join('');
            if (pv) el.value = pv;
        });
    } catch (e) { showToast('세션 로드 실패', 'error'); }
}

function toggleBtCompareMode() {
    _btCompareMode = !_btCompareMode;
    const panel = document.getElementById('btComparePanel');
    const single = document.getElementById('backtestPicksList');
    const slotBar = document.getElementById('backtestSlotBar');
    const summary = document.getElementById('backtestSummary');
    const btn = document.getElementById('btCompareToggleBtn');
    if (_btCompareMode) {
        panel.style.display = '';
        single.style.display = 'none';
        slotBar.style.display = 'none';
        summary.style.display = 'none';
        btn.textContent = '✕ 비교 닫기';
        loadBacktestSessions();
    } else {
        panel.style.display = 'none';
        single.style.display = '';
        btn.textContent = '⚖️ 버전 비교';
        if (_btAllPicks.length) { slotBar.style.display = ''; summary.style.display = ''; }
    }
}

async function loadBacktestSession() {
    const sel = document.getElementById('backtestSessionSelect');
    const sessionId = sel.value;
    const slotBar = document.getElementById('backtestSlotBar');
    const summary = document.getElementById('backtestSummary');
    const list = document.getElementById('backtestPicksList');
    const banner = document.getElementById('btVersionBanner');

    if (!sessionId) {
        slotBar.style.display = 'none';
        summary.style.display = 'none';
        banner.style.display = 'none';
        list.innerHTML = '<p class="empty-state">세션을 선택하면 추천 종목이 표시됩니다.</p>';
        return;
    }
    try {
        const res = await fetch(`/api/backtest/sessions/${sessionId}`, { credentials: 'same-origin' });
        const r = await res.json();
        if (!r.success) { showToast(r.error || '로드 실패', 'error'); return; }
        _btAllPicks = r.data || [];
        _btActiveSlot = 'all';
        slotBar.style.display = '';
        summary.style.display = '';
        document.querySelectorAll('.slot-btn').forEach(b => b.classList.toggle('active', b.dataset.slot === 'all'));

        // 버전 배너
        const meta = _btAllSessions.find(s => String(s.id) === String(sessionId));
        if (meta) {
            const ver = meta.version || 'v1';
            const desc = meta.strategy_desc || '';
            banner.textContent = `${ver}  ${meta.run_date}${desc ? '  ·  ' + desc : ''}`;
            banner.style.display = '';
        }

        renderBacktestPicks();
    } catch (e) { showToast('로드 실패', 'error'); }
}

async function loadBtCompare() {
    const sidA = document.getElementById('btSessionA').value;
    const sidB = document.getElementById('btSessionB').value;
    const descA = document.getElementById('btVersionDescA');
    const descB = document.getElementById('btVersionDescB');
    const result = document.getElementById('btCompareResult');

    const getDesc = sid => {
        const s = _btAllSessions.find(x => String(x.id) === String(sid));
        return s ? (s.strategy_desc || s.notes || '') : '';
    };
    descA.textContent = getDesc(sidA);
    descB.textContent = getDesc(sidB);

    if (!sidA || !sidB) return;
    try {
        const res = await fetch(`/api/backtest/compare?session_a=${sidA}&session_b=${sidB}`, { credentials: 'same-origin' });
        const r = await res.json();
        if (!r.success) { result.innerHTML = `<p class="empty-state">${r.error}</p>`; return; }
        result.innerHTML = renderBtCompareTable(r.session_a, r.session_b);
    } catch (e) { result.innerHTML = '<p class="empty-state">로드 실패</p>'; }
}

function renderBtCompareTable(sA, sB) {
    const metaA = sA.meta || {}; const metaB = sB.meta || {};
    const picksA = sA.picks || []; const picksB = sB.picks || [];

    const statsA = btStats(picksA); const statsB = btStats(picksB);
    const verA = metaA.version || 'A'; const verB = metaB.version || 'B';

    // 통계 요약
    let html = `<div class="bt-compare-stats">
      <table class="bt-compare-table">
        <tr><th></th><th>${verA} · ${metaA.run_date||''}</th><th>${verB} · ${metaB.run_date||''}</th></tr>
        <tr><td>추천 종목</td><td>${statsA.total}</td><td>${statsB.total}</td></tr>
        <tr><td>H급</td><td>${statsA.h}</td><td>${statsB.h}</td></tr>
        <tr><td>승/패 (P&L 입력)</td><td>${statsA.wins}승 ${statsA.losses}패</td><td>${statsB.wins}승 ${statsB.losses}패</td></tr>
        <tr><td>평균 수익률</td><td>${statsA.avg !== null ? statsA.avg + '%' : '-'}</td><td>${statsB.avg !== null ? statsB.avg + '%' : '-'}</td></tr>
      </table>
    </div>`;

    // 종목 교차 비교
    const namesA = new Set(picksA.map(p => p.stock_name));
    const namesB = new Set(picksB.map(p => p.stock_name));
    const allNames = [...new Set([...namesA, ...namesB])].sort();

    html += `<div style="margin-top:12px;font-size:12px;font-weight:600;margin-bottom:6px;">종목별 비교</div>
    <table class="bt-compare-table">
      <tr><th>종목</th><th>${verA}</th><th>${verB}</th></tr>`;

    allNames.forEach(name => {
        const pA = picksA.find(p => p.stock_name === name);
        const pB = picksB.find(p => p.stock_name === name);
        const rowClass = pA && pB ? 'in-both' : pA ? 'only-a' : 'only-b';
        const cellA = pA ? `[${pA.confidence||'?'}] ${pA.slot_time} ${pA.tag_type||''}${pA.result ? ' → '+pA.result+(pA.profit_pct!=null?'('+pA.profit_pct+'%)':'') : ''}` : '—';
        const cellB = pB ? `[${pB.confidence||'?'}] ${pB.slot_time} ${pB.tag_type||''}${pB.result ? ' → '+pB.result+(pB.profit_pct!=null?'('+pB.profit_pct+'%)':'') : ''}` : '—';
        html += `<tr class="${rowClass}"><td>${name}</td><td>${cellA}</td><td>${cellB}</td></tr>`;
    });
    html += '</table>';
    return html;
}

function btStats(picks) {
    const withPnl = picks.filter(p => p.result);
    const wins = withPnl.filter(p => p.result === 'win').length;
    const losses = withPnl.filter(p => p.result === 'loss' || p.result === 'stoploss').length;
    const avg = withPnl.length ? +(withPnl.reduce((s,p) => s+(p.profit_pct||0), 0) / withPnl.length).toFixed(2) : null;
    return { total: picks.length, h: picks.filter(p => p.confidence==='H').length, wins, losses, avg };
}

function filterBacktestSlot(slot) {
    _btActiveSlot = slot;
    document.querySelectorAll('.slot-btn').forEach(b => b.classList.toggle('active', b.dataset.slot === slot));
    renderBacktestPicks();
}

function renderBacktestPicks() {
    const picks = _btActiveSlot === 'all'
        ? _btAllPicks
        : _btAllPicks.filter(p => p.slot_time === _btActiveSlot);

    // 통계
    const total = picks.length;
    const withPnl = picks.filter(p => p.result);
    const wins = withPnl.filter(p => p.result === 'win').length;
    const losses = withPnl.filter(p => p.result === 'loss' || p.result === 'stoploss').length;
    const avgPct = withPnl.length
        ? (withPnl.reduce((s, p) => s + (p.profit_pct || 0), 0) / withPnl.length).toFixed(2)
        : null;

    document.getElementById('btSummaryTotal').textContent = `총 ${total}종목`;
    document.getElementById('btSummaryWin').textContent = wins ? `▲ ${wins}승` : '';
    document.getElementById('btSummaryLoss').textContent = losses ? `▼ ${losses}패` : '';
    document.getElementById('btSummaryAvgPct').textContent = avgPct !== null ? `평균 ${avgPct}%` : '';

    const list = document.getElementById('backtestPicksList');
    if (!picks.length) {
        list.innerHTML = '<p class="empty-state">해당 슬롯에 추천 종목이 없습니다.</p>';
        return;
    }

    list.innerHTML = picks.map(p => renderBacktestPickCard(p)).join('');
}

function renderBacktestPickCard(p) {
    const confClass = p.confidence ? `bt-confidence-${p.confidence}` : '';
    const confLabel = p.confidence ? `[${p.confidence}]` : '';
    const tagLabel = { ss_up: '🚀 상한가', vi: '⚡ VI', ss: '📈 급등', news: '📰 뉴스' }[p.tag_type] || (p.tag_type || '');
    const priceStr = p.price_at_slot ? `추천가 ${Number(p.price_at_slot).toLocaleString()}원` : '';
    const themeStr = p.theme ? `테마: ${p.theme}` : '';

    // 추천 시점 상승률 배지 (hotstock 소스에서 파싱)
    let changePctHtml = '';
    const sources = p.sources || [];
    const hsSource = sources.find(s => s.type === 'hotstock');
    if (hsSource && hsSource.text) {
        const m = hsSource.text.match(/([+-]?\d+\.?\d*)\s*%/);
        if (m) {
            const pct = parseFloat(m[1]);
            const isHigh = pct >= 10;
            changePctHtml = `<span class="bt-change-pct ${isHigh ? 'bt-change-high' : 'bt-change-normal'}">+${pct}%${isHigh ? ' ⚠️' : ''}</span>`;
        }
    }

    // 관련 상한가 종목 (catalyst나 analysis_text에서 '상한가' 언급 종목, 또는 소스 텍스트의 SS⬆️/상한가 정보)
    let leaderStockHtml = '';
    const allText = [p.catalyst || '', p.analysis_text || '', ...sources.map(s => s.text || '')].join(' ');
    const leaderMatch = allText.match(/(?:상한가|SS⬆️)[^가-힣]*([가-힣A-Za-z0-9]+(?:\s+[가-힣A-Za-z0-9]+)?)\s*(?:\(|상한가)/);
    // hotstock 소스 중 SS⬆️ 포함된 별도 종목 텍스트 탐색
    const leaderSources = sources.filter(s => s.type === 'hotstock' && s.text && s.text.includes('SS⬆️') && s.text.replace(/SS⬆️/g,'').trim() && !s.text.includes(p.stock_name));
    if (leaderSources.length) {
        const leaderTexts = leaderSources.map(s => {
            const nm = s.text.match(/\]\s*([가-힣A-Za-z0-9]+)/);
            return nm ? escapeHtml(nm[1]) : escapeHtml(s.text.slice(0, 30));
        });
        leaderStockHtml = `<div class="bt-leader-stock">🚀 대장주: ${leaderTexts.join(', ')}</div>`;
    }

    const pnlResult = p.result
        ? `<span class="bt-pnl-result ${p.result}">${p.result === 'win' ? '▲ 수익' : p.result === 'stoploss' ? '✂ 손절' : '▼ 손실'} ${p.profit_pct != null ? p.profit_pct + '%' : ''}</span>`
        : '';

    const noteSourceHtml = p.note_source
        ? `<div class="bt-note-source">📝 ${p.note_source}</div>`
        : '';

    // 소스 타임스탬프 목록
    const typeLabel = { hotstock: '🚀급등주', news: '📰뉴스DB', google: '🔍실검', dart: '📋공시' };
    const sourcesHtml = sources.length ? `
    <div class="bt-sources">
        <div class="bt-sources-label">확인 소스</div>
        ${sources.map(s => `<div class="bt-source-item">
            <span class="bt-source-type">${typeLabel[s.type] || s.type}</span>
            <span class="bt-source-time">${s.time || ''}</span>
            <span class="bt-source-text">${escapeHtml(s.text || '')}</span>
        </div>`).join('')}
    </div>` : '';

    // 감시리스트 등록 버튼 (종목코드 있을 때만)
    const watchlistBtnHtml = p.stock_code ? `
    <div class="bt-watchlist-row">
        <div class="bt-pnl-field">
            <label>버짓(만원)</label>
            <input type="number" id="btBudget_${p.id}" placeholder="100">
        </div>
        <button class="btn btn-sm btn-success" onclick="btRegisterMode2(${p.id})">📊 Mode2 등록</button>
    </div>` : '';

    // 재무정보 버튼 (종목코드 있을 때만)
    const financeBtnHtml = p.stock_code ? `
    <div class="bt-finance-row">
        <button class="btn btn-sm btn-outline bt-finance-btn" onclick="btLoadFinance(${p.id}, '${p.stock_code}')">📈 재무정보</button>
        <div id="btFinance_${p.id}" class="bt-finance-panel" style="display:none;"></div>
    </div>` : '';

    return `
<div class="bt-pick-card${p.result === 'win' ? ' bt-card-win' : p.result === 'stoploss' || p.result === 'loss' ? ' bt-card-loss' : ''}" id="btCard_${p.id}">
    <div class="bt-pick-header">
        <span class="bt-pick-name">${p.stock_name}${p.stock_code ? ` (${p.stock_code})` : ''}</span>
        ${changePctHtml}
        <span class="bt-pick-slot">${p.slot_time}</span>
        ${tagLabel ? `<span class="tag-badge">${tagLabel}</span>` : ''}
        ${confLabel ? `<span class="${confClass}">${confLabel}</span>` : ''}
        ${pnlResult}
    </div>
    ${leaderStockHtml}
    <div class="bt-pick-meta">${[priceStr, themeStr].filter(Boolean).join(' · ')}</div>
    ${p.catalyst ? `<div class="bt-catalyst"><div class="bt-catalyst-label">촉매/시황</div>${escapeHtml(p.catalyst)}</div>` : ''}
    ${sourcesHtml}
    ${p.analysis_text ? `<div class="bt-pick-analysis">${escapeHtml(p.analysis_text)}</div>` : ''}
    ${noteSourceHtml}
    <div class="bt-pnl-form">
        <div class="bt-pnl-field">
            <label>매수가</label>
            <input type="number" id="btBuy_${p.id}" value="${p.buy_price || ''}" placeholder="0"
                oninput="btCalcExitFromPct(${p.id})">
        </div>
        <div class="bt-pnl-field">
            <label>익절가</label>
            <input type="number" id="btExit_${p.id}" value="${p.exit_price || ''}" placeholder="0">
        </div>
        <div class="bt-pnl-field bt-pnl-field-pct">
            <label>익절 %</label>
            <div class="bt-pct-row">
                <input type="number" id="btExitPct_${p.id}" placeholder="%" step="0.5" min="0"
                    oninput="btCalcExitFromPct(${p.id})">
                <span class="bt-pct-hint">→ 자동 계산</span>
            </div>
        </div>
        <div class="bt-pnl-field">
            <label>손절가</label>
            <input type="number" id="btStop_${p.id}" value="${p.stoploss_price || ''}" placeholder="0">
        </div>
        <div class="bt-pnl-field">
            <label>메모</label>
            <input type="text" id="btNote_${p.id}" value="${p.pnl_notes || ''}" placeholder="">
        </div>
        <button class="btn btn-sm btn-primary" onclick="saveBacktestPnl(${p.id})">저장</button>
    </div>
    ${watchlistBtnHtml}
    ${financeBtnHtml}
</div>`;
}

function btCalcExitFromPct(pickId) {
    const buyInput = document.getElementById(`btBuy_${pickId}`);
    const pctInput = document.getElementById(`btExitPct_${pickId}`);
    const exitInput = document.getElementById(`btExit_${pickId}`);
    if (!buyInput || !pctInput || !exitInput) return;
    const buy = parseFloat(buyInput.value);
    const pct = parseFloat(pctInput.value);
    if (buy > 0 && pct > 0) {
        exitInput.value = Math.round(buy * (1 + pct / 100));
    }
}

async function btLoadFinance(pickId, stockCode) {
    const panel = document.getElementById(`btFinance_${pickId}`);
    const btn = panel?.previousElementSibling;
    if (!panel) return;

    // 토글
    if (panel.style.display !== 'none') {
        panel.style.display = 'none';
        if (btn) btn.textContent = '📈 재무정보';
        return;
    }

    // 이미 로드된 데이터 있으면 그냥 표시
    if (panel.dataset.loaded === '1') {
        panel.style.display = '';
        if (btn) btn.textContent = '📈 닫기';
        return;
    }

    panel.style.display = '';
    panel.innerHTML = '<span class="bt-finance-loading">조회 중...</span>';
    if (btn) btn.textContent = '📈 닫기';

    try {
        const res = await fetch(`/api/financial-info?stock_code=${stockCode}`, { credentials: 'same-origin' });
        const r = await res.json();
        if (!r.success) { panel.innerHTML = `<span class="bt-finance-error">조회 실패</span>`; return; }

        const d = r.data;
        const fmt = (v, unit='') => v != null ? `${Number(v).toLocaleString()}${unit}` : '-';
        const fmtPct = (v) => v != null ? `${v}%` : '-';

        // 부채비율 경고색
        const debtClass = d.debt_ratio != null
            ? (d.debt_ratio > 200 ? 'bt-fi-warn' : d.debt_ratio > 100 ? 'bt-fi-caution' : 'bt-fi-good')
            : '';

        panel.innerHTML = `
<div class="bt-finance-grid">
    <div class="bt-fi-item">
        <span class="bt-fi-label">시가총액</span>
        <span class="bt-fi-value">${fmt(d.market_cap_bil, '억')}</span>
    </div>
    <div class="bt-fi-item">
        <span class="bt-fi-label">영업이익</span>
        <span class="bt-fi-value">${fmt(d.op_income_bil, '억')}</span>
    </div>
    <div class="bt-fi-item">
        <span class="bt-fi-label">매출액</span>
        <span class="bt-fi-value">${fmt(d.sales_bil, '억')}</span>
    </div>
    <div class="bt-fi-item">
        <span class="bt-fi-label">당기순이익</span>
        <span class="bt-fi-value">${fmt(d.net_income_bil, '억')}</span>
    </div>
    <div class="bt-fi-item">
        <span class="bt-fi-label">PER</span>
        <span class="bt-fi-value">${fmt(d.per, '배')}</span>
    </div>
    <div class="bt-fi-item">
        <span class="bt-fi-label">PBR</span>
        <span class="bt-fi-value">${fmt(d.pbr, '배')}</span>
    </div>
    <div class="bt-fi-item">
        <span class="bt-fi-label">ROE</span>
        <span class="bt-fi-value">${fmtPct(d.roe)}</span>
    </div>
    <div class="bt-fi-item">
        <span class="bt-fi-label">유통비율</span>
        <span class="bt-fi-value">${fmtPct(d.flo_rt)}</span>
    </div>
    ${d.debt_ratio != null ? `<div class="bt-fi-item">
        <span class="bt-fi-label">부채비율</span>
        <span class="bt-fi-value ${debtClass}">${fmtPct(d.debt_ratio)}</span>
    </div>` : ''}
    ${d.current_ratio != null ? `<div class="bt-fi-item">
        <span class="bt-fi-label">유동비율</span>
        <span class="bt-fi-value">${fmtPct(d.current_ratio)}</span>
    </div>` : ''}
</div>
${d.bsns_year ? `<div class="bt-fi-source">DART ${d.bsns_year} 사업보고서 + Kiwoom 실시간</div>` : '<div class="bt-fi-source">Kiwoom 실시간</div>'}`;
        panel.dataset.loaded = '1';
    } catch (e) {
        panel.innerHTML = `<span class="bt-finance-error">조회 오류: ${e.message}</span>`;
    }
}

async function saveBacktestPnl(pickId) {
    const buy = parseFloat(document.getElementById(`btBuy_${pickId}`).value) || null;
    const exit = parseFloat(document.getElementById(`btExit_${pickId}`).value) || null;
    const stop = parseFloat(document.getElementById(`btStop_${pickId}`).value) || null;
    const notes = document.getElementById(`btNote_${pickId}`).value.trim();

    try {
        const res = await fetch(`/api/backtest/picks/${pickId}/pnl`, {
            method: 'PUT',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ buy_price: buy, exit_price: exit, stoploss_price: stop, notes })
        });
        const r = await res.json();
        if (r.success) {
            showToast(`저장 완료 ${r.profit_pct != null ? r.profit_pct + '%' : ''}`, 'success');
            // 로컬 데이터 업데이트 후 카드 재렌더
            const pick = _btAllPicks.find(p => p.id === pickId);
            if (pick) {
                pick.buy_price = buy; pick.exit_price = exit; pick.stoploss_price = stop;
                pick.result = r.result; pick.profit_pct = r.profit_pct; pick.pnl_notes = notes;
            }
            const card = document.getElementById(`btCard_${pickId}`);
            if (card) card.outerHTML = renderBacktestPickCard(pick || { id: pickId });
            renderBacktestPicks();
        } else {
            showToast(r.error || '저장 실패', 'error');
        }
    } catch (e) { showToast('저장 실패', 'error'); }
}

async function btRegisterMode2(pickId) {
    const pick = _btAllPicks.find(p => p.id === pickId);
    if (!pick || !pick.stock_code) { showToast('종목코드 없음', 'error'); return; }

    const buy = parseFloat(document.getElementById(`btBuy_${pickId}`)?.value) || null;
    const exit = parseFloat(document.getElementById(`btExit_${pickId}`)?.value) || null;
    const stop = parseFloat(document.getElementById(`btStop_${pickId}`)?.value) || null;
    const budgetMan = parseFloat(document.getElementById(`btBudget_${pickId}`)?.value) || null;

    if (!buy) { showToast('매수가 입력 필요', 'error'); return; }
    if (!budgetMan) { showToast('버짓(만원) 입력 필요', 'error'); return; }

    const payload = {
        code: pick.stock_code,
        name: pick.stock_name,
        buy_target_price: buy,
        resistance_1_price: exit || null,
        support_1_price: stop || null,
        budget: budgetMan * 10000,
        notify_only: true,
    };

    try {
        const res = await fetch('/api/mode2/watchers', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const r = await res.json();
        if (r.success) {
            showToast(`📊 Mode2 등록 완료: ${pick.stock_name}`, 'success');
        } else {
            showToast(r.error || '등록 실패', 'error');
        }
    } catch (e) { showToast('등록 실패', 'error'); }
}

function escapeHtml(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ─── 格言(Trading Mottos) ──────────────────────────────────────────────────

let _mottos = [];
let _mottoEditVisible = false;

function toggleMottoEdit() {
    _mottoEditVisible = !_mottoEditVisible;
    document.getElementById('mottoEditPanel').style.display = _mottoEditVisible ? 'block' : 'none';
    if (_mottoEditVisible) renderMottoEditList();
}

async function loadMottos() {
    try {
        const res = await fetch('/api/mottos', { credentials: 'same-origin' });
        const r = await res.json();
        if (!r.success) return;
        _mottos = r.mottos || [];
        renderMottoDisplayList();
        if (_mottoEditVisible) renderMottoEditList();
    } catch (e) { /* 格言 로드 실패는 무시 */ }
}

function renderMottoDisplayList() {
    const el = document.getElementById('mottoDisplayList');
    if (!el) return;
    if (!_mottos.length) {
        el.innerHTML = '<p class="bt-motto-empty">매매 지침을 추가해보세요 (✏️ 편집 버튼)</p>';
        return;
    }
    el.innerHTML = _mottos.map(m => `
        <div class="bt-motto-item">
            <span class="bt-motto-bullet">📌</span>
            <span class="bt-motto-text">${escapeHtml(m.content)}</span>
        </div>`).join('');
}

function renderMottoEditList() {
    const el = document.getElementById('mottoEditList');
    if (!el) return;
    if (!_mottos.length) { el.innerHTML = ''; return; }
    el.innerHTML = _mottos.map(m => `
        <div class="bt-motto-edit-item" id="mottoEdit_${m.id}">
            <textarea class="bt-motto-edit-input" id="mottoEditText_${m.id}" rows="2">${escapeHtml(m.content)}</textarea>
            <div class="bt-motto-edit-actions">
                <button class="btn btn-xs btn-primary" onclick="saveMotto(${m.id})">저장</button>
                <button class="btn btn-xs btn-danger" onclick="deleteMotto(${m.id})">삭제</button>
            </div>
        </div>`).join('');
}

async function addMotto() {
    const input = document.getElementById('mottoNewInput');
    const content = (input.value || '').trim();
    if (!content) { showToast('내용을 입력하세요', 'error'); return; }
    try {
        const res = await fetch('/api/mottos', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        const r = await res.json();
        if (r.success) {
            input.value = '';
            showToast('지침 추가됨', 'success');
            await loadMottos();
        } else {
            showToast(r.error || '추가 실패', 'error');
        }
    } catch (e) { showToast('추가 실패', 'error'); }
}

async function saveMotto(mottoId) {
    const el = document.getElementById(`mottoEditText_${mottoId}`);
    const content = (el?.value || '').trim();
    if (!content) { showToast('내용을 입력하세요', 'error'); return; }
    try {
        const res = await fetch(`/api/mottos/${mottoId}`, {
            method: 'PUT',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        const r = await res.json();
        if (r.success) {
            showToast('저장됨', 'success');
            await loadMottos();
        } else {
            showToast(r.error || '저장 실패', 'error');
        }
    } catch (e) { showToast('저장 실패', 'error'); }
}

async function deleteMotto(mottoId) {
    if (!confirm('이 지침을 삭제하시겠습니까?')) return;
    try {
        const res = await fetch(`/api/mottos/${mottoId}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });
        const r = await res.json();
        if (r.success) {
            showToast('삭제됨', 'success');
            await loadMottos();
        }
    } catch (e) { showToast('삭제 실패', 'error'); }
}

// ========== 실전 트레이딩 (Live) ==========
let _liveAllPicks = [];
let _liveSlotPicks = [];
let _liveActiveSlot = 'current';
let _liveCarouselIdx = 0;
const _liveChartLoaded = {};  // pickId → true (차트 로드 완료 여부)

const _LIVE_SLOTS = ['09:15','09:45','10:15','10:45','11:15','11:45',
                     '12:15','12:45','13:15','13:45','14:15','14:45','15:15'];

function _getCurrentLiveSlot() {
    const now = new Date();
    const hhmm = String(now.getHours()).padStart(2,'0') + ':' + String(now.getMinutes()).padStart(2,'0');
    const past = _LIVE_SLOTS.filter(s => s <= hhmm);
    if (past.length) return past[past.length - 1];
    return hhmm < '09:15' ? _LIVE_SLOTS[0] : _LIVE_SLOTS[_LIVE_SLOTS.length - 1];
}

// run_at (UTC stored as "YYYY-MM-DD HH:MM:SS") → KST slot_time "HH:MM"
function _runAtToSlot(run_at) {
    if (!run_at) return null;
    try {
        // SQLite UTC timestamp → JS Date (add Z for UTC parsing)
        const utcStr = run_at.replace(' ', 'T') + 'Z';
        const d = new Date(utcStr);
        const kstH = d.getUTCHours() + 9;  // KST = UTC+9
        const h = String(kstH % 24).padStart(2, '0');
        const m = String(d.getUTCMinutes()).padStart(2, '0');
        return h + ':' + m;
    } catch(e) { return null; }
}

// run_at KST 시간 → 가장 가까운 이전 슬롯 반환
function _runAtToNearestSlot(run_at) {
    const hhmm = _runAtToSlot(run_at);
    if (!hhmm) return null;
    const past = _LIVE_SLOTS.filter(s => s <= hhmm);
    return past.length ? past[past.length - 1] : _LIVE_SLOTS[0];
}

async function loadLive() {
    try {
        const res = await fetch('/api/live/picks', { credentials: 'same-origin' });
        const r = await res.json();
        if (!r.success) { showToast(r.error || '로드 실패', 'error'); return; }

        // siwhang_results 기반 — slot_time이 없으면 run_at에서 추정
        _liveAllPicks = (r.data || []).map(p => ({
            ...p,
            _slotKey: p.slot_time || _runAtToNearestSlot(p.run_at) || '기타',
            _runKst: _runAtToSlot(p.run_at),
        }));

        const emptyState = document.getElementById('liveEmptyState');
        const slotBar = document.getElementById('liveSlotBar');
        const banner = document.getElementById('liveSessionBanner');

        if (!_liveAllPicks.length) {
            emptyState.style.display = '';
            slotBar.style.display = 'none';
            banner.style.display = 'none';
            document.getElementById('liveCarouselTrack').innerHTML = '';
            document.getElementById('liveDesktopList').innerHTML = '';
            return;
        }

        emptyState.style.display = 'none';
        slotBar.style.display = '';
        banner.textContent = r.date + '  실전 시황체크 결과  ' + _liveAllPicks.length + '건';
        banner.style.display = '';

        _liveActiveSlot = _getCurrentLiveSlot();
        _highlightLiveSlotBtn(_liveActiveSlot);
        _liveCarouselIdx = 0;
        Object.keys(_liveChartLoaded).forEach(k => delete _liveChartLoaded[k]);
        _renderLive();
        loadReentrySignals();
    } catch (e) {
        showToast('로드 실패', 'error');
        console.error(e);
    }
}

function filterLiveSlot(slot) {
    _liveActiveSlot = slot;
    _highlightLiveSlotBtn(slot);
    _liveCarouselIdx = 0;
    Object.keys(_liveChartLoaded).forEach(k => delete _liveChartLoaded[k]);
    _renderLive();
}

function _highlightLiveSlotBtn(slot) {
    document.querySelectorAll('#liveSlotBar .slot-btn').forEach(b =>
        b.classList.toggle('active', b.dataset.slot === slot));
}

function _renderLive() {
    _liveSlotPicks = _liveActiveSlot === 'all'
        ? _liveAllPicks
        : _liveAllPicks.filter(p => p._slotKey === _liveActiveSlot);

    const isMobile = window.innerWidth <= 768;
    const carouselWrapper = document.getElementById('liveCarouselWrapper');
    const desktopList = document.getElementById('liveDesktopList');

    if (isMobile) {
        carouselWrapper.style.display = '';
        desktopList.style.display = 'none';
        renderLiveCarousel();
    } else {
        carouselWrapper.style.display = 'none';
        desktopList.style.display = '';
        renderLiveDesktop();
    }
}

function renderLiveCarousel() {
    const track = document.getElementById('liveCarouselTrack');
    const dots = document.getElementById('liveCarouselDots');

    if (!_liveSlotPicks.length) {
        track.innerHTML = '<div class="live-carousel-slide"><p class="empty-state" style="padding:32px 16px;">해당 슬롯에 추천 종목이 없습니다.</p></div>';
        dots.innerHTML = '';
        return;
    }

    track.innerHTML = _liveSlotPicks.map(p =>
        `<div class="live-carousel-slide">${renderLivePickCard(p)}</div>`
    ).join('');

    dots.innerHTML = _liveSlotPicks.map((_, i) =>
        `<span class="live-carousel-dot${i === _liveCarouselIdx ? ' active' : ''}" onclick="liveCarouselGoTo(${i})"></span>`
    ).join('');

    _updateCarouselPosition();
    // 첫 번째 카드 차트 지연 로드
    setTimeout(() => _loadLiveCardChart(_liveCarouselIdx), 100);
}

function renderLiveDesktop() {
    const list = document.getElementById('liveDesktopList');
    if (!_liveSlotPicks.length) {
        list.innerHTML = '<p class="empty-state">해당 슬롯에 추천 종목이 없습니다.</p>';
        return;
    }
    list.innerHTML = _liveSlotPicks.map(p => renderLivePickCard(p)).join('');
    // 데스크탑은 모든 카드 차트 순차 로드
    _liveSlotPicks.forEach((p, i) => {
        setTimeout(() => _loadLiveCardChart(i), i * 300);
    });
}

function renderLivePickCard(p) {
    const confClass = p.confidence === 'H' ? 'bt-conf-h' : p.confidence === 'M' ? 'bt-conf-m' : 'bt-conf-l';
    const tagLabel = { ss_up: '🚀 상한가', vi: '⚡ VI', ss: '📈 급등', news: '📰 뉴스' }[p.tag_type] || (p.tag_type || '');
    const priceStr = p.price_at_slot ? Number(p.price_at_slot).toLocaleString() + '원' : '';
    const slotDisplay = p._slotKey || p.slot_time || p._runKst || '';

    // siwhang_results: news_summary + watchlist_match 활용
    const wlMatch = (() => {
        if (!p.watchlist_match) return [];
        try { return typeof p.watchlist_match === 'string' ? JSON.parse(p.watchlist_match) : p.watchlist_match; }
        catch(e) { return []; }
    })();
    const relatedStocks = (() => {
        if (!p.related_stocks) return [];
        try { return typeof p.related_stocks === 'string' ? JSON.parse(p.related_stocks) : p.related_stocks; }
        catch(e) { return []; }
    })();

    const sourcesHtml = (() => {
        if (!p.sources_json) return '';
        try {
            const srcs = JSON.parse(p.sources_json);
            if (!srcs || !srcs.length) return '';
            return `<div class="bt-sources">${srcs.slice(0,3).map(s =>
                `<div class="bt-source-item"><span class="bt-src-type">${s.type||''}</span><span class="bt-src-text">${escapeHtml((s.text||'').substring(0,60))}${(s.text||'').length>60?'…':''}</span></div>`
            ).join('')}</div>`;
        } catch(e) { return ''; }
    })();

    const wlHtml = wlMatch.length
        ? `<div class="live-wl-match">📌 관심종목 매칭: ${wlMatch.map(w => `<span class="live-wl-tag">${escapeHtml(typeof w === 'string' ? w : w.name || '')}</span>`).join('')}</div>`
        : '';
    const relatedHtml = relatedStocks.length
        ? `<div class="live-related">연관주: ${relatedStocks.slice(0,5).map(s => `<span class="live-related-tag">${escapeHtml(s)}</span>`).join('')}</div>`
        : '';

    return `
<div class="bt-pick-card live-pick-card" id="liveCard_${p.id}">
    <div class="bt-pick-header">
        <span class="bt-pick-name">${escapeHtml(p.stock_name)}${p.stock_code ? ` <small style="color:#868e96">${p.stock_code}</small>` : ''}</span>
        ${slotDisplay ? `<span class="bt-pick-slot">${slotDisplay}</span>` : ''}
        ${tagLabel ? `<span class="tag-badge tag-${p.tag_type||'ss'}">${tagLabel}</span>` : ''}
        ${p.confidence ? `<span class="${confClass}" style="font-weight:700;font-size:13px;">[${p.confidence}]</span>` : ''}
    </div>
    <div class="bt-pick-meta">
        ${p.theme ? `<span>📌 ${escapeHtml(p.theme)}</span>` : ''}
        ${priceStr ? `<span>추천가 <strong>${priceStr}</strong></span>` : ''}
    </div>
    ${wlHtml}
    ${p.catalyst ? `<div class="bt-catalyst"><span class="bt-catalyst-label">촉매</span>${escapeHtml(p.catalyst)}</div>` : ''}
    ${p.news_summary ? `<div class="bt-catalyst"><span class="bt-catalyst-label">뉴스</span>${escapeHtml(p.news_summary)}</div>` : ''}
    ${p.analysis_text ? `<div class="bt-pick-analysis">${escapeHtml(p.analysis_text)}</div>` : ''}
    ${relatedHtml}
    ${sourcesHtml}
    ${p.stock_code ? `
    <div id="liveChartContainer_${p.id}" class="live-chart-container" style="display:none;">
        <div class="live-chart-loading">차트 로딩 중...</div>
        <canvas id="liveChart_${p.id}"></canvas>
    </div>
    <div class="live-register-row">
        <div class="live-register-field">
            <label>매수가</label>
            <input type="number" id="liveBuyPrice_${p.id}" placeholder="${p.price_at_slot ? Math.round(p.price_at_slot) : ''}">
        </div>
        <div class="live-register-field">
            <label>예산(만원)</label>
            <input type="number" id="liveBudget_${p.id}" placeholder="100">
        </div>
        <button class="btn btn-sm btn-success" onclick="liveRegisterMode2(${p.id})">📊 Mode2 등록</button>
    </div>` : '<div class="live-register-row"><span style="color:#868e96;font-size:12px">종목코드 없음 — Mode2 등록 불가</span></div>'}
</div>`;
}

function liveCarouselMove(dir) {
    const max = _liveSlotPicks.length - 1;
    _liveCarouselIdx = Math.max(0, Math.min(max, _liveCarouselIdx + dir));
    _updateCarouselPosition();
    _updateCarouselDots();
    setTimeout(() => _loadLiveCardChart(_liveCarouselIdx), 50);
}

function liveCarouselGoTo(idx) {
    _liveCarouselIdx = idx;
    _updateCarouselPosition();
    _updateCarouselDots();
    setTimeout(() => _loadLiveCardChart(idx), 50);
}

function _updateCarouselPosition() {
    const track = document.getElementById('liveCarouselTrack');
    if (track) track.style.transform = `translateX(-${_liveCarouselIdx * 100}%)`;
}

function _updateCarouselDots() {
    document.querySelectorAll('.live-carousel-dot').forEach((d, i) =>
        d.classList.toggle('active', i === _liveCarouselIdx));
}

async function _loadLiveCardChart(idx) {
    if (idx >= _liveSlotPicks.length) return;
    const p = _liveSlotPicks[idx];
    if (!p.stock_code) return;
    if (_liveChartLoaded[p.id]) return;

    const containerId = `liveChartContainer_${p.id}`;
    const canvasId = `liveChart_${p.id}`;
    const container = document.getElementById(containerId);
    if (!container) return;

    container.style.display = '';
    try {
        const res = await fetch('/api/test/daily-chart', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: p.stock_code })
        });
        const result = await res.json();
        if (result.success) {
            const loadingEl = container.querySelector('.live-chart-loading');
            if (loadingEl) loadingEl.style.display = 'none';
            _liveChartLoaded[p.id] = true;
            drawCandlestickChart(result.data, canvasId, containerId);
        } else {
            container.querySelector('.live-chart-loading').textContent = '차트 조회 실패';
        }
    } catch (e) {
        const el = container.querySelector('.live-chart-loading');
        if (el) el.textContent = '차트 조회 실패';
    }
}

async function liveRegisterMode2(pickId) {
    const pick = _liveAllPicks.find(p => p.id === pickId);
    if (!pick || !pick.stock_code) { showToast('종목코드 없음', 'error'); return; }

    const buyPriceInput = document.getElementById(`liveBuyPrice_${pickId}`);
    const budgetInput = document.getElementById(`liveBudget_${pickId}`);
    const buyPrice = parseFloat(buyPriceInput?.value) || pick.price_at_slot || null;
    const budgetMan = parseFloat(budgetInput?.value) || null;

    if (!budgetMan) { showToast('예산(만원) 입력 필요', 'error'); return; }

    const payload = {
        code: pick.stock_code,
        name: pick.stock_name,
        buy_target_price: buyPrice ? Math.round(buyPrice) : 0,
        budget: budgetMan * 10000,
        notify_only: true,
        support_1_price: 0,
        support_2_price: 0,
        resistance_1_price: 0,
        resistance_2_price: 0,
        polling_interval: 60,
    };
    try {
        const res = await fetch('/api/mode2/watchers', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const r = await res.json();
        if (r.success) {
            showToast(`📊 Mode2 등록: ${pick.stock_name}`, 'success');
            const btn = document.querySelector(`#liveCard_${pickId} .btn-success`);
            if (btn) { btn.textContent = '✅ 등록됨'; btn.disabled = true; }
        } else {
            showToast(r.error || '등록 실패', 'error');
        }
    } catch (e) { showToast('등록 실패', 'error'); }
}

async function requestLiveAnalysis() {
    const btn = document.getElementById('liveAnalysisBtn');
    btn.disabled = true;
    btn.textContent = '⏳ 요청 중...';
    try {
        const res = await fetch('/api/analysis/request', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
        });
        const r = await res.json();
        if (r.success) {
            showToast('분석 요청 전송 — poll_trigger.py가 실행합니다', 'success');
            btn.textContent = '✓ 요청됨';
            setTimeout(() => { btn.disabled = false; btn.textContent = '▶ 지금 분석'; }, 60000);
        } else {
            showToast('요청 실패', 'error');
            btn.disabled = false; btn.textContent = '▶ 지금 분석';
        }
    } catch (e) {
        showToast('요청 실패', 'error');
        btn.disabled = false; btn.textContent = '▶ 지금 분석';
    }
}

// ─── 재진입 체크 (Seeking Signal Type3) ──────────────────────────────

async function checkReentry() {
    const stockCode = document.getElementById('reStockCode').value.trim();
    const stockName = document.getElementById('reStockName').value.trim();
    const buyPrice = parseFloat(document.getElementById('reBuyPrice').value);
    const exitPrice = parseFloat(document.getElementById('reExitPrice').value);
    const exitDate = document.getElementById('reExitDate').value.trim();
    const backtestMode = document.getElementById('reBacktestMode')?.checked || false;
    const resultEl = document.getElementById('reentryResult');

    if (!stockCode || !buyPrice || !exitPrice) {
        showToast('종목코드, 매수가, 익절가 필수', 'error');
        return;
    }

    resultEl.innerHTML = `<p style="color:#868e96">${backtestMode ? '히스토리컬 백테스트 분석 중...' : '분석 중...'}</p>`;
    try {
        const res = await fetch('/api/seeking-signal/reentry-check', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stock_code: stockCode, buy_price: buyPrice, exit_price: exitPrice, exit_date: exitDate, backtest_mode: backtestMode }),
        });
        const r = await res.json();
        if (!r.success) { resultEl.innerHTML = `<p style="color:#e74c3c">${r.error}</p>`; return; }
        const d = r.data;
        const signals = d.signals || [];
        if (!signals.length) {
            resultEl.innerHTML = `<p style="color:#868e96; padding: 12px 0;">${backtestMode ? '백테스트 기간 내 시그널 없음' : '현재 시그널 없음 — 계속 모니터링'}</p>`;
            return;
        }
        const typeColor = {
            A: '#3498db', B: '#f39c12',
            C1: '#2ecc71', C2: '#27ae60', C3: '#1a8a4a',
            OVERHEAT: '#e74c3c',
        };
        const typeLabel = {
            A: 'Type A', B: 'Type B',
            C1: 'Type C1', C2: 'Type C2', C3: 'Type C3',
            OVERHEAT: '🚫 과열',
        };

        function renderSignalCard(s, compact) {
            if (s.type === 'OVERHEAT') {
                return `<div style="padding:6px 10px;background:#2d1a1a;border-left:3px solid #e74c3c;margin-bottom:6px;border-radius:4px;font-size:12px;color:#e74c3c;">
                    🚫 ${s.date} — ${s.desc}
                </div>`;
            }
            const overheatBadge = s.overheat_warning
                ? `<span style="background:#c0392b;color:#fff;font-size:11px;padding:1px 6px;border-radius:3px;font-weight:600;">⚠️ 단기과열</span>` : '';
            const entryLine = s.entry_price
                ? `<div class="reentry-entry" style="font-size:13px;">추천 진입가: <strong>${s.entry_price.toLocaleString()}원</strong></div>` : '';
            const noteLine = s.note ? `<div style="font-size:12px;color:#868e96;margin-top:2px;">${s.note}</div>` : '';
            const overheatLine = s.overheat_msg ? `<div style="font-size:12px;color:#e74c3c;margin-top:4px;">${s.overheat_msg}</div>` : '';
            return `<div class="reentry-signal-card" style="margin-bottom:8px;">
                <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;flex-wrap:wrap;">
                    <span class="reentry-type-badge" style="background:${typeColor[s.type]||'#95a5a6'}">${typeLabel[s.type]||s.type}</span>
                    <span class="reentry-confidence">${s.confidence||'M'}</span>
                    ${compact ? `<span style="font-size:12px;color:#adb5bd;">${s.date||''}</span>` : ''}
                    ${overheatBadge}
                </div>
                <div class="reentry-desc" style="font-size:13px;">${s.desc}</div>
                ${entryLine}${noteLine}${overheatLine}
            </div>`;
        }

        if (backtestMode) {
            const realSignals = signals.filter(s => s.type !== 'OVERHEAT');
            const overheatDayStr = d.overheat_date ? ` | 폭등일: ${d.overheat_date}` : '';
            const summary = `<div style="font-size:13px;color:#868e96;margin-bottom:12px;">
                📊 백테스트 결과: 실시그널 <strong style="color:#fff">${realSignals.length}개</strong> (${d.bars_analyzed||'-'}봉 분석${overheatDayStr})
            </div>`;
            resultEl.innerHTML = summary + signals.map(s => renderSignalCard(s, true)).join('');
        } else {
            const overheatDayStr = d.overheat_date ? `<div style="font-size:12px;color:#868e96;margin-bottom:8px;">감지된 폭등일: ${d.overheat_date}</div>` : '';
            resultEl.innerHTML = overheatDayStr + signals.map(s => renderSignalCard(s, false)).join('');
        }
    } catch (e) {
        resultEl.innerHTML = `<p style="color:#e74c3c">오류: ${e.message}</p>`;
    }
}

async function saveTradeWatchlist() {
    const stockCode = document.getElementById('reStockCode').value.trim();
    const stockName = document.getElementById('reStockName').value.trim();
    const buyPrice = parseFloat(document.getElementById('reBuyPrice').value);
    const buyDate = document.getElementById('reBuyDate').value.trim();
    const exitPrice = parseFloat(document.getElementById('reExitPrice').value);
    const exitDate = document.getElementById('reExitDate').value.trim();

    if (!stockCode || !stockName || !buyPrice || !exitPrice) {
        showToast('종목코드, 종목명, 매수가, 익절가 필수', 'error');
        return;
    }
    await _registerStyle3Item({ code: stockCode, name: stockName, buyPrice, buyDate, exitPrice, exitDate });
    loadTradeWatchlist();
}

async function _registerStyle3Item({ code, name, buyPrice, buyDate, exitPrice, exitDate }) {
    try {
        // 1. trade_watchlist 등록
        const res = await fetch('/api/trade-watchlist', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stock_code: code, stock_name: name, buy_price: buyPrice, buy_date: buyDate, exit_price: exitPrice, exit_date: exitDate }),
        });
        const r = await res.json();
        if (!r.success) { showToast('감시 등록 실패', 'error'); return false; }

        // 2. Mode2 섹션 자동 생성/조회
        const today = new Date().toISOString().slice(0, 10);
        const sectionName = `${today} Style3 발라먹기`;
        const sectionsRes = await fetch('/api/mode2/sections', { credentials: 'same-origin' });
        const sectionsData = await sectionsRes.json();
        let sectionId = null;
        const existing = (sectionsData.sections || []).find(s => s.name === sectionName);
        if (existing) {
            sectionId = existing.id;
        } else {
            const createRes = await fetch('/api/mode2/sections', {
                method: 'POST', credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: sectionName }),
            });
            const createData = await createRes.json();
            sectionId = createData.id;
        }

        // 3. Mode2 watcher 등록 (support_1_price = 익절가의 97% 초기값, 실제 C2 계산은 price_monitor에서)
        const supportPrice = Math.round(exitPrice * 0.97);
        await fetch('/api/mode2/watchers', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code, name, buy_target_price: Math.round(buyPrice * 1.01),
                budget: 0, polling_interval: 180, notify_only: true,
                section: sectionId, support_1_price: supportPrice,
                notes: `Style3 발라먹기 | 매수가:${buyPrice} 익절가:${exitPrice} 익절일:${exitDate}`,
            }),
        });

        showToast(`${name} Style3 감시 등록 완료`, 'success');
        return true;
    } catch (e) {
        showToast('오류: ' + e.message, 'error');
        return false;
    }
}

async function loadTradeWatchlist() {
    const container = document.getElementById('tradeWatchlistContainer');
    if (!container) return;
    try {
        const res = await fetch('/api/trade-watchlist', { credentials: 'same-origin' });
        const r = await res.json();
        const items = r.data || [];
        if (!items.length) {
            container.innerHTML = '<p style="color:#868e96;font-size:14px;">등록된 감시 종목 없음</p>';
            return;
        }
        const today = new Date();
        container.innerHTML = `<table class="reentry-watchlist-table">
            <thead><tr><th>종목</th><th>매수가</th><th>익절가</th><th>익절일</th><th>등록</th><th>상태</th><th></th></tr></thead>
            <tbody>${items.map(w => {
                const createdAt = w.created_at ? new Date(w.created_at) : null;
                const daysSince = createdAt ? Math.floor((today - createdAt) / 86400000) + 1 : '-';
                const dayLabel = typeof daysSince === 'number' ? `등록 ${daysSince}일차` : '-';
                return `
                <tr>
                    <td><strong>${w.stock_name}</strong><br><small style="color:#868e96">${w.stock_code}</small></td>
                    <td>${(w.buy_price||0).toLocaleString()}원</td>
                    <td>${(w.exit_price||0).toLocaleString()}원</td>
                    <td>${w.exit_date||'-'}</td>
                    <td style="font-size:12px;color:#868e96;">${dayLabel}</td>
                    <td><span class="reentry-status-${w.status}">${w.status}</span></td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="deleteTradeWatchlist(${w.id})">삭제</button>
                    </td>
                </tr>`;
            }).join('')}</tbody>
        </table>`;
    } catch (e) {
        container.innerHTML = '<p style="color:#e74c3c">로드 실패</p>';
    }
}

async function deleteTradeWatchlist(id) {
    if (!confirm('감시 목록에서 삭제할까요?')) return;
    const res = await fetch(`/api/trade-watchlist/${id}`, { method: 'DELETE', credentials: 'same-origin' });
    const r = await res.json();
    if (r.success) loadTradeWatchlist();
}

// ─── Style3 벌크 등록 + 탭 전환 ──────────────────────────────────────

function switchReentryTab(tab) {
    document.getElementById('reTabSingleContent').style.display = tab === 'single' ? '' : 'none';
    document.getElementById('reTabBulkContent').style.display = tab === 'bulk' ? '' : 'none';
    document.getElementById('reTabSingle').classList.toggle('btn-primary', tab === 'single');
    document.getElementById('reTabSingle').classList.toggle('btn-secondary', tab !== 'single');
    document.getElementById('reTabBulk').classList.toggle('btn-primary', tab === 'bulk');
    document.getElementById('reTabBulk').classList.toggle('btn-secondary', tab !== 'bulk');
}

function parseBulkReentry() {
    const raw = document.getElementById('reBulkInput').value.trim();
    const preview = document.getElementById('reBulkPreview');
    if (!raw) { preview.innerHTML = ''; return; }

    const lines = raw.split('\n').map(l => l.trim()).filter(l => l);
    const items = [];
    const errors = [];

    lines.forEach((line, idx) => {
        const parts = line.split(',').map(p => p.trim());
        if (parts.length < 6) { errors.push(`줄 ${idx+1}: 필드 부족 (${parts.length}개)`); return; }
        const [code, name, buyDate, buyPrice, exitDate, exitPrice] = parts;
        if (!/^\d{5,6}$/.test(code)) { errors.push(`줄 ${idx+1}: 종목코드 오류 (${code})`); return; }
        if (!parseFloat(buyPrice) || !parseFloat(exitPrice)) { errors.push(`줄 ${idx+1}: 가격 오류`); return; }
        items.push({ code, name, buyDate, buyPrice: parseFloat(buyPrice), exitDate, exitPrice: parseFloat(exitPrice) });
    });

    if (errors.length) {
        preview.innerHTML = `<div style="color:#e74c3c;font-size:13px;margin-bottom:8px;">${errors.join('<br>')}</div>`;
    }

    if (!items.length) { preview.innerHTML += '<p style="color:#868e96;font-size:13px;">유효한 항목 없음</p>'; return; }

    preview.innerHTML += `
        <div style="font-size:13px;color:#495057;margin-bottom:8px;">${items.length}건 파싱 완료</div>
        <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:12px;">
            <thead><tr style="background:#f8f9fa;">
                <th style="padding:6px;border:1px solid #dee2e6;">종목</th>
                <th style="padding:6px;border:1px solid #dee2e6;">매수가</th>
                <th style="padding:6px;border:1px solid #dee2e6;">매수일</th>
                <th style="padding:6px;border:1px solid #dee2e6;">익절가</th>
                <th style="padding:6px;border:1px solid #dee2e6;">익절일</th>
                <th style="padding:6px;border:1px solid #dee2e6;"></th>
            </tr></thead>
            <tbody>${items.map((it, i) => `
                <tr id="bulkRow${i}">
                    <td style="padding:6px;border:1px solid #dee2e6;"><strong>${it.name}</strong> <small style="color:#868e96">${it.code}</small></td>
                    <td style="padding:6px;border:1px solid #dee2e6;text-align:right;">${it.buyPrice.toLocaleString()}원</td>
                    <td style="padding:6px;border:1px solid #dee2e6;">${it.buyDate}</td>
                    <td style="padding:6px;border:1px solid #dee2e6;text-align:right;">${it.exitPrice.toLocaleString()}원</td>
                    <td style="padding:6px;border:1px solid #dee2e6;">${it.exitDate}</td>
                    <td style="padding:6px;border:1px solid #dee2e6;">
                        <button class="btn btn-sm btn-primary" onclick="registerBulkItem(${i})">감시 등록</button>
                    </td>
                </tr>
            `).join('')}</tbody>
        </table>
        <button class="btn btn-primary" onclick="registerAllBulkItems()">📋 전체 등록</button>
    `;
    window._reBulkItems = items;
}

async function registerBulkItem(idx) {
    const items = window._reBulkItems || [];
    const it = items[idx];
    if (!it) return;
    const ok = await _registerStyle3Item({ code: it.code, name: it.name, buyPrice: it.buyPrice, buyDate: it.buyDate, exitPrice: it.exitPrice, exitDate: it.exitDate });
    if (ok) {
        const row = document.getElementById('bulkRow' + idx);
        if (row) row.style.opacity = '0.4';
        loadTradeWatchlist();
    }
}

async function registerAllBulkItems() {
    const items = window._reBulkItems || [];
    if (!items.length) return;
    let ok = 0;
    for (let i = 0; i < items.length; i++) {
        const it = items[i];
        const success = await _registerStyle3Item({ code: it.code, name: it.name, buyPrice: it.buyPrice, buyDate: it.buyDate, exitPrice: it.exitPrice, exitDate: it.exitDate });
        if (success) { ok++; const row = document.getElementById('bulkRow' + i); if (row) row.style.opacity = '0.4'; }
    }
    showToast(`${ok}/${items.length}건 등록 완료`, 'success');
    loadTradeWatchlist();
}

// ─── Mode2 날짜 필터 ──────────────────────────────────────────────────

function applyMode2DateFilter() {
    const filterDate = document.getElementById('mode2DateFilter')?.value || '';
    document.querySelectorAll('.mode2-section-card').forEach(card => {
        const sectionDate = card.dataset.sectionDate || '';
        if (!filterDate || sectionDate === filterDate) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

function clearMode2DateFilter() {
    const el = document.getElementById('mode2DateFilter');
    if (el) el.value = '';
    document.querySelectorAll('.mode2-section-card').forEach(card => {
        card.style.display = '';
    });
}

// ─── 실전페이지 재진입 시그널 ─────────────────────────────────────────

async function loadReentrySignals() {
    const container = document.getElementById('liveReentryList');
    if (!container) return;
    const today = new Date().toISOString().slice(0, 10);
    try {
        const res = await fetch(`/api/reentry/signals?date=${today}`, { credentials: 'same-origin' });
        const r = await res.json();
        const signals = r.data || [];
        if (!signals.length) {
            container.innerHTML = '<p style="color:#868e96;font-size:14px;text-align:center;padding:16px;">오늘 재진입 시그널 없음</p>';
            return;
        }
        const typeColor = { A: '#3498db', B: '#f39c12', C: '#27ae60' };
        container.innerHTML = signals.map(s => `
            <div class="reentry-signal-card" style="margin-bottom:12px;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                    <strong>${s.stock_name}</strong>
                    <span class="reentry-type-badge" style="background:${typeColor[s.signal_type]||'#95a5a6'}">Type ${s.signal_type}</span>
                    <span class="reentry-confidence">${s.confidence||'M'}</span>
                    ${s.ss_matched ? '<span style="font-size:11px;background:#e8f5e9;color:#27ae60;padding:2px 6px;border-radius:4px;">SS감지</span>' : ''}
                </div>
                <div style="font-size:13px;color:#495057;margin-bottom:4px;">${s.reason||''}</div>
                <div style="font-size:13px;">
                    추천 진입가: <strong>${(s.entry_price_suggestion||0).toLocaleString()}원</strong>
                    &nbsp;|&nbsp; 매수가: ${(s.buy_price||0).toLocaleString()}원
                    &nbsp;|&nbsp; 익절가: ${(s.exit_price||0).toLocaleString()}원
                </div>
                ${s.stock_code ? `<div style="margin-top:8px;">
                    <button class="btn btn-sm btn-success" onclick="liveRegisterMode2FromReentry(${JSON.stringify(s).replace(/"/g,'&quot;')})">📊 Mode2 등록</button>
                </div>` : ''}
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<p style="color:#e74c3c">로드 실패</p>';
    }
}

async function liveRegisterMode2FromReentry(signal) {
    const buyPrice = signal.entry_price_suggestion || signal.buy_price;
    const name = signal.stock_name;
    const code = signal.stock_code;
    if (!code) { showToast('종목코드 없음', 'error'); return; }

    const payload = {
        code, name,
        buy_target_price: buyPrice,
        notify_only: true,
        tag: `재진입 Type${signal.signal_type}`,
    };
    try {
        const res = await fetch('/api/mode2/watchers', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const r = await res.json();
        if (r.success || r.code === code) {
            showToast(`${name} Mode2 등록 완료`, 'success');
        } else {
            showToast('등록 실패: ' + (r.error || ''), 'error');
        }
    } catch (e) {
        showToast('오류: ' + e.message, 'error');
    }
}

// 캐로셀 터치 스와이프
(function() {
    let _touchStartX = 0;
    document.addEventListener('touchstart', e => {
        if (!e.target.closest('#liveCarouselWrapper')) return;
        _touchStartX = e.touches[0].clientX;
    }, { passive: true });
    document.addEventListener('touchend', e => {
        if (!e.target.closest('#liveCarouselWrapper')) return;
        const dx = e.changedTouches[0].clientX - _touchStartX;
        if (Math.abs(dx) > 40) liveCarouselMove(dx < 0 ? 1 : -1);
    }, { passive: true });
})();
