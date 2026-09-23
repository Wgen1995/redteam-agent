@echo off
rem Windows 包装：tanyin-budgetctl（与 py -3 cli\tanyin-budgetctl 等价；需 py launcher，
rem 无 launcher 时用: python "%~dp0tanyin-budgetctl" %*）
setlocal
set "HERE=%~dp0"
py -3 "%HERE%tanyin-budgetctl" %*
endlocal & exit /b %ERRORLEVEL%
