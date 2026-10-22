'use strict';
(() => {
  const KEY = 'slam-learning-v1';
  // 2026-10 课程由 23 课扩为 33 课，课号改变。旧记录（版本 1）按此表迁到新课号，只迁一次。
  const OLD_TO_NEW = {'0001':'0002','0002':'0003','0003':'0006','0004':'0007','0005':'0008','0006':'0009','0007':'0010','0008':'0012','0009':'0013','0010':'0015','0011':'0016','0012':'0017','0013':'0018','0014':'0019','0015':'0020','0016':'0023','0017':'0027','0018':'0028','0019':'0029','0020':'0030','0021':'0031','0022':'0032','0023':'0033'};
  const LAYOUT = KEY + ':layout';
  function migrate(old) {
    const result = {};
    for (const [id, values] of Object.entries(old)) result[OLD_TO_NEW[id] || id] = values;
    return result;
  }
  let records = {};
  let storageOK = true;
  function readRecords() {
    let result = {};
    try { result = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (_) { /* 可恢复旧格式损坏 */ }
    if (!result || typeof result !== 'object' || Array.isArray(result)) result = {};
    // 各字段独立保存，避免不同页面用过期的整份快照覆盖彼此。
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key?.startsWith(KEY + ':')) continue;
      const match = key.slice(KEY.length + 1).match(/^(\d{4}|home):(answer|reason|state|updated|review)$/);
      if (!match) continue;
      const value = localStorage.getItem(key);
      if (value === null) continue;
      const [_, id, field] = match;
      if (!result[id] || typeof result[id] !== 'object') result[id] = {};
      result[id][field] = value;
    }
    return result;
  }
  try {
    records = readRecords();
    if (localStorage.getItem(LAYOUT) !== '2') {
      const moved = migrate(records);
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i);
        if (key?.startsWith(KEY + ':') && key !== LAYOUT && localStorage.removeItem) localStorage.removeItem(key);
      }
      localStorage.setItem(KEY, '{}');
      for (const [id, values] of Object.entries(moved)) {
        for (const [field, value] of Object.entries(values)) if (typeof value === 'string') localStorage.setItem(`${KEY}:${id}:${field}`, value);
      }
      localStorage.setItem(LAYOUT, '2');
      records = readRecords();
    }
  } catch (_) { storageOK = false; }
  if (!records || typeof records !== 'object' || Array.isArray(records)) records = {};
  const lessonID = document.body.dataset.lesson;
  const status = document.getElementById('save-status');
  const fields = [...document.querySelectorAll('[data-save]')];
  function persist(changes) {
    for (const [id, values] of Object.entries(changes)) records[id] = {...records[id], ...values};
    try {
      for (const [id, values] of Object.entries(changes)) {
        for (const [field, value] of Object.entries(values)) localStorage.setItem(`${KEY}:${id}:${field}`, value);
      }
      records = readRecords(); storageOK = true;
    }
    catch (_) { storageOK = false; }
    if (status) status.textContent = storageOK ? '已保存在此浏览器。建议导出备份。' : '浏览器未允许持久保存；本页仍可使用，请离开前导出。';
  }
  fields.forEach(el => {
    const saved = records[lessonID]?.[el.dataset.save];
    if (typeof saved === 'string') el.value = saved;
    el.addEventListener('input', () => {
      // 同一字段在多个页面编辑时，最后一次保存生效；其他字段不受影响。
      persist({[lessonID]: {[el.dataset.save]: el.value, updated: new Date().toISOString()}});
    });
  });
  if (status) status.textContent = storageOK ? '记录仅存于当前浏览器；尚未提交任何掌握证明。' : '本地存储不可用，请导出备份。';
  function updateCards() {
    document.querySelectorAll('[data-progress]').forEach(el => {
      el.textContent = records[el.dataset.progress]?.state || '尚未记录';
    });
  }
  updateCards();
  document.querySelectorAll('[data-export]').forEach(button => button.addEventListener('click', () => {
    if (storageOK) { try { records = readRecords(); } catch (_) { storageOK = false; } }
    const blob = new Blob([JSON.stringify({version: 2, exported: new Date().toISOString(), records}, null, 2)], {type:'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'learning-export-'+new Date().toISOString().slice(0,10)+'.json'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }));
  document.getElementById('import-progress')?.addEventListener('change', async event => {
    const feedback = document.getElementById('import-status');
    try {
      const file = event.target.files[0]; if (!file) return;
      if (file.size > 2000000) throw new Error('文件过大');
      const data = JSON.parse(await file.text());
      if ((data.version !== 1 && data.version !== 2) || !data.records || typeof data.records !== 'object' || Array.isArray(data.records)) throw new Error('格式不符');
      const clean = {};
      // 版本 1 是 23 课时代导出的文件，课号先迁到新编号。
      const incoming = data.version === 1 ? migrate(data.records) : data.records;
      for (const [id, values] of Object.entries(incoming)) {
        if (!/^(\d{4}|home)$/.test(id) || !values || typeof values !== 'object') continue;
        clean[id] = {};
        for (const name of ['answer','reason','state','updated','review']) {
          if (typeof values[name] === 'string') clean[id][name] = values[name].slice(0,20000);
        }
      }
      // 同课以导入内容为准，其他课记录保留。只接收限定字段，不解析 HTML。
      persist(clean); updateCards();
      feedback.textContent = storageOK ? '已导入；同课采用导入字段，其他记录保留。' : '已在本页载入，但浏览器无法持久保存；请离开前导出。';
    } catch (err) { feedback.textContent = '未导入：'+err.message+'。请选择本教材导出的 JSON。'; }
  });
  document.querySelectorAll('[data-copy]').forEach(button => button.addEventListener('click', async () => {
    const source = button.previousElementSibling;
    const text = source ? source.textContent : '';
    try { await navigator.clipboard.writeText(text); button.textContent = '已复制'; }
    catch (err) { button.textContent = '请手动选中复制'; }
    setTimeout(() => { button.textContent = '复制提示词'; }, 2000);
  }));
  document.querySelectorAll('[data-filter]').forEach(input => input.addEventListener('input', () => {
    const term = input.value.trim().toLowerCase();
    document.querySelectorAll(input.dataset.filter).forEach(item => { item.hidden = !item.textContent.toLowerCase().includes(term); });
  }));
  document.querySelectorAll('[data-check]').forEach(button => button.addEventListener('click', () => {
    const box = button.closest('.numeric');
    const raw = box.querySelector('input').value.trim();
    const value = Number(raw), expected = Number(button.dataset.check);
    const out = box.querySelector('output');
    out.textContent = raw === '' || !Number.isFinite(value) ? '先输入一个有限数字，再检查。' : Math.abs(value-expected) <= 0.001 ? '数值正确。请继续解释单位、公式与改变条件后的结果；这还不是掌握认证。' : '数值不一致。'+button.dataset.explain;
  }));
  const val = (root, key) => Number(root.querySelector(`[name="${key}"]`).value);
  document.querySelectorAll('[data-lab]').forEach(root => {
    const out = root.querySelector('output');
    function draw() {
      const inputs = [...root.querySelectorAll('input')];
      if (inputs.some(x => x.value.trim() === '' || !Number.isFinite(Number(x.value)))) { out.textContent = '请输入有效数字。'; return; }
      const type = root.dataset.lab;
      if (type === 'residual') {
        const x=val(root,'x'), predicted=10-x, r=predicted-3;
        out.textContent = `位置 x=${x.toFixed(2)} 米 → 预测距离 10−x=${predicted.toFixed(2)} 米\n残差=预测−3=${r.toFixed(2)} 米；残差平方=${(r*r).toFixed(2)} 米²\n本图只是一条墙距观测，不是第7课两观测总成本。`;
        root.querySelector('.robot').setAttribute('cx', String(30+40*x));
      } else if(type === 'transform') {
        const angle=val(root,'angle'), px=val(root,'px'), py=val(root,'py'), tx=2, ty=1;
        const c=Math.cos(angle*Math.PI/180),s=Math.sin(angle*Math.PI/180);
        const x=c*px-s*py+tx,y=s*px+c*py+ty;
        out.textContent=`cos=${c.toFixed(3)}, sin=${s.toFixed(3)}\nx=${c.toFixed(3)}×${px}−${s.toFixed(3)}×${py}+2=${x.toFixed(3)} 米\ny=${s.toFixed(3)}×${px}+${c.toFixed(3)}×${py}+1=${y.toFixed(3)} 米\n蓝点：地图坐标；绿点：机器人原点 (2,1)。右为地图 x，上为地图 y。`;
        root.querySelector('.point').setAttribute('cx',String(180+30*x)); root.querySelector('.point').setAttribute('cy',String(200-30*y));
        root.querySelector('.direction').setAttribute('x2',String(240+35*c)); root.querySelector('.direction').setAttribute('y2',String(170-35*s));
      } else if(type === 'fusion') {
        const r=val(root,'r'),k=.05/(.05+r),x=1+k*.2;
        out.textContent=`预测位置=1 米，方差 P⁻=0.05 米²；测量 z=1.2 米\n测量方差 R=${r.toFixed(3)} 米²\nK=0.05/(0.05+R)=${k.toFixed(3)}\n融合位置=1+K×0.2=${x.toFixed(4)} 米；更新方差=${((1-k)*.05).toFixed(4)} 米²`;
        root.querySelector('.estimate').setAttribute('cx',String(60+(x-1)*1500));
      } else if(type === 'camera') {
        const z=val(root,'z'),u=400/z+320,v=200/z+240;
        out.textContent=`X=1 米，Y=0.5 米，Z=${z.toFixed(1)} 米\nu=400×1/Z+320=${u.toFixed(1)} 像素\nv=400×0.5/Z+240=${v.toFixed(1)} 像素\n深度越大，投影越接近主点 (320,240)。超出 640×480 画幅时点不可见。`;
        root.querySelector('.pixel').setAttribute('cx',String(u));root.querySelector('.pixel').setAttribute('cy',String(v));
      } else if(type === 'world') {
        const theta=val(root,'theta'),n=val(root,'n'),pred=theta*n,truth=.8*n;
        out.textContent=`模型每单位动作移动 θ=${theta.toFixed(2)} 米；假设真实为0.8米\n连续 ${n} 步动作 a=1：预测 ${pred.toFixed(2)} 米，真实 ${truth.toFixed(2)} 米\n误差=${(pred-truth).toFixed(2)} 米。这里固定真实动力学，观察模型误差如何累积。`;
        root.querySelector('.prediction').setAttribute('width',String(pred*20));root.querySelector('.truth').setAttribute('width',String(truth*20));
      }
    }
    root.addEventListener('input',draw); draw();
  });
})();
