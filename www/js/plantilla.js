// ===== Plantilla de navegación SPA =====
// Todas las "páginas" (.pg) heredan de aquí: pgShow muestra una y esconde
// las demás; pgBack regresa con una pila de historial.
var _pgStack=[];
function pgShow(id){
  var cur=document.querySelector('.pg.on');
  if(cur&&cur.id!=id)_pgStack.push(cur.id);
  if(_pgStack.length>20)_pgStack.splice(0,_pgStack.length-20);
  $$('.pg').forEach(function(p){p.classList.remove('on')});
  var m=document.getElementById(id);
  if(m){m.classList.add('on');window.scrollTo(0,0)}
  var f=document.getElementById('savefab');if(f)f.style.display=(id=='mCot')?'flex':'none';
  var pf=document.getElementById('pgfab');if(pf)pf.style.display=(id=='pg-home')?'none':'flex';
}
function pgBack(){
  var t=_pgStack.length?_pgStack.pop():'pg-home';
  pgShow(t);
}
function pgHome(){_pgStack=[];pgShow('pg-home')}
