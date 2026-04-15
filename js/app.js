/**
 * COVID-19 Sentiment Dashboard — Static Site Application
 * Loads pre-computed JSON data and builds Plotly charts client-side.
 */

// ============================================================
// Constants
// ============================================================
const DATA_PATH = 'data/json';
const COUNTRIES = ['England', 'Scotland', 'Northern Ireland', 'Wales'];
const NLP_TYPES = ['nn', 'vader', 'textblob', 'native'];
const NLP_LABELS = { nn: 'LSTM', vader: 'Vader', textblob: 'TextBlob', native: 'Naive Bayes' };

// Design system colors
const COLORS = {
  text: '#1a1915',
  muted: '#6b6860',
  dim: '#9c9890',
  border: '#d4d1c7',
  borderSubtle: '#e3e0d8',
  phase1: '#4a7c9b',
  phase2: '#8b6b9e',
  phase3: '#b8860b',
  phase4: '#5a8a5e',
  orange: '#c67035',
  hard: '#c4584a',
};

const COUNTRY_COLORS = {
  England: COLORS.phase1,
  Scotland: COLORS.phase2,
  'Northern Ireland': COLORS.orange,
  Wales: COLORS.phase4,
};

const SENTIMENT_COLORS = {
  neg: COLORS.hard,
  neu: COLORS.dim,
  pos: COLORS.phase4,
};

// Diverging colorscale for sentiment: red (neg) → warm (neu) → blue (pos)
const SENTIMENT_COLORSCALE = [
  [0.0, '#c4584a'],
  [0.25, '#e8a06f'],
  [0.5, '#f5f3ed'],
  [0.75, '#7fa9c0'],
  [1.0, '#4a7c9b'],
];

const CHART_CONFIG = {
  responsive: true,
  displayModeBar: false,
};

const COMMON_LAYOUT = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: { family: 'DM Mono, monospace', size: 11, color: COLORS.text },
};

const START_DATE = '2020-03-20';

// ============================================================
// State
// ============================================================
const state = {
  dates: [],
  dateIndex: 0,
  playing: false,
  playTimer: null,
  topic: 'covid',
  nlpType: 'vader',
  analysisTopic: 'covid',
  analysisNlp: 'vader',
  chartType: 'show_sentiment_comparison',
  shared: null,
  topicData: {},
};

// ============================================================
// Data Loading
// ============================================================
const jsonCache = {};

async function loadJSON(path) {
  if (jsonCache[path]) return jsonCache[path];
  const resp = await fetch(`${DATA_PATH}/${path}`);
  if (!resp.ok) throw new Error(`Failed to load ${path}: ${resp.status}`);
  const data = await resp.json();
  jsonCache[path] = data;
  return data;
}

async function loadSharedData() {
  const [datesData, stats, rNums, events, news, statsMa, geojson] = await Promise.all([
    loadJSON('dates.json'),
    loadJSON('covid_stats.json'),
    loadJSON('r_numbers.json'),
    loadJSON('events.json'),
    loadJSON('news.json'),
    loadJSON('covid_stats_ma.json'),
    loadJSON('geojson.json'),
  ]);
  state.dates = datesData.dates;
  state.shared = { datesData, stats, rNums, events, news, statsMa, geojson };
  return state.shared;
}

async function loadTopicData(topic) {
  if (state.topicData[topic]) return state.topicData[topic];
  const [county, sentCounts, sentMa, sentComp, volMa, hashtags, emojis, notable, scatter] =
    await Promise.all([
      loadJSON(`${topic}/county_sentiment.json`),
      loadJSON(`${topic}/sentiment_counts.json`),
      loadJSON(`${topic}/sentiment_ma.json`),
      loadJSON(`${topic}/sentiment_comp.json`),
      loadJSON(`${topic}/tweet_volume_ma.json`),
      loadJSON(`${topic}/hashtags.json`),
      loadJSON(`${topic}/emojis.json`),
      loadJSON(`${topic}/notable_days.json`),
      loadJSON(`${topic}/scatter.json`),
    ]);
  const data = { county, sentCounts, sentMa, sentComp, volMa, hashtags, emojis, notable, scatter };
  state.topicData[topic] = data;
  return data;
}

// ============================================================
// Helpers
// ============================================================
function lookupRNumber(rNums, date) {
  // R-number pairs have start/end in dd/mm/yyyy format
  const [cy, cm, cd] = date.split('-').map(Number);
  const current = new Date(cy, cm - 1, cd);
  for (const pair of rNums) {
    const [sd, sm, sy] = pair.start.split('/').map(Number);
    const [ed, em, ey] = pair.end.split('/').map(Number);
    const start = new Date(sy, sm - 1, sd);
    const end = new Date(ey, em - 1, ed);
    if (current > start && current <= end) return pair.r;
  }
  return 'N/A';
}

function renderChart(elementId, figure) {
  const el = document.getElementById(elementId);
  if (!el) return;
  Plotly.react(el, figure.data, figure.layout, CHART_CONFIG);
}

/** Scale a desktop chart height down for smaller viewports. */
function rh(desktop) {
  const w = window.innerWidth;
  if (w <= 600) return Math.round(desktop * 0.62);
  if (w <= 900) return Math.round(desktop * 0.78);
  if (w <= 1100) return Math.round(desktop * 0.9);
  return desktop;
}

/** Viewport-aware font sizes for chart text. */
function isMobile() { return window.innerWidth <= 600; }
function isTablet() { return window.innerWidth <= 900; }

function formatNumber(n) {
  if (typeof n !== 'number') return n;
  return n.toLocaleString();
}

/** Return the URL only if it's http(s); otherwise null (prevents javascript: href injection). */
function safeHttpUrl(raw) {
  if (typeof raw !== 'string' || !raw) return null;
  try {
    const u = new URL(raw);
    return (u.protocol === 'http:' || u.protocol === 'https:') ? u.href : null;
  } catch {
    return null;
  }
}

// ============================================================
// Chart Builders
// ============================================================

function buildChoropleth(countyData, geojson, date, nlpType) {
  const dayData = countyData[date] || [];
  return {
    data: [{
      type: 'choroplethmapbox',
      geojson,
      locations: dayData.map(d => d.id),
      z: dayData.map(d => d[nlpType] || 0),
      featureidkey: 'properties.id',
      text: dayData.map(d => d.county),
      hovertemplate: '<b>%{text}</b><br>Score: %{z:.3f}<extra></extra>',
      colorscale: SENTIMENT_COLORSCALE,
      zmin: -1,
      zmax: 1,
      marker: { opacity: 0.75, line: { width: 0.3, color: COLORS.border } },
      colorbar: {
        title: { text: 'Sentiment', font: { size: 10, family: 'DM Mono, monospace' } },
        thickness: 12,
        len: 0.6,
        x: 1,
        tickfont: { size: 9, family: 'DM Mono, monospace' },
      },
    }],
    layout: {
      mapbox: {
        style: 'white-bg',
        center: { lat: 55, lon: -2 },
        zoom: isMobile() ? 3.8 : 4.3,
      },
      height: rh(600),
      autosize: true,
      margin: { l: 0, r: 0, t: 10, b: 0 },
      ...COMMON_LAYOUT,
    },
  };
}

function buildSentimentBar(sentCounts, date, nlpType) {
  const dayData = sentCounts[date];
  if (!dayData || !dayData[nlpType]) {
    return {
      data: [],
      layout: {
        ...COMMON_LAYOUT,
        height: 350,
        annotations: [{
          text: 'No data for this date',
          xref: 'paper', yref: 'paper',
          x: 0.5, y: 0.5,
          showarrow: false,
          font: { family: 'Newsreader, serif', size: 14, color: COLORS.muted },
        }],
      },
    };
  }

  const labels = { neg: 'Negative', neu: 'Neutral', pos: 'Positive' };
  const traces = ['neg', 'neu', 'pos'].map(sent => ({
    x: COUNTRIES,
    y: COUNTRIES.map(c => (dayData[nlpType][c] && dayData[nlpType][c][sent]) || 0),
    name: labels[sent],
    type: 'bar',
    marker: { color: SENTIMENT_COLORS[sent] },
  }));

  return {
    data: traces,
    layout: {
      ...COMMON_LAYOUT,
      barmode: 'group',
      height: rh(350),
      autosize: true,
      margin: { l: 50, r: 20, t: 40, b: 60 },
      legend: { orientation: 'h', y: 1.12, x: 0.5, xanchor: 'center', font: { size: 10 } },
      xaxis: { showgrid: false, tickfont: { size: 10 } },
      yaxis: {
        showgrid: true,
        gridcolor: COLORS.borderSubtle,
        title: { text: 'Count', font: { size: 10 } },
        tickfont: { size: 10 },
      },
    },
  };
}

function buildEmojiBar(emojiData, date, allDates) {
  // Emoji data is keyed by weekly start date
  const dateIdx = allDates.indexOf(date);
  const weekIdx = Math.max(0, dateIdx - (dateIdx % 7));
  const weekDate = allDates[weekIdx];
  const data = emojiData[weekDate] || emojiData[date] || [];

  if (!data.length) {
    return {
      data: [],
      layout: {
        ...COMMON_LAYOUT,
        height: 350,
        annotations: [{
          text: 'No emoji data for this week',
          xref: 'paper', yref: 'paper',
          x: 0.5, y: 0.5,
          showarrow: false,
          font: { family: 'Newsreader, serif', size: 14, color: COLORS.muted },
        }],
      },
    };
  }

  const sorted = [...data].sort((a, b) => b.count - a.count).slice(0, 10);
  return {
    data: [{
      x: sorted.map(d => d.emoji),
      y: sorted.map(d => d.count),
      type: 'bar',
      marker: { color: sorted.map(d => d.colour || COLORS.phase1) },
      texttemplate: '%{x}<br>%{y}',
      textposition: 'outside',
      cliponaxis: false,
      hoverinfo: 'none',
    }],
    layout: {
      ...COMMON_LAYOUT,
      height: rh(350),
      autosize: true,
      margin: { l: 20, r: 20, t: 40, b: 40 },
      xaxis: { visible: false, showline: false },
      yaxis: { visible: false, showline: false },
      bargap: 0.15,
      font: { ...COMMON_LAYOUT.font, size: 13 },
    },
  };
}

function buildHashtagTable(hashtagData, date) {
  const data = hashtagData[date] || [];
  return {
    data: [{
      type: 'table',
      header: {
        values: ['<b>HASHTAG</b>', '<b>COUNT</b>'],
        align: ['left', 'right'],
        fill: { color: COLORS.phase1 },
        font: { color: 'white', family: 'DM Mono, monospace', size: 11 },
        height: 32,
        line: { width: 0 },
      },
      cells: {
        values: [data.map(h => h.tag), data.map(h => h.count)],
        align: ['left', 'right'],
        fill: { color: ['#f5f3ed', 'white'] },
        font: { family: 'DM Mono, monospace', size: 11, color: COLORS.text },
        height: 28,
        line: { width: 0.5, color: COLORS.borderSubtle },
      },
      columnwidth: [3, 1],
    }],
    layout: {
      ...COMMON_LAYOUT,
      height: rh(380),
      autosize: true,
      margin: { l: 0, r: 0, t: 10, b: 10 },
    },
  };
}

// 2x2 subplot layout helper (with optional secondary y-axes)
function make2x2Layout(titles, height, axisTitles = {}) {
  const mobile = isMobile();
  const tick = mobile ? 8 : 9;
  const titleFont = mobile ? 11 : 13;
  const leftPrimary = { text: axisTitles.leftPrimary || '', font: { size: tick + 1 } };
  const rightSecondary = { text: axisTitles.rightSecondary || '', font: { size: tick + 1 } };
  // Tighter gap between subplots on mobile
  const hGap = mobile ? 0.08 : 0.12;
  const colEnd1 = 0.5 - hGap / 2;
  const colStart2 = 0.5 + hGap / 2;
  return {
    annotations: titles.map((t, i) => ({
      text: `<b>${t}</b>`,
      xref: 'paper', yref: 'paper',
      x: i % 2 === 0 ? colEnd1 / 2 : colStart2 + (1 - colStart2) / 2,
      y: i < 2 ? 1.04 : 0.46,
      xanchor: 'center',
      showarrow: false,
      font: { family: 'Newsreader, serif', size: titleFont, color: COLORS.text },
    })),
    xaxis: { domain: [0, colEnd1], showgrid: false, tickfont: { size: tick } },
    xaxis2: { domain: [colStart2, 1], showgrid: false, anchor: 'y3', tickfont: { size: tick } },
    xaxis3: { domain: [0, colEnd1], showgrid: false, anchor: 'y5', tickfont: { size: tick } },
    xaxis4: { domain: [colStart2, 1], showgrid: false, anchor: 'y7', tickfont: { size: tick } },
    yaxis: { domain: [0.58, 1], showgrid: true, gridcolor: COLORS.borderSubtle, tickfont: { size: tick }, title: leftPrimary },
    yaxis2: { domain: [0.58, 1], overlaying: 'y', side: 'right', showgrid: false, tickfont: { size: tick }, title: rightSecondary },
    yaxis3: { domain: [0.58, 1], anchor: 'x2', showgrid: true, gridcolor: COLORS.borderSubtle, tickfont: { size: tick } },
    yaxis4: { domain: [0.58, 1], anchor: 'x2', overlaying: 'y3', side: 'right', showgrid: false, tickfont: { size: tick } },
    yaxis5: { domain: [0, 0.42], anchor: 'x3', showgrid: true, gridcolor: COLORS.borderSubtle, tickfont: { size: tick }, title: leftPrimary },
    yaxis6: { domain: [0, 0.42], anchor: 'x3', overlaying: 'y5', side: 'right', showgrid: false, tickfont: { size: tick }, title: rightSecondary },
    yaxis7: { domain: [0, 0.42], anchor: 'x4', showgrid: true, gridcolor: COLORS.borderSubtle, tickfont: { size: tick } },
    yaxis8: { domain: [0, 0.42], anchor: 'x4', overlaying: 'y7', side: 'right', showgrid: false, tickfont: { size: tick } },
    height,
    autosize: true,
    margin: mobile
      ? { l: 38, r: 38, t: 55, b: 30 }
      : { l: 55, r: 55, t: 70, b: 40 },
    ...COMMON_LAYOUT,
  };
}

function buildStatsGraph(statsMa, eventsArray, allDates, startDate, endDate) {
  const data = statsMa.filter(d => d.date >= startDate && d.date <= endDate);
  const axisMap = [
    { x: 'x', yp: 'y', ys: 'y2' },
    { x: 'x2', yp: 'y3', ys: 'y4' },
    { x: 'x3', yp: 'y5', ys: 'y6' },
    { x: 'x4', yp: 'y7', ys: 'y8' },
  ];

  const traces = [];
  COUNTRIES.forEach((country, i) => {
    const cData = data.filter(d => d.country === country);
    const dates = cData.map(d => d.date);
    const ax = axisMap[i];
    // Align events text to dates
    const texts = dates.map(d => {
      const idx = allDates.indexOf(d);
      return idx >= 0 ? (eventsArray[idx] || '') : '';
    });

    traces.push({
      x: dates,
      y: cData.map(d => d.cases),
      name: 'Cases',
      type: 'scatter',
      mode: 'lines',
      line: { color: COLORS.phase1, width: 1.5 },
      xaxis: ax.x,
      yaxis: ax.yp,
      text: texts,
      hovertemplate: '<b>%{fullData.name}</b>: %{y:.0f}<br>%{x}<br>%{text}<extra></extra>',
      showlegend: i === 0,
      legendgroup: 'cases',
    });
    traces.push({
      x: dates,
      y: cData.map(d => d.deaths),
      name: 'Deaths',
      type: 'scatter',
      mode: 'lines',
      line: { color: COLORS.hard, width: 1.5 },
      xaxis: ax.x,
      yaxis: ax.ys,
      text: texts,
      hovertemplate: '<b>%{fullData.name}</b>: %{y:.0f}<br>%{x}<br>%{text}<extra></extra>',
      showlegend: i === 0,
      legendgroup: 'deaths',
    });
  });

  const layout = make2x2Layout(
    ['England', 'Scotland', 'N. Ireland', 'Wales'],
    rh(700),
    { leftPrimary: 'Cases', rightSecondary: 'Deaths' }
  );
  layout.legend = { orientation: 'h', y: 1.1, x: 1, xanchor: 'right', font: { size: 10 } };
  return { data: traces, layout };
}

function buildSentimentMA(sentMa, nlpType, startDate, endDate) {
  const filtered = sentMa.filter(d => d.date >= startDate && d.date <= endDate);
  const traces = COUNTRIES.map(country => {
    const cData = filtered.filter(d => d.country === country);
    return {
      x: cData.map(d => d.date),
      y: cData.map(d => d[nlpType]),
      name: country,
      type: 'scatter',
      mode: 'lines',
      line: { color: COUNTRY_COLORS[country], width: 1.8 },
      hovertemplate: `<b>${country}</b><br>%{x}<br>Sentiment: %{y:.3f}<extra></extra>`,
    };
  });

  return {
    data: traces,
    layout: {
      ...COMMON_LAYOUT,
      height: rh(500),
      autosize: true,
      margin: { l: 55, r: 20, t: 50, b: 50 },
      legend: { orientation: 'h', y: 1.1, x: 1, xanchor: 'right', font: { size: 10 } },
      xaxis: { showgrid: false, title: { text: 'Date', font: { size: 11 } }, tickfont: { size: 10 } },
      yaxis: {
        title: { text: 'Sentiment (7-day MA)', font: { size: 11 } },
        range: nlpType === 'native' ? [-0.4, 0.6] : [-0.4, 0.5],
        showgrid: true,
        gridcolor: COLORS.borderSubtle,
        tickfont: { size: 10 },
      },
    },
  };
}

function buildSentimentComp(sentComp, startDate, endDate) {
  const filtered = sentComp.filter(d => d.date >= startDate && d.date <= endDate);
  const techColors = { nn: COLORS.phase1, textblob: COLORS.phase2, vader: COLORS.phase3, native: COLORS.phase4 };
  const traces = NLP_TYPES.map(t => ({
    x: filtered.map(d => d.date),
    y: filtered.map(d => d[t]),
    name: NLP_LABELS[t],
    type: 'scatter',
    mode: 'lines',
    line: { color: techColors[t], width: 1.8 },
    hovertemplate: `<b>${NLP_LABELS[t]}</b><br>%{x}<br>Sentiment: %{y:.3f}<extra></extra>`,
  }));

  return {
    data: traces,
    layout: {
      ...COMMON_LAYOUT,
      height: rh(600),
      autosize: true,
      margin: { l: 55, r: 20, t: 50, b: 50 },
      legend: { orientation: 'h', y: 1.08, x: 1, xanchor: 'right', font: { size: 10 } },
      xaxis: { showgrid: false, title: { text: 'Date', font: { size: 11 } }, tickfont: { size: 10 } },
      yaxis: {
        title: { text: 'Sentiment (7-day MA)', font: { size: 11 } },
        range: [-0.4, 0.5],
        showgrid: true,
        gridcolor: COLORS.borderSubtle,
        tickfont: { size: 10 },
      },
    },
  };
}

function buildSentVsVol(sentMa, volMa, nlpType, eventsArray, allDates, startDate, endDate) {
  const sent = sentMa.filter(d => d.date >= startDate && d.date <= endDate);
  const vol = volMa.filter(d => d.date >= startDate && d.date <= endDate);

  const axisMap = [
    { x: 'x', yp: 'y', ys: 'y2' },
    { x: 'x2', yp: 'y3', ys: 'y4' },
    { x: 'x3', yp: 'y5', ys: 'y6' },
    { x: 'x4', yp: 'y7', ys: 'y8' },
  ];

  const traces = [];
  COUNTRIES.forEach((country, i) => {
    const cSent = sent.filter(d => d.country === country);
    const dates = cSent.map(d => d.date);
    const texts = dates.map(d => {
      const idx = allDates.indexOf(d);
      return idx >= 0 ? (eventsArray[idx] || '') : '';
    });
    const ax = axisMap[i];

    traces.push({
      x: dates,
      y: cSent.map(d => d[nlpType]),
      name: 'Sentiment',
      type: 'scatter',
      mode: 'lines',
      line: { color: COUNTRY_COLORS[country], width: 1.8 },
      xaxis: ax.x,
      yaxis: ax.yp,
      text: texts,
      hovertemplate: '<b>%{fullData.name}</b>: %{y:.3f}<br>%{x}<br>%{text}<extra></extra>',
      showlegend: i === 0,
      legendgroup: 'sentiment',
    });
    traces.push({
      x: vol.map(d => d.date),
      y: vol.map(d => d[country]),
      name: 'Tweet Volume',
      type: 'scatter',
      mode: 'lines',
      line: { color: COLORS.dim, width: 1.2, dash: 'dot' },
      xaxis: ax.x,
      yaxis: ax.ys,
      text: texts,
      hovertemplate: '<b>%{fullData.name}</b>: %{y:.0f}<br>%{x}<br>%{text}<extra></extra>',
      showlegend: i === 0,
      legendgroup: 'volume',
    });
  });

  const layout = make2x2Layout(
    ['England', 'Scotland', 'N. Ireland', 'Wales'],
    rh(700),
    { leftPrimary: 'Sentiment (7MA)', rightSecondary: 'Volume' }
  );
  layout.legend = { orientation: 'h', y: 1.1, x: 1, xanchor: 'right', font: { size: 10 } };
  // Constrain primary y-axis range
  ['yaxis', 'yaxis3', 'yaxis5', 'yaxis7'].forEach(k => {
    layout[k] = { ...layout[k], range: [-0.4, 0.5] };
  });
  return { data: traces, layout };
}

function buildNotableDays(notableDays, nlpType) {
  const data = notableDays[nlpType] || [];
  return {
    data: [{
      type: 'table',
      header: {
        values: ['<b>METRIC</b>', '<b>DATE</b>', '<b>VALUE</b>'],
        align: 'left',
        fill: { color: COLORS.phase3 },
        font: { color: 'white', family: 'DM Mono, monospace', size: 11 },
        height: 32,
        line: { width: 0 },
      },
      cells: {
        values: [
          data.map(d => d.label),
          data.map(d => d.date),
          data.map(d => d.rate.toFixed ? d.rate.toFixed(2) : d.rate),
        ],
        align: 'left',
        fill: { color: ['#f5f3ed', 'white'] },
        font: { family: 'DM Mono, monospace', size: 10, color: COLORS.text },
        height: 38,
        line: { width: 0.5, color: COLORS.borderSubtle },
      },
      columnwidth: [3, 2, 1.5],
    }],
    layout: {
      ...COMMON_LAYOUT,
      height: rh(460),
      autosize: true,
      margin: { l: 0, r: 0, t: 10, b: 10 },
    },
  };
}

function buildScatterMatrix(scatterData, nlpType) {
  const sentCol = nlpType;
  const countryIndex = d => COUNTRIES.indexOf(d.country);

  return {
    data: [{
      type: 'splom',
      dimensions: [
        { label: 'Sentiment', values: scatterData.map(d => d[sentCol]) },
        { label: 'Volume', values: scatterData.map(d => d.volume) },
        { label: 'Cases', values: scatterData.map(d => d.cases) },
        { label: 'Deaths', values: scatterData.map(d => d.deaths) },
      ],
      text: scatterData.map(d => d.country),
      hovertemplate: '<b>%{text}</b><br>%{xaxis.title.text}: %{x:.2f}<br>%{yaxis.title.text}: %{y:.2f}<extra></extra>',
      marker: {
        color: scatterData.map(d => COUNTRY_COLORS[d.country]),
        size: 8,
        opacity: 0.7,
        line: { width: 0.5, color: 'white' },
      },
      showupperhalf: false,
      diagonal: { visible: true },
    }],
    layout: {
      ...COMMON_LAYOUT,
      height: rh(520),
      autosize: true,
      margin: { l: 60, r: 30, t: 30, b: 60 },
      font: { family: 'DM Mono, monospace', size: 9, color: COLORS.text },
    },
  };
}

// ============================================================
// UI Controllers
// ============================================================

function initNavigation() {
  const links = document.querySelectorAll('.nav-link');
  const pages = document.querySelectorAll('.page');
  links.forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const pageId = link.dataset.page + '-page';
      links.forEach(l => l.classList.remove('active'));
      pages.forEach(p => p.classList.remove('active'));
      link.classList.add('active');
      const target = document.getElementById(pageId);
      if (target) {
        target.classList.add('active');
        // Trigger Plotly resize for charts that are now visible
        window.setTimeout(() => window.dispatchEvent(new Event('resize')), 50);
      }
    });
  });
}

function initSlider() {
  const slider = document.getElementById('days-slider');
  if (!slider) return;
  slider.min = 0;
  slider.max = Math.max(0, state.dates.length - 1);
  slider.value = 0;
  slider.addEventListener('input', e => {
    state.dateIndex = parseInt(e.target.value, 10);
    updateTimeline();
  });
}

function initControls() {
  const prev = document.getElementById('prev-button');
  const next = document.getElementById('next-button');
  const play = document.getElementById('play-button');

  if (prev) prev.addEventListener('click', () => {
    if (state.dateIndex > 0) {
      state.dateIndex--;
      syncSlider();
      updateTimeline();
    }
  });

  if (next) next.addEventListener('click', () => {
    if (state.dateIndex < state.dates.length - 1) {
      state.dateIndex++;
      syncSlider();
      updateTimeline();
    }
  });

  if (play) play.addEventListener('click', () => {
    state.playing = !state.playing;
    play.textContent = state.playing ? 'Pause' : 'Play';
    play.classList.toggle('playing', state.playing);
    if (state.playing) {
      state.playTimer = setInterval(() => {
        if (state.dateIndex < state.dates.length - 1) {
          state.dateIndex++;
          syncSlider();
          updateTimeline();
        } else {
          stopPlayback();
        }
      }, 800);
    } else {
      stopPlayback();
    }
  });
}

function stopPlayback() {
  state.playing = false;
  const play = document.getElementById('play-button');
  if (play) {
    play.textContent = 'Play';
    play.classList.remove('playing');
  }
  if (state.playTimer) {
    clearInterval(state.playTimer);
    state.playTimer = null;
  }
}

function syncSlider() {
  const slider = document.getElementById('days-slider');
  if (slider) slider.value = state.dateIndex;
}

function initSelectors() {
  const src = document.getElementById('source-dropdown');
  const nlp = document.getElementById('nlp-dropdown');
  if (src) src.addEventListener('change', async e => {
    state.topic = e.target.value;
    await loadTopicData(state.topic);
    updateTimeline();
  });
  if (nlp) nlp.addEventListener('change', e => {
    state.nlpType = e.target.value;
    updateTimeline();
  });

  const aSrc = document.getElementById('analysis-source-dropdown');
  const aNlp = document.getElementById('analysis-nlp-dropdown');
  const chart = document.getElementById('chart-dropdown');
  if (aSrc) aSrc.addEventListener('change', async e => {
    state.analysisTopic = e.target.value;
    await loadTopicData(state.analysisTopic);
    updateAnalysis();
  });
  if (aNlp) aNlp.addEventListener('change', e => {
    state.analysisNlp = e.target.value;
    updateAnalysis();
  });
  if (chart) chart.addEventListener('change', e => {
    state.chartType = e.target.value;
    updateAnalysis();
  });
}

function initToggles() {
  const toggles = [
    { toggle: 'heatmap-container-toggle', target: 'heatmap-container' },
    { toggle: 'bar-chart-div-toggle', target: 'bar-chart-div' },
    { toggle: 'news-hashtag-div-toggle', target: 'news-hashtag-div' },
    { toggle: 'deaths-and-cases-div-toggle', target: 'deaths-and-cases-div' },
    { toggle: '7-day-MA-div-toggle', target: '7-day-MA-div' },
  ];
  toggles.forEach(({ toggle, target }) => {
    const t = document.getElementById(toggle);
    const el = document.getElementById(target);
    if (t && el) {
      t.addEventListener('change', () => {
        el.style.display = t.checked ? '' : 'none';
      });
    }
  });
}

// ============================================================
// Update Functions
// ============================================================

async function updateTimeline() {
  const date = state.dates[state.dateIndex];
  if (!date) return;

  const topic = state.topic;
  const nlpType = state.nlpType;
  const td = await loadTopicData(topic);
  const shared = state.shared;

  // KPIs
  const dayStats = shared.stats[date] || { deaths: 0, cases: 0 };
  setText('total-deaths-indicator', formatNumber(dayStats.deaths));
  setText('total-cases-indicator', formatNumber(dayStats.cases));
  setText('r-number-indicator', lookupRNumber(shared.rNums, date));
  setText('current-date-indicator', date);

  // Charts
  renderChart('county-choropleth', buildChoropleth(td.county, shared.geojson, date, nlpType));
  renderChart('sentiment-bar-chart', buildSentimentBar(td.sentCounts, date, nlpType));
  renderChart('emoji-bar-chart', buildEmojiBar(td.emojis, date, state.dates));
  renderChart('hashtag-table', buildHashtagTable(td.hashtags, date));
  renderChart('stats-graph',
    buildStatsGraph(shared.statsMa, shared.events.events_array, state.dates, START_DATE, date));
  renderChart('ma-sent-graph', buildSentimentMA(td.sentMa, nlpType, START_DATE, date));

  // News — build DOM nodes rather than interpolating into innerHTML (XSS-safe)
  const newsItems = shared.news[date] || [];
  const newsEl = document.getElementById('daily-news');
  if (newsEl) {
    newsEl.replaceChildren();
    if (newsItems.length) {
      newsItems.forEach((n, i) => {
        if (i > 0) {
          newsEl.appendChild(document.createElement('br'));
          newsEl.appendChild(document.createElement('br'));
        }
        const href = safeHttpUrl(n.url);
        if (href) {
          const a = document.createElement('a');
          a.href = href;
          a.target = '_blank';
          a.rel = 'noopener noreferrer';
          const b = document.createElement('b');
          b.textContent = n.headline || '';
          a.appendChild(b);
          newsEl.appendChild(a);
        } else {
          const b = document.createElement('b');
          b.textContent = n.headline || '';
          newsEl.appendChild(b);
        }
      });
    } else {
      const em = document.createElement('em');
      em.style.color = 'var(--muted)';
      em.textContent = 'No news stories for this date.';
      newsEl.appendChild(em);
    }
  }

  // Heatmap title
  const titleEl = document.querySelector('#heatmap-container h6');
  if (titleEl) {
    const topicLabel = topic === 'covid' ? 'COVID' : 'Lockdown';
    titleEl.textContent = `Sentiment Heatmap — ${topicLabel} tweets — ${date}`;
  }
}

async function updateAnalysis() {
  const topic = state.analysisTopic;
  const nlpType = state.analysisNlp;
  const chartType = state.chartType;
  const td = await loadTopicData(topic);
  const shared = state.shared;

  const endDate = state.dates[state.dates.length - 1];

  renderChart('notable-day-table', buildNotableDays(td.notable, nlpType));

  let dropdownFig;
  if (chartType === 'show_sentiment_vs_time') {
    dropdownFig = buildSentVsVol(
      td.sentMa, td.volMa, nlpType, shared.events.events_array, state.dates, START_DATE, endDate
    );
  } else {
    dropdownFig = buildSentimentComp(td.sentComp, START_DATE, endDate);
  }
  renderChart('dropdown-figure', dropdownFig);

  renderChart('corr-mat', buildScatterMatrix(td.scatter, nlpType));

  // Update wordclouds
  const emojiWc = document.getElementById('emoji-wordcloud');
  const wc = document.getElementById('wordcloud');
  if (emojiWc) emojiWc.src = `assets/${topic}_emoji_wordcloud.png`;
  if (wc) wc.src = `assets/${topic}_wordcloud.png`;
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

// ============================================================
// Init
// ============================================================

function initResizeHandler() {
  let t;
  let lastBucket = viewportBucket();
  const onResize = () => {
    // Immediate Plotly resize so containers reflow
    document.querySelectorAll('.chart').forEach(el => {
      if (el && el._fullLayout) {
        try { Plotly.Plots.resize(el); } catch (_) { /* noop */ }
      }
    });
    // Debounced re-render only when viewport bucket changes (avoids spam)
    clearTimeout(t);
    t = setTimeout(() => {
      const bucket = viewportBucket();
      if (bucket !== lastBucket) {
        lastBucket = bucket;
        updateTimeline();
        updateAnalysis();
      }
    }, 250);
  };
  window.addEventListener('resize', onResize);
  window.addEventListener('orientationchange', onResize);
}

function viewportBucket() {
  const w = window.innerWidth;
  if (w <= 600) return 'mobile';
  if (w <= 900) return 'tablet';
  if (w <= 1100) return 'narrow';
  return 'desktop';
}

// ============================================================
// Embed Mode (?embed=1&chart=<id>)
// ============================================================

function buildCountyRanking(countyDataByDate, nlpType, topN = 10) {
  const sums = {};
  const counts = {};
  Object.values(countyDataByDate).forEach(day => {
    day.forEach(row => {
      const v = row[nlpType];
      if (typeof v !== 'number') return;
      const key = row.county;
      sums[key] = (sums[key] || 0) + v;
      counts[key] = (counts[key] || 0) + 1;
    });
  });
  const avgs = Object.keys(sums).map(county => ({
    county,
    avg: sums[county] / counts[county],
  }));
  avgs.sort((a, b) => b.avg - a.avg);
  const happiest = avgs.slice(0, topN);
  const saddest = avgs.slice(-topN).reverse();

  const labels = [
    ...happiest.map((_, i) => `Happiest #${i + 1}`),
    ...saddest.map((_, i) => `Saddest #${i + 1}`),
  ];
  const counties = [...happiest.map(d => d.county), ...saddest.map(d => d.county)];
  const values = [...happiest.map(d => d.avg.toFixed(3)), ...saddest.map(d => d.avg.toFixed(3))];

  return {
    data: [{
      type: 'table',
      header: {
        values: ['<b>RANK</b>', '<b>COUNTY</b>', `<b>AVG ${NLP_LABELS[nlpType].toUpperCase()}</b>`],
        align: 'left',
        fill: { color: COLORS.phase3 },
        font: { color: 'white', family: 'DM Mono, monospace', size: 11 },
        height: 32,
        line: { width: 0 },
      },
      cells: {
        values: [labels, counties, values],
        align: 'left',
        fill: { color: ['#f5f3ed', 'white'] },
        font: { family: 'DM Mono, monospace', size: 11, color: COLORS.text },
        height: 28,
        line: { width: 0.5, color: COLORS.borderSubtle },
      },
      columnwidth: [1.2, 2, 1.2],
    }],
    layout: {
      ...COMMON_LAYOUT,
      height: rh(640),
      autosize: true,
      margin: { l: 0, r: 0, t: 10, b: 10 },
    },
  };
}

function buildRatesSingleCountry(statsMa, sentMa, country, nlpType, startDate, endDate) {
  const stats = statsMa.filter(d => d.country === country && d.date >= startDate && d.date <= endDate);
  const sent = sentMa.filter(d => d.country === country && d.date >= startDate && d.date <= endDate);

  return {
    data: [
      {
        x: sent.map(d => d.date),
        y: sent.map(d => d[nlpType]),
        name: `Sentiment (${NLP_LABELS[nlpType]})`,
        type: 'scatter',
        mode: 'lines',
        line: { color: COUNTRY_COLORS[country] || COLORS.phase1, width: 2 },
        yaxis: 'y',
        hovertemplate: '<b>%{fullData.name}</b>: %{y:.3f}<br>%{x}<extra></extra>',
      },
      {
        x: stats.map(d => d.date),
        y: stats.map(d => d.cases),
        name: 'Cases',
        type: 'scatter',
        mode: 'lines',
        line: { color: COLORS.phase3, width: 1.4 },
        yaxis: 'y2',
        hovertemplate: '<b>%{fullData.name}</b>: %{y:.0f}<br>%{x}<extra></extra>',
      },
      {
        x: stats.map(d => d.date),
        y: stats.map(d => d.deaths),
        name: 'Deaths',
        type: 'scatter',
        mode: 'lines',
        line: { color: COLORS.hard, width: 1.4 },
        yaxis: 'y2',
        hovertemplate: '<b>%{fullData.name}</b>: %{y:.0f}<br>%{x}<extra></extra>',
      },
    ],
    layout: {
      ...COMMON_LAYOUT,
      height: rh(520),
      autosize: true,
      margin: { l: 60, r: 60, t: 50, b: 50 },
      legend: { orientation: 'h', y: 1.1, x: 1, xanchor: 'right', font: { size: 10 } },
      xaxis: { showgrid: false, title: { text: 'Date', font: { size: 11 } }, tickfont: { size: 10 } },
      yaxis: {
        title: { text: `Sentiment (${NLP_LABELS[nlpType]})`, font: { size: 11 } },
        showgrid: true,
        gridcolor: COLORS.borderSubtle,
        tickfont: { size: 10 },
        zeroline: true,
        zerolinecolor: COLORS.border,
      },
      yaxis2: {
        title: { text: 'Cases / Deaths', font: { size: 11 } },
        overlaying: 'y',
        side: 'right',
        showgrid: false,
        tickfont: { size: 10 },
      },
    },
  };
}

// Registry: each entry returns { topic, render(shared, topicData, endDate) -> figure }
const EMBED_REGISTRY = {
  'models-covid': {
    topic: 'covid',
    render: (_s, td, end) => buildSentimentComp(td.sentComp, START_DATE, end),
  },
  'models-lockdown': {
    topic: 'lockdown',
    render: (_s, td, end) => buildSentimentComp(td.sentComp, START_DATE, end),
  },
  'country-sentiment': {
    topic: 'covid',
    render: (_s, td, end) => buildSentimentMA(td.sentMa, 'native', START_DATE, end),
  },
  'county-table': {
    topic: 'covid',
    render: (_s, td) => buildCountyRanking(td.county, 'native'),
  },
  'rates-england-covid': {
    topic: 'covid',
    render: (s, td, end) => buildRatesSingleCountry(s.statsMa, td.sentMa, 'England', 'native', START_DATE, end),
  },
  'rates-england-lockdown': {
    topic: 'lockdown',
    render: (s, td, end) => buildRatesSingleCountry(s.statsMa, td.sentMa, 'England', 'native', START_DATE, end),
  },
  'rates-scotland-covid': {
    topic: 'covid',
    render: (s, td, end) => buildRatesSingleCountry(s.statsMa, td.sentMa, 'Scotland', 'native', START_DATE, end),
  },
  'rates-scotland-lockdown': {
    topic: 'lockdown',
    render: (s, td, end) => buildRatesSingleCountry(s.statsMa, td.sentMa, 'Scotland', 'native', START_DATE, end),
  },
  'overall-table': {
    topic: 'covid',
    render: (_s, td) => buildNotableDays(td.notable, 'native'),
  },
};

function showEmbedError(msg) {
  const root = document.getElementById('embed-root');
  const err = document.getElementById('embed-error');
  const chart = document.getElementById('embed-chart');
  if (root) root.hidden = false;
  if (chart) chart.hidden = true;
  if (err) {
    err.hidden = false;
    err.textContent = msg;
  }
}

async function initEmbed(chartId) {
  document.body.classList.add('embed-mode');
  const root = document.getElementById('embed-root');
  if (root) root.hidden = false;

  const entry = EMBED_REGISTRY[chartId];
  if (!entry) {
    showEmbedError(`Unknown chart id: ${chartId}. Valid ids: ${Object.keys(EMBED_REGISTRY).join(', ')}`);
    return;
  }

  try {
    await loadSharedData();
    const td = entry.topic ? await loadTopicData(entry.topic) : null;
    const endDate = state.dates[state.dates.length - 1];
    const figure = entry.render(state.shared, td, endDate);
    Plotly.react(document.getElementById('embed-chart'), figure.data, figure.layout, CHART_CONFIG);

    // Resize on viewport change
    window.addEventListener('resize', () => {
      const el = document.getElementById('embed-chart');
      if (el && el._fullLayout) { try { Plotly.Plots.resize(el); } catch (_) {} }
    });

    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = 'none';
  } catch (err) {
    console.error('Embed init failed:', err);
    showEmbedError(`Failed to load chart: ${err && err.message ? err.message : 'unknown error'}`);
  }
}

function getEmbedParams() {
  const p = new URLSearchParams(window.location.search);
  if (p.get('embed') !== '1') return null;
  return { chart: p.get('chart') || '' };
}

async function init() {
  const embed = getEmbedParams();
  if (embed) {
    return initEmbed(embed.chart);
  }
  try {
    await loadSharedData();
    await loadTopicData('covid');

    initNavigation();
    initSlider();
    initControls();
    initSelectors();
    initToggles();
    initResizeHandler();

    await updateTimeline();
    await updateAnalysis();

    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
      overlay.classList.add('hidden');
      setTimeout(() => { overlay.style.display = 'none'; }, 400);
    }
  } catch (err) {
    console.error('Initialization failed:', err);
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
      overlay.replaceChildren();
      const wrap = document.createElement('div');
      wrap.style.cssText = 'color: var(--hard); padding: 2rem; text-align: center';

      const h = document.createElement('h3');
      h.textContent = 'Failed to load dashboard';

      const msg = document.createElement('p');
      msg.textContent = err && err.message ? err.message : 'Unknown error';

      const hint = document.createElement('p');
      hint.style.cssText = 'font-size: 0.7rem; color: var(--muted); margin-top: 1rem';
      hint.append('Make sure you are serving via HTTP (not file://). Run: ');
      const code = document.createElement('code');
      code.textContent = 'python3 -m http.server';
      hint.appendChild(code);

      wrap.append(h, msg, hint);
      overlay.appendChild(wrap);
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
