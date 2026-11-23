/* Cuentas bancarias y medios de pago del perfil (Mi Perfil → Cuentas) */
(function(){
var Q=function(s){return document.querySelector(s)};
var E=function(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})};
var T=function(m){if(typeof toast=='function')toast(m)};
var KEY='cpro_cuentas';

var F_BANCO=[
  {id:'tipo',l:'Tipo de cuenta',o:[['Ahorros','bi-piggy-bank'],['Corriente','bi-arrow-left-right'],['Sueldo','bi-briefcase'],['CTS','bi-shield-check']]},
  {id:'mon',l:'Moneda',o:[['Soles (PEN)','S/'],['Dólares (USD)','$']]},
  {id:'num',l:'Número de cuenta',ph:'Número de cuenta',im:'numeric'},
  {id:'cci',l:'CCI (20 dígitos)',ph:'Código de Cuenta Interbancario',im:'numeric',max:20},
  {id:'tit',l:'Titular',ph:'NOMBRE DEL TITULAR',k:'up'}
];
var F_BILL=[
  {id:'num',l:'Número de teléfono',ph:'Solo números',k:'tel'},
  {id:'mail',l:'Correo electrónico (si el servicio lo pide)',ph:'correo@ejemplo.com',k:'mail'},
  {id:'tit',l:'Titular (nombre en la cuenta)',ph:'NOMBRE QUE APARECE EN LA CUENTA',k:'up'}
];
var F_COD=[
  {id:'num',l:'Código o ID de comercio',ph:'Código de comercio'},
  {id:'tit',l:'Titular / razón social',ph:'NOMBRE DEL COMERCIO',k:'up'}
];
var TEL={pe:['+51',9],bz:['+501',7],cr:['+506',8],sv:['+503',8],gt:['+502',8],hn:['+504',8],ni:['+505',8],pa:['+507',8],co:['+57',10],cl:['+56',9]};
var MAILRE=/^[a-z0-9](?:[a-z0-9._%+-]*[a-z0-9])?@[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*\.[a-z]{2,}$/;
function telOf(){return TEL[Q('#bk-pais').value]||['+',15]}
var CIC={banco:'bi-bank',billetera:'bi-phone',efectivo:'bi-cash-coin',pos:'bi-credit-card-2-front',enlace:'bi-link-45deg'};
var F_LINK=[
  {id:'num',l:'Enlace de pago',ph:'https://…',k:'url'},
  {id:'tit',l:'Titular (nombre en la cuenta)',ph:'NOMBRE QUE APARECE EN LA CUENTA',k:'up'}
];
var LINKS={
  pe:[['Pasarelas locales',['Culqi (Culqi Link)','Niubiz (Pago Link)','Izipay (Link de pago)']],['Internacionales',['Mercado Pago','PayPal.me']]],
  cr:[['Pasarelas locales',['Tilopay','ONVO Pay','BAC Credomatic (Link de pago)']],['Internacionales',['PayPal.me']]],
  pa:[['Pasarelas locales',['PágueloFácil','Cuanto','Tilopay']],['Internacionales',['PayPal.me']]],
  gt:[['Pasarelas locales',['Recurrente','Pagalo']],['Internacionales',['PayPal.me']]],
  sv:[['Pasarelas locales',['N1co (Links de pago)','Wompi El Salvador']],['Internacionales',['PayPal.me']]],
  hn:[['Pasarelas locales',['PixelPay']],['Internacionales',['PayPal.me']]],
  ni:[['Internacionales',['PayPal.me']]],
  bz:[['Internacionales',['PayPal.me']]],
  co:[['Pasarelas locales',['Wompi (Bancolombia)','Bold (Link de pago)','ePayco','PayU']],['Internacionales',['Mercado Pago','PayPal.me']]],
  cl:[['Pasarelas locales',['Webpay (Transbank Link de pago)','Flow','Khipu']],['Internacionales',['Mercado Pago','PayPal.me']]]
};
var LDESC='Pegá el enlace de cobro de tu plataforma. Se guarda como una cuenta más y el cliente paga desde ese enlace.';

var PAISES={
  pe:{n:'Perú',flag:'🇵🇪',cats:[
    {k:'banco',n:'Cuenta bancaria',sub:'Bancos, cajas y financieras',f:F_BANCO,g:[
      ['Banca múltiple — principales',['Banco de Crédito del Perú (BCP)','BBVA Perú','Interbank','Scotiabank Perú']],
      ['Banca comercial, de consumo y microfinanzas',['BanBif (Banco Interamericano de Finanzas)','Banco Pichincha','Mibanco','Compartamos Banco','Banco Falabella','Banco Ripley','Bancom','Banco GNB Perú','Alfin Banco','Santander Consumer Perú','Banco BTG Pactual Perú','Revolut Bank Perú']],
      ['Banca corporativa y de inversión',['Banco Santander Perú','Citibank del Perú','Banco BCI Perú','ICBC Peru Bank','Bank of China (Perú)']],
      ['Banca estatal',['Banco de la Nación','Agrobanco','COFIDE (Corporación Financiera de Desarrollo)']],
      ['Cajas municipales',['Caja Arequipa','Caja Huancayo','Caja Piura','Caja Cusco']],
      ['Empresas financieras',['Financiera Confianza','Financiera Efectiva','Financiera Qapaq']]
    ]},
    {k:'billetera',n:'Billetera digital / QR',sub:'Yape, Plin, BIM, Mercado Pago…',f:F_BILL,g:[
      ['Billeteras locales P2P / QR',['Yape','Plin','BIM (Billetera Móvil)']],
      ['Otras billeteras y prepago',['Mercado Pago','Ligo','Agora Pay','Prex Perú','PayPal']],
      ['Billeteras internacionales NFC',['Apple Pay','Google Pay / Google Wallet']]
    ]},
    {k:'efectivo',n:'Pago en efectivo (online)',sub:'PagoEfectivo, KasNet',f:F_COD,g:[['Código CIP',['PagoEfectivo','KasNet']]]},
    {k:'pos',n:'Datáfono (POS)',sub:'Niubiz, Izipay',f:F_COD,g:[['Redes de datáfonos',['Niubiz','Izipay']]]}
  ],desc:{
    'Yape':'La plataforma dominante en Perú. Funciona con número de celular o código QR, es gratuita e interoperable con Plin y otras billeteras.',
    'Plin':'Integrada en las apps de BBVA, Interbank, Scotiabank, BanBif y varias Cajas. Envía y recibe dinero al instante desde y hacia Yape.',
    'BIM (Billetera Móvil)':'Billetera de inclusión financiera que opera incluso sin internet; interoperable con Yape y Plin.',
    'Apple Pay':'Aceptado en comercios con POS contactless. Compatible con tarjetas locales e internacionales.',
    'Google Pay / Google Wallet':'Operativo en Android y Wear OS. Aceptado en cualquier datáfono sin contacto.',
    'PagoEfectivo':'Genera un código CIP para compras en línea que se paga en efectivo en bodegas, farmacias o agentes.',
    'KasNet':'Red de agentes donde se pagan en efectivo los códigos CIP de compras en línea.',
    'Niubiz':'Red de terminales de pago: tarjetas, Apple Pay, Google Pay y QR de Yape/Plin.',
    'Izipay':'Red de terminales de pago: tarjetas, Apple Pay, Google Pay y QR de Yape/Plin.',
    'Mercado Pago':'Pagos con QR, comercio electrónico y tarjetas prepago.',
    'PayPal':'Pagos y transferencias internacionales.',
    '__cci':'El CCI permite transferencias inmediatas 24/7 entre cualquier banco o caja del país.'
  }}
};

PAISES.pe.reg='Sudamérica';
F_BANCO[3].re=/^\d{20}$/;F_BANCO[3].err='El CCI debe tener 20 dígitos';
function build(c){
  var fb=[{id:'tipo',l:'Tipo de cuenta',o:(c.tipos||['Ahorros','Corriente']).map(function(t){return[t,'bi-wallet2']})},{id:'mon',l:'Moneda',o:c.mon},{id:'num',l:'Número de cuenta',ph:'Número de cuenta',im:'numeric'}];
  if(c.ib)fb.push({id:'cci',l:c.ib.l,ph:c.ib.ph||c.ib.l,max:c.ib.max,re:c.ib.re,err:c.ib.err});
  if(c.doc)fb.push({id:'doc',l:c.doc,ph:c.doc});
  fb.push({id:'tit',l:'Titular',ph:'NOMBRE DEL TITULAR',k:'up'});
  var cats=[{k:'banco',n:'Cuenta bancaria',sub:'Bancos, cooperativas y financieras',f:fb,g:c.bancos}];
  if(c.bill)cats.push({k:'billetera',n:'Billetera digital / QR',sub:c.bill[0][1].slice(0,3).join(', ')+'…',f:F_BILL,g:c.bill});
  return{n:c.n,flag:c.flag,reg:c.reg,cats:cats,desc:c.desc||{}}}
(window.CPRO_PAISES||[]).forEach(function(c){PAISES[c.k]=build(c)});
Object.keys(LINKS).forEach(function(k){if(PAISES[k])PAISES[k].cats.push({k:'enlace',n:'Enlace de pago',sub:LINKS[k][0][1].slice(0,3).join(', ')+'…',f:F_LINK,g:LINKS[k]})});

/* ===== Selector estético (hoja inferior) en lugar del desplegable del sistema ===== */
function ini(t){return String(t||'').replace(/\(.*?\)/g,'').split(/\s+/).filter(function(w){return w&&!/^(de|del|la|el|y|\/)$/i.test(w)}).slice(0,2).map(function(w){return w.charAt(0)}).join('').toUpperCase()||'•'}
function icHtml(o){var ic=o&&o.getAttribute('data-ic');if(ic&&ic.indexOf('bi-')==0)return'<i class="bi '+ic+'"></i>';if(ic)return E(ic);return E(ini(o&&o.text))}
function hue(t){var h=0;for(var i=0;i<t.length;i++)h=(h*31+t.charCodeAt(i))%360;return h}
function fsync(sel){var b=sel&&sel._fb;if(!b)return;var o=sel.options[sel.selectedIndex],ph=!o||o.value==='';
  b.disabled=sel.disabled;b.classList.toggle('ph',ph);
  b.querySelector('.fsel-v').textContent=o?o.text:'';
  var i=b.querySelector('.fsel-i');i.innerHTML=ph?'<i class="bi '+(sel.getAttribute('data-ic')||'bi-list-ul')+'"></i>':icHtml(o);
  i.style.cssText=!ph&&!o.getAttribute('data-ic')?'background:hsla('+hue(o.text)+',70%,55%,.16);color:hsl('+hue(o.text)+',60%,45%)':''}
function enhance(sel,title){if(!sel)return;if(sel._fb)return fsync(sel);sel.classList.add('d-none');
  var b=document.createElement('button');b.type='button';b.className='fsel';
  b.innerHTML='<span class="fsel-i"></span><span class="fsel-v"></span><i class="bi bi-chevron-down fsel-ch"></i>';
  sel.parentNode.insertBefore(b,sel.nextSibling);sel._fb=b;b.onclick=function(){if(!sel.disabled)sheet(sel,title)};fsync(sel)}
function sheet(sel,title){
  var n=0,h='';
  function row(o){if(o.value==='')return'';n++;var sub=o.getAttribute('data-sub'),own=o.getAttribute('data-ic');
    return'<button type="button" class="fs-o'+(sel.value===o.value?' on':'')+'" data-v="'+E(o.value)+'"><span class="fs-ic"'+(own?'':' style="background:hsla('+hue(o.text)+',70%,55%,.16);color:hsl('+hue(o.text)+',60%,45%)"')+'>'+icHtml(o)+'</span><span class="fs-t">'+E(o.text)+(sub?'<small>'+E(sub)+'</small>':'')+'</span><i class="bi bi-check-circle-fill fs-ck"></i></button>'}
  Array.prototype.forEach.call(sel.children,function(c){if(c.tagName=='OPTGROUP'){h+='<div class="fs-grp"><div class="fs-g">'+E(c.label)+'</div>'+Array.prototype.map.call(c.children,row).join('')+'</div>'}else h+=row(c)});
  var ov=document.createElement('div');ov.className='fsheet-ov';
  ov.innerHTML='<div class="fsheet" role="dialog" aria-label="'+E(title)+'"><div class="fs-grab"></div><div class="fs-h"><span class="fs-hi"><i class="bi '+(sel.getAttribute('data-ic')||'bi-list-ul')+'"></i></span><b>'+E(title)+'</b><button type="button" class="fs-x" title="Cerrar"><i class="bi bi-x-lg"></i></button></div>'+(n>6?'<div class="fs-s"><i class="bi bi-search"></i><input type="search" class="halo-inp" placeholder="Buscar…"></div>':'')+'<div class="fs-l">'+h+'<div class="fs-none d-none">Sin resultados</div></div></div>';
  document.body.appendChild(ov);
  function close(){ov.classList.remove('on');setTimeout(function(){ov.remove()},260)}
  ov.onclick=function(e){if(e.target===ov||e.target.closest('.fs-x'))return close();var o=e.target.closest('.fs-o');if(!o)return;
    sel.value=o.getAttribute('data-v');sel.dispatchEvent(new Event('change'));fsync(sel);close()};
  var s=ov.querySelector('.fs-s input');if(s)s.oninput=function(){var q=s.value.trim().toLowerCase(),any=0;
    Array.prototype.forEach.call(ov.querySelectorAll('.fs-o'),function(o){var m=!q||o.textContent.toLowerCase().indexOf(q)>=0;o.classList.toggle('d-none',!m);if(m)any=1});
    Array.prototype.forEach.call(ov.querySelectorAll('.fs-grp'),function(g){g.classList.toggle('d-none',!g.querySelector('.fs-o:not(.d-none)'))});
    ov.querySelector('.fs-none').classList.toggle('d-none',!!any)};
  requestAnimationFrame(function(){ov.classList.add('on');var on=ov.querySelector('.fs-o.on');if(on)on.scrollIntoView({block:'center'})})}

/* ===== Datos ===== */
function load(){try{return JSON.parse(localStorage.getItem(KEY))||[]}catch(e){return[]}}
function save(a){localStorage.setItem(KEY,JSON.stringify(a))}
function cat(){var p=PAISES[Q('#bk-pais').value];return p&&p.cats.filter(function(c){return c.k==Q('#bk-cat').value})[0]}
function syncAll(){['#bk-pais','#bk-cat','#bk-ent'].forEach(function(s){fsync(Q(s))})}

function fillPais(){var regs={};Object.keys(PAISES).forEach(function(k){var r=PAISES[k].reg||'Otros';(regs[r]=regs[r]||[]).push(k)});
  Q('#bk-pais').innerHTML='<option value="">Selecciona tu país</option>'+['Centroamérica','Sudamérica','Otros'].filter(function(r){return regs[r]}).map(function(r){return'<optgroup label="'+r+'">'+regs[r].sort(function(a,b){return PAISES[a].n.localeCompare(PAISES[b].n,'es')}).map(function(k){return'<option value="'+k+'" data-ic="'+PAISES[k].flag+'" data-sub="'+PAISES[k].cats.map(function(c){return c.n}).join(' · ')+'">'+E(PAISES[k].n)+'</option>'}).join('')+'</optgroup>'}).join('')}
function onPais(){var p=PAISES[Q('#bk-pais').value],c=Q('#bk-cat');c.disabled=!p;c.innerHTML='<option value="">Selecciona el tipo de cuenta</option>'+(p?p.cats.map(function(x){return'<option value="'+x.k+'" data-ic="'+CIC[x.k]+'" data-sub="'+E(x.sub||'')+'">'+E(x.n)+'</option>'}).join(''):'');onCat()}
function onCat(){var c=cat(),s=Q('#bk-ent');s.disabled=!c;s.setAttribute('data-ic',c?CIC[c.k]:'bi-building');s.innerHTML='<option value="">Selecciona la entidad</option>'+(c?c.g.map(function(g){return'<optgroup label="'+E(g[0])+'">'+g[1].map(function(n){return'<option>'+E(n)+'</option>'}).join('')+'</optgroup>'}).join(''):'');onEnt()}
function onEnt(){var c=cat(),en=Q('#bk-ent').value,p=PAISES[Q('#bk-pais').value],d=Q('#bk-desc'),fw=Q('#bk-fields');
  d.textContent=en&&p?(c.k=='enlace'?LDESC:(p.desc[en]||(c.k=='banco'?p.desc.__cci||'':''))):'';
  fw.innerHTML=en&&c?c.f.map(function(f){return'<div class="bk-f"><span class="cs-l">'+E(f.l)+'</span>'+(f.o?'<select class="form-select" data-f="'+f.id+'" data-ic="'+(f.id=='mon'?'bi-currency-exchange':'bi-wallet2')+'">'+f.o.map(function(o){return'<option data-ic="'+E(o[1])+'">'+E(o[0])+'</option>'}).join('')+'</select>':(f.k=='tel'?'<div class="input-group"><span class="input-group-text bk-cc">'+E(telOf()[0])+'</span><input class="form-control" data-f="'+f.id+'" data-k="tel" type="tel" inputmode="numeric" autocomplete="tel-national" maxlength="'+telOf()[1]+'" placeholder="'+E(f.ph||'')+'"></div>':
    f.k=='url'?'<div class="input-group"><span class="input-group-text bk-cc"><i class="bi bi-link-45deg"></i></span><input class="form-control" data-f="'+f.id+'" data-k="url" type="url" inputmode="url" autocapitalize="off" autocorrect="off" spellcheck="false" placeholder="'+E(f.ph||'')+'"></div>':
    f.k=='mail'?'<input class="form-control" data-f="'+f.id+'" data-k="mail" type="email" inputmode="email" autocapitalize="off" autocorrect="off" spellcheck="false" autocomplete="email" placeholder="'+E(f.ph||'')+'">':
    '<input class="form-control" data-f="'+f.id+'"'+(f.k?' data-k="'+f.k+'"':'')+(f.k=='up'?' autocapitalize="characters" style="text-transform:uppercase"':'')+' placeholder="'+E(f.ph||'')+'"'+(f.im?' inputmode="'+f.im+'"':'')+(f.max?' maxlength="'+f.max+'"':'')+'>'))+'</div>'}).join(''):'';
  if(c)c.f.forEach(function(f){if(f.o)enhance(fw.querySelector('[data-f="'+f.id+'"]'),f.l)});
  Q('#bk-save').classList.toggle('d-none',!en);syncAll()}

var GCL={};
function list(){var a=load(),el=Q('#bk-list');if(!el)return;
  var card=function(x,i){var lab=(PAISES[x.p]&&PAISES[x.p].n)||x.p,ct=PAISES[x.p]&&PAISES[x.p].cats.filter(function(c){return c.k==x.c})[0],cn=ct?ct.n:'';var det=Object.keys(x.f||{}).filter(function(k){return x.f[k]}).map(function(k){return'<div class="r"><span class="mut">'+E(x.l&&x.l[k]||k)+':</span> '+(x.c=='enlace'&&k=='num'?'<a href="'+E(x.f[k])+'" target="_blank" rel="noopener" style="word-break:break-all">'+E(x.f[k])+'</a>':E(x.f[k]))+'</div>'}).join('');
    return'<div class="ccard'+(x.show===false?' off':'')+'"><div class="ccard-h"><span class="ccard-av"><i class="bi '+(CIC[x.c]||'bi-bank')+'"></i></span><span class="ccard-t"><b>'+(PAISES[x.p]?PAISES[x.p].flag+' ':'')+E(x.e)+'</b><span class="mut">'+E((x.f&&x.f.num)||'')+' · '+E(cn||lab)+'</span></span><label class="bk-sw form-switch" title="Mostrar en la cotización"><input type="checkbox" class="form-check-input" data-bsw="'+i+'"'+(x.show===false?'':' checked')+'><span>Mostrar</span></label><i class="bi bi-chevron-down ccard-ch"></i></div><div class="ccard-b">'+(det||'<div class="r mut">Sin datos</div>')+
      '<div class="bk-act"><button type="button" class="btn btn-sm btn-outline-primary" data-bed="'+i+'"><i class="bi bi-pencil"></i> Editar</button><button type="button" class="btn btn-sm btn-success" data-bsh="'+i+'"><i class="bi bi-whatsapp"></i> Compartir</button><button type="button" class="btn btn-sm btn-outline-danger" data-bdel="'+i+'"><i class="bi bi-trash"></i> Eliminar</button></div></div></div>'};
  var ord=[],gp={};a.forEach(function(x,i){if(!gp[x.p]){gp[x.p]=[];ord.push(x.p)}gp[x.p].push(card(x,i))});
  el.innerHTML=a.length?visBar(a)+ord.map(function(k){var p=PAISES[k];return'<div class="bk-grp'+(GCL[k]?'':' open')+'" data-gp="'+E(k)+'"><div class="bk-gh"><span class="bk-gf">'+(p?p.flag:'🌐')+'</span><b>'+E(p?p.n:(k||'Otros medios'))+'</b><span class="bk-gn">'+gp[k].length+'</span><i class="bi bi-chevron-down bk-gc"></i></div><div class="bk-gb">'+gp[k].join('')+'</div></div>'}).join(''):'<p class="mut" style="padding:10px 4px">Todavía no agregaste cuentas</p>';
  el.onchange=function(e){var s=e.target.closest('[data-bsw]');if(!s)return;var a3=load(),k=+s.getAttribute('data-bsw');if(!a3[k])return;a3[k].show=s.checked;save(a3);
    var cd=s.closest('.ccard');if(cd)cd.classList.toggle('off',!s.checked);var vn=Q('#bk-vis-n');if(vn)vn.textContent=visN(a3);rer();T(s.checked?'Se mostrará en la cotización':'Oculta en la cotización')};
  Array.prototype.forEach.call(el.querySelectorAll('[data-ball]'),function(bt){bt.onclick=function(){var v=bt.getAttribute('data-ball')=='1',a3=load();a3.forEach(function(x){x.show=v});save(a3);list();rer();T(v?'Todas las cuentas en la cotización':'Ninguna cuenta en la cotización')}});
  Array.prototype.forEach.call(el.querySelectorAll('.bk-gh'),function(h){h.onclick=function(){var g=h.parentNode;g.classList.toggle('open');GCL[g.getAttribute('data-gp')]=!g.classList.contains('open')}});
  Array.prototype.forEach.call(el.querySelectorAll('.ccard'),function(r){r.onclick=function(e){if(e.target.closest('.bk-sw'))return;var b=e.target.closest('[data-bdel],[data-bed],[data-bsh]');
    if(b){var i=+(b.getAttribute('data-bdel')||b.getAttribute('data-bed')||b.getAttribute('data-bsh')),x=load()[i];if(!x)return;
      if(b.hasAttribute('data-bdel'))confirmDel(x,function(){var a2=load();a2.splice(i,1);save(a2);if(EDIT==i)resetEdit();else if(EDIT>i)EDIT--;list();rer();T('Cuenta eliminada')});
      else if(b.hasAttribute('data-bed'))edit(i);else share(x);return}
    if(e.target.closest('.ccard-h'))r.classList.toggle('open')}})}

function fmt(x){var f=x.f||{},l=x.l||{},sh=function(k){return String(l[k]||k).split('(')[0].trim()};
  return[f.tipo,f.mon,f.num,f.cci?sh('cci')+': '+f.cci:'',f.doc?sh('doc')+': '+f.doc:'',f.mail,f.tit].filter(Boolean).join(' · ')}
function visN(a){return a.filter(function(x){return x.show!==false}).length+' de '+a.length}
function visBar(a){return'<div class="bk-vis"><span><i class="bi bi-eye"></i> Mostrar en la cotización: <b id="bk-vis-n">'+visN(a)+'</b></span><div class="bk-vis-b"><button type="button" class="btn btn-sm btn-outline-primary" data-ball="1"><i class="bi bi-check2-all"></i> Todas</button><button type="button" class="btn btn-sm btn-outline-secondary" data-ball="0"><i class="bi bi-eye-slash"></i> Ninguna</button></div></div>'}
window.cproCtas=function(){return load().filter(function(x){return x.show!==false}).map(function(x){var f=x.f||{},l=x.l||{},p=PAISES[x.p],sh=function(k){return String(l[k]||k).split('(')[0].trim()},ct=p&&p.cats.filter(function(c){return c.k==x.c})[0];
  return{e:x.e,c:x.c,cat:(ct?ct.n:'')||x.cat||'',flag:p?p.flag:'🌐',pais:p?p.n:'',num:f.num||'',det:[f.tipo,f.mon,f.cci?sh('cci')+': '+f.cci:'',f.doc?sh('doc')+': '+f.doc:'',f.mail].filter(Boolean).join(' · '),tit:f.tit||'',v:fmt(x),u:x.c=='enlace'?f.num:''}})};
function rer(){try{if(typeof render=='function')render()}catch(e){}try{qpickBtn()}catch(e){}}
function share(x){var p=PAISES[x.p],t=['*'+x.e+'*'+(p?' ('+p.n+')':'')];Object.keys(x.f||{}).forEach(function(k){if(x.f[k])t.push((x.l&&x.l[k]||k)+': '+x.f[k])});
  var txt=t.join('\n'),PL=window.Capacitor&&Capacitor.Plugins;
  if(PL&&PL.Share)PL.Share.share({title:x.e,text:txt,dialogTitle:'Compartir por WhatsApp'}).catch(function(){});else window.open('https://wa.me/?text='+encodeURIComponent(txt),'_blank')}
function confirmDel(x,fn){var ov=document.createElement('div');ov.className='fsheet-ov ctr';
  ov.innerHTML='<div class="fsheet bk-del" role="dialog" aria-label="Eliminar cuenta"><div class="bk-del-ic"><i class="bi bi-trash3"></i></div><b class="bk-del-t">¿Eliminar esta cuenta?</b><div class="bk-del-n"><i class="bi '+(CIC[x.c]||'bi-bank')+'"></i> '+E(x.e)+'</div><p class="mut bk-del-m">Se borrará de tus cuentas y dejará de aparecer en tus cotizaciones.</p><div class="bk-del-b"><button type="button" class="btn btn-outline-secondary" data-no>Cancelar</button><button type="button" class="btn btn-danger" data-yes><i class="bi bi-trash"></i> Eliminar</button></div></div>';
  document.body.appendChild(ov);requestAnimationFrame(function(){ov.classList.add('on')});
  function close(){ov.classList.remove('on');setTimeout(function(){ov.remove()},260)}
  ov.onclick=function(e){if(e.target==ov||e.target.closest('[data-no]'))close();else if(e.target.closest('[data-yes]')){close();fn()}}}
var EDIT=-1;
function resetEdit(){EDIT=-1;var b=Q('#bk-save');if(b)b.innerHTML='<i class="bi bi-save"></i> Guardar cuenta'}
function edit(i){var x=load()[i];if(!x)return;Q('#bk-pais').value=x.p;onPais();Q('#bk-cat').value=x.c;onCat();Q('#bk-ent').value=x.e;onEnt();
  Object.keys(x.f||{}).forEach(function(k){var el=Q('#bk-fields [data-f="'+k+'"]');if(!el)return;var v=x.f[k];if(x.c=='billetera'&&k=='num')v=v.replace(/^\+\d+\s*/,'');el.value=v;if(el._fb)fsync(el)});
  syncAll();EDIT=i;Q('#bk-save').innerHTML='<i class="bi bi-check2-circle"></i> Actualizar cuenta';
  var s=Q('#mBank .cs');if(s)s.scrollIntoView({behavior:'smooth',block:'start'});T('Editando '+x.e)}

function onSave(){var c=cat(),en=Q('#bk-ent').value;if(!c||!en)return T('Seleccioná país, tipo y entidad');
  var f={},l={};Array.prototype.forEach.call(Q('#bk-fields').querySelectorAll('[data-f]'),function(i){f[i.dataset.f]=i.value.trim()});
  c.f.forEach(function(d){l[d.id]=d.l});
  if(c.k=='billetera'){var tl=telOf();
    if(!f.num&&!f.mail)return T('Escribí el teléfono o el correo');
    if(f.num&&f.num.length!=tl[1])return T('El teléfono debe tener '+tl[1]+' dígitos');
    if(f.mail&&(!MAILRE.test(f.mail)||/\.\./.test(f.mail)))return T('Correo electrónico no válido');
    if(f.num)f.num=tl[0]+' '+f.num}
  else if(c.k=='enlace'){if(!f.num)return T('Pegá el enlace de pago');
    if(!/^https?:\/\//i.test(f.num))f.num='https://'+f.num;
    try{var u=new URL(f.num);if(!/^https?:$/.test(u.protocol)||!/\.[a-z]{2,}$/i.test(u.hostname))throw 0}catch(x){return T('El enlace no es válido')}}
  else if(!f.num)return T('Escribí el número');
  for(var i=0;i<c.f.length;i++){var fd=c.f[i];if(fd.re&&f[fd.id]){f[fd.id]=f[fd.id].replace(/[\s-]/g,'').toUpperCase();if(!fd.re.test(f[fd.id]))return T(fd.err||('Revisá '+fd.l))}}
  var a=load(),o={p:Q('#bk-pais').value,c:c.k,e:en,f:f,l:l,ts:Date.now()},up=EDIT>=0&&a[EDIT];if(up){if(a[EDIT].show===false)o.show=false;a[EDIT]=o}else a.push(o);save(a);resetEdit();
  Q('#bk-ent').value='';onEnt();list();rer();T(up?'Cuenta actualizada':'Cuenta guardada');
  if(_qret){var _r=_qret;_qret=null;if(typeof pgShow=='function')pgShow(_r)}}

/* ===== Selector de cuentas para la cotización (Información de pago) ===== */
var _qsel=null;                 // null = todas (por defecto) · [] = ninguna · [{e,num}]
var _qoff=false;                // trigger: incluir cuentas en la cotización
var _qret=null;                 // volver a esta hoja tras guardar cuenta en el perfil
function qpickCards(){var box=Q('#qpick-cards');if(!box)return;var eff=window.cproCtasPick?_qsel==null?window.cproCtas():window.cproCtasPick(_qsel):[];
  box.innerHTML=eff.length?'<div class="qctas">'+eff.map(function(x){return'<div class="qcta"><div class="qcta-h">'+(x.flag?'<span class="qcta-f">'+E(x.flag)+'</span>':'')+'<b>'+E(x.e)+'</b>'+(x.pais?'<span class="qcta-c">'+E(x.pais)+'</span>':'')+'</div>'+(x.num?'<div class="qcta-n">'+E(x.num)+'</div>':'')+(x.det||x.cat?'<div class="qcta-d">'+E([x.det,x.cat].filter(Boolean).join(' · '))+'</div>':'')+(x.tit?'<div class="qcta-t">'+E(x.tit)+'</div>':'')+'</div>'}).join('')+'</div>':''}
function qpickBtn(){var noAcc=!load().length,he=Q('#ctas-have'),ee=Q('#ctas-empty');if(he)he.classList.toggle('d-none',noAcc);if(ee)ee.classList.toggle('d-none',!noAcc);var pc=Q('#qpick-cards');if(pc)pc.classList.toggle('d-none',_qoff);qpickCards()}
function ctasSheet(){var all=load();if(!all.length)return T('Configurá cuentas en Mi Perfil → Cuentas');
  function xNum(x){return(x.f&&x.f.num)||''}
  function xCat(x){var p=PAISES[x.p],ct=p&&p.cats.filter(function(c){return c.k==x.c})[0];return ct?ct.n:(x.cat||'')}
  function isOn(x){return x.show!==false&&(_qsel==null||_qsel.some(function(s){return s.e==x.e&&s.num==xNum(x)}))}
  var gps=[],gi={};all.forEach(function(x,i){var p=PAISES[x.p],k=p?p.n:'Otros medios';if(gi[k]===undefined){gi[k]=gps.length;gps.push({flag:p?p.flag:'🌐',pais:k,rows:[]})}gps[gi[k]].rows.push(i)});
  gps.sort(function(a,b){return a.pais.localeCompare(b.pais,'es')});
  var ov=document.createElement('div');ov.className='fsheet-ov';
  ov.innerHTML='<div class="fsheet" role="dialog" aria-label="Mis cuentas configuradas"><div class="fs-grab"></div><div class="fs-h"><span class="fs-hi"><i class="bi bi-wallet2"></i></span><b>Mis cuentas configuradas</b><button type="button" class="fs-x" title="Cerrar"><i class="bi bi-x-lg"></i></button></div><div class="fs-l">'+gps.map(function(g){
    return'<div class="fs-grp"><div class="fs-g">'+E(g.flag)+' '+E(g.pais)+' · '+g.rows.length+'</div>'+g.rows.map(function(i){var x=all[i],off=x.show===false;
      return'<button type="button" class="fs-o'+(isOn(x)?' on':'')+(off?' dis':'')+'" data-i="'+i+'"><span class="fs-ic"><i class="bi '+(CIC[x.c]||'bi-bank')+'"></i></span><span class="fs-t">'+E(x.e)+'<small>'+E([xNum(x),xCat(x),x.f&&x.f.tit].filter(Boolean).join(' · '))+(off?' · oculta':'')+'</small></span><i class="bi bi-check-circle-fill fs-ck"></i></button>'}).join('')+'</div>'}).join('')+'</div><div class="fs-ft"><button type="button" class="btn btn-primary w-100" data-edit><i class="bi bi-pencil-square"></i> Editar mis cuentas</button></div></div>';
  document.body.appendChild(ov);
  function close(){ov.classList.remove('on');setTimeout(function(){ov.remove()},260)}
  function setOn(x,on){var n=xNum(x),j=-1;for(var k=0;k<_qsel.length;k++)if(_qsel[k].e==x.e&&_qsel[k].num==n)j=k;if(on&&j<0)_qsel.push({e:x.e,num:n});if(!on&&j>=0)_qsel.splice(j,1)}
  ov.onclick=function(e){if(e.target===ov||e.target.closest('.fs-x'))return close();
    if(e.target.closest('[data-edit]')){close();_qret='mPago';if(typeof pgShow=='function')pgShow('mBank');list();return}
    var o=e.target.closest('.fs-o');if(!o)return;var x=all[+o.getAttribute('data-i')];if(!x)return;
    if(x.show===false)return T('Está oculta: activá "Mostrar" en Mi Perfil → Cuentas');
    if(_qsel==null)_qsel=all.filter(function(y){return y.show!==false}).map(function(y){return{e:y.e,num:xNum(y)}});
    o.classList.toggle('on');setOn(x,o.classList.contains('on'));qpickBtn();rer()};
  requestAnimationFrame(function(){ov.classList.add('on')})}
window.cproQSel=function(){return _qsel};
window.cproQSet=function(s){_qsel=s==null?null:s.map(function(x){return{e:x.e,num:x.num}});qpickBtn()};
window.cproQOff=function(){return _qoff};
window.cproQOffSet=function(v){_qoff=!!v;var ng=Q('#npg-on');if(ng)ng.checked=!_qoff;qpickBtn()};
window.cproCtasPick=function(sel){if(_qoff)return[];var a=window.cproCtas();return sel==null?a:a.filter(function(x){return sel.some(function(s){return s.e==x.e&&s.num==x.num})})};

function init(){if(!Q('#mBank'))return;fillPais();
  Q('#bk-pais').setAttribute('data-ic','bi-globe-americas');Q('#bk-cat').setAttribute('data-ic','bi-grid');
  enhance(Q('#bk-pais'),'Selecciona tu país');enhance(Q('#bk-cat'),'Tipo de cuenta');enhance(Q('#bk-ent'),'Selecciona la entidad');
  Q('#bk-fields').addEventListener('input',function(e){var i=e.target,k=i.getAttribute&&i.getAttribute('data-k');if(!k)return;
    var v=i.value,n=k=='tel'?v.replace(/\D/g,''):k=='mail'?v.toLowerCase().replace(/\s/g,''):k=='url'?v.replace(/\s/g,''):v.toUpperCase();
    if(n!==v){var p=(i.selectionStart||n.length)-(v.length-n.length);i.value=n;try{i.setSelectionRange(p,p)}catch(x){}}});
  Q('#bk-pais').onchange=onPais;Q('#bk-cat').onchange=onCat;Q('#bk-ent').onchange=onEnt;Q('#bk-save').onclick=onSave;
  window.cproFsync=fsync;enhance(Q('#cpais'),'País del cliente');enhance(Q('#cur'),'Moneda');enhance(Q('#cf-pago'),'Tipo de pago');
  var mt=Q('#bk-mt');if(mt)mt.onclick=function(){var l=Q('#bk-list');l.classList.toggle('d-none');mt.classList.toggle('shut',l.classList.contains('d-none'))};
  var g=Q('#bankgo');if(g)g.onclick=function(){if(typeof pgShow=='function')pgShow('mBank');list()};
  var vw=Q('#ctas-view');if(vw)vw.onclick=ctasSheet;qpickBtn();
  var qa=Q('#qacc');if(qa){var qh=qa.querySelector('.acc-h')||qa;qh.onclick=function(){qa.classList.toggle('open')}}
  var goBank=function(){_qret='mPago';if(typeof pgShow=='function')pgShow('mBank');list()};var cg=Q('#ctas-go');if(cg)cg.onclick=goBank;var cg2=Q('#ctas-go2');if(cg2)cg2.onclick=goBank;
  var ng=Q('#npg-on');if(ng)ng.onchange=function(){_qoff=!ng.checked;qpickBtn();rer();T(ng.checked?'Cuentas en la cotización':'Sin cuentas en la cotización')};
  onPais();list();rer()}
init();
window.CPRO_CUENTAS=load;
})();
