# Comic Editor - MSI Kurulum Dosyasi Olusturucu
# Kullanim: PowerShell'de calistirin: .\build_msi.ps1
# Gereksinimler: Python 3.x, PyInstaller, .NET 8+

$ErrorActionPreference = "Stop"
$ProjectDir = $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Comic Editor - MSI Build Scripti" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $ProjectDir

# ---- Adim 1: WiX Toolset v4 kurulumu (yoksa) ----
Write-Host "[1/4] WiX Toolset kontrol ediliyor..." -ForegroundColor Yellow

# dotnet tools PATH'e ekle (her zaman)
$env:PATH = "$env:USERPROFILE\.dotnet\tools;$env:PATH"

$wixCmd = Get-Command wix -ErrorAction SilentlyContinue
if (-not $wixCmd) {
    Write-Host "     WiX bulunamadi, kuruluyor..." -ForegroundColor Gray
    dotnet tool install --global wix
    if ($LASTEXITCODE -ne 0) {
        Write-Host "HATA: WiX yuklenemedi." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "     WiX bulundu: $($wixCmd.Source)" -ForegroundColor Gray
}

Write-Host "     OK" -ForegroundColor Green

# ---- Adim 2: PyInstaller ile build ----
Write-Host ""
Write-Host "[2/4] PyInstaller build basliyor..." -ForegroundColor Yellow
Write-Host "      (Bu adim 5-15 dakika surebilir, lutfen bekleyin)" -ForegroundColor Gray

# Calisiyorsa uygulamayi kapat
Get-Process -Name "ComicEditor" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# cmd ile sil (PowerShell Remove-Item bazi DLL/PYD dosyalarini silemiyor)
if (Test-Path "dist\ComicEditor") {
    cmd /c "rmdir /s /q dist\ComicEditor"
}
if (Test-Path "build\ComicEditor") {
    cmd /c "rmdir /s /q build\ComicEditor"
}

python -m PyInstaller ComicEditor.spec --noconfirm
if ($LASTEXITCODE -ne 0) {
    Write-Host "HATA: PyInstaller build basarisiz!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "dist\ComicEditor\ComicEditor.exe")) {
    Write-Host "HATA: dist\ComicEditor\ComicEditor.exe olusturulamadi!" -ForegroundColor Red
    exit 1
}
Write-Host "     Build tamamlandi: dist\ComicEditor\" -ForegroundColor Green

# ---- Adim 3: Dosya listesi uretimi (Python ile) ----
Write-Host ""
Write-Host "[3/4] Dosya listesi olusturuluyor..." -ForegroundColor Yellow

python installer\generate_harvest.py "dist\ComicEditor" "installer\HarvestedFiles.wxs"

if ($LASTEXITCODE -ne 0) {
    Write-Host "HATA: Dosya listesi olusturulamadi!" -ForegroundColor Red
    exit 1
}
Write-Host "     Tamamlandi: installer\HarvestedFiles.wxs" -ForegroundColor Green

# ---- Adim 4: MSI derleme ----
Write-Host ""
Write-Host "[4/4] MSI derleniyor..." -ForegroundColor Yellow

if (Test-Path "dist\ComicEditor_Setup.msi") {
    Remove-Item "dist\ComicEditor_Setup.msi"
}

wix build `
    "installer\Product.wxs" `
    "installer\HarvestedFiles.wxs" `
    -d "SourceDir=dist\ComicEditor" `
    -d "ProjectDir=$ProjectDir\" `
    -out "dist\ComicEditor_Setup.msi"

if ($LASTEXITCODE -ne 0) {
    Write-Host "HATA: MSI derlemesi basarisiz!" -ForegroundColor Red
    exit 1
}

# ---- Tamamlandi ----
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  BASARILI!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
$msiSize = [math]::Round((Get-Item "dist\ComicEditor_Setup.msi").Length / 1MB, 1)
Write-Host "  MSI Dosyasi : dist\ComicEditor_Setup.msi ($msiSize MB)" -ForegroundColor White
Write-Host ""
Write-Host "  Kurulum ozellikleri:" -ForegroundColor White
Write-Host "   - Program Files\Comic Editor\ dizinine yukler" -ForegroundColor Gray
Write-Host "   - Masaustune kisayol olusturur" -ForegroundColor Gray
Write-Host "   - Baslat Menusu'ne kisayol olusturur" -ForegroundColor Gray
Write-Host "   - Program Ekle/Kaldir'a eklenir (kaldirma destegi)" -ForegroundColor Gray
Write-Host ""

# MSI'yi Explorer'da goster
$msiPath = Resolve-Path "dist\ComicEditor_Setup.msi"
explorer.exe /select,"$msiPath"
