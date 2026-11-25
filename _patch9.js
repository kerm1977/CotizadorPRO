const fs=require('fs');
function rep(file,o,n){
  let s=fs.readFileSync(file,'utf8');
  const i=s.indexOf(o);
  if(i<0){console.log('MISS:',file,'->',o.slice(0,90));process.exitCode=1;return}
  s=s.slice(0,i)+n+s.slice(i+o.length);
  fs.writeFileSync(file,s);
  console.log('ok  :',file,'->',o.slice(0,60));
}

// Título → "Agrega tus servicios"
rep('www/index.html',`<i class="bi bi-sliders"></i> Detalles <i class="bi bi-info-circle`,
`<i class="bi bi-sliders"></i> Agrega tus servicios <i class="bi bi-info-circle`);
// Modal del título con el nuevo nombre
rep('www/index.html',`id="detl-ov"><div class="noi"><div class="cs-t"><i class="bi bi-sliders"></i> Detalles</div>`,
`id="detl-ov"><div class="noi"><div class="cs-t"><i class="bi bi-sliders"></i> Agrega tus servicios</div>`);
// Listas colapsadas al inicio en modo inline
rep('www/js/app.js',
`(inl?' up':'down')+' fs-ch"></i></div><div class="fs-gpb'+(inl?' on':'')`,
`down')+' fs-ch"></i></div><div class="fs-gpb'`);
// Sin buscador en modo inline
rep('www/js/app.js',
`')+'<div class="fs-fx"><input type="search" class="form-control" placeholder="Buscar…"></div>`,
`')+(inl?'':'<div class="fs-fx"><input type="search" class="form-control" placeholder="Buscar…"></div>')+`);
// Guard: inp puede no existir en inline
rep('www/js/app.js',
`  var inp=ov.querySelector('.fs-fx input');inp.oninput=`,
`  var inp=ov.querySelector('.fs-fx input');if(inp)inp.oninput=`);
console.log('done');
