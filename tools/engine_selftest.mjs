#!/usr/bin/env node
/* ============================================================
   engine_selftest.mjs — docs/js/engine.js 自检
   运行: node tools/engine_selftest.mjs
   断言:
   1. 同 profile 两次选题结果完全一致、恰好 120 题、id 无重复
   2. 覆盖率约束满足（九型每型 >=5、MBTI 每极 >=4、
      盖洛普每领域 >=8、反向题 >=12；另附霍兰德 R>=1 其余 >=2）
   3. 两套相反答案的 top_themes 与 MBTI 类型不同
   4. 所有 normalized 值在 [0,1] 且无 NaN
   ============================================================ */
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

const Engine = require(path.join(ROOT, 'docs', 'js', 'engine.js'));
const bank = JSON.parse(readFileSync(path.join(ROOT, 'docs', 'data', 'items.json'), 'utf-8'));

let passed = 0;
let failed = 0;

function check(name, cond, detail) {
    if (cond) {
        passed++;
        console.log(`  ✓ ${name}`);
    } else {
        failed++;
        console.log(`  ✗ ${name}${detail ? ' — ' + detail : ''}`);
    }
}

console.log(`题库: ${bank.length} 题\n`);

/* ---------- 测试 profile ---------- */
const profiles = [
    {
        name: '测试用户',
        age: 22,
        role: 'student-undergrad',
        purpose: 'career-planning',
        current_state: 'stuck',
        gender: 'male'
    },
    {
        age: 35,
        role: 'employed',
        purpose: 'self-exploration'
    }
];

for (const profile of profiles) {
    console.log(`--- profile: ${JSON.stringify(profile)} ---`);

    /* 1. 确定性 + 120 题 + id 无重复 */
    const q1 = Engine.selectQuestions(profile, bank);
    const q2 = Engine.selectQuestions(profile, bank);
    const ids1 = q1.map((q) => q.id);
    const ids2 = q2.map((q) => q.id);

    check('恰好 120 题', q1.length === 120, `实际 ${q1.length}`);
    check('同 profile 两次选题完全一致（含顺序）',
        JSON.stringify(ids1) === JSON.stringify(ids2));
    check('题目 id 无重复', new Set(ids1).size === ids1.length,
        `去重后 ${new Set(ids1).size}`);

    /* 2. 覆盖率约束 */
    const cov = Engine._internals.coverageOf(q1);

    let enOk = true, enDetail = [];
    for (let i = 1; i <= 9; i++) {
        const n = cov.en['type' + i] || 0;
        if (n < 5) { enOk = false; enDetail.push(`type${i}=${n}`); }
    }
    check('九型每型 >= 5 题', enOk, enDetail.join(','));

    let mbOk = true, mbDetail = [];
    for (const p of 'EISNTFJP') {
        const n = cov.mb[p] || 0;
        if (n < 4) { mbOk = false; mbDetail.push(`${p}=${n}`); }
    }
    check('MBTI 每极 >= 4 题', mbOk, mbDetail.join(','));

    let gaOk = true, gaDetail = [];
    for (const d of ['executing', 'influencing', 'relationship_building', 'strategic_thinking']) {
        const n = cov.ga[d] || 0;
        if (n < 8) { gaOk = false; gaDetail.push(`${d}=${n}`); }
    }
    check('盖洛普每领域 >= 8 题', gaOk, gaDetail.join(','));

    const revCount = q1.filter((q) => q.reverse).length;
    check('反向题 >= 12 题', revCount >= 12, `实际 ${revCount}`);

    let hoOk = true, hoDetail = [];
    for (const t of 'RIASEC') {
        const min = t === 'R' ? 1 : 2;
        const n = cov.ho[t] || 0;
        if (n < min) { hoOk = false; hoDetail.push(`${t}=${n}`); }
    }
    check('霍兰德 R >= 1 其余 >= 2 题（附加）', hoOk, hoDetail.join(','));

    /* 3. 两套相反答案 → top_themes 与 MBTI 不同 */
    // 答案集 A：偏 E/S/T/J + 盖洛普执行力；答案集 B：偏 I/N/F/P + 关系建立
    function pickBy(q, weightFn) {
        let best = 0, bestVal = -Infinity;
        (q.options || []).forEach((opt, idx) => {
            const v = weightFn(opt.score || {});
            if (v > bestVal) { bestVal = v; best = idx; }
        });
        return best;
    }
    const wA = (s) => (s['mbti.E'] || 0) + (s['mbti.S'] || 0) + (s['mbti.T'] || 0) + (s['mbti.J'] || 0)
        - ((s['mbti.I'] || 0) + (s['mbti.N'] || 0) + (s['mbti.F'] || 0) + (s['mbti.P'] || 0))
        + (s['gallup.executing'] || 0) - (s['gallup.relationship_building'] || 0);
    const wB = (s) => -wA(s);

    const answersA = q1.map((q) => ({ question_id: q.id, option_index: pickBy(q, wA) }));
    const answersB = q1.map((q) => ({ question_id: q.id, option_index: pickBy(q, wB) }));

    const resA = Engine.scoreAnswers(q1, answersA);
    const resB = Engine.scoreAnswers(q1, answersB);

    check('相反答案 MBTI 类型不同',
        resA.mbti.type !== resB.mbti.type,
        `A=${resA.mbti.type} B=${resB.mbti.type}`);
    check('相反答案 top_themes 不同',
        JSON.stringify(resA.gallup.top_themes) !== JSON.stringify(resB.gallup.top_themes),
        `A=[${resA.gallup.top_themes}] B=[${resB.gallup.top_themes}]`);
    check('top_themes 数量 <= 5 且非空',
        resA.gallup.top_themes.length > 0 && resA.gallup.top_themes.length <= 5 &&
        resB.gallup.top_themes.length > 0 && resB.gallup.top_themes.length <= 5);

    /* 4. normalized 值域检查 */
    function collectNormalized(res) {
        const out = [];
        for (const sys of ['enneagram', 'mbti', 'holland', 'gallup']) {
            const norm = res[sys].normalized;
            for (const k of Object.keys(norm)) out.push([`${sys}.${k}`, norm[k]]);
        }
        return out;
    }
    for (const [label, res] of [['A', resA], ['B', resB]]) {
        const pairs = collectNormalized(res);
        const bad = pairs.filter(([, v]) =>
            typeof v !== 'number' || Number.isNaN(v) || v < 0 || v > 1);
        check(`答案集 ${label} 所有 normalized 在 [0,1] 且无 NaN（${pairs.length} 个值）`,
            bad.length === 0,
            bad.map(([k, v]) => `${k}=${v}`).join(','));
    }

    /* 5. 免费简评昵称回退 */
    const sumWithName = Engine.freeSummary(resA, profile);
    const sumNoName = Engine.freeSummary(resA, { age: 22, role: 'employed', purpose: 'career-planning' });
    const sumEmptyName = Engine.freeSummary(resA, { name: '', age: 22 });
    if (profile.name) {
        check('简评使用昵称', sumWithName.indexOf(profile.name + '的') === 0);
    } else {
        check('无昵称简评回退"你的"', sumWithName.indexOf('你的') === 0);
    }
    check('缺省/空串昵称回退"你的"',
        sumNoName.indexOf('你的') === 0 && sumEmptyName.indexOf('你的') === 0);
    check('简评不含 None/undefined',
        [sumWithName, sumNoName, sumEmptyName].every(
            (s) => s.indexOf('None') < 0 && s.indexOf('undefined') < 0));

    console.log('');
}

/* ---------- 汇总 ---------- */
console.log('============================================');
console.log(`通过 ${passed} 项，失败 ${failed} 项`);
if (failed > 0) {
    process.exit(1);
} else {
    console.log('全部断言通过 ✓');
}
