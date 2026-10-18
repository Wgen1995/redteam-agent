// 出处:人工构造(依据 CWE-601 营销退订跳板,落地页可控)
@GetMapping("/unsubscribe")
public void unsubscribe(@RequestParam String cont, HttpServletResponse response) {
    response.setStatus(HttpServletResponse.SC_FOUND);
    response.addHeader("Location", marketingService.landingPage(cont));
}
