# Запуск: powershell.exe -NoProfile -File scripts/generate_dictation_audio.ps1
param([string]$VoiceName = 'Microsoft Irina', [ValidateSet('dictation_1', 'dictation_2', 'dictation_3', 'novgorod_dictation')][string]$TaskDirectory = 'dictation_1', [ValidateRange(0.5, 1.5)][double]$SpeechRate = 0.85)
$ErrorActionPreference = 'Stop'
if ($TaskDirectory -eq 'novgorod_dictation' -and -not $PSBoundParameters.ContainsKey('SpeechRate')) { $SpeechRate = 0.70 }
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$voiceType = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media.SpeechSynthesis, ContentType=WindowsRuntime]
$synth = New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer
$voice = $voiceType::AllVoices | Where-Object { $_.DisplayName -eq $VoiceName -and $_.Language -eq 'ru-RU' } | Select-Object -First 1
if (-not $voice) { throw 'Русский голос не найден.' }
$synth.Voice = $voice
$awaitMethod = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
} | Select-Object -First 1
$projectRoot = Split-Path $PSScriptRoot -Parent
$outputDir = Join-Path $projectRoot ("tasks/lesson3/{0}/audio" -f $TaskDirectory)
# Stage the whole set: a rejected phoneme must not overwrite existing recordings.
$stagingDir = Join-Path $outputDir ('.generation-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stagingDir | Out-Null
$words = Get-Content -LiteralPath (Join-Path $outputDir 'words.json') -Encoding UTF8 | ConvertFrom-Json
try {
    foreach ($item in $words) {
        $parts = @($item.pronunciation)
        if ($parts.Count -eq 0) { throw "Missing pronunciation for item $($item.id)" }
        $separator = if ($null -ne $item.separator) { [string]$item.separator } else { ' и ' }
        $expectedText = ($parts | ForEach-Object { $_.text }) -join $separator
        if ($expectedText -cne $item.noun) { throw "Pronunciation does not match item $($item.id)" }
        $fragments = foreach ($part in $parts) {
            if ([string]::IsNullOrWhiteSpace($part.ipa)) { throw "Missing IPA for $($part.text)" }
            # Microsoft may stress the preceding syllable unless ALL syllables are delimited.
            $syllables = ([string]$part.ipa).Split('.')
            foreach ($syllable in $syllables) {
                if ([regex]::Matches($syllable, '[aʌəɛiɪɨɔuoɐe]').Count -ne 1) {
                    throw "IPA must mark every syllable with a dot: $($part.text)"
                }
            }
            if ($syllables.Count -gt 1 -and ([regex]::Matches([string]$part.ipa, 'ˈ').Count -ne 1 -or [string]$part.ipa -notmatch '(^|\.)ˈ')) {
                throw "IPA stress must start exactly one syllable: $($part.text)"
            }
            $text = [System.Security.SecurityElement]::Escape([string]$part.text)
            $ipa = [System.Security.SecurityElement]::Escape([string]$part.ipa)
            '<phoneme alphabet="ipa" ph="' + $ipa + '">' + $text + '</phoneme>'
        }
        $rate = $SpeechRate.ToString('0.##', [System.Globalization.CultureInfo]::InvariantCulture)
        $ssml = '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ru-RU"><break time="500ms"/><prosody rate="' + $rate + '">' + ($fragments -join $separator) + [System.Security.SecurityElement]::Escape([string]$item.sentence_end) + '</prosody></speak>'
        # No plain-text fallback: it would silently discard the prescribed stress.
        $operation = $synth.SynthesizeSsmlToStreamAsync($ssml)
        $task = $awaitMethod.MakeGenericMethod([Windows.Media.SpeechSynthesis.SpeechSynthesisStream]).Invoke($null, @($operation))
        $task.Wait()
        $speech = $task.Result
        $stream = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($speech)
        $target = Join-Path $stagingDir ('{0:D2}.wav' -f [int]$item.id)
        $file = [System.IO.File]::Create($target)
        try { $stream.CopyTo($file) } finally { $file.Dispose(); $stream.Dispose(); $speech.Dispose() }
        Write-Output ('Generated {0:D2}.wav' -f [int]$item.id)
    }
    # Add cue before the existing SSML pause; speech bytes are preserved.
    & python (Join-Path $PSScriptRoot 'add_dictation_cue.py') $stagingDir
    if ($LASTEXITCODE -ne 0) { throw 'Failed to add the audio cue; existing recordings were preserved.' }
    foreach ($item in $words) {
        $name = '{0:D2}.wav' -f [int]$item.id
        Move-Item -LiteralPath (Join-Path $stagingDir $name) -Destination (Join-Path $outputDir $name) -Force
    }
} finally {
    $synth.Dispose()
    # This directory was created above, inside the selected task audio directory.
    Remove-Item -LiteralPath $stagingDir -Recurse -Force
}
