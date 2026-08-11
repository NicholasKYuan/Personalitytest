/* ============================================================
   星耀启程 · 人格测评 — 交互逻辑（GitHub Pages 静态演示版）
   纯原生 JS，无框架依赖。管理三步骤流程。
   与后端版差异：
   - 三个 API 调用替换为本地 Engine 调用（engine.js）
   - 题库 ./data/items.json 首次加载后缓存
   - 报告在浏览器本地生成（fetch 模板 + 占位符替换 + Blob 下载）
   - 无任何数据上传
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
        'self_assurance': '自信', 'self-assurance': '自信',
        'significance': '追求', 'strategic': '战略', 'woo': '取悦'
    };

    /* ---------- 报告生成用映射（移植自 report_generator.py） ---------- */
    var ROLE_CN = {
        'student-junior-high': '初中生', 'student-senior-high': '高中生',
        'student-undergrad': '本科生', 'student-grad': '硕士生',
        'student-phd': '博士生', 'employed': '在职人士',
        'freelancer': '自由职业者', 'entrepreneur': '创业者',
        'parent': '家长', 'job-seeker': '求职者'
    };

    var PURPOSE_CN = {
        'career-planning': '职业规划', 'study-direction': '学习方向选择',
        'study-abroad-planning': '留学规划', 'graduate-school-planning': '考研/保研规划',
        'self-exploration': '自我探索', 'relationship-insight': '人际关系洞察',
        'leadership-growth': '领导力成长', 'entrepreneur-fit': '创业适配评估',
        'academic-stress-relief': '学业压力舒缓', 'parent-understanding-child': '了解孩子'
    };

    var HOLLAND_LABELS = {
        'R': '实际型', 'I': '研究型', 'A': '艺术型',
        'S': '社会型', 'E': '企业型', 'C': '常规型'
    };

    var MBTI_LABELS = {
        'INTJ': '建筑师', 'INTP': '逻辑学家', 'ENTJ': '指挥官', 'ENTP': '辩论家',
        'INFJ': '提倡者', 'INFP': '调停者', 'ENFJ': '主人公', 'ENFP': '竞选者',
        'ISTJ': '物流师', 'ISFJ': '守卫者', 'ESTJ': '总经理', 'ESFJ': '执政官',
        'ISTP': '鉴赏家', 'ISFP': '探险家', 'ESTP': '企业家', 'ESFP': '表演者'
    };

    /* AI 章节固定文案（演示版无后端） */
    var DEMO_AI_NOTICE = '在线演示版不含 AI 深度解读';

    /* ---------- 全局状态 ---------- */
    var state = {
        step: 1,
        bank: null,             // 题库缓存（首次加载后复用）
        profile: null,          // 用户填写的 profile
        questions: [],          // 题目列表
        currentIndex: 0,        // 当前题目索引
        answers: {},            // { questionId: optionIndex }
        results: null,          // Engine.scoreAnswers 结果
        freeSummary: '',        // 免费简评
        reportTemplate: null,   // 报告模板缓存
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
    }

    /* ============================================================
       本地引擎封装（替代原 API 客户端）
       ============================================================ */

    /**
     * 加载题库（首次 fetch 后缓存）
     */
    function loadBank() {
        if (state.bank) {
            return Promise.resolve(state.bank);
        }
        return fetch('./data/items.json').then(function (res) {
            if (!res.ok) {
                throw new Error('题库加载失败 (' + res.status + ')');
            }
            return res.json();
        }).then(function (bank) {
            state.bank = bank;
            return bank;
        });
    }

    /**
     * 本地"创建会话"：加载题库并用 Engine 选题
     */
    function createSession(profile) {
        return loadBank().then(function (bank) {
            var questions = Engine.selectQuestions(profile, bank);
            return { questions: questions };
        });
    }

    /**
     * 本地"提交答案"：Engine 评分 + 免费简评
     */
    function submitAnswersLocal(answersArray) {
        return new Promise(function (resolve) {
            var results = Engine.scoreAnswers(state.questions, answersArray);
            var summary = Engine.freeSummary(results, state.profile);
            resolve({ results: results, free_summary: summary });
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
        ['age', 'role', 'purpose'].forEach(function (field) {
            var el = document.getElementById('error-' + field);
            var input = document.getElementById('field-' + field);
            if (el) el.textContent = '';
            if (input) input.classList.remove('form-input--error');
        });

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

        // 可选字段：只有非空才纳入
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
        if (state.isLoading) return;

        var validation = validateForm();
        if (!validation.valid) {
            showFormErrors(validation.errors);
            return;
        }

        showFormErrors({});
        var profile = getProfileData();

        state.isLoading = true;
        setButtonLoading(DOM.btnStart, true);

        createSession(profile)
            .then(function (data) {
                state.profile = profile;
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
                showError(err.message || '题目生成失败，请刷新页面重试');
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
            html += '<button class="option-btn' + selectedClass + '" data-index="' + idx + '">' +
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
            DOM.btnSubmitQuiz.style.display = 'none';
            renderQuestion();
        }
    }

    /**
     * 更新导航按钮状态
     */
    function updateNavButtons() {
        DOM.btnPrev.disabled = state.currentIndex === 0;

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

        submitAnswersLocal(answersArray)
            .then(function (data) {
                state.results = data.results;
                state.freeSummary = data.free_summary;
                // 进入结果页
                showStep(3);
                renderResults(data);
            })
            .catch(function (err) {
                showError(err.message || '评分失败，请重试');
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
    }

    /**
     * 下载报告按钮（本地生成，无网络请求）
     */
    function setupDownloadSection() {
        var btnDownload = document.getElementById('btn-download-report');
        if (btnDownload) {
            btnDownload.addEventListener('click', function () {
                if (!state.results) {
                    showError('请先完成测评');
                    return;
                }
                if (state.isLoading) return;
                state.isLoading = true;
                setButtonLoading(btnDownload, true);

                loadReportTemplate()
                    .then(function (template) {
                        var html = generateReportHtml(template, state.results, state.profile || {});
                        downloadHtml(html, '星耀启程-人格测评报告.html');
                    })
                    .catch(function (err) {
                        showError(err.message || '报告生成失败，请重试');
                    })
                    .finally(function () {
                        state.isLoading = false;
                        setButtonLoading(btnDownload, false);
                    });
            });
        }
    }

    /* ============================================================
       报告生成（移植自 report_generator.py，纯浏览器端）
       ============================================================ */

    /**
     * 加载报告模板（首次 fetch 后缓存）
     */
    function loadReportTemplate() {
        if (state.reportTemplate) {
            return Promise.resolve(state.reportTemplate);
        }
        return fetch('./templates/report-detailed.html').then(function (res) {
            if (!res.ok) {
                throw new Error('报告模板加载失败 (' + res.status + ')');
            }
            return res.text();
        }).then(function (text) {
            state.reportTemplate = text;
            return text;
        });
    }

    /**
     * 百分比：最小 5%，max 为 0 时取 5
     */
    function pct(score, maxScore) {
        if (!maxScore) return 5;
        return Math.max(5, Math.min(100, Math.round(score / maxScore * 100)));
    }

    /**
     * 对象值的最大值（空对象回退 1）
     */
    function maxValue(obj) {
        var vals = Object.keys(obj || {}).map(function (k) { return obj[k]; });
        return vals.length ? Math.max.apply(null, vals) : 1;
    }

    /**
     * 雷达图五边形坐标（移植 _radar_points）
     */
    function radarPoints(results) {
        var en = results.enneagram || {};
        var mb = results.mbti || {};
        var ho = results.holland || {};
        var ga = results.gallup || {};

        var enMax = maxValue(en.scores);
        var mbMax = maxValue(mb.dimensions);
        var hoMax = maxValue(ho.scores);
        var gaMax = maxValue(ga.domains);

        var composite = (enMax + mbMax + hoMax + gaMax) / 4;

        var vals = [enMax, mbMax, hoMax, gaMax, composite];
        var allMax = Math.max.apply(null, vals);
        var normalized = vals.map(function (v) { return allMax > 0 ? v / allMax : 0; });

        var cx = 150, cy = 150, radius = 120;
        var angles = [-90, -90 + 72, -90 + 144, -90 + 216, -90 + 288];
        var points = [];
        for (var i = 0; i < angles.length; i++) {
            var rad = angles[i] * Math.PI / 180;
            var r = radius * normalized[i];
            var x = cx + r * Math.cos(rad);
            var y = cy + r * Math.sin(rad);
            points.push(x.toFixed(1) + ',' + y.toFixed(1));
        }
        return points.join(' ');
    }

    /**
     * 全量替换占位符（Python str.replace 语义：替换所有出现）
     */
    function replaceAllPlaceholders(html, replacements) {
        Object.keys(replacements).forEach(function (placeholder) {
            var value = replacements[placeholder];
            if (value === null || value === undefined) value = '';
            html = html.split(placeholder).join(String(value));
        });
        return html;
    }

    /**
     * 生成完整 HTML 报告（移植 generate_report_html）
     * AI 章节位置填固定演示文案；昵称空显示"探索者"。
     */
    function generateReportHtml(template, results, profile) {
        var html = template;

        // --- 基础信息 ---
        var name = profile.name ? String(profile.name) : '探索者';
        var age = (profile.age !== undefined && profile.age !== null) ? profile.age : '';
        var roleCn = ROLE_CN[profile.role] || profile.role || '';
        var purposeCn = PURPOSE_CN[profile.purpose] || profile.purpose || '';
        var now = new Date();
        var reportDate = now.getFullYear() + '年' +
            String(now.getMonth() + 1).padStart(2, '0') + '月' +
            String(now.getDate()).padStart(2, '0') + '日';
        var birthDate = profile.birth_date || '';

        // --- 四体系 ---
        var en = results.enneagram || {};
        var enScores = en.scores || {};
        var enMax = maxValue(enScores);

        var mb = results.mbti || {};
        var mbDims = mb.dimensions || {};
        var mbMax = maxValue(mbDims);

        var ho = results.holland || {};
        var hoScores = ho.scores || {};
        var hoMax = maxValue(hoScores);
        var hollandCode = ho.code || '';
        var hollandLabel = hollandCode.split('').map(function (c) {
            return HOLLAND_LABELS[c] || c;
        }).join('、');

        var ga = results.gallup || {};
        var gaDomains = ga.domains || {};
        var gaMax = maxValue(gaDomains);
        var gaThemes = (ga.top_themes || []).slice(0, 5);
        var gaDomainCn = GALLUP_DOMAIN_LABELS[ga.top_domain] || ga.top_domain || '';

        // 主题标签 HTML
        var themeTags = gaThemes.map(function (t) {
            return '<span class="theme-tag">' + (GALLUP_THEME_LABELS[t] || t) + '</span>';
        }).join('');

        // 职业推荐（无 AI 分析，使用兜底文案）
        var careerListHtml = '<li>请参考霍兰德代码对应的职业方向</li>';

        // AI 章节：演示版固定文案
        var aiNotice = '<p>' + DEMO_AI_NOTICE + '</p>';

        var mbtiType = mb.type || '';
        var mbtiLabel = MBTI_LABELS[mbtiType] || '';

        var replacements = {
            '{{USER_NAME}}': escapeHtml(name),
            '{{USER_AGE}}': String(age),
            '{{USER_ROLE_CN}}': roleCn,
            '{{USER_PURPOSE_CN}}': purposeCn,
            '{{REPORT_DATE}}': reportDate,
            '{{BIRTH_DATE}}': birthDate,

            '{{ENNEAGRAM_TYPE}}': String(en.main_type !== undefined && en.main_type !== null ? en.main_type : ''),
            '{{ENNEAGRAM_NAME}}': en.type_name || '',

            '{{MBTI_TYPE}}': mbtiType,
            '{{MBTI_LABEL}}': mbtiLabel,

            '{{HOLLAND_CODE}}': hollandCode,
            '{{HOLLAND_LABEL}}': hollandLabel,

            '{{GALLUP_DOMAIN_CN}}': gaDomainCn,
            '{{RADAR_POINTS}}': radarPoints(results),

            '{{CAREER_LIST}}': careerListHtml,
            '{{GALLUP_THEME_TAGS}}': themeTags,

            '{{ENNEAGRAM_ANALYSIS}}': aiNotice,
            '{{MBTI_ANALYSIS}}': aiNotice,
            '{{HOLLAND_ANALYSIS}}': aiNotice,
            '{{GALLUP_ANALYSIS}}': aiNotice,
            '{{CROSS_ANALYSIS}}': aiNotice,
            '{{SYNERGY_POINTS}}': DEMO_AI_NOTICE,
            '{{TENSION_POINTS}}': DEMO_AI_NOTICE,

            '{{LIFECYCLE_CURRENT}}': '',
            '{{LIFECYCLE_FOCUS}}': '',
            '{{LIFECYCLE_PITFALL}}': '',
            '{{LIFECYCLE_CROSS}}': ''
        };

        // 九型得分
        for (var i = 1; i <= 9; i++) {
            var enScore = enScores['type' + i] || 0;
            replacements['{{ENNEAGRAM_SCORE_' + i + '}}'] = String(enScore);
            replacements['{{ENNEAGRAM_PCT_' + i + '}}'] = String(pct(enScore, enMax));
        }

        // MBTI 得分
        'EISNTFJP'.split('').forEach(function (dim) {
            var mbScore = mbDims[dim] || 0;
            replacements['{{MBTI_SCORE_' + dim + '}}'] = String(mbScore);
            replacements['{{MBTI_PCT_' + dim + '}}'] = String(pct(mbScore, mbMax));
        });

        // 霍兰德得分
        'RIASEC'.split('').forEach(function (t) {
            var hoScore = hoScores[t] || 0;
            replacements['{{HOLLAND_SCORE_' + t + '}}'] = String(hoScore);
            replacements['{{HOLLAND_PCT_' + t + '}}'] = String(pct(hoScore, hoMax));
        });

        // 盖洛普得分
        [['EXEC', 'executing'], ['INFL', 'influencing'],
         ['REL', 'relationship_building'], ['STRAT', 'strategic_thinking']].forEach(function (pair) {
            var gaScore = gaDomains[pair[1]] || 0;
            replacements['{{GALLUP_SCORE_' + pair[0] + '}}'] = String(gaScore);
            replacements['{{GALLUP_PCT_' + pair[0] + '}}'] = String(pct(gaScore, gaMax));
        });

        html = replaceAllPlaceholders(html, replacements);

        // 处理条件块 {{IF_LIFECYCLE}} ... {{/IF_LIFECYCLE}}
        if (birthDate) {
            html = html.split('<!-- {{IF_LIFECYCLE}} -->').join('');
            html = html.split('<!-- {{/IF_LIFECYCLE}} -->').join('');
            html = html.split('{{IF_LIFECYCLE}}').join('');
            html = html.split('{{/IF_LIFECYCLE}}').join('');
        } else {
            html = html.replace(/<!--\s*\{\{IF_LIFECYCLE\}\}\s-->[\s\S]*?<!--\s*\{\{\/IF_LIFECYCLE\}\}\s-->/g, '');
            html = html.replace(/\{\{IF_LIFECYCLE\}\}[\s\S]*?\{\{\/IF_LIFECYCLE\}\}/g, '');
        }

        return html;
    }

    /**
     * Blob URL 触发下载
     */
    function downloadHtml(html, filename) {
        var blob = new Blob([html], { type: 'text/html;charset=utf-8' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(function () {
            URL.revokeObjectURL(url);
        }, 1000);
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
        setupDownloadSection();
        showStep(1);

        // 预加载题库（后台静默，不阻塞表单）
        loadBank().catch(function () { /* 首次进入失败时提交表单会重试 */ });
    }

    // DOM 就绪后启动
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // 冒烟测试钩子（不影响正常使用）
    window.__reportTestHooks = {
        generateReportHtml: generateReportHtml,
        loadReportTemplate: loadReportTemplate,
        loadBank: loadBank
    };
})();
