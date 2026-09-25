@echo off
rem Windows 包装：tanyin-evals（与 py -3 cli\tanyin-evals 等价；需 py launcher，
rem 无 launcher 时用: python "%~dp0tanyin-evals" %*）
setlocal
set "HERE=%~dp0"
py -3 "%HERE%tanyin-evals" %*
endlocal & exit /b %ERRORLEVEL%
