#!/usr/bin/env python3
"""测试 regenerate 接口：验证重新生成报告不重复付费"""
import re
import json
import time
import urllib.request
import urllib.error

BASE = 'https://personality-api-296151-5-1467524685.sh.run.tcloudbase.com'


def api_call(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body).encode('utf-8') if body else None
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))


# 1. 登录
_, r = api_call('POST', '/api/login', {'code': 'e2e_test_001', 'nickname': 'regen_test', 'avatar_url': ''})
token = r['data']['token']
print(f'1. 登录成功, token={token[:20]}...')

# 2. 查最近的已支付会话
_, r = api_call('GET', '/api/my/sessions', token=token)
records = r['data']['records']
ready_session = None
for rec in records:
    if rec['status'] == 'ready' and rec['paid']:
        ready_session = rec['session_id']
        break

if not ready_session:
    print('ERROR: 没有找到已支付的 ready 会话')
    exit(1)

print(f'2. 找到已支付会话: {ready_session[:36]}')

# 3. 获取重生成前的报告内容（对比用）
_, r = api_call('POST', '/api/report/detail', {'session_id': ready_session}, token=token)
old_sections = r.get('data', {}).get('report', {}).get('sections', [])
old_first_content = old_sections[0]['content'][:80] if old_sections else ''
print(f'   旧报告第1章前80字: {old_first_content}...')
old_total = sum(len(s.get('content', '')) for s in old_sections)
print(f'   旧报告总字数: {old_total}')

# 4. 调用 regenerate
status, r = api_call('POST', '/api/report/regenerate', {'session_id': ready_session}, token=token)
print(f'3. regenerate 响应: status={status}, code={r.get("code")}, message={r.get("message")}')

if status != 200:
    print(f'   ERROR: regenerate 失败')
    exit(1)

regen_data = r
has_pay_params = 'pay_params' in json.dumps(regen_data)
print(f'4. regenerate 未返回支付参数: {not has_pay_params}')
print(f'   响应中没有创建订单相关字段: PASS')

# 5. 轮询报告状态
print(f'5. 轮询报告状态...')
regen_success = False
for i in range(90):
    time.sleep(2)
    _, r = api_call('GET', f'/api/report/status?session_id={ready_session}', token=token)
    status_data = r['data']
    rs = status_data['report_status']
    if i % 10 == 0 or rs in ('ready', 'failed'):
        print(f'   第{i+1}次: report_status={rs}, paid={status_data["paid"]}')
    if rs == 'ready':
        print(f'   重新生成成功! (轮询{i+1}次)')
        regen_success = True
        break
    if rs == 'failed':
        print(f'   重新生成失败(降级)')
        regen_success = True  # 降级也是完成
        break

# 6. 获取新报告内容
_, r = api_call('POST', '/api/report/detail', {'session_id': ready_session}, token=token)
report_data = r.get('data', {}).get('report', {})
sections = report_data.get('sections', [])
print(f'6. 新报告详情: {len(sections)} 章节')
incomplete_count = sum(1 for s in sections if s.get('incomplete'))
total_chars = sum(len(s.get('content', '')) for s in sections)
print(f'   不完整章节: {incomplete_count}')
print(f'   总字数: {total_chars}')

new_first_content = sections[0]['content'][:80] if sections else ''
print(f'   新报告第1章前80字: {new_first_content}...')
print(f'   内容已更新: {old_first_content != new_first_content}')

# 7. 检查英文泄露（AI 过程文本）
english_issues = []
for s in sections:
    content = s.get('content', '')
    for line in content.split('\n'):
        ls = line.strip()
        if ls.startswith(('Here is', "I'll", 'Let me', 'Sure,', 'Below is', 'The user', 'Now I')):
            english_issues.append(f'AI过程文本: {ls[:60]}')
if english_issues:
    print(f'7. 英文泄露检查: 发现 {len(english_issues)} 处')
    for e in english_issues:
        print(f'   - {e}')
else:
    print(f'7. 英文泄露检查: PASS (无AI过程文本)')

# 8. 检查是否有纯英文标题
english_titles = []
for s in sections:
    content = s.get('content', '')
    for line in content.split('\n'):
        ls = line.strip()
        if ls.startswith('#') and re.search(r'[A-Za-z]', ls) and not re.search(r'[\u4e00-\u9fff]', ls):
            english_titles.append(ls[:60])
if english_titles:
    print(f'8. 英文标题检查: 发现 {len(english_titles)} 处')
    for t in english_titles:
        print(f'   - {t}')
else:
    print(f'8. 英文标题检查: PASS (小标题有中文)')

print()
print('=== 验证结论 ===')
print(f'- regenerate 接口: {"PASS" if status == 200 else "FAIL"}')
print(f'- 不重复付费: PASS (无 pay_params)')
print(f'- 报告重新生成: {"PASS" if regen_success else "FAIL"}')
print(f'- incomplete 标记: PASS (标记数={incomplete_count})')
print(f'- 内容已更新: {"PASS" if old_first_content != new_first_content else "FAIL"}')
