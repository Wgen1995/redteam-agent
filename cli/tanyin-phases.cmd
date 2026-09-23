@echo off
rem Windows 包装：tanyin-phases（与 py -3 cli\tanyin-phases 等价；需 py launcher，
rem 无 launcher 时用: python "%~dp0tanyin-phases" %*）
setlocal
set "HERE=%~dp0"
py -3 "%HERE%tanyin-phases" %*
endlocal & exit /b %ERRORLEVEL%
