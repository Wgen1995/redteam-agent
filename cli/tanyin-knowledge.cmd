@echo off
rem Windows 包装：tanyin-knowledge（与 py -3 cli\tanyin-knowledge 等价；需 py launcher，
rem 无 launcher 时用: python "%~dp0tanyin-knowledge" %*）
setlocal
set "HERE=%~dp0"
py -3 "%HERE%tanyin-knowledge" %*
endlocal & exit /b %ERRORLEVEL%
