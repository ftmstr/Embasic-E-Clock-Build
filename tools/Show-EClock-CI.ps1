#Requires -Version 5.1
<#
    Offline evidence-only E-Clock CI dashboard (not product completion).
    The JSON must be produced by diagnose_runner_startup.py.
    No network calls, private repository access or invented PASS states.
#>
param(
    [Parameter(Mandatory=$true)]
    [ValidateNotNullOrEmpty()]
    [string]$EvidencePath
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $EvidencePath -PathType Leaf)) {
    throw 'Evidence JSON does not exist.'
}
$e = Get-Content -LiteralPath $EvidencePath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($e.run_binding -eq 'VERIFIED_JOB_RUN_ID') {
    if ([int]$e.job_count -le 0 -or $e.jobs.Count -le 0) {
        throw 'Cannot verify job/run identity with no observed jobs.'
    }
    $seenJobIds = @{}
    foreach ($job in $e.jobs) {
        $idText = [string]$job.job_id
        if ($idText -cnotmatch '^[1-9][0-9]*$') {
            throw 'Missing or invalid job ID in diagnostic evidence.'
        }
        if ($seenJobIds.ContainsKey($idText)) {
            throw 'Duplicate job ID in diagnostic evidence.'
        }
        $seenJobIds[$idText] = $true
    }
    if ($seenJobIds.Count -ne [int]$e.job_count) {
        throw 'Job identity count does not match the reported job count.'
    }
} elseif ($e.run_binding -eq 'NO_JOB_EVIDENCE') {
    if ([int]$e.job_count -ne 0 -or $e.jobs.Count -ne 0) {
        throw 'No-job identity classification conflicts with supplied job records.'
    }
} else {
    throw 'Job/run identity evidence missing or inconsistent. Refusing mixed-run dashboard.'
}
if ($e.product_build_result -ne 'NOT_VERIFIED' -or $e.root_cause -ne 'UNDETERMINED') {
    throw 'Unexpected diagnostic contract. Refusing to render unsupported PASS.'
}
function Show-GateBar([string]$Label, $Item, [ConsoleColor]$Color) {
    $verified = [int]$Item.verified_ci_gates
    $total = [int]$Item.total_ci_gates
    if ($verified -ne 0 -or $total -ne 3 -or $Item.status -ne 'UNVERIFIED') {
        throw 'Only unverified 0/3 CI gate evidence is supported by this diagnostic.'
    }
    Write-Host ('{0,-12} [....................]  0/3 (0% CI evidence)' -f $Label) -ForegroundColor $Color
}
Write-Host ''
Write-Host ' EMBASIC E-CLOCK | CI KANIT PANOSU ' -BackgroundColor DarkBlue -ForegroundColor White
Write-Host (' Run: {0}   Sonuc: {1}' -f $e.run_id, $e.run_conclusion) -ForegroundColor Yellow
Write-Host (' HEAD: {0}' -f $e.head_sha) -ForegroundColor DarkGray
Write-Host (' Run status: {0}' -f $e.run_status) -ForegroundColor Yellow
if ($e.run_binding -eq 'NO_JOB_EVIDENCE') {
    Write-Host ' RUN ID MATCH: NOT ASSESSED (no jobs observed)' -ForegroundColor Yellow
} else {
    Write-Host ' RUN ID MATCH: VERIFIED (observed jobs bound to this run)' -ForegroundColor Green
    Write-Host (' Job ID AUDIT: {0} unique job ID(s)' -f $e.job_count) -ForegroundColor Cyan
}
foreach ($job in $e.jobs) {
    $color = if ($job.classification -eq 'NO_STEP_EVIDENCE' -or $job.classification -eq 'JOB_FAILURE_WITHOUT_FAILED_STEP') { 'Yellow' } elseif ($job.classification -eq 'SKIPPED') { 'DarkGray' } else { 'Cyan' }
    Write-Host (' #{0} {1}: {2} ({3} steps, {4} failed)' -f $job.job_id, $job.name, $job.classification, $job.observed_steps, $job.failed_steps) -ForegroundColor $color
    if ($job.classification -eq 'JOB_FAILURE_WITHOUT_FAILED_STEP') {
        Write-Host ' WARNING: no failing step in supplied job record; root cause unverified.' -ForegroundColor Yellow
    }
}
Write-Host (' Log evidence: {0}' -f $e.log_evidence) -ForegroundColor Yellow
Write-Host ' Kok neden: BELIRLENMEDI | Android derleme PASS: DOGRULANMADI' -ForegroundColor Red
Write-Host ''
Write-Host ' TELEFON / WEAR OS - AYRI CI DOGRULAMA GRAFIKLERI' -ForegroundColor White
Show-GateBar 'Telefon' $e.phone Cyan
Show-GateBar 'Wear OS' $e.wear Magenta
Write-Host ' 0% yalnizca bu CI kanit kapsamini belirtir, urun tamamlanma yuzdesi DEGILDIR.' -ForegroundColor DarkYellow
Write-Host ' NO-GO: test, lint, APK ve fiziksel cihaz PASS iddiasi YOK.' -ForegroundColor Red
