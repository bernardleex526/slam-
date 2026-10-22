// 用实际页面脚本和共享存储模拟多个页面，防止学习记录回退或丢失。
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../assets/app.js'), 'utf8');
const memory = new Map();
const storage = {
  get length() { return memory.size; },
  key: i => [...memory.keys()][i],
  getItem: k => memory.get(k) ?? null,
  setItem: (k,v) => memory.set(k,String(v)),
  removeItem: k => memory.delete(k),
};
function element(field) {
  return {dataset:{save:field},value:'',events:{},addEventListener(type, fn){this.events[type]=fn;}};
}
function page(id) {
  const answer=element('answer'), reason=element('reason'), exp=element(), imp=element();
  let exported;
  const document={
    body:{dataset:{lesson:id}},
    getElementById:key => key==='import-progress'?imp:{textContent:''},
    querySelectorAll:key => key==='[data-save]'?[answer,reason]:key==='[data-export]'?[exp]:[],
    createElement:()=>({click(){}}),
  };
  vm.runInNewContext(source,{document,localStorage:storage,Blob,URL:{createObjectURL:b=>{exported=b;return 'test';},revokeObjectURL(){}},setTimeout:fn=>fn()});
  return {
    answer,reason,
    write(field,value){this[field].value=value;this[field].events.input();},
    async export(){exp.events.click();return JSON.parse(await exported.text()).records;},
    async import(records,version=2){await imp.events.change({target:{files:[{size:100,text:async()=>JSON.stringify({version,records})}]}});},
  };
}
(async()=>{
  memory.set('slam-learning-v1',JSON.stringify({'0003':{answer:'旧版答案'}}));
  const first=page('0001'),second=page('0002'),home=page('home');
  first.write('answer','第一课'); second.write('answer','第二课');
  let records=await home.export();
  assert.equal(records['0001'].answer,'第一课');
  assert.equal(records['0002'].answer,'第二课');
  // 旧第 3 课（坐标和向量）在 33 课版是第 6 课。
  assert.equal(records['0006'].answer,'旧版答案');
  assert.equal(records['0003'],undefined);
  const duplicate=page('0001');
  first.write('answer','新的答案'); duplicate.write('reason','另一个字段');
  records=await home.export();
  assert.equal(records['0001'].answer,'新的答案');
  assert.equal(records['0001'].reason,'另一个字段');
  await home.import({'0003':{answer:'导入答案'}});
  records=await home.export();
  assert.equal(records['0001'].answer,'新的答案');
  assert.equal(records['0002'].answer,'第二课');
  assert.equal(records['0003'].answer,'导入答案');
  await home.import({'0007':{answer:'旧导出第七课'}},1);
  records=await home.export();
  assert.equal(records['0010'].answer,'旧导出第七课');
  assert.equal(page('0001').answer.value,'新的答案');
  duplicate.write('answer','最后一次保存');
  assert.equal(page('0001').answer.value,'最后一次保存');
  console.log('Cross-page saves, field isolation, legacy records, 23→33 migration, import/export and reload passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
