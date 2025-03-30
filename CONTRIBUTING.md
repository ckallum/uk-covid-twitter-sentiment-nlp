# Contributing to COVID-19 Sentiment Analysis in the UK

Thank you for considering contributing to this project! Here are some guidelines to help you get started.

## Ways to Contribute

- Reporting bugs
- Suggesting enhancements
- Adding new features
- Improving documentation
- Submitting pull requests

## Development Setup

1. Fork the repository
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/covid-sentiment-nlp-uk.git
   cd covid-sentiment-nlp-uk
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Project Architecture

This project uses a modern web architecture:

- **Backend**: Flask-based API that provides data processing and visualization generation
- **Frontend**: HTML, CSS, and JavaScript for the user interface

### Key Files

- `api.py`: Contains all API endpoints
- `static/`: Frontend assets
  - `index.html`: Main HTML file
  - `css/main.css`: Styling
  - `js/main.js`: Main JavaScript functionality
  - `js/api.js`: API client for interacting with the backend
- `utils/`: Helper modules for data processing and visualization

## Submitting Changes

1. Commit your changes with clear commit messages:
   ```bash
   git commit -m "Add feature X" -m "Description of the changes made"
   ```
2. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
3. Submit a pull request to the main repository

## Coding Guidelines

- Follow PEP 8 for Python code
- Use clear, descriptive function and variable names
- Add comments for complex logic
- Write tests for new features when possible

## Adding New Visualizations

1. Create a new endpoint in `api.py` that generates the visualization data
2. Add a corresponding function in `static/js/api.js` to fetch the data
3. Update the UI in `static/index.html` and `static/js/main.js` to display the visualization

## Questions?

If you have any questions, feel free to open an issue or contact the project maintainers.

Thank you for your contributions!