const fs=require('fs');
let s=fs.readFileSync('www/js/app.js','utf8');
const o1=`(inl?'up':'down')`;
const i1=s.indexOf(o1);
console.log('idx1',i1);
if(i1<0){console.log('MISS1');process.exitCode=1}
s=s.slice(0,i1)+`'down'`+s.slice(i1+o1.length);
const o2=`'fs-gpb'+(inl?' on':'')`;
const i2=s.indexOf(o2);
console.log('idx2',i2);
if(i2<0){console.log('MISS2');process.exitCode=1}
s=s.slice(0,i2)+`'fs-gpb'`+s.slice(i2+o2.length);
fs.writeFileSync('www/js/app.js',s);
console.log('ok');
