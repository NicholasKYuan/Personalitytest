/* ============================================================
   engine.js — 纯前端测评引擎
   selector.py 的忠实移植（选题）+ 统一评分规范（评分/简评）。
   浏览器全局暴露 window.Engine；末尾 module.exports 供 node 测试。

   确定性说明：
   - 选题用 profile 规范化 JSON（键排序）的 djb2 哈希做种子，
     mulberry32 PRNG，全程不使用 Math.random。
   - 与 selector.py 的关系：同一 profile 选出的 120 题集合与
     Python 完全一致，但呈现顺序刻意不同（种子/PRNG 为 JS 专用，
     仅影响第 5 步类别交错的随机决胜）。评分语义与 scorer.py 逐字段一致。
   ============================================================ */
(function (global) {
    'use strict';

    /* ================= 常量表（与 selector.py 一致） ================= */

    var PURPOSE_TO_STATES = {
        'career-planning': ['career-choice', 'career-transition', 'mid-career'],
        'study-direction': ['study-direction', 'graduate-school'],
        'study-abroad-planning': ['study-abroad'],
        'graduate-school-planning': ['graduate-school', 'academic-stress'],
        'self-exploration': ['self-exploration'],
        'relationship-insight': ['relationship-conflict'],
        'leadership-growth': ['leadership-growth', 'mid-career'],
        'entrepreneur-fit': ['entrepreneur-stage'],
        'academic-stress-relief': ['academic-stress'],
        'parent-understanding-child': ['parenting-teen']
    };
    var ROLE_TO_STATES = {
        'student-junior-high': ['academic-stress', 'study-direction'],
        'student-senior-high': ['academic-stress', 'study-direction', 'graduate-school'],
        'student-undergrad': ['fresh-grad', 'study-direction', 'graduate-school', 'study-abroad'],
        'student-grad': ['graduate-school', 'career-choice', 'study-abroad'],
        'student-phd': ['academic-stress', 'career-choice'],
        'employed': ['mid-career', 'career-transition', 'leadership-growth'],
        'freelancer': ['entrepreneur-stage', 'career-transition', 'life-transition'],
        'entrepreneur': ['entrepreneur-stage', 'leadership-growth'],
        'parent': ['parenting-teen', 'life-transition'],
        'job-seeker': ['career-choice', 'fresh-grad', 'career-transition']
    };
    var STATE_TO_STATES = {
        'stable': [],
        'transition': ['career-transition', 'life-transition'],
        'stress': ['academic-stress', 'mid-career'],
        'stuck': ['self-exploration', 'life-transition'],
        'growth-seeking': ['leadership-growth', 'self-exploration']
    };

    var CATEGORIES = ['interpersonal-relationship', 'decision-making', 'stress-response', 'motivation-value',
        'learning-cognition', 'work-career', 'emotion-self', 'action-habit',
        'future-vision', 'conflict-choice'];

    var MIN_ENNEAGRAM_PER_TYPE = 5;
    var MIN_MBTI_PER_POLE = 4;
    var MIN_HOLLAND_PER_TYPE = 2;
    var MIN_HOLLAND_R = 1;
    var MIN_GALLUP_PER_DOMAIN = 8;
    var MIN_REVERSE = 12;

    var GALLUP_DOMAINS = ['executing', 'influencing', 'relationship_building', 'strategic_thinking'];

    /* CliftonStrengths 官方 34 主题 → 领域映射 */
    var THEME_TO_DOMAIN = {
        // executing
        achiever: 'executing', arranger: 'executing', belief: 'executing',
        consistency: 'executing', deliberative: 'executing', discipline: 'executing',
        focus: 'executing', responsibility: 'executing', restorative: 'executing',
        // influencing
        activator: 'influencing', command: 'influencing', communication: 'influencing',
        competition: 'influencing', maximizer: 'influencing', self_assurance: 'influencing',
        significance: 'influencing', woo: 'influencing',
        // relationship_building
        adaptability: 'relationship_building', connectedness: 'relationship_building',
        developer: 'relationship_building', empathy: 'relationship_building',
        harmony: 'relationship_building', includer: 'relationship_building',
        individualization: 'relationship_building', positivity: 'relationship_building',
        relator: 'relationship_building',
        // strategic_thinking
        analytical: 'strategic_thinking', context: 'strategic_thinking',
        futuristic: 'strategic_thinking', ideation: 'strategic_thinking',
        input: 'strategic_thinking', intellection: 'strategic_thinking',
        learner: 'strategic_thinking', strategic: 'strategic_thinking'
    };

    /* 旧版/非官方主题名 → 官方 34 主题名（与 scorer.py 的 GALLUP_THEME_ALIASES 一致） */
    var THEME_ALIASES = {
        compliance: 'consistency',
        individuality: 'individualization',
        fixer: 'restorative'
    };

    var ENNEAGRAM_NAMES = {
        1: '完美主义者', 2: '助人者', 3: '成就者', 4: '个人主义者', 5: '观察者',
        6: '忠诚者', 7: '热情者', 8: '挑战者', 9: '和平者'
    };

    var GALLUP_DOMAIN_NAMES = {
        executing: '执行力', influencing: '影响力',
        relationship_building: '关系建立', strategic_thinking: '战略思维'
    };

    var GALLUP_THEME_NAMES = {
        achiever: '成就', activator: '行动', adaptability: '适应',
        analytical: '分析', arranger: '统筹', belief: '信仰',
        command: '统率', communication: '沟通', competition: '竞争',
        connectedness: '关联', context: '回顾', consistency: '公平',
        deliberative: '审慎', developer: '伯乐', discipline: '纪律',
        empathy: '体谅', focus: '专注', futuristic: '前瞻',
        harmony: '和谐', ideation: '理念', includer: '包容',
        individualization: '个别', input: '搜集', intellection: '思维',
        learner: '学习', maximizer: '完美', positivity: '积极',
        relator: '交往', responsibility: '责任', restorative: '排难',
        self_assurance: '自信', significance: '追求', strategic: '战略',
        woo: '取悦'
    };

    /* ================= 确定性随机数 ================= */

    /** 稳定序列化：对象键排序后 JSON 化（数组保持顺序） */
    function stableStringify(value) {
        if (value === null || typeof value !== 'object') {
            return JSON.stringify(value === undefined ? null : value);
        }
        if (Array.isArray(value)) {
            return '[' + value.map(stableStringify).join(',') + ']';
        }
        var keys = Object.keys(value).sort();
        var parts = [];
        for (var i = 0; i < keys.length; i++) {
            var v = value[keys[i]];
            if (v === undefined) continue;
            parts.push(JSON.stringify(keys[i]) + ':' + stableStringify(v));
        }
        return '{' + parts.join(',') + '}';
    }

    /** djb2 字符串哈希（>>> 0 保证无符号 32 位） */
    function djb2(str) {
        var h = 5381;
        for (var i = 0; i < str.length; i++) {
            h = ((h << 5) + h + str.charCodeAt(i)) >>> 0;
        }
        return h;
    }

    /** mulberry32 PRNG，返回 [0,1) */
    function mulberry32(seed) {
        var a = seed >>> 0;
        return function () {
            a = (a + 0x6D2B79F5) >>> 0;
            var t = a;
            t = Math.imul(t ^ (t >>> 15), t | 1);
            t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
            return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
        };
    }

    /* ================= 工具函数（移植自 selector.py） ================= */

    function targetStates(profile) {
        var ts = {};
        var add = function (arr) {
            for (var i = 0; i < arr.length; i++) ts[arr[i]] = true;
        };
        add(PURPOSE_TO_STATES[profile.purpose] || []);
        add(ROLE_TO_STATES[profile.role] || []);
        add(STATE_TO_STATES[profile.current_state || 'stable'] || []);
        return ts;
    }

    function stateMatchScore(item, ts) {
        var s = 0;
        var aps = item.applicable_states || [];
        var overlap = 0;
        var seen = {};  // 去重, 与 Python 的集合交集语义一致
        for (var i = 0; i < aps.length; i++) {
            if (ts[aps[i]] && !seen[aps[i]]) { seen[aps[i]] = true; overlap++; }
        }
        if (overlap > 0) s += 3;       // profile_purpose_in: 有交集 +3
        s += 2 * overlap;              // 每个交集 +2
        return s;
    }

    /** 题目贡献的维度集合（options 各选项 score 键的并集） */
    function itemDims(item) {
        var dims = {};
        var opts = item.options || [];
        for (var i = 0; i < opts.length; i++) {
            var score = opts[i].score || {};
            for (var k in score) {
                if (Object.prototype.hasOwnProperty.call(score, k)) dims[k] = true;
            }
        }
        return dims;
    }

    function coverageOf(selected) {
        var en = {}, mb = {}, ho = {}, ga = {};
        for (var i = 0; i < selected.length; i++) {
            var dims = itemDims(selected[i]);
            for (var d in dims) {
                var idx = d.indexOf('.');
                if (idx < 0) continue;
                var p = d.slice(0, idx);
                var sub = d.slice(idx + 1);
                if (p === 'enneagram') en[sub] = (en[sub] || 0) + 1;
                else if (p === 'mbti') mb[sub] = (mb[sub] || 0) + 1;
                else if (p === 'holland') ho[sub] = (ho[sub] || 0) + 1;
                else if (p === 'gallup') ga[sub] = (ga[sub] || 0) + 1;
            }
        }
        return { en: en, mb: mb, ho: ho, ga: ga };
    }

    /** 标准化题干用于去重比较（与 _normalize_stem 一致） */
    function normalizeStem(stem) {
        var s = String(stem).replace(/[，。？！,. ?！]/g, '');
        s = s.replace(/[（(][^）)]*[）)]/g, '');
        s = s.split('②').join('').trim();
        s = s.replace(/[你我]$/, '');
        s = s.replace(/时$/, '');
        return s;
    }

    function isNearDuplicate(stem1, stem2) {
        var n1 = normalizeStem(stem1);
        var n2 = normalizeStem(stem2);
        if (n1 === n2) return true;
        if (n1.length > 4 && n2.length > 4 && (n1.indexOf(n2) >= 0 || n2.indexOf(n1) >= 0)) {
            return true;
        }
        return false;
    }

    /** 数组移除首个匹配元素（对应 Python list.remove） */
    function removeFirst(arr, elem) {
        var idx = arr.indexOf(elem);
        if (idx >= 0) arr.splice(idx, 1);
    }

    /** 返回 key 最小的首个元素（对应 Python min(iterable, key=...)） */
    function minByKey(arr, keyFn) {
        if (!arr.length) return null;
        var best = arr[0];
        var bestKey = keyFn(best);
        for (var i = 1; i < arr.length; i++) {
            var k = keyFn(arr[i]);
            if (k < bestKey) {
                best = arr[i];
                bestKey = k;
            }
        }
        return best;
    }

    /* ================= selectQuestions：selector.select() 移植 ================= */

    /**
     * 为用户筛选 120 题。确定性：同一 profile 结果恒定。
     * @param {Object} profile 用户信息（age/role/purpose 必填）
     * @param {Array} bank 题库数组（items.json）
     * @returns {Array} 排序后的 120 题
     */
    function selectQuestions(profile, bank) {
        var seed = djb2(stableStringify(profile));
        var rng = mulberry32(seed);
        var ts = targetStates(profile);

        var i, j, k, s, it;

        // Step 1: 打分
        var scored = [];
        for (i = 0; i < bank.length; i++) {
            scored.push({ s: stateMatchScore(bank[i], ts), it: bank[i] });
        }

        // Step 2: 类别配额 —— 每类先取分数最高的前 10 题
        // （稳定排序：JS Array.sort 为稳定排序，与 Python 一致保留题库顺序）
        var byCat = {};
        for (i = 0; i < scored.length; i++) {
            var cat = scored[i].it.category;
            if (!byCat[cat]) byCat[cat] = [];
            byCat[cat].push(scored[i]);
        }
        for (var c in byCat) {
            byCat[c].sort(function (a, b) {
                if (b.s !== a.s) return b.s - a.s;
                return b.it.difficulty - a.it.difficulty;
            });
        }

        var selected = [];
        var selectedIds = {};
        for (i = 0; i < CATEGORIES.length; i++) {
            var pool = byCat[CATEGORIES[i]] || [];
            var take = pool.slice(0, 10);
            for (j = 0; j < take.length; j++) {
                selected.push(take[j].it);
                selectedIds[take[j].it.id] = true;
            }
        }

        // 剩余 20 题：全局分数最高且未选，限制每类不超过 14 题
        var catCount = {};
        for (i = 0; i < selected.length; i++) {
            catCount[selected[i].category] = (catCount[selected[i].category] || 0) + 1;
        }
        var remaining = scored.slice().sort(function (a, b) { return b.s - a.s; });
        for (i = 0; i < remaining.length; i++) {
            if (selected.length >= 120) break;
            it = remaining[i].it;
            if (!selectedIds[it.id] && (catCount[it.category] || 0) < 14) {
                var isDup = false;
                for (j = 0; j < selected.length; j++) {
                    if (isNearDuplicate(selected[j].stem, it.stem)) { isDup = true; break; }
                }
                if (isDup) continue;
                selected.push(it);
                selectedIds[it.id] = true;
                catCount[it.category] = (catCount[it.category] || 0) + 1;
            }
        }

        // Step 2.5: 近似题去重 — 替换近似重复的题干（忠实移植原 while 循环语义）
        var scoredDesc = scored.slice().sort(function (a, b) { return b.s - a.s; });
        i = 0;
        while (i < selected.length) {
            j = i + 1;
            while (j < selected.length) {
                if (isNearDuplicate(selected[i].stem, selected[j].stem)) {
                    var si = stateMatchScore(selected[i], ts);
                    var sj = stateMatchScore(selected[j], ts);
                    var worse = si >= sj ? selected[j] : selected[i];
                    delete selectedIds[worse.id];
                    removeFirst(selected, worse);
                    // 找替代题
                    var replacement = null;
                    for (k = 0; k < scoredDesc.length; k++) {
                        var cand = scoredDesc[k].it;
                        if (!selectedIds[cand.id] && cand.id !== worse.id) {
                            var dup = false;
                            for (var m = 0; m < selected.length; m++) {
                                if (isNearDuplicate(selected[m].stem, cand.stem)) { dup = true; break; }
                            }
                            if (!dup) { replacement = cand; break; }
                        }
                    }
                    if (replacement) {
                        selected.push(replacement);
                        selectedIds[replacement.id] = true;
                    }
                    // 不递增 j：selected[j] 已被移除（与 Python 版行为一致）
                } else {
                    j++;
                }
            }
            i++;
        }

        // Step 3: 维度覆盖校验与替换
        function tryFix(coverageOk, dimPoolPred) {
            if (coverageOk()) return;
            var cands = [];
            for (var a = 0; a < bank.length; a++) {
                if (!selectedIds[bank[a].id] && dimPoolPred(bank[a])) cands.push(bank[a]);
            }
            cands.sort(function (a, b) {
                return stateMatchScore(b, ts) - stateMatchScore(a, ts);
            });
            for (var b2 = 0; b2 < cands.length; b2++) {
                var c2 = cands[b2];
                var dup2 = false;
                for (var d2 = 0; d2 < selected.length; d2++) {
                    if (isNearDuplicate(selected[d2].stem, c2.stem)) { dup2 = true; break; }
                }
                if (dup2) continue;
                var cc = {};
                for (var e2 = 0; e2 < selected.length; e2++) {
                    cc[selected[e2].category] = (cc[selected[e2].category] || 0) + 1;
                }
                if ((cc[c2.category] || 0) >= 16) continue;
                // 只从超额类别(>10题)中淘汰状态分最低的题
                var evictable = [];
                for (var f2 = 0; f2 < selected.length; f2++) {
                    if (cc[selected[f2].category] > 10) evictable.push(selected[f2]);
                }
                if (!evictable.length) return;
                var worst = minByKey(evictable, function (x) { return stateMatchScore(x, ts); });
                removeFirst(selected, worst);
                delete selectedIds[worst.id];
                selected.push(c2);
                selectedIds[c2.id] = true;
                if (coverageOk()) return;
            }
        }

        function hasSystem(item, prefix) {
            var opts = item.options || [];
            for (var a = 0; a < opts.length; a++) {
                var sc = opts[a].score || {};
                for (var kk in sc) {
                    if (kk.indexOf(prefix) === 0) return true;
                }
            }
            return false;
        }

        function enOk() {
            var cov = coverageOf(selected);
            for (var n = 1; n <= 9; n++) {
                if ((cov.en['type' + n] || 0) < MIN_ENNEAGRAM_PER_TYPE) return false;
            }
            return true;
        }
        function mbOk() {
            var cov = coverageOf(selected);
            var poles = 'EISNTFJP';
            for (var n = 0; n < poles.length; n++) {
                if ((cov.mb[poles[n]] || 0) < MIN_MBTI_PER_POLE) return false;
            }
            return true;
        }
        function hoOk() {
            var cov = coverageOf(selected);
            var types = 'RIASEC';
            for (var n = 0; n < types.length; n++) {
                var t = types[n];
                var min = t === 'R' ? MIN_HOLLAND_R : MIN_HOLLAND_PER_TYPE;
                if ((cov.ho[t] || 0) < min) return false;
            }
            return true;
        }
        function gaOk() {
            var cov = coverageOf(selected);
            for (var n = 0; n < GALLUP_DOMAINS.length; n++) {
                if ((cov.ga[GALLUP_DOMAINS[n]] || 0) < MIN_GALLUP_PER_DOMAIN) return false;
            }
            return true;
        }

        tryFix(enOk, function (x) { return hasSystem(x, 'enneagram.'); });
        tryFix(mbOk, function (x) { return hasSystem(x, 'mbti.'); });
        tryFix(hoOk, function (x) { return hasSystem(x, 'holland.'); });
        tryFix(gaOk, function (x) { return hasSystem(x, 'gallup.'); });

        // Step 4: reverse 题补足
        var revCount = 0;
        for (i = 0; i < selected.length; i++) {
            if (selected[i].reverse) revCount++;
        }
        if (revCount < MIN_REVERSE) {
            var revCands = [];
            for (i = 0; i < bank.length; i++) {
                if (bank[i].reverse && !selectedIds[bank[i].id]) revCands.push(bank[i]);
            }
            revCands.sort(function (a, b) {
                return stateMatchScore(b, ts) - stateMatchScore(a, ts);
            });
            var need = MIN_REVERSE - revCount;
            for (i = 0; i < Math.min(need, revCands.length); i++) {
                var nonReverse = [];
                for (j = 0; j < selected.length; j++) {
                    if (!selected[j].reverse) nonReverse.push(selected[j]);
                }
                if (!nonReverse.length) break;
                var worst2 = minByKey(nonReverse, function (x) { return stateMatchScore(x, ts); });
                removeFirst(selected, worst2);
                delete selectedIds[worst2.id];
                selected.push(revCands[i]);
                selectedIds[revCands[i].id] = true;
            }
        }

        // Step 5: 排序 —— 类别交错 + 难度递增
        var byCat2 = {};        // 插入顺序 = selected 顺序（与 Python defaultdict 语义一致）
        var catOrder = [];
        for (i = 0; i < selected.length; i++) {
            var c3 = selected[i].category;
            if (!byCat2[c3]) { byCat2[c3] = []; catOrder.push(c3); }
            byCat2[c3].push(selected[i]);
        }
        for (i = 0; i < catOrder.length; i++) {
            byCat2[catOrder[i]].sort(function (a, b) { return a.difficulty - b.difficulty; });
        }

        var ordered = [];
        var pools = {};
        var poolOrder = catOrder.slice();
        for (i = 0; i < catOrder.length; i++) {
            pools[catOrder[i]] = byCat2[catOrder[i]].slice();
        }
        var lastCat = null;
        while (poolOrder.length > 0) {
            var catsAvail = [];
            for (i = 0; i < poolOrder.length; i++) {
                var pc = poolOrder[i];
                if (pools[pc].length > 0 && pc !== lastCat) catsAvail.push(pc);
            }
            if (!catsAvail.length) {
                for (i = 0; i < poolOrder.length; i++) {
                    if (pools[poolOrder[i]].length > 0) catsAvail.push(poolOrder[i]);
                }
            }
            if (!catsAvail.length) break;
            // 选剩余题难度最低的类（带随机扰动），让整体难度递增
            var chosen = minByKey(catsAvail, function (x) {
                return pools[x][0].difficulty + rng() * 0.5;
            });
            ordered.push(pools[chosen].shift());
            if (!pools[chosen].length) {
                delete pools[chosen];
                removeFirst(poolOrder, chosen);
            }
            lastCat = chosen;
        }

        return ordered;
    }

    /* ================= scoreAnswers：统一评分规范 ================= */

    /**
     * 计算四体系结果（含盖洛普主题加权 + 归一化判型）。
     * @param {Array} questions 本卷完整题目（含 options[].score）
     * @param {Array} answers [{question_id, option_index}, ...]
     */
    function scoreAnswers(questions, answers) {
        var qMap = {};
        var i, j, k;
        for (i = 0; i < questions.length; i++) {
            qMap[questions[i].id] = questions[i];
        }

        // ---- raw 累加（与 scorer.py 相同） ----
        var enneagramScores = {};
        var mbtiScores = {};
        var hollandScores = {};
        var gallupDomainScores = {};
        var themeWeights = {};       // 主题加权（统一规范新逻辑）
        var answeredQuestions = [];  // 已答且有效的题，用于归一化

        for (i = 0; i < answers.length; i++) {
            var qid = answers[i].question_id;
            var optIdx = answers[i].option_index;
            var q = qMap[qid];
            if (!q) continue;
            if (optIdx < 0 || optIdx >= (q.options || []).length) continue;

            answeredQuestions.push(q);
            var score = q.options[optIdx].score || {};

            for (var dimKey in score) {
                if (!Object.prototype.hasOwnProperty.call(score, dimKey)) continue;
                var parts = dimKey.split('.');
                if (parts.length !== 2) continue;
                var system = parts[0], sub = parts[1];
                var val = score[dimKey];

                if (system === 'enneagram') {
                    enneagramScores[sub] = (enneagramScores[sub] || 0) + val;
                } else if (system === 'mbti') {
                    mbtiScores[sub] = (mbtiScores[sub] || 0) + val;
                } else if (system === 'holland') {
                    hollandScores[sub] = (hollandScores[sub] || 0) + val;
                } else if (system === 'gallup') {
                    gallupDomainScores[sub] = (gallupDomainScores[sub] || 0) + val;
                    // 主题加权：所选选项 gallup.<domain> 分值 v>0 时，
                    // 该题 gallup_themes 中属于该 domain 的主题各 += v
                    if (val > 0) {
                        var themes = q.gallup_themes || [];
                        for (j = 0; j < themes.length; j++) {
                            var t = String(themes[j]).replace(/-/g, '_');  // 归一 '-' → '_'
                            t = THEME_ALIASES[t] || t;                     // 旧名 → 官方名
                            if (THEME_TO_DOMAIN[t] === sub) {
                                themeWeights[t] = (themeWeights[t] || 0) + val;
                            }
                        }
                    }
                }
            }
        }

        // ---- 归一化：max_attainable[key] = 每题各选项中该 key 的最大分值之和 ----
        var maxAttainable = {};
        for (i = 0; i < answeredQuestions.length; i++) {
            var opts = answeredQuestions[i].options || [];
            var perQuestionMax = {};
            for (j = 0; j < opts.length; j++) {
                var sc = opts[j].score || {};
                for (k in sc) {
                    if (!Object.prototype.hasOwnProperty.call(sc, k)) continue;
                    if (perQuestionMax[k] === undefined || sc[k] > perQuestionMax[k]) {
                        perQuestionMax[k] = sc[k];
                    }
                }
            }
            for (k in perQuestionMax) {
                maxAttainable[k] = (maxAttainable[k] || 0) + perQuestionMax[k];
            }
        }

        // 与 Python round(v, 3) 完全一致的三位小数舍入：
        // - 对浮点值按其真实二进制值做正确的十进制舍入（toFixed 语义）；
        // - 仅当值恰为千分位中点（即 1/16 的奇数倍，二进制可精确表示）时，
        //   按银行家舍入取偶，如 0.3125 → 0.312、0.1875 → 0.188。
        function round3(v) {
            var t = v * 16;
            if (Number.isInteger(t) && Math.abs(t) % 2 === 1) {
                var q = Math.floor(v * 1000);
                return (q % 2 === 0 ? q : q + 1) / 1000;
            }
            return Number(v.toFixed(3));
        }
        // 归一化值不舍入，判型比较一律用精确值；仅展示输出时 round3（与 Python scorer 一致）
        function normOf(system, sub, raw) {
            var ma = maxAttainable[system + '.' + sub] || 0;
            if (ma <= 0) return 0;
            return (raw || 0) / ma;
        }

        // ---- 九型人格：normalized 最高，平手取型号小的 ----
        var enneagramResult = {};
        var enNormalized = {};
        for (i = 1; i <= 9; i++) {
            var tkey = 'type' + i;
            enneagramResult[tkey] = enneagramScores[tkey] || 0;
            enNormalized[tkey] = normOf('enneagram', tkey, enneagramResult[tkey]);
        }
        var mainTypeNum = 1;
        var bestEnNorm = enNormalized.type1;
        for (i = 2; i <= 9; i++) {
            if (enNormalized['type' + i] > bestEnNorm) {
                bestEnNorm = enNormalized['type' + i];
                mainTypeNum = i;
            }
        }
        var mainTypeName = ENNEAGRAM_NAMES[mainTypeNum];

        // ---- MBTI：四对按 normalized 比较，>= 取前者（E/S/T/J 优先） ----
        var mbtiPairs = [['E', 'I'], ['S', 'N'], ['T', 'F'], ['J', 'P']];
        var mbNormalized = {};
        var poles = 'EISNTFJP';
        for (i = 0; i < poles.length; i++) {
            mbNormalized[poles[i]] = normOf('mbti', poles[i], mbtiScores[poles[i]] || 0);
        }
        var mbtiType = '';
        for (i = 0; i < mbtiPairs.length; i++) {
            var a = mbtiPairs[i][0], b = mbtiPairs[i][1];
            mbtiType += (mbNormalized[a] >= mbNormalized[b]) ? a : b;
        }
        var mbtiDimensions = {};
        for (i = 0; i < poles.length; i++) {
            mbtiDimensions[poles[i]] = mbtiScores[poles[i]] || 0;
        }

        // ---- 霍兰德：normalized 前 3，平手按字母序 ----
        var hollandAll = {};
        var hoNormalized = {};
        var hollandTypes = 'RIASEC';
        for (i = 0; i < hollandTypes.length; i++) {
            var ht = hollandTypes[i];
            hollandAll[ht] = hollandScores[ht] || 0;
            hoNormalized[ht] = normOf('holland', ht, hollandAll[ht]);
        }
        var hollandSorted = hollandTypes.split('').sort(function (x, y) {
            if (hoNormalized[y] !== hoNormalized[x]) return hoNormalized[y] - hoNormalized[x];
            return x < y ? -1 : (x > y ? 1 : 0);
        });
        var hollandCode = hollandSorted.slice(0, 3).join('');

        // ---- 盖洛普：top_domain 按归一化判定，平手按领域名字母序
        //      （GALLUP_DOMAINS 本身即字母序，严格大于才替换 = 平手取前者） ----
        var gallupDomains = {};
        var gaNormalized = {};
        for (i = 0; i < GALLUP_DOMAINS.length; i++) {
            var gd = GALLUP_DOMAINS[i];
            gallupDomains[gd] = gallupDomainScores[gd] || 0;
            gaNormalized[gd] = normOf('gallup', gd, gallupDomains[gd]);
        }
        var topDomain = GALLUP_DOMAINS[0];
        for (i = 1; i < GALLUP_DOMAINS.length; i++) {
            if (gaNormalized[GALLUP_DOMAINS[i]] > gaNormalized[topDomain]) {
                topDomain = GALLUP_DOMAINS[i];
            }
        }

        // ---- top_themes：weight>0，按 (weight 降序, 主题名字典序升序) 取前 5 ----
        var themeList = [];
        for (var tn in themeWeights) {
            if (themeWeights[tn] > 0) themeList.push(tn);
        }
        themeList.sort(function (x, y) {
            if (themeWeights[y] !== themeWeights[x]) return themeWeights[y] - themeWeights[x];
            return x < y ? -1 : (x > y ? 1 : 0);
        });
        var topThemes = themeList.slice(0, 5);

        // ---- normalized 子字典（保留 3 位小数） ----
        var enNormOut = {}, mbNormOut = {}, hoNormOut = {}, gaNormOut = {};
        for (i = 1; i <= 9; i++) enNormOut['type' + i] = round3(enNormalized['type' + i]);
        for (i = 0; i < poles.length; i++) mbNormOut[poles[i]] = round3(mbNormalized[poles[i]]);
        for (i = 0; i < hollandTypes.length; i++) hoNormOut[hollandTypes[i]] = round3(hoNormalized[hollandTypes[i]]);
        for (i = 0; i < GALLUP_DOMAINS.length; i++) gaNormOut[GALLUP_DOMAINS[i]] = round3(gaNormalized[GALLUP_DOMAINS[i]]);

        return {
            enneagram: {
                main_type: mainTypeNum,
                type_name: mainTypeName,
                scores: enneagramResult,
                normalized: enNormOut
            },
            mbti: {
                type: mbtiType,
                dimensions: mbtiDimensions,
                normalized: mbNormOut
            },
            holland: {
                code: hollandCode,
                scores: hollandAll,
                normalized: hoNormOut
            },
            gallup: {
                top_domain: topDomain,
                domains: gallupDomains,
                top_themes: topThemes,
                normalized: gaNormOut
            }
        };
    }

    /* ================= freeSummary：generate_free_summary 移植 ================= */

    /**
     * 免费简评。昵称回退：name 为 None/空串时用 "你"。
     */
    function freeSummary(results, profile) {
        var name = (profile && profile.name) ? profile.name : '你';
        var enneagram = results.enneagram;
        var mbti = results.mbti;
        var holland = results.holland;
        var gallup = results.gallup;

        var parts = [
            name + '的九型人格主型为【' + enneagram.main_type + '号 - ' + enneagram.type_name + '】。',
            'MBTI类型为【' + mbti.type + '】。',
            '霍兰德职业兴趣代码为【' + holland.code + '】。',
            '盖洛普优势主导领域为【' + (GALLUP_DOMAIN_NAMES[gallup.top_domain] || gallup.top_domain) + '】。'
        ];

        if (gallup.top_themes && gallup.top_themes.length) {
            var themesCn = [];
            var top3 = gallup.top_themes.slice(0, 3);
            for (var i = 0; i < top3.length; i++) {
                themesCn.push(GALLUP_THEME_NAMES[top3[i]] || top3[i]);
            }
            parts.push('核心优势主题包括：' + themesCn.join('、') + '。');
        }

        parts.push('解锁深度报告，获取四体系交叉解读与AI个性化建议。');

        return parts.join(' ');
    }

    /* ================= 导出 ================= */

    var Engine = {
        selectQuestions: selectQuestions,
        scoreAnswers: scoreAnswers,
        freeSummary: freeSummary,
        // 供测试/报告使用的内部工具
        _internals: {
            stableStringify: stableStringify,
            djb2: djb2,
            mulberry32: mulberry32,
            targetStates: targetStates,
            stateMatchScore: stateMatchScore,
            coverageOf: coverageOf,
            isNearDuplicate: isNearDuplicate,
            THEME_TO_DOMAIN: THEME_TO_DOMAIN,
            GALLUP_DOMAINS: GALLUP_DOMAINS,
            GALLUP_DOMAIN_NAMES: GALLUP_DOMAIN_NAMES,
            GALLUP_THEME_NAMES: GALLUP_THEME_NAMES,
            ENNEAGRAM_NAMES: ENNEAGRAM_NAMES
        }
    };

    global.Engine = Engine;

    if (typeof module !== 'undefined') {
        module.exports = Engine;
    }
})(typeof window !== 'undefined' ? window : globalThis);
