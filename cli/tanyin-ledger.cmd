@echo off
rem Windows 包装：tanyin-ledger（与 py -3 cli\tanyin-ledger 等价；需 py launcher，
rem 无 launcher 时用: python "%~dp0tanyin-ledger" %*）
setlocal
set "HERE=%~dp0"
py -3 "%HERE%tanyin-ledger" %*
endlocal & exit /b %ERRORLEVEL%
