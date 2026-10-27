/** AstroDestination Explorer: dashboard data, charts and navigation. */
'use strict';

const API_BASE = '/api';
const MONTH_LABELS = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];

const CHART_COLORS = {
  blue: '#375B9B',
  purple: '#7F74B5',
  gold: '#C58B58',
  text: '#667085',
  grid: 'rgba(24, 43, 77, 0.09)',
};

const state = {
  municipality: '',
  comparisonMunicipality: '',
  year: null,
  charts: new Map(),
};

const fields = {
  municipality: document.querySelector('#municipality'),
  comparison: document.querySelector('#comparison-municipality'),
  year: document.querySelector('#year'),
  status: document.querySelector('#status'),
};

const navigationLinks = [...document.querySelectorAll('.nav-link[data-section]')];
const sections = navigationLinks
  .map(link => document.getElementById(link.dataset.section))
  .filter(Boolean);

const formatNumber = value =>
  value === null || value === undefined
    ? '—'
    : new Intl.NumberFormat('en-US').format(value);

/** Fetch JSON from our FastAPI backend, reporting server errors clearly. */
async function fetchStatistics(path, parameters = {}) {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);

  for (const [name, value] of Object.entries(parameters)) {
    url.searchParams.set(name, String(value));
  }

  const response = await fetch(url);
  if (!response.ok) {
    let message = `Request failed (HTTP ${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') message = body.detail;
    } catch {
      // Keep the HTTP status if the response is not JSON.
    }
    throw new Error(message);
  }

  return response.json();
}

function showStatus(message, isError = false) {
  fields.status.textContent = message;
  fields.status.classList.toggle('error', isError);
}

function populateSelect(select, values, selectedValue) {
  select.replaceChildren();

  for (const value of values) {
    const option = document.createElement('option');
    option.value = String(value);
    option.textContent = String(value);
    select.append(option);
  }

  if (values.some(value => String(value) === String(selectedValue))) {
    select.value = String(selectedValue);
  }
  select.disabled = values.length === 0;
}

function setFiltersDisabled(disabled) {
  for (const field of [fields.municipality, fields.comparison, fields.year]) {
    field.disabled = disabled;
  }
}

/** Maintain exactly one selected navigation link, including accessibility state. */
function setActiveSection(sectionId) {
  for (const link of navigationLinks) {
    const isActive = link.dataset.section === sectionId;
    link.classList.toggle('active', isActive);
    if (isActive) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  }
}

/**
 * Keep navigation synchronized with clicks and manual scrolling.
 * The section closest to the upper viewing area is considered active.
 */
function initializeNavigation() {
  let scheduled = false;

  function updateActiveSection() {
    scheduled = false;
    const referenceLine = window.innerHeight * 0.32;
    let activeId = sections[0]?.id;

    for (const section of sections) {
      if (section.getBoundingClientRect().top <= referenceLine) {
        activeId = section.id;
      }
    }

    // The final section may not reach the reference line on short screens.
    const atPageBottom = window.scrollY + window.innerHeight >=
      document.documentElement.scrollHeight - 3;
    if (atPageBottom) activeId = sections.at(-1)?.id;

    if (activeId) setActiveSection(activeId);
  }

  function scheduleNavigationUpdate() {
    if (!scheduled) {
      scheduled = true;
      window.requestAnimationFrame(updateActiveSection);
    }
  }

  for (const link of navigationLinks) {
    link.addEventListener('click', () => {
      setActiveSection(link.dataset.section);
    });
  }

  window.addEventListener('scroll', scheduleNavigationUpdate, { passive: true });
  window.addEventListener('resize', scheduleNavigationUpdate);
  window.addEventListener('hashchange', scheduleNavigationUpdate);
  scheduleNavigationUpdate();
}

/** Replace an existing Chart.js instance without leaking chart listeners. */
function drawChart(canvasId, chartType, datasets, labels) {
  state.charts.get(canvasId)?.destroy();

  const canvas = document.getElementById(canvasId);
  const chart = new Chart(canvas, {
    type: chartType,
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 350 },
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: datasets.length > 1,
          position: 'bottom',
          labels: { color: CHART_COLORS.text, usePointStyle: true, padding: 22 },
        },
        tooltip: {
          backgroundColor: '#202B46',
          titleColor: '#FFFFFF',
          bodyColor: '#F5F7FC',
          padding: 12,
          callbacks: {
            label: context => `${context.dataset.label}: ${formatNumber(context.parsed.y)}`,
          },
        },
      },
      scales: {
        x: {
          ticks: { color: CHART_COLORS.text, maxRotation: 0 },
          grid: { display: false },
          border: { display: false },
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: CHART_COLORS.text,
            callback: value => Intl.NumberFormat('en', { notation: 'compact' }).format(value),
          },
          grid: { color: CHART_COLORS.grid },
          border: { display: false },
        },
      },
    },
  });

  state.charts.set(canvasId, chart);
}

function renderSummary(monthlyData, extremeMonths) {
  const availableMonths = monthlyData.months.filter(row => row.overnights !== null);
  const totalStays = availableMonths.reduce((total, row) => total + row.overnights, 0);

  document.getElementById('total-stays').textContent = formatNumber(totalStays);
  document.getElementById('total-caption').textContent =
    `${state.year} · ${availableMonths.length} available months`;
  document.getElementById('busiest-month').textContent = extremeMonths.most_visited.month;
  document.getElementById('busiest-caption').textContent =
    `${formatNumber(extremeMonths.most_visited.overnights)} overnight stays`;
  document.getElementById('quietest-month').textContent = extremeMonths.least_visited.month;
  document.getElementById('quietest-caption').textContent =
    `${formatNumber(extremeMonths.least_visited.overnights)} overnight stays`;
  document.getElementById('coverage').textContent = `${availableMonths.length} / 12`;
  document.getElementById('coverage-caption').textContent =
    availableMonths.length === 12 ? 'Complete calendar year' : 'Incomplete year · missing months excluded';
}

function renderMonthlyChart(monthlyData) {
  document.getElementById('monthly-subtitle').textContent =
    `${state.municipality} · ${state.year} · Tourist overnight stays`;

  drawChart('monthly-chart', 'bar', [{
    label: state.municipality,
    data: monthlyData.months.map(row => row.overnights),
    backgroundColor: CHART_COLORS.blue,
    hoverBackgroundColor: CHART_COLORS.gold,
    borderRadius: 6,
    maxBarThickness: 48,
  }], MONTH_LABELS);
}

function renderComparisonChart(comparisonData) {
  document.getElementById('comparison-subtitle').textContent =
    `${state.municipality} vs ${state.comparisonMunicipality} · ${state.year}`;

  drawChart('comparison-chart', 'line', [
    {
      label: state.municipality,
      data: comparisonData.months.map(row => row.first_overnights),
      borderColor: CHART_COLORS.blue,
      backgroundColor: CHART_COLORS.blue,
      pointRadius: 3,
      tension: 0.3,
      spanGaps: false,
    },
    {
      label: state.comparisonMunicipality,
      data: comparisonData.months.map(row => row.second_overnights),
      borderColor: CHART_COLORS.purple,
      backgroundColor: CHART_COLORS.purple,
      pointRadius: 3,
      tension: 0.3,
      spanGaps: false,
    },
  ], MONTH_LABELS);
}

function renderYearlyChart(trendData) {
  document.getElementById('trends-subtitle').textContent =
    `${state.municipality} · Complete years in blue, partial years in gold`;

  drawChart('trends-chart', 'bar', [{
    label: 'Overnight stays',
    data: trendData.years.map(row => row.total_overnights),
    backgroundColor: trendData.years.map(row =>
      row.complete_year ? CHART_COLORS.blue : CHART_COLORS.gold),
    borderRadius: 6,
    maxBarThickness: 48,
  }], trendData.years.map(row => row.complete_year ? String(row.year) : `${row.year}*`));
}

/** Update all displays from the current municipality and year selection. */
async function refreshDashboard() {
  if (!state.municipality || !state.comparisonMunicipality || !state.year) return;

  setFiltersDisabled(true);
  showStatus('Updating tourism statistics…');

  try {
    const parameters = { municipality: state.municipality, year: state.year };
    const [monthly, extremes, comparison, trends] = await Promise.all([
      fetchStatistics('/monthly', parameters),
      fetchStatistics('/extremes', parameters),
      fetchStatistics('/compare', {
        first: state.municipality,
        second: state.comparisonMunicipality,
        year: state.year,
      }),
      fetchStatistics('/trends', { municipality: state.municipality }),
    ]);

    renderSummary(monthly, extremes);
    renderMonthlyChart(monthly);
    renderComparisonChart(comparison);
    renderYearlyChart(trends);
    showStatus(`SURS / OPSI · ${state.municipality} · ${state.year}`);
  } catch (error) {
    showStatus(`Could not load data: ${error.message}`, true);
  } finally {
    setFiltersDisabled(false);
  }
}

async function refreshAvailableYears() {
  const result = await fetchStatistics('/years', { municipality: state.municipality });
  if (!result.years.length) throw new Error('No years available for the selected municipality.');

  const selectedYear = result.years.includes(state.year)
    ? state.year : Math.max(...result.years);

  populateSelect(fields.year, [...result.years].reverse(), selectedYear);
  state.year = Number(fields.year.value);
}

async function initializeDashboard() {
  initializeNavigation();

  if (typeof Chart === 'undefined') {
    showStatus('Chart.js could not load. Check the internet connection.', true);
    return;
  }

  try {
    const { municipalities } = await fetchStatistics('/municipalities');
    if (municipalities.length < 2) throw new Error('Not enough municipalities available.');

    state.municipality = municipalities.includes('Bohinj') ? 'Bohinj' : municipalities[0];
    state.comparisonMunicipality = municipalities.includes('Bled') && state.municipality !== 'Bled'
      ? 'Bled' : municipalities.find(name => name !== state.municipality);

    populateSelect(fields.municipality, municipalities, state.municipality);
    populateSelect(fields.comparison, municipalities, state.comparisonMunicipality);
    await refreshAvailableYears();
    await refreshDashboard();
  } catch (error) {
    showStatus(`Could not initialize the dashboard: ${error.message}`, true);
  }
}

fields.municipality.addEventListener('change', async () => {
  state.municipality = fields.municipality.value;
  try {
    await refreshAvailableYears();
    await refreshDashboard();
  } catch (error) {
    showStatus(error.message, true);
  }
});

fields.comparison.addEventListener('change', () => {
  state.comparisonMunicipality = fields.comparison.value;
  refreshDashboard();
});

fields.year.addEventListener('change', () => {
  state.year = Number(fields.year.value);
  refreshDashboard();
});

initializeDashboard();
