/**
 * API functions to handle data fetching from Python backend
 */

class CovidDataAPI {
  constructor() {
    this.baseUrl = '/api';
    this.cache = {};
  }

  /**
   * Generic fetch method with caching
   */
  async fetchData(endpoint, params = {}) {
    // Create a cache key based on the endpoint and parameters
    const queryString = new URLSearchParams(params).toString();
    const cacheKey = `${endpoint}?${queryString}`;
    
    // Check if we have cached data
    if (this.cache[cacheKey]) {
      return this.cache[cacheKey];
    }
    
    try {
      const url = `${this.baseUrl}/${endpoint}${queryString ? '?' + queryString : ''}`;
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Cache the result
      this.cache[cacheKey] = data;
      
      return data;
    } catch (error) {
      console.error('Error fetching data:', error);
      throw error;
    }
  }

  // Timeline page data endpoints
  async getCovidStats(date) {
    return this.fetchData('covid_stats', { date });
  }

  async getRNumbers(date) {
    return this.fetchData('r_numbers', { date });
  }

  async getCountyChoropleth(date, nlpType, topic) {
    return this.fetchData('county_choropleth', { date, nlp_type: nlpType, topic });
  }

  async getSentimentBarChart(date, source, nlpType) {
    return this.fetchData('sentiment_bar_chart', { date, source, nlp_type: nlpType });
  }

  async getEmojiBarChart(date, topic) {
    return this.fetchData('emoji_bar_chart', { date, topic });
  }

  async getHashtagTable(date, source) {
    return this.fetchData('hashtag_table', { date, source });
  }

  async getDailyNews(date) {
    return this.fetchData('daily_news', { date });
  }

  async getStatsGraph(date) {
    return this.fetchData('stats_graph', { date });
  }

  async getMASentGraph(date, topic, sentimentType) {
    return this.fetchData('ma_sent_graph', { date, topic, sentiment_type: sentimentType });
  }

  // Analysis page data endpoints
  async getNotableDays(topic, nlpType) {
    return this.fetchData('notable_days', { topic, nlp_type: nlpType });
  }

  async getDropdownFigure(topic, sentimentType, chartValue) {
    return this.fetchData('dropdown_figure', { topic, sentiment_type: sentimentType, chart_value: chartValue });
  }

  async getCorrMat(topic, sentimentType) {
    return this.fetchData('corr_mat', { topic, sentiment_type: sentimentType });
  }

  // Get list of all available dates
  async getDates() {
    return this.fetchData('dates');
  }
}

// Create a global instance
const api = new CovidDataAPI();