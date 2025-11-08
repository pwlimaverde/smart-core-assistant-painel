Param(
  [string]$RustTarget = "x86_64-pc-windows-msvc",
  [string]$Profile = "release"
)

# Caminhos (baseados na localização do script)
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../../"))
$RustLibRoot = Join-Path $RepoRoot "frontend/appflowy_custom/vendor/AppFlowy/frontend/rust-lib"
$DartFfiCrate = Join-Path $RustLibRoot "dart-ffi"
$BuiltDll = Join-Path $RustLibRoot "target/$RustTarget/$Profile/dart_ffi.dll"
$FlutterWindowsDir = Join-Path $RepoRoot "frontend/appflowy_custom/vendor/AppFlowy/frontend/appflowy_flutter/windows/flutter"
$DestDir = Join-Path $FlutterWindowsDir "dart_ffi"
$DestDll = Join-Path $DestDir "dart_ffi.dll"

Write-Host "Compilando crate dart-ffi para $RustTarget ($Profile)..."
# Configurar LIBCLANG_PATH (necessário para bindgen/librocksdb-sys)
$libClangCandidates = @(
  "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\VC\\Tools\\Llvm\\x64\\bin",
  "C:\\Program Files\\LLVM\\bin",
  "C:\\Program Files\\Microsoft Visual Studio\\2022\\BuildTools\\VC\\Tools\\Llvm\\bin"
)
foreach ($path in $libClangCandidates) {
  if (Test-Path (Join-Path $path "libclang.dll")) {
    $env:LIBCLANG_PATH = $path
    Write-Host "LIBCLANG_PATH definido para: $path"
    break
  }
}

Push-Location $RustLibRoot
cargo build -p dart-ffi --$Profile --target $RustTarget
if ($LASTEXITCODE -ne 0) {
  Write-Error "Falha ao compilar dart-ffi. Verifique o ambiente MSVC/CMake/SDK."
  Pop-Location
  exit 1
}
Pop-Location

if (!(Test-Path $BuiltDll)) {
  Write-Error "Arquivo não encontrado: $BuiltDll"
  exit 1
}

Write-Host "Criando diretório de destino: $DestDir"
New-Item -ItemType Directory -Path $DestDir -Force | Out-Null

Write-Host "Copiando DLL para $DestDll"
Copy-Item $BuiltDll $DestDll -Force

Write-Host "Concluído. dart_ffi.dll disponível em: $DestDll"