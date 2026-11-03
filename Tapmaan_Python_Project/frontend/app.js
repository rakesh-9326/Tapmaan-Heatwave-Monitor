/* FRONTEND -> BACKEND: request() sends JSON to backend/server.py. */
const $ = (selector) => document.querySelector(selector);
const state = {city: 'dombivli', mode: 'demo', page: 'overview', chart: 'forecast', dashboard: null, readings: [], reviewed: false, generation: 0};
const timeFormat = new Intl.DateTimeFormat('en-IN', {timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit'});
const dateFormat = new Intl.DateTimeFormat('en-IN', {timeZone: 'Asia/Kolkata', day: 'numeric', month: 'short', year: 'numeric'});
const dayFormat = new Intl.DateTimeFormat('en-IN', {timeZone: 'Asia/Kolkata', day: 'numeric', month: 'short'});
const time = (value) => timeFormat.format(new Date(value));
const date = (value) => dateFormat.format(new Date(value));
const number = (value) => Number(value).toFixed(1);
const escapeHTML = (value) => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const risk = (temperature) => temperature >= 45 ? 'Severe' : temperature >= 40 ? 'High' : temperature >= 35 ? 'Watch' : 'Normal';
const pill = (level) => `<span class="pill ${level.toLowerCase()}">${escapeHTML(level)}</span>`;
const icon = (name) => `<svg aria-hidden="true"><use href="#i-${name}"/></svg>`;
let toastTimer;

async function request(path, body) {
  if (window.TAPMAAN_API) return window.TAPMAAN_API(path, body);
  const response = await fetch(path, body ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)} : {});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'The request failed. Please retry.');
  return result;
}

function toast(message) {
  $('#toast').textContent = message;
  $('#toast').hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $('#toast').hidden = true, 4500);
}

function setBusy(busy) {
  $('#loading').hidden = !busy;
  for (const id of ['#refresh', '#empty-refresh', '#mode-demo', '#mode-live', '#city-select']) $(id).disabled = busy;
}

async function load(refresh = false) {
  const generation = ++state.generation;
  setBusy(true);
  $('#error-banner').hidden = true;
  try {
    const dashboard = refresh
      ? await request('/api/refresh', {city:state.city, mode:state.mode})
      : await request(`/api/dashboard?city=${state.city}&mode=${state.mode}`);
    const readings = await request(`/api/readings?city=${state.city}`);
    if (generation !== state.generation) return;
    state.dashboard = dashboard;
    state.readings = readings;
    renderDashboard(); renderReadings();
    if (refresh) toast(state.mode === 'demo' ? 'Sample scenario refreshed.' : 'Live weather saved successfully.');
  } catch (error) {
    if (generation !== state.generation) return;
    $('#error-banner').textContent = error.message;
    $('#error-banner').hidden = false;
    if (!state.dashboard || state.dashboard.mode !== state.mode || state.dashboard.city.id !== state.city) {
      $('#dashboard-content').hidden = true; $('#empty-state').hidden = false;
      $('#empty-text').textContent = 'No weather data is loaded for this selection. Try again or choose Sample data.';
    }
  } finally {
    if (generation === state.generation) setBusy(false);
  }
}

function renderDashboard() {
  const data = state.dashboard;
  $('#dashboard-content').hidden = data.empty;
  $('#empty-state').hidden = !data.empty;
  $('#data-time').textContent = data.empty ? '' : `${state.mode === 'demo' ? 'Sample scenario' : 'Updated'} · ${date(data.current.recorded_at)} · ${time(data.current.recorded_at)} IST`;
  if (data.empty) { $('#empty-text').textContent = data.message; return; }
  const current = data.current;
  const level = risk(data.peak);
  const active = data.alerts.filter(alert => !alert.acknowledged);
  const peak = data.forecast.reduce((best, row) => !best || row.temperature > best.temperature ? row : best, null);
  $('#current-temp').textContent = number(current.temperature);
  $('#humidity').textContent = number(current.humidity);
  $('#humidity-fill').style.width = `${current.humidity}%`;
  $('#current-risk').textContent = current.risk;
  $('#current-risk').className = `pill ${current.risk.toLowerCase()}`;
  $('#current-time').textContent = `${time(current.recorded_at)} IST`;
  $('#peak').textContent = peak ? number(peak.temperature) : '—';
  $('#peak-time').textContent = peak ? `At ${time(peak.recorded_at)}` : 'No forecast available';
  $('#alert-count').textContent = active.length;
  $('#warning-banner').classList.toggle('normal', data.peak < 40);
  $('#warning-title').textContent = level === 'Severe' ? 'Severe heat in the outlook' : level === 'High' ? 'High heat ahead. Keep an eye on the afternoon.' : level === 'Watch' ? 'Temperatures are elevated. Stay aware.' : 'No high-heat threshold crossings in the outlook.';
  $('#warning-detail').textContent = `${data.city.name} may reach ${number(data.peak)}°C in the next 24h. ${state.mode === 'demo' ? 'Fictional sample scenario' : 'Open-Meteo forecast'} · educational thresholds.`;
  if (data.stale) { $('#error-banner').hidden = false; $('#error-banner').textContent = 'Saved live data is more than 2 hours old. Refresh before interpreting the outlook.'; }
  const prediction = data.prediction;
  $('#prediction-temp').textContent = prediction.available ? number(prediction.temperature) : '—';
  $('#prediction-info').textContent = prediction.available ? `${prediction.slope >= 0 ? '+' : ''}${prediction.slope}°C/hour trend · ${time(prediction.for_time)} IST` : prediction.reason;
  $('#model-samples').textContent = prediction.available ? `Fitted to ${prediction.samples} ${state.mode === 'demo' ? 'sample' : 'live'} observations` : 'More observations are needed';
  $('#forecast-source').textContent = state.mode === 'demo' ? 'Fictional hourly outlook · 18–19 May 2026' : 'Hourly outlook from Open-Meteo';
  $('#forecast-strip').innerHTML = data.forecast.filter((_, index) => index % 3 === 0).slice(0,8).map(row => `<div class="forecast-hour"><span class="hour">${time(row.recorded_at)}</span><span class="day">${dayFormat.format(new Date(row.recorded_at))}</span>${icon('sun')}<strong>${number(row.temperature)}°</strong>${pill(row.risk)}</div>`).join('') || '<p class="empty-alert">No forecast data available.</p>';
  renderChart(); renderAlerts();
}

function renderChart() {
  const rows = state.dashboard[state.chart];
  document.querySelectorAll('[data-chart]').forEach(button => {button.classList.toggle('selected', button.dataset.chart === state.chart); button.setAttribute('aria-pressed', button.dataset.chart === state.chart);});
  $('#chart-caption').textContent = `${state.chart === 'history' ? 'Observed' : 'Forecast'} hourly temperature · °C · ${state.mode === 'demo' ? 'sample data' : 'Open-Meteo'}`;
  if (!rows.length) { $('#temperature-chart').innerHTML = '<p class="empty-alert">No temperatures to plot yet.</p>'; $('#chart-summary').textContent = ''; return; }
  const width=660, height=224, left=36, right=14, top=17, bottom=31;
  const low=Math.floor((Math.min(...rows.map(row=>row.temperature), 40)-2)/5)*5;
  const high=Math.ceil((Math.max(...rows.map(row=>row.temperature), 40)+2)/5)*5;
  const x = index => left + index / Math.max(1,rows.length-1) * (width-left-right);
  const y = temperature => top + (high-temperature)/(high-low)*(height-top-bottom);
  const line = rows.map((row,index)=>`${index?'L':'M'}${x(index).toFixed(2)},${y(row.temperature).toFixed(2)}`).join(' ');
  let grid='';
  for(let temperature=low; temperature<=high; temperature+=5) grid += `<line x1="${left}" y1="${y(temperature)}" x2="${width-right}" y2="${y(temperature)}" stroke="#e9eddf" stroke-width="1"/><text x="${left-10}" y="${y(temperature)+3}" text-anchor="end" fill="#9ba38e" font-size="9">${temperature}°</text>`;
  const indices = [...new Set([0, Math.floor((rows.length-1)/4), Math.floor((rows.length-1)/2), Math.floor((rows.length-1)*3/4), rows.length-1])];
  const labels=indices.map(index=>`<text x="${x(index)}" y="${height-9}" text-anchor="${index===0?'start':index===rows.length-1?'end':'middle'}" fill="#9ba38e" font-size="9">${time(rows[index].recorded_at)}</text>`).join('');
  $('#temperature-chart').innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${state.chart === 'history' ? 'Past' : 'Next'} 24 hours temperature chart. Range ${number(Math.min(...rows.map(r=>r.temperature)))} to ${number(Math.max(...rows.map(r=>r.temperature)))} degrees Celsius."><defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#efac78" stop-opacity=".24"/><stop offset="100%" stop-color="#efac78" stop-opacity=".01"/></linearGradient></defs>${grid}<path d="${line} L${x(rows.length-1)},${height-bottom} L${left},${height-bottom} Z" fill="url(#area)"/><line x1="${left}" y1="${y(40)}" x2="${width-right}" y2="${y(40)}" stroke="#bea98c" stroke-dasharray="4 5"/><path d="${line}" fill="none" stroke="#df8954" stroke-width="2.4" stroke-linejoin="round"/>${rows.map((row,index)=>`<circle tabindex="0" cx="${x(index)}" cy="${y(row.temperature)}" r="3" fill="#fffefa" stroke="#df8954" stroke-width="1.5"><title>${date(row.recorded_at)}, ${time(row.recorded_at)}: ${number(row.temperature)}°C, ${row.risk}</title></circle>`).join('')}${labels}</svg>`;
  $('#chart-summary').textContent = `${rows.filter(row=>row.temperature>=40).length} ${state.chart==='history'?'observations':'hours'} at or above 40°C`;
}

function renderAlerts() {
  const alerts = state.dashboard.alerts.filter(alert => state.reviewed || !alert.acknowledged);
  $('#warnings-total').textContent = alerts.length;
  $('#show-reviewed').textContent = state.reviewed ? 'Hide reviewed' : 'Show reviewed';
  $('#show-reviewed').setAttribute('aria-pressed',state.reviewed);
  $('#alerts-list').innerHTML = alerts.map(alert => `<div class="alert-row"><span class="alert-marker">${icon('bell')}</span><div><h3>${alert.kind === 'forecast' ? 'Heat forecast' : 'Current heat'} · ${number(alert.temperature)}°C</h3><p>${date(alert.recorded_at)} · ${time(alert.recorded_at)} IST · ${alert.source==='demo'?'Sample scenario':'Open-Meteo'}</p></div>${pill(alert.level)}${alert.acknowledged?'<span class="reviewed">✓ Reviewed</span>':`<button class="review-button" data-ack="${alert.id}">Mark reviewed</button>`}</div>`).join('') || '<p class="empty-alert">All clear here — no unreviewed warnings in this window.</p>';
}

function filteredReadings() {
  const source = $('#source-filter').value;
  return [...state.readings].filter(row => source === 'all' || row.source === source).sort((a,b)=>new Date(b.recorded_at)-new Date(a.recorded_at));
}

function renderReadings() {
  const rows = filteredReadings();
  $('#readings-body').innerHTML = rows.map(row=>`<tr><td>${date(row.recorded_at)} · ${time(row.recorded_at)}</td><td>${number(row.temperature)}°C</td><td>${number(row.humidity)}%</td><td>${pill(row.risk)}</td><td><span class="source-label">${row.source==='demo'?'Sample':row.source}</span></td><td>${row.source==='manual'?`<button class="delete-button" data-delete="${row.id}" aria-label="Delete manual reading from ${date(row.recorded_at)} ${time(row.recorded_at)}">Delete</button>`:'—'}</td></tr>`).join('') || '<tr><td colspan="6">No readings here yet. Add an observation or change the source filter.</td></tr>';
  $('#readings-count').textContent = `${rows.length} observation${rows.length===1?'':'s'} · ${$('#city-select').selectedOptions[0]?.textContent || state.city}`;
}

function showPage(page) {
  const titles={overview:['Heatwave overview','Keep an eye on the temperature. Get ahead of the next peak.'],readings:['Saved readings','Your observations, in one place. Ready to explore and export.'],about:['How Tapmaan works','A simple project you can follow, explain and build on.']};
  state.page=page;
  document.querySelectorAll('.page').forEach(section=>section.hidden=section.id!==`page-${page}`);
  document.querySelectorAll('[data-page]').forEach(button=>{button.classList.toggle('active',button.dataset.page===page);button.setAttribute('aria-current',button.dataset.page===page?'page':'false');});
  $('#breadcrumb').textContent={overview:'Overview',readings:'Saved readings',about:'How it works'}[page];
  $('#page-title').textContent=titles[page][0]; $('#page-subtitle').textContent=titles[page][1];
  $('.toolbar').hidden=page==='about'; $('#add-reading').hidden=page==='about';
  if(page==='readings')renderReadings();
}

async function switchMode(mode) {
  state.mode=mode;
  for(const name of ['demo','live']){$(`#mode-${name}`).classList.toggle('selected',name===mode);$(`#mode-${name}`).setAttribute('aria-pressed',name===mode);}
  await load();
}

function exportCSV() {
  const rows=filteredReadings();
  if(!rows.length){toast('There are no readings to export.');return;}
  const csv=[['city','recorded_at_IST','temperature_c','humidity_percent','risk','source'],...rows.map(row=>[state.city,row.recorded_at,row.temperature,row.humidity,row.risk,row.source])].map(row=>row.map(cell=>'"'+String(cell).replaceAll('"','""')+'"').join(',')).join('\r\n');
  const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8;'}));
  const link=document.createElement('a'); link.href=url;link.download=`tapmaan-${state.city}-readings.csv`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  toast(`Exported ${rows.length} observations.`);
}

$('#city-select').addEventListener('change',()=>{state.city=$('#city-select').value;load();});
$('#mode-demo').addEventListener('click',()=>switchMode('demo'));
$('#mode-live').addEventListener('click',()=>switchMode('live'));
$('#refresh').addEventListener('click',()=>load(true));
$('#empty-refresh').addEventListener('click',()=>load(true));
document.querySelectorAll('[data-page]').forEach(button=>button.addEventListener('click',()=>showPage(button.dataset.page)));
$('.brand').addEventListener('click',()=>showPage('overview'));
document.querySelectorAll('[data-chart]').forEach(button=>button.addEventListener('click',()=>{state.chart=button.dataset.chart;renderChart();}));
$('#show-reviewed').addEventListener('click',()=>{state.reviewed=!state.reviewed;renderAlerts();});
$('#source-filter').addEventListener('change',renderReadings);
$('#export-csv').addEventListener('click',exportCSV);
$('#alerts-list').addEventListener('click',async event=>{
  const button=event.target.closest('[data-ack]'); if(!button)return;
  button.disabled=true;
  try{await request('/api/acknowledge',{id:Number(button.dataset.ack)});await load();toast('Warning marked as reviewed.');}catch(error){toast(error.message);button.disabled=false;}
});
$('#readings-body').addEventListener('click',async event=>{
  const button=event.target.closest('[data-delete]');if(!button)return;
  if(!confirm('Delete this manual reading?'))return;
  button.disabled=true;
  try{await request('/api/delete-reading',{id:Number(button.dataset.delete)});await load();toast('Manual reading deleted.');}catch(error){toast(error.message);button.disabled=false;}
});
$('#add-reading').addEventListener('click',()=>{
  $('#reading-form').reset();$('#form-error').textContent='';
  $('#manual-city').textContent=$('#city-select').selectedOptions[0].textContent;
  const ist=new Date(Date.now()+330*60000).toISOString().slice(0,16);
  const input=$('[name="recorded_at"]');input.value=ist;input.max=ist;
  $('#reading-dialog').showModal();
});
$('#close-dialog').addEventListener('click',()=>$('#reading-dialog').close());
$('#reading-form').addEventListener('submit',async event=>{
  event.preventDefault();$('#save-reading').disabled=true;$('#form-error').textContent='';
  const fields=new FormData(event.target);
  try{
    const saved=await request('/api/readings',{city_id:state.city,temperature:Number(fields.get('temperature')),humidity:Number(fields.get('humidity')),recorded_at:fields.get('recorded_at')+':00+05:30'});
    $('#reading-dialog').close();$('#source-filter').value='manual';showPage('readings');await load();toast(`Reading saved · ${saved.risk} temperature level.`);
  }catch(error){$('#form-error').textContent=error.message;}
  finally{$('#save-reading').disabled=false;}
});

async function init() {
  if(window.TAPMAAN_RUNTIME==='preview'){$('#preview-note').hidden=false;$('#runtime-badge').textContent='Interactive preview';}
  try{
    const cities=await request('/api/cities');
    $('#city-select').innerHTML=cities.map(city=>`<option value="${city.id}">${escapeHTML(city.name)}, ${escapeHTML(city.region)}</option>`).join('');
    await load();
  }catch(error){$('#error-banner').hidden=false;$('#error-banner').textContent=`Could not load Tapmaan: ${error.message}. Run python run_web.py and open http://127.0.0.1:8000.`;}
}
init();
