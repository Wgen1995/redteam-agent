@echo off
rem Windows 包装：tanyin-selfcheck（与 py -3 cli\tanyin-selfcheck 等价；需 py launcher，
rem 无 launcher 时用: python "%~dp0tanyin-selfcheck" %*）
setlocal
set "HERE=%~dp0"
py -3 "%HERE%tanyin-selfcheck" %*
endlocal & exit /b %ERRORLEVEL%
