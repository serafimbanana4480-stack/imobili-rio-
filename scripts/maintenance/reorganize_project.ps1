$ErrorActionPreference = 'Stop'

$root = 'c:/Users/rodri/Desktop/Projeto analize mercado imobeleario'
$scripts = Join-Path $root 'scripts'
$debug = Join-Path $scripts 'debug'
$tests = Join-Path $root 'tests'
$reports = Join-Path $root 'docs/reports'

New-Item -ItemType Directory -Force -Path $scripts, $debug, $tests, $reports | Out-Null

# Move root-level Python utilities and debug helpers
$rootPy = Get-ChildItem -Path $root -File -Filter '*.py'
foreach ($f in $rootPy) {
    if ($f.Name -match '^test_') {
        Move-Item -Force $f.FullName $tests
        continue
    }

    if ($f.Name -match '^(check_|verify_|analyze_|audit_|benchmark_|clean_|cleanup_|count_|debug_|_debug_|_run_|find_duplicates|init_db|investigate_|migrate_|probe_|re_enrich_|re_score_|restructure_|run_scoring_only|run_scraper_manual|run_valuation_only|simple_re_score|system_audit).+\.py$') {
        Move-Item -Force $f.FullName $debug
        continue
    }
}

# Move shell/batch launchers to scripts/
$rootLaunchers = Get-ChildItem -Path $root -File | Where-Object { $_.Extension -in '.bat', '.sh' }
foreach ($f in $rootLaunchers) {
    Move-Item -Force $f.FullName $scripts
}

# Move root markdown reports to docs/reports/ but keep README.md in place
$rootMd = Get-ChildItem -Path $root -File -Filter '*.md'
$keepMd = @('README.md')
foreach ($f in $rootMd) {
    if ($keepMd -contains $f.Name) { continue }
    Move-Item -Force $f.FullName $reports
}

# Keep a copy of log documentation in reports for discoverability
$logReadme = Join-Path $root 'logs/scraping/README.md'
if (Test-Path $logReadme) {
    Copy-Item -Force $logReadme (Join-Path $reports 'LOGS_SCRAPING_README.md')
}

# Move the Linux deployment helper if present
$deploySh = Join-Path $root 'realestate_engine/deploy.sh'
if (Test-Path $deploySh) {
    Move-Item -Force $deploySh $scripts
}

# Remove empty or placeholder directories and generated artifacts
foreach ($dir in @('app', 'ci', 'configs', 'docker', 'htmlcov', '__pycache__', '.pytest_cache')) {
    $path = Join-Path $root $dir
    if (Test-Path $path) {
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $path
    }
}

$coverage = Join-Path $root '.coverage'
if (Test-Path $coverage) {
    Remove-Item -Force $coverage
}

# Create macOS launcher if needed (placeholder; actual content is added separately)
$macosDir = Join-Path $root 'macos'
New-Item -ItemType Directory -Force -Path $macosDir | Out-Null
