@echo off
rem Windows 包装：tanyin-canary（与 py -3 cli\tanyin-canary 等价；需 py launcher，
rem 无 launcher 时用: python "%~dp0tanyin-canary" %*）
setlocal
set "HERE=%~dp0"
py -3 "%HERE%tanyin-canary" %*
endlocal & exit /b %ERRORLEVEL%
