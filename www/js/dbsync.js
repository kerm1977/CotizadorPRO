// ===== dbsync.js — Base SQLite real en el servidor =====
// Escribe primero en la base remota (Flask/SQLite); IndexedDB y localStorage
// quedan como respaldo para trabajar offline. Al recuperar conexión, sincroniza.
var CDB={
  url0:'http://192.168.100.129:5000',
  url:'',on:false,q:[],_p:0,_t:0
};
try{CDB.url=localStorage.getItem('cpro_api')||CDB.url0}catch(e){CDB.url=CDB.url0}
try{CDB.q=JSON.parse(localStorage.getItem('cpro_dbsync_q')||'[]')}catch(e){CDB.q=[]}
function cdbSave(){try{localStorage.setItem('cpro_dbsync_q',JSON.stringify(CDB.q.slice(0,400)))}catch(e){}}
function cdbReq(path,body){
  var u=CDB.url+'/api/cpro'+path;
  var P=window.Capacitor&&window.Capacitor.Plugins;
  if(P&&P.CapacitorHttp){
    return P.CapacitorHttp.request({method:body?'POST':'GET',url:u,headers:{'Content-Type':'application/json'},data:body||undefined}).then(function(r){CDB.on=true;var d=r.data;return typeof d=='string'?JSON.parse(d):d}).catch(function(e){CDB.on=false;throw e})
  }
  return fetch(u,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):null}).then(function(r){return r.json()}).then(function(j){CDB.on=true;return j}).catch(function(e){CDB.on=false;throw e})
}
function dbsyncPut(st,id,data){cdbReq('/put',{store:st,id:String(id),data:data}).then(dbsyncFlush).catch(function(){CDB.q.push({a:'put',st:st,id:String(id),data:data});cdbSave()})}
function dbsyncDel(st,id){cdbReq('/del',{store:st,id:String(id)}).then(dbsyncFlush).catch(function(){CDB.q.push({a:'del',st:st,id:String(id)});cdbSave()})}
function dbsyncFlush(){if(!CDB.on||!CDB.q.length)return;var q=CDB.q.splice(0,CDB.q.length);cdbSave();q.forEach(function(o){if(o.a=='put')dbsyncPut(o.st,o.id,o.data);else dbsyncDel(o.st,o.id)})}
function dbsyncCfg(){var o={};try{for(var i=0;i<localStorage.length;i++){var k=localStorage.key(i);if(k&&k.indexOf('cpro_')==0&&k!='cpro_dbsync_q'&&k!='cpro_api')o[k]=localStorage.getItem(k)}}catch(e){}dbsyncPut('cfg','settings',o)}
function dbsyncPull(){
  cdbReq('/all').then(function(j){
    var d=(j&&j.data)||{};CDB._p=1;
    ['q','cat','cli'].forEach(function(st){var docs=d[st]||{};Object.keys(docs).forEach(function(id){var rec=docs[id];if(rec&&typeof rec=='object'&&rec.id===undefined)rec.id=isNaN(+id)?id:+id;idb('put',0,rec,st)})});
    var cfg=(d.cfg||{}).settings;
    if(cfg){Object.keys(cfg).forEach(function(k){if(String(k).indexOf('cpro_')==0)try{localStorage.setItem(k,cfg[k])}catch(e){}});if(cfg.cpro_logo){try{LOGO=cfg.cpro_logo;LIM.src=cfg.cpro_logo}catch(e){}}}
    CDB._p=0;dbsyncFlush();if(window.clog)clog('dbsync: base remota cargada');if(window.syncHome)try{syncHome()}catch(e){}
  }).catch(function(){if(window.clog)clog('dbsync: sin servidor — modo offline')})
}
// Llamado por el hook de idb() tras cada put/del (con _p para no hacer eco en pull)
window.CPROSYNC=function(m,st,k,v){if(CDB._p)return;if(m=='put')dbsyncPut(st,v&&v.id!==undefined?v.id:k,v);else dbsyncDel(st,k)};
// Ajustes → un solo documento 'cfg/settings' cada 20 s y al ocultar la app
setInterval(function(){dbsyncCfg();dbsyncFlush()},20000);
document.addEventListener('visibilitychange',function(){if(document.visibilityState=='hidden')dbsyncCfg()});
