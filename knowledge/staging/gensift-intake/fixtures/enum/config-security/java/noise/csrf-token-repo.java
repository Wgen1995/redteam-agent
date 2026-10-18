// 出处: CSRF 显式启用+token 仓库（noise——CS-J02 锚不出现，csrf() 在场但未 disable）
http.csrf(csrf -> csrf.csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse()));
