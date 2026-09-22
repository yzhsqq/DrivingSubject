$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$appDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$jarPath = Join-Path $appDirectory "driving-subject1.jar"
$cssPath = Join-Path $appDirectory "dify-assistant.css"
$jsPath = Join-Path $appDirectory "dify-assistant.js"
$utf8 = New-Object System.Text.UTF8Encoding($false)

$archive = [System.IO.Compression.ZipFile]::Open($jarPath, [System.IO.Compression.ZipArchiveMode]::Update)
try {
    $indexEntry = $archive.GetEntry("BOOT-INF/classes/static/index.html")
    if ($null -eq $indexEntry) {
        throw "Static index.html was not found in the application JAR."
    }

    $reader = New-Object System.IO.StreamReader($indexEntry.Open(), [System.Text.Encoding]::UTF8)
    try {
        $indexHtml = $reader.ReadToEnd()
    }
    finally {
        $reader.Dispose()
    }

    if ($indexHtml -notmatch "/dify-assistant\.js") {
        $injection = "    <link rel=`"stylesheet`" href=`"/dify-assistant.css`">`n    <script src=`"/dify-assistant.js`" defer></script>`n"
        $indexHtml = $indexHtml.Replace("  </head>", "$injection  </head>")
        $indexEntry.Delete()
        $indexEntry = $archive.CreateEntry("BOOT-INF/classes/static/index.html", [System.IO.Compression.CompressionLevel]::Optimal)
        $writer = New-Object System.IO.StreamWriter($indexEntry.Open(), $utf8)
        try {
            $writer.Write($indexHtml)
        }
        finally {
            $writer.Dispose()
        }
    }

    foreach ($asset in @(
        @{ Source = $cssPath; Entry = "BOOT-INF/classes/static/dify-assistant.css" },
        @{ Source = $jsPath; Entry = "BOOT-INF/classes/static/dify-assistant.js" }
    )) {
        $existingEntry = $archive.GetEntry($asset.Entry)
        if ($null -ne $existingEntry) {
            $existingEntry.Delete()
        }
        $newEntry = $archive.CreateEntry($asset.Entry, [System.IO.Compression.CompressionLevel]::Optimal)
        $sourceStream = [System.IO.File]::OpenRead($asset.Source)
        $targetStream = $newEntry.Open()
        try {
            $sourceStream.CopyTo($targetStream)
        }
        finally {
            $targetStream.Dispose()
            $sourceStream.Dispose()
        }
    }
}
finally {
    $archive.Dispose()
}

Write-Host "Dify assistant assets embedded successfully."
