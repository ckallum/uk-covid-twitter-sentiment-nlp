/**
 * Main JavaScript for the COVID-19 Sentiment Dashboard
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize UI components and event listeners
  initNavigation();
  initSlider();
  initButtons();
  initSelectors();
  initToggleSwitches();
  
  // Initial data load
  loadTimelinePage();
  loadAnalysisPage();
});

// Global variables
let allDates = [];
let currentDateIndex = 0;
let isPlaying = false;
let playInterval;
const START_DATE = '2020-03-20';
const END_DATE = '2021-03-25';

// -------------------------
// Navigation
// -------------------------
function initNavigation() {
  const navLinks = document.querySelectorAll('.nav-link');
  const pages = document.querySelectorAll('.page');
  
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      
      // Remove active class from all links and pages
      navLinks.forEach(l => l.classList.remove('active'));
      pages.forEach(p => p.classList.remove('active'));
      
      // Add active class to clicked link and corresponding page
      link.classList.add('active');
      const pageId = `${link.dataset.page}-page`;
      document.getElementById(pageId).classList.add('active');
    });
  });
}

// -------------------------
// Timeline Page
// -------------------------
async function loadTimelinePage() {
  try {
    // Load dates if not already loaded
    if (allDates.length === 0) {
      const datesData = await api.getDates();
      allDates = datesData.dates;
      initializeDateSlider();
    }
    
    // Load initial data
    updateTimelineData();
  } catch (error) {
    console.error('Error loading timeline page:', error);
  }
}

function initSlider() {
  // We'll initialize the actual slider after loading dates from the API
  const slider = document.getElementById('days-slider');
  // Will be initialized with noUiSlider in initializeDateSlider function
}

function initializeDateSlider() {
  const slider = document.getElementById('days-slider');
  
  // Create a simple slider for now - this would be replaced with a proper slider library in a real implementation
  // For this example, we're using a simple range input
  const range = document.createElement('input');
  range.type = 'range';
  range.min = 0;
  range.max = allDates.length - 1;
  range.value = 0;
  range.style.width = '100%';
  
  range.addEventListener('input', (e) => {
    currentDateIndex = parseInt(e.target.value);
    updateTimelineData();
  });
  
  slider.appendChild(range);
}

function initButtons() {
  const prevButton = document.getElementById('prev-button');
  const nextButton = document.getElementById('next-button');
  const playButton = document.getElementById('play-button');
  
  prevButton.addEventListener('click', () => {
    if (currentDateIndex > 0) {
      currentDateIndex--;
      updateSlider();
      updateTimelineData();
    }
  });
  
  nextButton.addEventListener('click', () => {
    if (currentDateIndex < allDates.length - 1) {
      currentDateIndex++;
      updateSlider();
      updateTimelineData();
    }
  });
  
  playButton.addEventListener('click', () => {
    isPlaying = !isPlaying;
    playButton.textContent = isPlaying ? 'Stop' : 'Play';
    
    if (isPlaying) {
      playInterval = setInterval(() => {
        if (currentDateIndex < allDates.length - 1) {
          currentDateIndex++;
          updateSlider();
          updateTimelineData();
        } else {
          stopPlayback();
        }
      }, 1000);
    } else {
      stopPlayback();
    }
  });
}

function stopPlayback() {
  isPlaying = false;
  document.getElementById('play-button').textContent = 'Play';
  clearInterval(playInterval);
}

function updateSlider() {
  const slider = document.querySelector('#days-slider input');
  if (slider) {
    slider.value = currentDateIndex;
  }
}

function initSelectors() {
  // Timeline page selectors
  const sourceDropdown = document.getElementById('source-dropdown');
  const nlpDropdown = document.getElementById('nlp-dropdown');
  
  sourceDropdown.addEventListener('change', updateTimelineData);
  nlpDropdown.addEventListener('change', updateTimelineData);
  
  // Analysis page selectors
  const analysisSourceDropdown = document.getElementById('analysis-source-dropdown');
  const analysisNlpDropdown = document.getElementById('analysis-nlp-dropdown');
  const chartDropdown = document.getElementById('chart-dropdown');
  
  analysisSourceDropdown.addEventListener('change', updateAnalysisData);
  analysisNlpDropdown.addEventListener('change', updateAnalysisData);
  chartDropdown.addEventListener('change', updateAnalysisData);
}

function initToggleSwitches() {
  // Set up toggle switches for showing/hiding sections
  const toggles = [
    'heatmap-container-toggle',
    'bar-chart-div-toggle',
    'news-hashtag-div-toggle',
    'deaths-and-cases-div-toggle',
    '7-day-MA-div-toggle',
    'sentiment-bar-chart-toggle',
    'emoji-bar-chart-toggle',
    'daily-news-toggle',
    'hashtag-table-toggle'
  ];
  
  toggles.forEach(toggleId => {
    const toggle = document.getElementById(toggleId);
    if (toggle) {
      toggle.addEventListener('change', function() {
        const targetId = this.id.replace('-toggle', '');
        const target = document.getElementById(targetId);
        if (target) {
          target.style.display = this.checked ? 'block' : 'none';
        }
      });
    }
  });
}

async function updateTimelineData() {
  // Get the current date
  if (allDates.length === 0) return;
  
  const currentDate = allDates[currentDateIndex];
  const sourceDropdown = document.getElementById('source-dropdown');
  const nlpDropdown = document.getElementById('nlp-dropdown');
  
  const source = sourceDropdown.value;
  const nlpType = nlpDropdown.value;
  
  // Update the date display
  document.getElementById('current-date-indicator').textContent = currentDate;
  
  try {
    // Load all data in parallel
    const [
      covidStats,
      rNumbers,
      countyChoropleth,
      sentimentBarChart,
      emojiBarChart,
      hashtagTable,
      dailyNews,
      statsGraph,
      maSentGraph
    ] = await Promise.all([
      api.getCovidStats(currentDate),
      api.getRNumbers(currentDate),
      api.getCountyChoropleth(currentDate, nlpType, source),
      api.getSentimentBarChart(currentDate, source, nlpType),
      api.getEmojiBarChart(currentDate, source),
      api.getHashtagTable(currentDate, source),
      api.getDailyNews(currentDate),
      api.getStatsGraph(currentDate),
      api.getMASentGraph(currentDate, source, nlpType)
    ]);
    
    // Update indicators
    document.getElementById('total-deaths-indicator').textContent = covidStats.total_deaths;
    document.getElementById('total-cases-indicator').textContent = covidStats.total_cases;
    document.getElementById('r-number-indicator').textContent = rNumbers.r_number;
    
    // Update heatmap title
    document.getElementById('heatmap-title').textContent = 
      `Heatmap of Sentiment Within ${source} Related Tweets in the UK. Date: ${currentDate}`;
    
    // Update visualizations with Plotly
    Plotly.react('county-choropleth', countyChoropleth.data, countyChoropleth.layout);
    Plotly.react('sentiment-bar-chart', sentimentBarChart.data, sentimentBarChart.layout);
    Plotly.react('emoji-bar-chart', emojiBarChart.data, emojiBarChart.layout);
    Plotly.react('hashtag-table', hashtagTable.data, hashtagTable.layout);
    Plotly.react('stats-graph', statsGraph.data, statsGraph.layout);
    Plotly.react('ma-sent-graph', maSentGraph.data, maSentGraph.layout);
    
    // Update news content
    document.getElementById('daily-news').innerHTML = dailyNews.content;
    
  } catch (error) {
    console.error('Error updating timeline data:', error);
  }
}

// -------------------------
// Analysis Page
// -------------------------
async function loadAnalysisPage() {
  try {
    updateAnalysisData();
  } catch (error) {
    console.error('Error loading analysis page:', error);
  }
}

async function updateAnalysisData() {
  const analysisSourceDropdown = document.getElementById('analysis-source-dropdown');
  const analysisNlpDropdown = document.getElementById('analysis-nlp-dropdown');
  const chartDropdown = document.getElementById('chart-dropdown');
  
  const source = analysisSourceDropdown.value;
  const nlpType = analysisNlpDropdown.value;
  const chartValue = chartDropdown.value;
  
  try {
    // Load all data in parallel
    const [
      notableDays,
      dropdownFigure,
      corrMat
    ] = await Promise.all([
      api.getNotableDays(source, nlpType),
      api.getDropdownFigure(source, nlpType, chartValue),
      api.getCorrMat(source, nlpType)
    ]);
    
    // Update visualizations
    Plotly.react('notable-day-table', notableDays.data, notableDays.layout);
    Plotly.react('dropdown-figure', dropdownFigure.data, dropdownFigure.layout);
    Plotly.react('corr-mat', corrMat.data, corrMat.layout);
    
    // Update wordcloud images
    document.getElementById('emoji-wordcloud').src = `assets/${source}_emoji_wordcloud.png`;
    document.getElementById('wordcloud').src = `assets/${source}_wordcloud.png`;
    
  } catch (error) {
    console.error('Error updating analysis data:', error);
  }
}

// Utility function to format dates for API calls
function formatDate(date) {
  return date.toISOString().split('T')[0];
}