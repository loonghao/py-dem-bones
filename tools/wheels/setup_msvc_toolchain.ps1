$ErrorActionPreference = 'Stop'
$selection = Get-Content (Join-Path $PSScriptRoot msvc-kit.json) -Raw | ConvertFrom-Json
$native = switch ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()) {
    'X64' { 'x64' }; 'Arm64' { 'arm64' }; default { throw 'Unsupported Windows runner architecture' }
}
if ($env:WHEEL_ARCH -ne $native) { throw 'Use a native runner for the selected Python ABI' }
$exe = (Resolve-Path .toolchains/msvc-kit-source/target/release/msvc-kit.exe).Path
$root = Join-Path $env:RUNNER_TEMP py-dem-bones-msvc
$configPath = Join-Path $env:RUNNER_TEMP py-dem-bones-msvc-config.toml
$manifestRoot = Join-Path $env:RUNNER_TEMP py-dem-bones-msvc-manifests
@"
install_dir = "$($root.Replace('\', '/'))"
cache_dir = "$($manifestRoot.Replace('\', '/'))"
default_arch = "$native"
verify_hashes = true
parallel_downloads = 2
default_msvc_version = "$($selection.msvc_version)"
default_sdk_version = "$($selection.sdk_version)"
default_vs_channel = "17"
"@ | Set-Content -LiteralPath $configPath -Encoding utf8
$env:MSVC_KIT_CONFIG = $configPath
"MSVC_KIT_CONFIG=$configPath" >> $env:GITHUB_ENV
$selectors = @('--arch', $native, '--host-arch', $native,
    '--msvc-version', $selection.msvc_version, '--sdk-version', $selection.sdk_version)
& $exe download --target $root --vs-channel 17 --parallel-downloads 2 @selectors
if ($LASTEXITCODE -ne 0) { throw 'Verified toolchain acquisition failed' }
$lock = Join-Path $env:RUNNER_TEMP py-dem-bones-msvc.lock.json
& $exe lock --dir $root --output $lock @selectors
if ($LASTEXITCODE -ne 0) { throw 'Toolchain lock capture failed' }
$receipt = Get-Content -LiteralPath $lock -Raw | ConvertFrom-Json
if ($receipt.receipts.Count -ne 2 -or @($receipt.receipts | Where-Object { $_.payloads.Count -eq 0 }).Count) {
    throw 'Compiler and SDK require verified acquisition receipts'
}
foreach ($item in @{exe=$exe; root=$root; lock=$lock}.GetEnumerator()) {
    "$($item.Key)=$($item.Value)" >> $env:GITHUB_OUTPUT
}
