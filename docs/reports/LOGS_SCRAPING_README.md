# Scraping Logs Organization

## Directory Structure
```
logs/
scraping/
|-- README.md
|-- idealista/
|   |-- 2024-04-22_idealista_scrape.log
|   |-- 2024-04-22_idealista_errors.log
|   |-- 2024-04-22_idealista_performance.log
|   |-- 2024-04-22_idealista_debug.log
|   `-- archive/
|       |-- 2024-04-21_idealista_scrape.log.gz
|       `-- 2024-04-20_idealista_scrape.log.gz
|-- imovirtual/
|   |-- 2024-04-22_imovirtual_scrape.log
|   |-- 2024-04-22_imovirtual_errors.log
|   |-- 2024-04-22_imovirtual_performance.log
|   |-- 2024-04-22_imovirtual_debug.log
|   `-- archive/
|-- casa_sapo/
|   |-- 2024-04-22_casa_sapo_scrape.log
|   |-- 2024-04-22_casa_sapo_errors.log
|   |-- 2024-04-22_casa_sapo_performance.log
|   |-- 2024-04-22_casa_sapo_debug.log
|   `-- archive/
|-- era/
|   |-- 2024-04-22_era_scrape.log
|   |-- 2024-04-22_era_errors.log
|   |-- 2024-04-22_era_performance.log
|   |-- 2024-04-22_era_debug.log
|   `-- archive/
|-- remax/
|   |-- 2024-04-22_remax_scrape.log
|   |-- 2024-04-22_remax_errors.log
|   |-- 2024-04-22_remax_performance.log
|   |-- 2024-04-22_remax_debug.log
|   `-- archive/
|-- century21/
|   |-- 2024-04-22_century21_scrape.log
|   |-- 2024-04-22_century21_errors.log
|   |-- 2024-04-22_century21_performance.log
|   |-- 2024-04-22_century21_debug.log
|   `-- archive/
|-- supercasa/
|   |-- 2024-04-22_supercasa_scrape.log
|   |-- 2024-04-22_supercasa_errors.log
|   |-- 2024-04-22_supercasa_performance.log
|   |-- 2024-04-22_supercasa_debug.log
|   `-- archive/
|-- olx/
|   |-- 2024-04-22_olx_scrape.log
|   |-- 2024-04-22_olx_errors.log
|   |-- 2024-04-22_olx_performance.log
|   |-- 2024-04-22_olx_debug.log
|   `-- archive/
|-- aggregated/
|   |-- 2024-04-22_daily_summary.log
|   |-- 2024-04-22_weekly_summary.log
|   |-- 2024-04-22_monthly_summary.log
|   `-- archive/
`-- monitoring/
    |-- scraping_health.log
    |-- circuit_breaker_events.log
    |-- proxy_rotation.log
    |-- rate_limiting.log
    `-- performance_metrics.log
```

## Log Types

### 1. Main Scrape Log (`*_scrape.log`)
- General scraping activities
- Start/end times
- Pages scraped
- Listings found
- Success/failure counts

### 2. Error Log (`*_errors.log`)
- All errors and exceptions
- Stack traces
- Failed URLs
- Proxy failures
- Network issues

### 3. Performance Log (`*_performance.log`)
- Page load times
- Parsing times
- Memory usage
- CPU usage
- Request/response times

### 4. Debug Log (`*_debug.log`)
- Detailed debugging information
- HTML snippets
- Selector matches
- Intermediate processing steps

### 5. Aggregated Logs
- Daily summaries across all portals
- Weekly trends
- Monthly reports
- Cross-portal comparisons

### 6. Monitoring Logs
- Circuit breaker events
- Proxy rotation events
- Rate limiting violations
- Health check results

## Log Rotation Policy
- **Daily**: Main logs rotate daily at midnight
- **Weekly**: Debug logs rotate weekly
- **Monthly**: Archive logs compress monthly
- **Retention**: Keep 30 days daily, 12 weeks weekly, 12 months monthly

## Log Format
```
2024-04-22 14:30:15 | INFO | idealista | Started scraping page 1
2024-04-22 14:30:17 | DEBUG | idealista | Found 20 listings on page 1
2024-04-22 14:30:18 | PERF | idealista | Page load time: 2.34s
2024-04-22 14:30:20 | ERROR | idealista | Failed to parse listing 123: Invalid HTML
2024-04-22 14:30:22 | INFO | idealista | Completed scraping page 1: 18 listings
```

## Log Analysis Tools
- `grep` for pattern matching
- `awk` for data extraction
- `sed` for log transformation
- Python scripts for complex analysis
- Grafana dashboards for visualization
