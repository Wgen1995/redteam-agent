// 出处: 安全链放行声明（S1 起步集——config-security CS-J04）
http.authorizeRequests()
  .antMatchers("/public/**").permitAll()
  .anyRequest().authenticated();
