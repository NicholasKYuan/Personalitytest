/* ============================================================
   星耀启程 · 人格测评 — 交互逻辑
   纯原生 JS，无框架依赖。管理三步骤流程。
   ============================================================ */

(function () {
    'use strict';

    /* ---------- 类别/领域中文映射 ---------- */
    var CATEGORY_LABELS = {
        'interpersonal-relationship': '人际交往',
        'decision-making': '决策方式',
        'stress-response': '压力应对',
        'motivation-value': '动力与价值观',
        'learning-cognition': '学习与认知',
        'work-career': '工作与职业',
        'emotion-self': '情绪与自我',
        'action-habit': '行为习惯',
        'future-vision': '未来展望',
        'conflict-choice': '冲突与选择'
    };

    var GALLUP_DOMAIN_LABELS = {
        'executing': '执行力',
        'influencing': '影响力',
        'relationship_building': '关系建立',
        'strategic_thinking': '战略思维'
    };

    var GALLUP_THEME_LABELS = {
        'achiever': '成就', 'activator': '行动', 'adaptability': '适应',
        'analytical': '分析', 'arranger': '统筹', 'belief': '信仰',
        'command': '统率', 'communication': '沟通', 'competition': '竞争',
        'connectedness': '关联', 'context': '回顾', 'consistency': '公平',
        'deliberative': '审慎', 'developer': '伯乐', 'discipline': '纪律',
        'empathy': '体谅', 'focus': '专注', 'futuristic': '前瞻',
        'harmony': '和谐', 'ideation': '理念', 'includer': '包容',
        'individualization': '个别', 'input': '搜集', 'intellection': '思维',
        'learner': '学习', 'maximizer': '完美', 'positivity': '积极',
        'relator': '交往', 'responsibility': '责任', 'restorative': '排难',
        'self-assurance': '自信', 'significance': '追求', 'strategic': '战略',
        'woo': '取悦'
    };

    /* ---------- 全局状态 ---------- */
    var state = {
        step: 1,
        sessionId: null,
        questions: [],          // 题目列表
        currentIndex: 0,        // 当前题目索引
        answers: {},             // { questionId: optionIndex }
        results: null,          // POST /api/submit 返回结果
        analysisSections: null, // POST /api/analyze 返回章节
        isLoading: false,
        autoAdvanceTimer: null  // 自动跳题定时器
    };

    /* ---------- DOM 缓存 ---------- */
    var DOM = {};

    function cacheDOM() {
        DOM.stepProfile = document.getElementById('step-profile');
        DOM.stepQuiz = document.getElementById('step-quiz');
        DOM.stepResults = document.getElementById('step-results');

        // 表单
        DOM.form = document.getElementById('profile-form');
        DOM.btnStart = document.getElementById('btn-start');

        // 答题
        DOM.questionLoading = document.getElementById('question-loading');
        DOM.questionBody = document.getElementById('question-body');
        DOM.questionCategory = document.getElementById('question-category');
        DOM.questionStem = document.getElementById('question-stem');
        DOM.optionsGrid = document.getElementById('options-grid');
        DOM.btnPrev = document.getElementById('btn-prev');
        DOM.btnSubmitQuiz = document.getElementById('btn-submit-quiz');
        DOM.progressText = document.getElementById('progress-text');
        DOM.progressPercent = document.getElementById('progress-percent');
        DOM.progressFill = document.getElementById('progress-fill');

        // 结果
        DOM.resultsLoading = document.getElementById('results-loading');
        DOM.resultsContent = document.getElementById('results-content');
        DOM.enneagramNumber = document.getElementById('enneagram-number');
        DOM.enneagramName = document.getElementById('enneagram-name');
        DOM.mbtiType = document.getElementById('mbti-type');
        DOM.hollandCode = document.getElementById('holland-code');
        DOM.gallupDomain = document.getElementById('gallup-domain');
        DOM.gallupThemes = document.getElementById('gallup-themes');
        DOM.freeSummaryText = document.getElementById('free-summary-text');

        // 付费
        DOM.paidOverlay = document.getElementById('paid-overlay');
        DOM.btnUnlock = document.getElementById('btn-unlock');
        DOM.analysisLoading = document.getElementById('analysis-loading');
        DOM.analysisContent = document.getElementById('analysis-content');
    }

    /* ============================================================
       API 客户端
       ============================================================ */

    /**
     * 通用 API 调用封装
     */
    function apiCall(url, body) {
        return fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        }).then(function (res) {
            if (!res.ok) {
                return res.json().then(function (err) {
                    var msg = (err && err.detail) ? err.detail : ('请求失败 (' + res.status + ')');
                    throw new Error(msg);
                }).catch(function (parseErr) {
                    if (parseErr instanceof Error && parseErr.message.indexOf('请求失败') === 0) {
                        throw parseErr;
                    }
                    throw new Error('服务器错误 (' + res.status + ')');
                });
            }
            return res.json();
        });
    }

    /**
     * POST /api/session — 创建会话，获取题目
     */
    function createSession(profile) {
        return apiCall('/api/session', profile);
    }

    /**
     * POST /api/submit — 提交答案，获取免费结果
     */
    function submitAnswers(sessionId, answers) {
        return apiCall('/api/submit', {
            session_id: sessionId,
            answers: answers
        });
    }

    /**
     * POST /api/analyze — 获取深度分析
     */
    function getAnalysis(sessionId) {
        return apiCall('/api/analyze', {
            session_id: sessionId
        });
    }

    /* ============================================================
       Step 导航
       ============================================================ */

    function showStep(stepNum) {
        state.step = stepNum;

        [DOM.stepProfile, DOM.stepQuiz, DOM.stepResults].forEach(function (el) {
            el.classList.remove('step--active');
        });

        if (stepNum === 1) {
            DOM.stepProfile.classList.add('step--active');
        } else if (stepNum === 2) {
            DOM.stepQuiz.classList.add('step--active');
        } else if (stepNum === 3) {
            DOM.stepResults.classList.add('step--active');
        }

        // 滚动到顶部
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    /* ============================================================
       Step 1: 个人信息表单
       ============================================================ */

    function setupProfileForm() {
        DOM.form.addEventListener('submit', function (e) {
            e.preventDefault();
            handleFormSubmit();
        });
    }

    /**
     * 验证表单字段
     * @returns {Object} { valid: boolean, errors: { fieldName: string } }
     */
    function validateForm() {
        var errors = {};

        // 年龄
        var ageVal = document.getElementById('field-age').value.trim();
        var age = parseInt(ageVal, 10);
        if (!ageVal || isNaN(age) || age < 12 || age > 80) {
            errors.age = '请输入有效的年龄（12-80岁）';
        }

        // 当前身份
        var role = document.getElementById('field-role').value;
        if (!role) {
            errors.role = '请选择你的当前身份';
        }

        // 测评目的
        var purpose = document.getElementById('field-purpose').value;
        if (!purpose) {
            errors.purpose = '请选择测评目的';
        }

        return { valid: Object.keys(errors).length === 0, errors: errors };
    }

    /**
     * 显示/清除表单错误
     */
    function showFormErrors(errors) {
        // 清除所有旧错误
        ['age', 'role', 'purpose'].forEach(function (field) {
            var el = document.getElementById('error-' + field);
            var input = document.getElementById('field-' + field);
            if (el) el.textContent = '';
            if (input) input.classList.remove('form-input--error');
        });

        // 显示新错误
        Object.keys(errors).forEach(function (field) {
            var el = document.getElementById('error-' + field);
            var input = document.getElementById('field-' + field);
            if (el) el.textContent = errors[field];
            if (input) input.classList.add('form-input--error');
        });
    }

    /**
     * 收集表单数据
     */
    function getProfileData() {
        var data = {
            age: parseInt(document.getElementById('field-age').value.trim(), 10),
            role: document.getElementById('field-role').value,
            purpose: document.getElementById('field-purpose').value
        };

        // 可选字段：只有非空才发送
        var name = document.getElementById('field-name').value.trim();
        if (name) data.name = name;

        var gender = document.getElementById('field-gender').value;
        if (gender) data.gender = gender;

        var currentState = document.getElementById('field-current-state').value;
        if (currentState) data.current_state = currentState;

        var decisionHorizon = document.getElementById('field-decision-horizon').value;
        if (decisionHorizon) data.decision_horizon = decisionHorizon;

        var birthDate = document.getElementById('field-birth-date').value;
        if (birthDate) data.birth_date = birthDate;

        return data;
    }

    /**
     * 表单提交处理
     */
    function handleFormSubmit() {
        // 防止重复提交
        if (state.isLoading) return;

        var validation = validateForm();
        if (!validation.valid) {
            showFormErrors(validation.errors);
            return;
        }

        showFormErrors({}); // 清除错误
        var profile = getProfileData();

        state.isLoading = true;
        setButtonLoading(DOM.btnStart, true);

        createSession(profile)
            .then(function (data) {
                state.sessionId = data.session_id;
                state.questions = data.questions || [];
                state.currentIndex = 0;
                state.answers = {};

                if (state.questions.length === 0) {
                    throw new Error('未获取到测评题目，请重试');
                }

                // 进入答题页
                showStep(2);
                renderQuestion();
            })
            .catch(function (err) {
                showError(err.message || '创建会话失败，请检查网络后重试');
            })
            .finally(function () {
                state.isLoading = false;
                setButtonLoading(DOM.btnStart, false);
            });
    }

    /* ============================================================
       Step 2: 答题页
       ============================================================ */

    /**
     * 渲染当前题目
     */
    function renderQuestion() {
        var question = state.questions[state.currentIndex];
        if (!question) return;

        // 清除自动跳题定时器
        if (state.autoAdvanceTimer) {
            clearTimeout(state.autoAdvanceTimer);
            state.autoAdvanceTimer = null;
        }

        // 显示题目体，隐藏加载态
        DOM.questionLoading.style.display = 'none';
        DOM.questionBody.style.display = 'block';

        // 类别标签
        DOM.questionCategory.textContent = CATEGORY_LABELS[question.category] || question.category;

        // 题型标签
        var scaleBadge = document.getElementById('question-scale');
        if (question.scale === 'likert-4') {
            scaleBadge.textContent = '程度选择';
            scaleBadge.style.display = 'inline-block';
        } else if (question.scale === 'forced-choice') {
            scaleBadge.textContent = '场景选择';
            scaleBadge.style.display = 'inline-block';
        } else {
            scaleBadge.style.display = 'none';
        }

        // 题干
        DOM.questionStem.textContent = question.stem;

        // 选项
        var options = question.options || [];
        var html = '';
        var currentAnswer = state.answers[question.id];
        var isAnswered = typeof currentAnswer === 'number';

        options.forEach(function (opt, idx) {
            var selectedClass = (isAnswered && currentAnswer === idx) ? ' option-btn--selected' : '';
            html += '<button class="option-btn' + selectedClass + '" data-index="' + idx +
                    '" ' + (isAnswered ? '' : '') + '>' +
                    escapeHtml(opt.text) +
                    '</button>';
        });

        DOM.optionsGrid.innerHTML = html;

        // 绑定选项点击事件
        var optionBtns = DOM.optionsGrid.querySelectorAll('.option-btn');
        optionBtns.forEach(function (btn) {
            btn.addEventListener('click', function () {
                var idx = parseInt(this.getAttribute('data-index'), 10);
                handleOptionClick(idx);
            });
        });

        // 更新导航按钮状态
        updateNavButtons();
        updateProgress();
    }

    /**
     * 选项点击处理
     */
    function handleOptionClick(index) {
        // 防止重复点击（已选中同一选项）
        var question = state.questions[state.currentIndex];
        if (state.answers[question.id] === index) return;

        // 保存答案
        state.answers[question.id] = index;

        // 更新选项 UI
        var allBtns = DOM.optionsGrid.querySelectorAll('.option-btn');
        allBtns.forEach(function (btn) {
            btn.classList.remove('option-btn--selected');
        });
        allBtns[index].classList.add('option-btn--selected');

        // 更新导航按钮
        updateNavButtons();
        updateProgress();

        // 自动跳下一题（最后一题不自动跳）
        if (state.currentIndex < state.questions.length - 1) {
            if (state.autoAdvanceTimer) {
                clearTimeout(state.autoAdvanceTimer);
            }
            state.autoAdvanceTimer = setTimeout(function () {
                advanceToNext();
            }, 800);
        } else {
            // 最后一题，显示提交按钮
            DOM.btnSubmitQuiz.style.display = 'inline-flex';
        }
    }

    /**
     * 前进到下一题
     */
    function advanceToNext() {
        if (state.currentIndex < state.questions.length - 1) {
            state.currentIndex++;
            renderQuestion();
        }
    }

    /**
     * 回到上一题
     */
    function goToPrev() {
        if (state.currentIndex > 0) {
            state.currentIndex--;
            // 如果不是最后一题，隐藏提交按钮
            DOM.btnSubmitQuiz.style.display = 'none';
            renderQuestion();
        }
    }

    /**
     * 更新导航按钮状态
     */
    function updateNavButtons() {
        // 上一题按钮
        DOM.btnPrev.disabled = state.currentIndex === 0;

        // 提交按钮：只有最后一题才显示
        if (state.currentIndex === state.questions.length - 1) {
            var currentAnswer = state.answers[state.questions[state.currentIndex].id];
            if (typeof currentAnswer === 'number') {
                DOM.btnSubmitQuiz.style.display = 'inline-flex';
            } else {
                DOM.btnSubmitQuiz.style.display = 'none';
            }
        } else {
            DOM.btnSubmitQuiz.style.display = 'none';
        }
    }

    /**
     * 更新进度条
     */
    function updateProgress() {
        var total = state.questions.length;
        var answered = Object.keys(state.answers).length;
        var current = state.currentIndex + 1;

        DOM.progressText.textContent = '第 ' + current + ' / ' + total + ' 题';
        var pct = Math.max(Math.round((answered / total) * 100), Math.round((current / total) * 100));
        DOM.progressPercent.textContent = pct + '%';
        DOM.progressFill.style.width = pct + '%';
    }

    /**
     * 提交测评答案
     */
    function submitQuiz() {
        if (state.isLoading) return;

        // 验证是否所有题目都已作答
        var unanswered = state.questions.filter(function (q) {
            return typeof state.answers[q.id] !== 'number';
        });

        if (unanswered.length > 0) {
            var msg = unanswered.length === state.questions.length
                ? '请至少回答一道题目后再提交'
                : '还有 ' + unanswered.length + ' 道题目未作答，请完成后提交';
            showError(msg);
            // 跳转到第一道未答题目
            var firstUnansweredIdx = state.questions.findIndex(function (q) {
                return typeof state.answers[q.id] !== 'number';
            });
            if (firstUnansweredIdx >= 0) {
                state.currentIndex = firstUnansweredIdx;
                DOM.btnSubmitQuiz.style.display = 'none';
                renderQuestion();
            }
            return;
        }

        // 构建答案数组
        var answersArray = state.questions.map(function (q) {
            return {
                question_id: q.id,
                option_index: state.answers[q.id]
            };
        });

        state.isLoading = true;
        setButtonLoading(DOM.btnSubmitQuiz, true);

        submitAnswers(state.sessionId, answersArray)
            .then(function (data) {
                state.results = data;
                // 进入结果页
                showStep(3);
                renderResults(data);
            })
            .catch(function (err) {
                showError(err.message || '提交失败，请检查网络后重试');
            })
            .finally(function () {
                state.isLoading = false;
                setButtonLoading(DOM.btnSubmitQuiz, false);
            });
    }

    /**
     * 初始化答题页事件
     */
    function setupQuizEvents() {
        DOM.btnPrev.addEventListener('click', function (e) {
            e.preventDefault();
            goToPrev();
        });

        DOM.btnSubmitQuiz.addEventListener('click', function (e) {
            e.preventDefault();
            if (confirm('确认提交全部答案？提交后将无法修改。')) {
                submitQuiz();
            }
        });

        // 键盘导航
        document.addEventListener('keydown', function (e) {
            if (state.step !== 2) return;
            if (e.key === 'ArrowLeft') {
                e.preventDefault();
                goToPrev();
            } else if (e.key === 'ArrowRight' && state.currentIndex < state.questions.length - 1) {
                e.preventDefault();
                advanceToNext();
            } else if (e.key >= '1' && e.key <= '4') {
                var idx = parseInt(e.key, 10) - 1;
                if (idx < (state.questions[state.currentIndex].options || []).length) {
                    e.preventDefault();
                    handleOptionClick(idx);
                }
            }
        });
    }

    /* ============================================================
       Step 3: 结果页
       ============================================================ */

    /**
     * 渲染免费结果
     */
    function renderResults(data) {
        DOM.resultsLoading.style.display = 'none';
        DOM.resultsContent.style.display = 'block';

        var results = data.results;

        // --- 九型人格 ---
        if (results.enneagram) {
            DOM.enneagramNumber.textContent = results.enneagram.main_type + '号';
            DOM.enneagramName.textContent = results.enneagram.type_name || '';
        }

        // --- MBTI ---
        if (results.mbti) {
            DOM.mbtiType.textContent = results.mbti.type || '';
        }

        // --- 霍兰德 ---
        if (results.holland) {
            DOM.hollandCode.textContent = results.holland.code || '';
        }

        // --- 盖洛普 ---
        if (results.gallup) {
            var domain = results.gallup.top_domain;
            DOM.gallupDomain.textContent = '优势领域：' + (GALLUP_DOMAIN_LABELS[domain] || domain);

            var themes = (results.gallup.top_themes || []).slice(0, 5);
            var themeLabels = themes.map(function (t) {
                return GALLUP_THEME_LABELS[t] || t;
            });
            DOM.gallupThemes.textContent = 'Top 5 主题：' + themeLabels.join('、');
        }

        // --- 免费简述 ---
        if (data.free_summary) {
            DOM.freeSummaryText.textContent = data.free_summary;
        }

        // --- 付费区 ---
        setupPaySection();
    }

    /**
     * 设置付费区交互
     */
    function setupPaySection() {
        DOM.btnUnlock.addEventListener('click', function () {
            if (state.isLoading) return;
            unlockAnalysis();
        });

        // 下载报告按钮
        var btnDownload = document.getElementById('btn-download-report');
        if (btnDownload) {
            btnDownload.addEventListener('click', function () {
                if (state.sessionId) {
                    window.open('/api/report/' + state.sessionId, '_blank');
                }
            });
        }
    }

    /**
     * 解锁深度分析
     */
    function unlockAnalysis() {
        state.isLoading = true;
        setButtonLoading(DOM.btnUnlock, true);

        // 显示加载状态
        DOM.analysisLoading.style.display = 'block';
        DOM.analysisContent.style.display = 'none';

        getAnalysis(state.sessionId)
            .then(function (data) {
                state.analysisSections = data.sections || [];
                // 隐藏遮罩
                DOM.paidOverlay.classList.add('paid-overlay--hidden');
                // 隐藏加载
                DOM.analysisLoading.style.display = 'none';
                // 渲染分析
                renderAnalysis(state.analysisSections);
                // 显示下载按钮
                var dlSection = document.getElementById('download-section');
                if (dlSection) dlSection.style.display = 'block';
            })
            .catch(function (err) {
                DOM.analysisLoading.style.display = 'none';
                showError(err.message || '获取深度分析失败，请重试');
            })
            .finally(function () {
                state.isLoading = false;
                setButtonLoading(DOM.btnUnlock, false);
            });
    }

    /**
     * 渲染分析结果
     */
    function renderAnalysis(sections) {
        DOM.analysisContent.style.display = 'block';
        DOM.analysisContent.innerHTML = '';

        if (!sections || sections.length === 0) {
            DOM.analysisContent.innerHTML = '<p style="text-align:center;color:var(--color-text-muted);">暂无深度分析内容</p>';
            return;
        }

        sections.forEach(function (section) {
            var sectionEl = document.createElement('div');
            sectionEl.className = 'analysis-section';

            var titleEl = document.createElement('h3');
            titleEl.textContent = section.title;
            sectionEl.appendChild(titleEl);

            var contentEl = document.createElement('div');
            contentEl.innerHTML = markdownToHtml(section.content || '');
            sectionEl.appendChild(contentEl);

            DOM.analysisContent.appendChild(sectionEl);
        });
    }

    /* ============================================================
       Markdown 简易渲染器
       支持：标题(##/###)、段落、加粗(**) 、斜体(*)、
             无序列表(-)、有序列表(1.)、分割线(---)
       ============================================================ */

    function markdownToHtml(md) {
        if (!md) return '';

        // 转义 HTML 特殊字符
        var text = escapeHtml(md);

        // 按行处理
        var lines = text.split('\n');
        var html = '';
        var inList = false;
        var listType = ''; // 'ul' | 'ol'

        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];
            var trimmed = line.trim();

            // 空行处理
            if (!trimmed) {
                if (inList) {
                    html += '</' + listType + '>';
                    inList = false;
                }
                continue;
            }

            // 分割线
            if (/^---+$/.test(trimmed)) {
                if (inList) {
                    html += '</' + listType + '>';
                    inList = false;
                }
                html += '<hr>';
                continue;
            }

            // 标题
            var headingMatch = trimmed.match(/^(#{2,3})\s+(.+)/);
            if (headingMatch) {
                if (inList) {
                    html += '</' + listType + '>';
                    inList = false;
                }
                var level = headingMatch[1].length;
                var headingText = headingMatch[2];
                html += '<h' + level + '>' + applyInlineFormatting(headingText) + '</h' + level + '>';
                continue;
            }

            // 无序列表
            var ulMatch = trimmed.match(/^-\s+(.+)/);
            if (ulMatch) {
                if (!inList || listType !== 'ul') {
                    if (inList) html += '</' + listType + '>';
                    html += '<ul>';
                    inList = true;
                    listType = 'ul';
                }
                html += '<li>' + applyInlineFormatting(ulMatch[1]) + '</li>';
                continue;
            }

            // 有序列表
            var olMatch = trimmed.match(/^\d+[\.\)]\s+(.+)/);
            if (olMatch) {
                if (!inList || listType !== 'ol') {
                    if (inList) html += '</' + listType + '>';
                    html += '<ol>';
                    inList = true;
                    listType = 'ol';
                }
                html += '<li>' + applyInlineFormatting(olMatch[1]) + '</li>';
                continue;
            }

            // 普通段落
            if (inList) {
                html += '</' + listType + '>';
                inList = false;
            }
            html += '<p>' + applyInlineFormatting(trimmed) + '</p>';
        }

        // 关闭未结束的列表
        if (inList) {
            html += '</' + listType + '>';
        }

        return html;
    }

    /**
     * 内联格式化：加粗、斜体
     */
    function applyInlineFormatting(text) {
        // **加粗**
        text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // *斜体*
        text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
        return text;
    }

    /* ============================================================
       UI 工具函数
       ============================================================ */

    /**
     * HTML 字符转义
     */
    function escapeHtml(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    /**
     * 显示错误提示（toast 样式）
     */
    function showError(message) {
        // 移除已有 toast
        var existing = document.querySelector('.error-toast');
        if (existing) {
            existing.classList.add('error-toast--dismissing');
            setTimeout(function () {
                if (existing.parentNode) existing.parentNode.removeChild(existing);
            }, 300);
        }

        var toast = document.createElement('div');
        toast.className = 'error-toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        // 3秒后自动消失
        setTimeout(function () {
            if (toast.parentNode) {
                toast.classList.add('error-toast--dismissing');
                setTimeout(function () {
                    if (toast.parentNode) toast.parentNode.removeChild(toast);
                }, 300);
            }
        }, 3000);
    }

    /**
     * 设置按钮加载状态
     */
    function setButtonLoading(btn, loading) {
        if (loading) {
            btn.classList.add('btn--loading');
            btn.disabled = true;
        } else {
            btn.classList.remove('btn--loading');
            btn.disabled = false;
        }
    }

    /* ============================================================
       初始化
       ============================================================ */

    function init() {
        cacheDOM();
        setupProfileForm();
        setupQuizEvents();
        showStep(1);
    }

    // DOM 就绪后启动
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
