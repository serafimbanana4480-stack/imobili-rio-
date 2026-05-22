$ErrorActionPreference = 'Stop'

$root = 'c:/Users/rodri/Desktop/Projeto analize mercado imobeleario'
$scripts = Join-Path $root 'scripts'
$debug = Join-Path $scripts 'debug'
$archive = Join-Path $root 'logs/archive'
$logsRoot = Join-Path $root 'logs'

New-Item -ItemType Directory -Force -Path $scripts, $debug, $archive, (Join-Path $logsRoot 'app') | Out-Null

# Move remaining root utilities
foreach ($name in @(
    'find_duplicates.py',
    'init_db.py',
    'run_scoring_only.py',
    'run_scraper_manual.py',
    'run_valuation_only.py',
    'simple_re_score.py',
    'system_audit.py'
)) {
    $path = Join-Path $root $name
    if (Test-Path $path) {
        Move-Item -Force $path $scripts
    }
}

# Move remaining root artifacts and generated outputs
foreach ($name in @(
    '_debug_spider.log',
    '_pipeline_full.log',
    '_pipeline_run2.log',
    '_run_output.txt',
    '_test_results_phase1_v2.log',
    'audit_output.txt',
    'audit_report.txt',
    'pipeline_test_output.txt',
    'test_results.txt',
    'remax_debug.html',
    'remax_detail.html'
)) {
    $path = Join-Path $root $name
    if (Test-Path $path) {
        try {
            Move-Item -Force $path $archive
        } catch {
            Write-Warning "Skipping locked or inaccessible file: $path"
        }
    }
}

# Consolidate active log files
foreach ($name in @('dashboard.log', 'errors.log')) {
    $path = Join-Path $logsRoot $name
    if (Test-Path $path) {
        try {
            Move-Item -Force $path $archive
        } catch {
            Write-Warning "Skipping locked or inaccessible log: $path"
        }
    }
}

# Consolidate app-level logs if present
$appLogs = Join-Path $root 'realestate_engine/logs'
if (Test-Path $appLogs) {
    Get-ChildItem $appLogs -File | ForEach-Object {
        try {
            Move-Item -Force $_.FullName (Join-Path $logsRoot 'app')
        } catch {
            Write-Warning "Skipping locked or inaccessible app log: $($_.FullName)"
        }
    }
}
