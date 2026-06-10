@echo off
REM Single Best Opportunity 24H Scheduler
REM Runs continuous 60-minute cycles: 45min scraping/clean + 15min analysis
REM Selects and sends only the best opportunity per cycle

echo ========================================
echo Single Best Opportunity 24H Scheduler
echo ========================================
echo.
echo Starting scheduler with 60-minute cycles:
echo   - Phase 1: 45min scraping + clean
echo   - Phase 2: 15min analysis + notification
echo.

cd /d "%~dp0.."
call venv312\Scripts\activate.bat

python -m realestate_engine.scheduler.single_best_scheduler

pause
