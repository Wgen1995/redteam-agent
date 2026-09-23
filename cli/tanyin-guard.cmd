@echo off
rem Windows 包装：tanyin-guard（与 py -3 cli\tanyin-guard 等价；需 py launcher，
rem 无 launcher 时用: python "%~dp0tanyin-guard" %*）
setlocal
set "HERE=%~dp0"
py -3 "%HERE%tanyin-guard" %*
endlocal & exit /b %ERRORLEVEL%
