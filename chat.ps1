# CMD-клиент для того же Supabase, что и index.html.
$ErrorActionPreference = 'Stop'
$SupabaseUrl = 'https://vzbgaldclnsedbjjvykq.supabase.co'
$SupabaseKey = 'sb_publishable_R-bKrL5gZp0IsMRYgYKZSw_zD9EbHqx'
$Headers = @{ apikey = $SupabaseKey; Authorization = "Bearer $SupabaseKey"; Prefer = 'resolution=merge-duplicates' }
$OnlineMinutes = 10

function Test-Username([string]$Name) {
    return $Name -match '^[A-Za-z0-9_]{3,24}$'
}

function Update-Presence([string]$Name) {
    $payload = @{ id = $Name; name = $Name; last_seen = (Get-Date).ToUniversalTime().ToString('o') } |
        ConvertTo-Json -Compress
    Invoke-RestMethod -Method Post -Uri "$SupabaseUrl/rest/v1/presence?on_conflict=id" `
        -Headers $Headers -ContentType 'application/json' -Body $payload | Out-Null
}

function Get-Online-Users([string]$MyName) {
    $all = Invoke-RestMethod -Method Get `
        -Uri "$SupabaseUrl/rest/v1/presence?select=id,name,last_seen&order=last_seen.desc" `
        -Headers $Headers
    $now = (Get-Date).ToUniversalTime()
    return @($all | Where-Object {
        $_.id -ne $MyName -and (($now - [datetime]$_.last_seen).TotalMinutes -lt $OnlineMinutes)
    })
}

Clear-Host
Write-Host '=== BrawlfOnline: CMD чат ===' -ForegroundColor Cyan
do {
    $Me = (Read-Host 'Ваш username (например user456)').Trim()
    if (-not (Test-Username $Me)) {
        Write-Host 'Ошибка: 3-24 символа A-Z, цифры или _. Пробелы нельзя.' -ForegroundColor Red
    }
} while (-not (Test-Username $Me))

try {
    Update-Presence $Me
    Write-Host "Вы вошли как $Me" -ForegroundColor Green
} catch {
    Write-Host "Нет связи с Supabase: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

while ($true) {
    try {
        Update-Presence $Me
        $Users = Get-Online-Users $Me
    } catch {
        Write-Host "Ошибка подключения: $($_.Exception.Message)" -ForegroundColor Red
        Start-Sleep -Seconds 3
        continue
    }

    Clear-Host
    Write-Host "Вы: $Me" -ForegroundColor Cyan
    Write-Host ''
    Write-Host 'Пользователи онлайн:'
    if ($Users.Count -eq 0) {
        Write-Host 'Никого нет. Нажмите Enter, чтобы обновить.' -ForegroundColor Yellow
        Read-Host | Out-Null
        continue
    }

    for ($i = 0; $i -lt $Users.Count; $i++) {
        Write-Host "$($i + 1). $($Users[$i].name)"
    }
    [int]$choice = 0
    $choiceText = Read-Host 'Выбор (0 - выход)'
    if ($choiceText -eq '0') { break }
    if (-not [int]::TryParse($choiceText, [ref]$choice) -or $choice -lt 1 -or $choice -gt $Users.Count) {
        Write-Host 'Неверный номер.' -ForegroundColor Red
        Start-Sleep -Seconds 1
        continue
    }

    $Recipient = $Users[$choice - 1]
    $Text = (Read-Host "Напишите, что хотите отправить $($Recipient.name)").Trim()
    if (-not $Text) { continue }
    if ($Text.Length -gt 1000) {
        Write-Host 'Максимум 1000 символов.' -ForegroundColor Red
        continue
    }

    try {
        $message = @{ sender_id = $Me; receiver_id = $Recipient.id; content = $Text } | ConvertTo-Json -Compress
        Invoke-RestMethod -Method Post -Uri "$SupabaseUrl/rest/v1/messages" `
            -Headers $Headers -ContentType 'application/json' -Body $message | Out-Null
        Write-Host 'success' -ForegroundColor Green
        Start-Sleep -Seconds 1
    } catch {
        Write-Host "Ошибка отправки: $($_.Exception.Message)" -ForegroundColor Red
        Start-Sleep -Seconds 2
    }
}
