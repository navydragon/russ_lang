(function () {
  const production = "https://russ.emiit.ru";
  const local = "http://127.0.0.1:8888";
  window.ANALYZER_CONFIG = {
    apiBaseUrl: window.location.protocol === "https:" ? production : local,
    apiBaseUrlLocal: local,
  };
})();
